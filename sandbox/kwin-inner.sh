#!/bin/sh
set -eu
export VANTAH_COMPOSITOR=kwin
export GDK_BACKEND=x11
export TZ=Africa/Cairo
root=/home/sandbox/.local/share/alpine-shell
umask 077
printf 'export DISPLAY=%s\nexport DBUS_SESSION_BUS_ADDRESS=%s\nexport XDG_RUNTIME_DIR=%s\nexport VANTAH_COMPOSITOR=kwin\nexport GDK_BACKEND=x11\n' \
  "$DISPLAY" "$DBUS_SESSION_BUS_ADDRESS" "$XDG_RUNTIME_DIR" > /tmp/vantah-session.env
kwin_x11 --replace > /tmp/vantah-kwin.log 2>&1 &
wm_pid=$!
trap 'kill "$wm_pid" "${desktop_pid:-}" 2>/dev/null || true' EXIT INT TERM
xfconf-query -c xfce4-keyboard-shortcuts -p '/commands/custom/<Super>space' -n -t string \
  -s "sh $root/run-shell.sh --search"
xfsettingsd --replace > /tmp/vantah-settings.log 2>&1 &
for monitor in $(xrandr --query | awk '$2 == "connected" {print $1}') 0; do
for workspace in 0 1 2 3; do
  base="/backdrop/screen0/monitor$monitor/workspace$workspace"
  xfconf-query -c xfce4-desktop -p "$base/last-image" -n -t string -s "$root/assets/wallpaper.png"
  xfconf-query -c xfce4-desktop -p "$base/image-style" -n -t int -s 5
done
done
xfdesktop --disable-wm-check > /tmp/vantah-desktop.log 2>&1 &
desktop_pid=$!
python3 "$root/shell.py"
