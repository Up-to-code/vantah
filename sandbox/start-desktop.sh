#!/bin/sh
set -eu
export XDG_RUNTIME_DIR=/tmp/runtime-sandbox
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
width=${VANTAH_WIDTH:-1280}
height=${VANTAH_HEIGHT:-800}
if [ -z "${VANTAH_WIDTH:-}${VANTAH_HEIGHT:-}" ] && [ -r /home/sandbox/.config/vantah/display-size ]; then
  read -r width height < /home/sandbox/.config/vantah/display-size
fi
case "$width:$height" in *[!0-9:]*|:*|*:) echo 'Invalid desktop size' >&2; exit 1;; esac
[ "$width" -ge 480 ] && [ "$width" -le 4096 ] && [ "$height" -ge 360 ] && [ "$height" -le 4096 ]
if DISPLAY=:1 timeout 1 xprop -root _NET_SUPPORTING_WM_CHECK >/dev/null 2>&1; then
  echo 'Display :1 is already running' >&2
  exit 1
fi
# A container restart can leave sockets and a lock whose PID has been reused.
rm -f /tmp/.X1-lock /tmp/.X11-unix/X1
Xvfb :1 -screen 0 "${width}x${height}x24" +extension GLX -noreset -nolisten tcp > /tmp/vnc.log 2>&1 &
vnc_pid=$!
trap 'kill "$vnc_pid" "${desktop_pid:-}" 2>/dev/null || true' EXIT INT TERM
sleep 2
sh /home/sandbox/.local/share/alpine-shell/sandbox/start-kwin.sh > /tmp/desktop.log 2>&1 &
desktop_pid=$!
x11vnc -display :1 -localhost -nopw -forever -shared -rfbport 5901 -noxdamage > /tmp/vantah-vnc.log 2>&1 &
websockify --web=/usr/share/novnc 6080 localhost:5901
