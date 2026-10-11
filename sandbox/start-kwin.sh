#!/bin/sh
set -eu
root=/home/sandbox/.local/share/alpine-shell
export DISPLAY="${DISPLAY:-:1}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp/runtime-sandbox}"
mkdir -p "$XDG_RUNTIME_DIR" /home/sandbox/.config
chmod 700 "$XDG_RUNTIME_DIR"
if [ ! -f /home/sandbox/.config/kwinrc ]; then
  cp "$root/kwinrc" /home/sandbox/.config/kwinrc
fi
export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe
export LP_NUM_THREADS=2
export QT_QPA_PLATFORM=xcb
export QT_QUICK_BACKEND=software
export KWIN_OPENGL_INTERFACE=glx
exec dbus-run-session -- "$root/sandbox/kwin-inner.sh"
