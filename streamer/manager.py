import logging
import os
import signal
import subprocess
import threading
import time

from . import backends, detect, moonraker
from .config import Cam

log = logging.getLogger("streamer")
BACKOFF = (2, 5, 10, 30)


def resolve(cfg):
    """[(cam, device)] for the tier: configured cams with 'auto' devices filled in, or one per detected camera."""
    usb, pi = detect.usb_cameras(), detect.libcamera_count()
    free = list(usb) + (["libcamera"] if pi else [])
    cams = cfg.cams or [Cam(name=f"cam{i + 1}", port=8080 + i) for i in range(len(free))]
    out = []
    for cam in cams:
        device = cam.device
        if device == "auto":
            if not free:
                log.warning("%s: no free camera found, skipped", cam.name)
                continue
            device = free.pop(0)
        elif device in free:
            free.remove(device)
        if device.startswith(("rtsp://", "rtsps://", "http://", "https://")) and cfg.tier != "full":
            log.warning("%s: network cameras need the full tier, skipped", cam.name)
            continue
        out.append((cam, device))
    if cfg.tier == "light":
        out = out[:1]
    return out


def jobs(cfg, config_dir):
    host = detect.local_ip() if cfg.host == "auto" else cfg.host
    cams = resolve(cfg)
    if not cams:
        return []
    if cfg.tier == "full":
        return [backends.go2rtc(cams, host, os.path.join(config_dir, "go2rtc.yaml"))]
    return [backends.ustreamer(cam, device, host) for cam, device in cams]


class Supervisor:
    def __init__(self, cfg, config_dir):
        self.cfg, self.config_dir = cfg, config_dir
        self.stop = threading.Event()

    def _run(self, job):
        fails = 0
        while not self.stop.is_set():
            log.info("%s: starting %s", job.name, " ".join(job.cmd))
            started = time.monotonic()
            try:
                proc = subprocess.Popen(job.cmd)
            except OSError as ex:
                log.error("%s: can't start %s (%s)", job.name, job.cmd[0], ex)
                proc = None
            while proc and proc.poll() is None and not self.stop.is_set():
                time.sleep(1)
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                return
            # a run that lasted a minute counts as healthy, so the wait goes back to the shortest
            fails = 0 if time.monotonic() - started > 60 else fails + 1
            wait = BACKOFF[min(fails, len(BACKOFF) - 1)]
            log.warning("%s: stopped (exit %s), restarting in %ss", job.name, proc.returncode if proc else "-", wait)
            self.stop.wait(wait)

    def _register(self, webcams):
        while not self.stop.is_set() and not moonraker.register(self.cfg.moonraker, webcams):
            self.stop.wait(30)

    def run(self):
        todo = jobs(self.cfg, self.config_dir)
        if not todo:
            log.error("nothing to stream: no cameras found or configured (run with --list to see what's detected)")
            return 1
        signal.signal(signal.SIGTERM, lambda *_: self.stop.set())
        threads = [threading.Thread(target=self._run, args=(j,), daemon=True) for j in todo]
        if self.cfg.moonraker:
            threads.append(threading.Thread(target=self._register, args=([w for j in todo for w in j.webcams],), daemon=True))
        for t in threads:
            t.start()
        try:
            while not self.stop.is_set():
                self.stop.wait(1)
        except KeyboardInterrupt:
            self.stop.set()
        for t in threads:
            t.join(15)
        return 0
