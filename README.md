# Print Buddy Streamer

Camera streaming for Printer Buddy. Runs on whatever machine the camera is plugged into (a printer, a Pi, a server).
Installed and updated by Printer Buddy's `install.sh`, which also installs the backend for the chosen tier.

## Tiers

| Tier | Cameras | Streams | Backend |
|---|---|---|---|
| **light** | USB cameras | MJPEG + snapshot, one port per camera | mjpg-streamer |
| **basic** | USB cameras | MJPEG + snapshot, one port per camera | ustreamer |
| **advanced** | USB, Pi and network (RTSP / HTTP) cameras | WebRTC, RTSP, MJPEG + snapshot | ustreamer + go2rtc |

## Run

```bash
python3 -m streamer --list                      # cameras found on this machine
python3 -m streamer -c streamer.conf            # stream (stdlib only, Python 3.9+)
```

Copy `streamer.conf.example` to `streamer.conf` and set the tier. With no `[cam]` sections every camera found is
streamed. Cameras are added to Moonraker's webcam list (so they show in Fluidd, Mainsail and Printer Buddy) when
Moonraker is running on the same machine.

## Needs

- light: `mjpg_streamer` (prebuilt, from this repo's `mjpg-streamer` release), `libjpeg62-turbo`, `v4l2-ctl` (v4l-utils)
- basic: `ustreamer`, `v4l2-ctl` (v4l-utils)
- advanced: `ustreamer`, `v4l2-ctl`, `go2rtc`, `ffmpeg`; Pi cameras also `libcamerify` (libcamera-tools) and `rpicam-vid`

## URLs

| Tier | Stream | Snapshot |
|---|---|---|
| light | `http://<host>:<port>/?action=stream` | `http://<host>:<port>/?action=snapshot` |
| basic | `http://<host>:<port>/stream` | `http://<host>:<port>/snapshot` |
| advanced | `http://<host>:1984/api/webrtc?src=<name>` (WebRTC), `rtsp://<host>:8554/<name>` | `http://<host>:1984/api/frame.jpeg?src=<name>` |
