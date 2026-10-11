#!/bin/sh
# Build the separately licensed compositor effect against vAntah's KWin X11.
set -eu
revision=c1178d94ff2ec0db8d4d9a9782a3eb06aec13ce6
build_root="${VANTAH_CORNERS_BUILD_ROOT:-/tmp/vantah-round}"
apk add --no-cache cmake extra-cmake-modules build-base kwin-dev \
  qt6-qtbase-dev qt6-qtbase-private-dev qt6-qttools-dev kcmutils-dev \
  kconfigwidgets-dev ki18n-dev libepoxy-dev
mkdir -p "$build_root/source"
wget -qO "$build_root/source.tar.gz" "https://github.com/matinlotfali/KDE-Rounded-Corners/archive/$revision.tar.gz"
tar -xzf "$build_root/source.tar.gz" -C "$build_root/source" --strip-components=1
# Alpine's musl needs an explicit gettext library for the configuration module.
printf '\ntarget_link_libraries(kwin_shapecorners_config intl)\n' >> "$build_root/source/src/kcm/CMakeLists.txt"
cmake -S "$build_root/source" -B "$build_root/build" -DKWIN_X11=ON \
  -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF \
  -DCMAKE_CXX_FLAGS="-include libintl.h"
cmake --build "$build_root/build" -j1
cmake --install "$build_root/build"
mkdir -p /usr/share/doc/vantah-corners
cp "$build_root/source/LICENSE" /usr/share/doc/vantah-corners/LICENSE
printf '%s\n' "$revision" > /usr/share/doc/vantah-corners/REVISION
