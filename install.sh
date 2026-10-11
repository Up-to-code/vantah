#!/bin/sh
# Install into the existing sandbox without rebuilding or deleting it.
set -eu
cd "$(dirname "$0")"
container="${1:-alpine-gui}"
docker exec -u 0 "$container" apk add --no-cache py3-gobject3 py3-cairo libwnck3 xprop tzdata picom
docker exec "$container" mkdir -p /home/sandbox/.local/share/alpine-shell /home/sandbox/.config/autostart
docker cp . "$container":/home/sandbox/.local/share/alpine-shell/
docker cp alpine-shell.desktop "$container":/home/sandbox/.config/autostart/alpine-shell.desktop
docker cp fix-vnc.py "$container":/tmp/alpine-shell-fix-vnc.py
docker exec -u 0 "$container" python3 /tmp/alpine-shell-fix-vnc.py
docker exec "$container" sh -c '
  export DBUS_SESSION_BUS_ADDRESS=$(tr "\000" "\n" < "/proc/$(pgrep -x xfce4-session | head -n 1)/environ" | sed -n "s/^DBUS_SESSION_BUS_ADDRESS=//p")
  xfconf-query -c xfce4-keyboard-shortcuts -p "/commands/custom/<Super>space" -n -t string -s "sh /home/sandbox/.local/share/alpine-shell/run-shell.sh --search"
  if [ -f /tmp/alpine-shell-1000.pid ]; then
    kill -TERM "$(cat /tmp/alpine-shell-1000.pid)"
    for attempt in 1 2 3 4 5 6 7 8 9 10; do
      [ ! -f /tmp/alpine-shell-1000.pid ] && break
      sleep 0.2
    done
  fi
'
docker exec -d "$container" sh -c 'sh /home/sandbox/.local/share/alpine-shell/run-shell.sh > /tmp/alpine-shell.log 2>&1'
