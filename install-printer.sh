#!/usr/bin/env bash
#   curl -fsSL https://raw.githubusercontent.com/sterling5241/print-buddy-streamer/main/install-printer.sh | bash -s -- light
#   ... | bash -s -- basic
#   ... | bash -s -- advanced rtsp://192.168.0.50/stream
set -euo pipefail
REPO=https://github.com/sterling5241/print-buddy-streamer.git
MJPG_URL=https://github.com/sterling5241/print-buddy-streamer/releases/download/mjpg-streamer
MJPG_DIR=/usr/local/lib/print-buddy-streamer/mjpg-streamer
DIR="$HOME/print-buddy-streamer"
DATA="$HOME/printer_data"
CONF="$DATA/config/print-buddy-streamer.conf"
SERVICE=printer-buddy-streamer
tier="${1:-basic}"; shift || true

case "$tier" in light|basic|advanced) ;; *) echo "usage: install-printer.sh light | basic | advanced [camera address ...]"; exit 1 ;; esac
[ "$#" -eq 0 ] || [ "$tier" = advanced ] || { echo "Network cameras need the advanced level."; exit 1; }
command -v apt-get >/dev/null || { echo "This printer has no apt-get, so the streamer can't be installed here. Use the printer's own camera service."; exit 1; }
[ -d "$DATA/config" ] || { echo "No ~/printer_data/config here. Run this on the printer that runs Moonraker."; exit 1; }
python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))' || { echo "The streamer needs Python 3.9 or newer."; exit 1; }

echo "Installing packages (sudo may ask for your password)..."
pkgs="git v4l-utils"
case "$tier" in
  light) pkgs="$pkgs libjpeg62-turbo" ;;
  basic) pkgs="$pkgs ustreamer" ;;
  advanced) pkgs="$pkgs ustreamer libcamera-tools ffmpeg" ;;
esac
sudo apt-get update -q
# shellcheck disable=SC2086
sudo apt-get install -y -q $pkgs

if [ "$tier" = light ]; then
  case "$(uname -m)" in
    x86_64|amd64) a=amd64 ;; aarch64|arm64) a=arm64 ;; armv7l|armv6l) a=armhf ;;
    *) echo "no mjpg-streamer build for $(uname -m)"; exit 1 ;;
  esac
  tmp="$(mktemp)"
  curl -fsSL -o "$tmp" "$MJPG_URL/mjpg-streamer-$a.tar.gz"
  sudo mkdir -p "$MJPG_DIR"
  sudo tar -xzf "$tmp" -C "$MJPG_DIR" --strip-components=1
  rm -f "$tmp"
fi

if [ "$tier" = advanced ] && ! command -v go2rtc >/dev/null; then
  case "$(uname -m)" in
    x86_64|amd64) a=amd64 ;; aarch64|arm64) a=arm64 ;; armv7l) a=arm ;; armv6l) a=armv6 ;;
    *) echo "no go2rtc build for $(uname -m)"; exit 1 ;;
  esac
  sudo curl -fsSL -o /usr/local/bin/go2rtc "https://github.com/AlexxIT/go2rtc/releases/latest/download/go2rtc_linux_$a"
  sudo chmod 755 /usr/local/bin/go2rtc
fi

if [ -d "$DIR/.git" ]; then git -C "$DIR" pull -q --ff-only; else git clone -q "$REPO" "$DIR"; fi

if [ -f "$CONF" ]; then
  sed -i "s/^tier:.*/tier: $tier/" "$CONF"
else
  sed "s/^tier:.*/tier: $tier/" "$DIR/streamer.conf.example" | sed '/^\[cam /,$d' > "$CONF"
  n=0
  for addr in "$@"; do
    n=$((n + 1))
    printf '\n[cam %d]\nname: cam%d\ndevice: %s\nport: %d\n' "$n" "$n" "$addr" $((8080 + n)) >> "$CONF"
  done
fi

sudo tee "/etc/systemd/system/$SERVICE.service" >/dev/null <<UNIT
[Unit]
Description=Printer Buddy camera streamer
After=network-online.target moonraker.service
Wants=network-online.target

[Service]
User=$USER
SupplementaryGroups=video
WorkingDirectory=$DIR
ExecStart=$(command -v python3) -m streamer -c $CONF
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable -q --now "$SERVICE"
sudo systemctl restart "$SERVICE"

asvc="$DATA/moonraker.asvc"
[ -f "$asvc" ] && ! grep -qx "$SERVICE" "$asvc" && echo "$SERVICE" >> "$asvc"
mconf="$DATA/config/moonraker.conf"
if [ -f "$mconf" ] && ! grep -q "^\[update_manager print-buddy-streamer\]" "$mconf"; then
  cat >> "$mconf" <<CONF

[update_manager print-buddy-streamer]
type: git_repo
path: $DIR
origin: $REPO
primary_branch: main
managed_services: $SERVICE
CONF
  sudo systemctl restart moonraker
fi

echo "Done. The streamer is running and its cameras are added to Moonraker; update it from Fluidd / Mainsail."
