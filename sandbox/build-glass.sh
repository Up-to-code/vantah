#!/bin/sh
# Build the separately licensed upstream KWin Glass plugin at a fixed revision.
set -eu
revision=0ae94cf5e709a894a9f1f54544cb17deb7f77d58
kwin_revision=f53992fd00bd446c478adda5d4cf8b588cb32b75
script_dir=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
build_root="${VANTAH_GLASS_BUILD_ROOT:-/tmp/vantah-glass-build}"
apk add --no-cache python3 kwin kwin-dev cmake extra-cmake-modules build-base \
  qt6-qttools-dev kcmutils-dev kconfigwidgets-dev kcrash-dev kglobalaccel-dev \
  ki18n-dev kservice-dev knotifications-dev kio-dev kdecoration-dev libepoxy-dev \
  kglobalacceld-dev libdisplay-info-dev
mkdir -p "$build_root/source" "$build_root/kwin-source"
wget -qO "$build_root/kwin.tar.gz" "https://invent.kde.org/plasma/kwin-x11/-/archive/$kwin_revision/kwin-x11-$kwin_revision.tar.gz"
tar -xzf "$build_root/kwin.tar.gz" -C "$build_root/kwin-source" --strip-components=1
python3 "$script_dir/patch-kwin-x11.py" "$build_root/kwin-source"
cmake -S "$build_root/kwin-source" -B "$build_root/kwin-build" \
  -DCMAKE_INSTALL_PREFIX=/usr -DKDE_INSTALL_LIBDIR=lib -DKDE_INSTALL_LIBEXECDIR=libexec -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS_RELEASE="-O1 -DNDEBUG" -DBUILD_TESTING=OFF \
  -DKWIN_BUILD_KCMS=OFF -DKWIN_BUILD_SCREENLOCKER=OFF -DKWIN_BUILD_RUNNERS=OFF
cmake --build "$build_root/kwin-build" -j1
cmake --install "$build_root/kwin-build"
wget -qO "$build_root/source.tar.gz" "https://github.com/4v3ngR/kwin-effects-glass/archive/$revision.tar.gz"
tar -xzf "$build_root/source.tar.gz" -C "$build_root/source" --strip-components=1
# musl does not provide gettext in libc, unlike the upstream build environment.
printf '\ntarget_link_libraries(kwin_glass_config intl)\n' >> "$build_root/source/src/kcm/CMakeLists.txt"
cmake -S "$build_root/source" -B "$build_root/build" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr -DGLASS_WAYLAND=OFF -DGLASS_X11=ON \
  -DCMAKE_CXX_FLAGS="-include libintl.h"
# One compile job keeps memory use within the sandbox's limit.
cmake --build "$build_root/build" -j1
cmake --install "$build_root/build"
mkdir -p /usr/share/doc/vantah-glass
cp "$build_root/source/LICENSE" /usr/share/doc/vantah-glass/LICENSE
printf '%s\n' "$revision" > /usr/share/doc/vantah-glass/REVISION
printf '%s\n' "$kwin_revision" > /usr/share/doc/vantah-glass/KWIN_REVISION
cp "$script_dir/patch-kwin-x11.py" /usr/share/doc/vantah-glass/
cp -R "$build_root/kwin-source/LICENSES" /usr/share/doc/vantah-glass/kwin-LICENSES
