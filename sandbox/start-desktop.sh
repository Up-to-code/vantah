#!/bin/sh
set -eu
export XDG_RUNTIME_DIR=/tmp/runtime-sandbox
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
Xvnc :1 -geometry 1440x900 -depth 24 -localhost yes -SecurityTypes None -rfbport 5901 -AlwaysShared > /tmp/vnc.log 2>&1 &
vnc_pid=$!
trap 'kill "$vnc_pid" "${desktop_pid:-}" 2>/dev/null || true' EXIT INT TERM
sleep 2
dbus-run-session -- sh -c '
  for workspace in 0 1 2 3; do
    base="/backdrop/screen0/monitorVNC-0/workspace$workspace"
    xfconf-query -c xfce4-desktop -p "$base/last-image" -n -t string -s /home/sandbox/.local/share/alpine-shell/assets/wallpaper.png
    xfconf-query -c xfce4-desktop -p "$base/image-style" -n -t int -s 5
  done
  exec xfce4-session
' > /tmp/desktop.log 2>&1 &
desktop_pid=$!
websockify --web=/usr/share/novnc 6080 localhost:5901
