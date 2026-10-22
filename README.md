# Print Buddy Streamer

Camera streaming for Printer Buddy. Runs on whatever machine the camera is plugged into (a printer, a Pi, a server).
Installed and updated by Printer Buddy's `install.sh`, which also installs the backend for the chosen tier.

## Tiers

| Tier | Cameras | Streams | Backend |
|---|---|---|---|
| **light** | 1 USB or Pi camera | MJPEG + snapshot | ustreamer |
| **basic** | every USB + Pi camera | MJPEG + snapshot, one port per camera | ustreamer |
| **full** | USB, Pi and network (RTSP / HTTP) cameras | WebRTC, RTSP, MJPEG + snapshot | go2rtc |

## Run

```bash
python3 -m streamer --list                      # cameras found on this machine
python3 -m streamer -c streamer.conf            # stream (stdlib only, Python 3.9+)
```

Copy `streamer.conf.example` to `streamer.conf` and set the tier. With no `[cam]` sections every camera found is
streamed. Cameras are added to Moonraker's webcam list (so they show in Fluidd, Mainsail and Printer Buddy) when
Moonraker is running on the same machine.

## Needs

- light / basic: `ustreamer`, `v4l2-ctl` (v4l-utils); Pi cameras also `libcamerify` (libcamera-tools)
- full: `go2rtc`, `ffmpeg`; Pi cameras also `rpicam-vid`

## URLs

| Tier | Stream | Snapshot |
|---|---|---|
| light / basic | `http://<host>:<port>/stream` | `http://<host>:<port>/snapshot` |
| full | `http://<host>:1984/api/webrtc?src=<name>` (WebRTC), `rtsp://<host>:8554/<name>` | `http://<host>:1984/api/frame.jpeg?src=<name>` |
