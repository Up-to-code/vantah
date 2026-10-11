#!/bin/sh
# Upgrade the existing Alpine sandbox to KWin Glass without deleting its files.
set -eu
cd "$(dirname "$0")"
container="${1:-alpine-gui}"
revision=0ae94cf5e709a894a9f1f54544cb17deb7f77d58
kwin_revision=f53992fd00bd446c478adda5d4cf8b588cb32b75
docker exec -u 0 "$container" apk add --no-cache py3-gobject3 py3-cairo gvfs libwnck3 xprop tzdata \
  xvfb x11vnc kwin breeze breeze-cursors mesa-dri-gallium mesa-gl qt6-qtsensors
docker cp gtk-menus.css "$container":/tmp/vantah-gtk-menus.css
docker cp sandbox/install-appearance.sh "$container":/tmp/vantah-install-appearance.sh
docker exec -u 0 "$container" sh /tmp/vantah-install-appearance.sh
installed=$(docker exec "$container" cat /usr/share/doc/vantah-glass/REVISION 2>/dev/null || true)
installed_kwin=$(docker exec "$container" cat /usr/share/doc/vantah-glass/KWIN_REVISION 2>/dev/null || true)
if [ "$installed" != "$revision" ] || [ "$installed_kwin" != "$kwin_revision" ]; then
  printf 'Building KWin and Glass. This requires several GB of free disk space.\n'
  docker exec -u 0 "$container" mkdir -p /tmp/vantah-build
  docker cp sandbox/build-glass.sh "$container":/tmp/vantah-build/
  docker cp sandbox/patch-kwin-x11.py "$container":/tmp/vantah-build/
  docker exec -u 0 "$container" sh /tmp/vantah-build/build-glass.sh
fi
corners_revision=c1178d94ff2ec0db8d4d9a9782a3eb06aec13ce6
installed_corners=$(docker exec "$container" cat /usr/share/doc/vantah-corners/REVISION 2>/dev/null || true)
if [ "$installed_corners" != "$corners_revision" ]; then
  docker cp sandbox/build-rounded-corners.sh "$container":/tmp/vantah-build-rounded-corners.sh
  docker exec -u 0 "$container" sh /tmp/vantah-build-rounded-corners.sh
fi
docker exec -u 1000 "$container" mkdir -p /home/sandbox/.local/share/alpine-shell /home/sandbox/.config/autostart
# Explicit archive ownership also handles host UID differences on macOS.
if tar --version 2>/dev/null | sed -n '1p' | grep -q bsdtar; then
  COPYFILE_DISABLE=1 tar --no-xattrs --no-acls --no-fflags --uid 1000 --gid 1000 --exclude .git -cf - . | docker cp -a - "$container":/home/sandbox/.local/share/alpine-shell/
else
  tar --owner=1000 --group=1000 --exclude .git -cf - . | docker cp -a - "$container":/home/sandbox/.local/share/alpine-shell/
fi
docker exec -u 1000 "$container" sh -c '
  root=/home/sandbox/.local/share/alpine-shell
  cp "$root/alpine-shell.desktop" /home/sandbox/.config/autostart/alpine-shell.desktop
  cp "$root/kwinrc" /home/sandbox/.config/kwinrc
  python3 "$root/sandbox/install-menu-overlay.py"
'
docker cp fix-vnc.py "$container":/tmp/vantah-fix-vnc.py
docker cp sandbox/start-desktop.sh "$container":/tmp/vantah-start-desktop
docker exec -u 0 "$container" sh -c '
  python3 /tmp/vantah-fix-vnc.py
  rm -f /usr/local/bin/start-desktop
  cp /tmp/vantah-start-desktop /usr/local/bin/start-desktop
  chmod +x /usr/local/bin/start-desktop
'
docker restart "$container" >/dev/null
printf 'vAntah now starts with KWin Glass. Reload its noVNC browser.\n'
