import glob
import os
import re
import shutil
import socket
import subprocess


def usb_cameras():
    # by-id names stay the same across reboots and replugs; index0 is the capture node
    return sorted(glob.glob("/dev/v4l/by-id/*-video-index0"))


def libcamera_count():
    tool = shutil.which("rpicam-hello") or shutil.which("libcamera-hello")
    if not tool:
        return 0
    try:
        out = subprocess.run([tool, "--list-cameras"], capture_output=True, text=True, timeout=15).stdout
    except (OSError, subprocess.TimeoutExpired):
        return 0
    return len(re.findall(r"^\s*\d+\s*:", out, re.M))


def has_mjpeg(device):
    if not shutil.which("v4l2-ctl"):
        return False
    try:
        out = subprocess.run(["v4l2-ctl", "-d", device, "--list-formats"], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.TimeoutExpired):
        return False
    return "MJPG" in out


def local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def describe():
    lines = [f"USB: {d} -> {os.path.realpath(d)}{'  (MJPEG)' if has_mjpeg(d) else ''}" for d in usb_cameras()]
    n = libcamera_count()
    if n:
        lines.append(f"Pi camera (libcamera): {n}")
    return lines or ["no cameras found"]
