import os
import shlex
from dataclasses import dataclass

from . import detect

GO2RTC_API = 1984
GO2RTC_RTSP = 8554
GO2RTC_WEBRTC = 8555
MJPG_DIR = "/usr/local/lib/print-buddy-streamer/mjpg-streamer"


@dataclass
class Job:
    name: str
    cmd: list
    webcams: list   # [(name, service, stream_url, snapshot_url, fps)]


def ustreamer(cam, device, host):
    cmd = ["ustreamer", "--host", "0.0.0.0", "--port", str(cam.port),
           "--resolution", cam.resolution, "--desired-fps", str(cam.fps)]
    if device == "libcamera":
        cmd = ["libcamerify"] + cmd + ["--device", "/dev/video0"]
    else:
        cmd += ["--device", device]
        if detect.has_mjpeg(device):
            cmd += ["--format", "MJPEG", "--encoder", "HW"]
    cmd += shlex.split(cam.flags)
    base = f"http://{host}:{cam.port}"
    return Job(cam.name, cmd, [(cam.name, "mjpegstreamer-adaptive", f"{base}/stream", f"{base}/snapshot", cam.fps)])


def mjpg_streamer(cam, device, host):
    src = f"input_uvc.so -d {device} -r {cam.resolution} -f {cam.fps}"
    if not detect.has_mjpeg(device):
        src += " -y"
    if cam.flags:
        src += f" {cam.flags}"
    # TODO: check the input_uvc flags against a real camera
    cmd = ["env", f"LD_LIBRARY_PATH={MJPG_DIR}", os.path.join(MJPG_DIR, "mjpg_streamer"), "-i", src,
           "-o", f"output_http.so -p {cam.port} -w {os.path.join(MJPG_DIR, 'www')}"]
    base = f"http://{host}:{cam.port}"
    return Job(cam.name, cmd, [(cam.name, "mjpegstreamer", f"{base}/?action=stream", f"{base}/?action=snapshot", cam.fps)])


def is_network(device):
    return device.startswith(("rtsp://", "rtsps://", "http://", "https://"))


def go2rtc_source(cam, device):
    if is_network(device):
        return device
    # local cameras are read from their ustreamer, not the device
    return f"ffmpeg:http://127.0.0.1:{cam.port}/stream#video=h264"


def go2rtc(cams, host, config_path):
    lines = [f'api:\n  listen: ":{GO2RTC_API}"', f'rtsp:\n  listen: ":{GO2RTC_RTSP}"',
             f'webrtc:\n  listen: ":{GO2RTC_WEBRTC}"', "streams:"]
    webcams = []
    for cam, device in cams:
        lines.append(f"  {cam.name}: {go2rtc_source(cam, device)}")
        if not is_network(device):
            continue
        base = f"http://{host}:{GO2RTC_API}/api"
        webcams.append((cam.name, "webrtc-go2rtc", f"{base}/webrtc?src={cam.name}", f"{base}/frame.jpeg?src={cam.name}", cam.fps))
    with open(config_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return Job("go2rtc", ["go2rtc", "-config", config_path], webcams)
