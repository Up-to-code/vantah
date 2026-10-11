#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ "${1:-}" = "--search" ]; then
  if [ -f "/tmp/alpine-shell-$(id -u).pid" ]; then
    kill -USR1 "$(cat "/tmp/alpine-shell-$(id -u).pid")"
  fi
  exit 0
fi
export DISPLAY="${DISPLAY:-:1}"
if [ -f /tmp/vantah-session.env ] && pgrep -x kwin_x11 >/dev/null; then
  . /tmp/vantah-session.env
fi
if [ -z "${DBUS_SESSION_BUS_ADDRESS:-}" ]; then
  session_pid=$(pgrep -x xfce4-session | head -n 1)
  DBUS_SESSION_BUS_ADDRESS=$(tr '\000' '\n' < "/proc/$session_pid/environ" | sed -n 's/^DBUS_SESSION_BUS_ADDRESS=//p')
  export DBUS_SESSION_BUS_ADDRESS
fi
if pgrep -x xfce4-panel >/dev/null; then
  timeout 3 xfce4-panel --quit 2>/dev/null || true
fi
export TZ=Africa/Cairo
exec python3 shell.py
