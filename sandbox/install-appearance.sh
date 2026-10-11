#!/bin/sh
# Install pinned upstream Linux themes, with their original licenses.
set -eu
icons_revision=839848b9a8a38a92a6936e30c4abe35cc6f2546d
gtk_revision=1e45e19f510edb8cde18fa84d6cd5319f60b086b
kde_revision=cbf6a1f71b591d143184855d62f6272ce533e7c3
apk add --no-cache bash sassc coreutils sudo aurorae font-inter glib-dev libxml2-utils
build_root=$(mktemp -d /tmp/vantah-appearance.XXXXXX)
trap 'rm -rf "$build_root"' EXIT
fetch() {
  name=$1 revision=$2
  mkdir "$build_root/$name"
  wget -qO "$build_root/$name.tar.gz" "https://github.com/vinceliuice/$name/archive/$revision.tar.gz"
  tar -xzf "$build_root/$name.tar.gz" -C "$build_root/$name" --strip-components=1
}
fetch MacTahoe-icon-theme "$icons_revision"
fetch MacTahoe-gtk-theme "$gtk_revision"
fetch MacTahoe-kde "$kde_revision"
bash "$build_root/MacTahoe-icon-theme/install.sh" -d /usr/share/icons
bash "$build_root/MacTahoe-icon-theme/cursors/install.sh"
# The desktop uses its own appearance controls, not GNOME's switcher app.
sed -i 's/^  install_app$/  : # vAntah manages appearance/' "$build_root/MacTahoe-gtk-theme/install.sh"
USER=$(id -un) bash "$build_root/MacTahoe-gtk-theme/install.sh" -d /usr/share/themes -c light -c dark -o normal --silent-mode
[ -s /usr/share/themes/MacTahoe-Dark/gtk-3.0/gtk.css ]
[ -s /usr/share/themes/MacTahoe-Light/gtk-3.0/gtk.css ]
for color in Light Dark; do
  theme=MacTahoe-$color
  dest=/usr/share/aurorae/themes/$theme
  mkdir -p "$dest"
  cp "$build_root/MacTahoe-kde/aurorae/$theme/decoration.svg" "$dest/"
  cp "$build_root/MacTahoe-kde/aurorae/${color}rc" "$dest/${theme}rc"
  cp "$build_root/MacTahoe-kde/aurorae/icons-$color/"*.svg "$dest/"
  cp "$build_root/MacTahoe-kde/aurorae/metadata.desktop" "$build_root/MacTahoe-kde/aurorae/metadata.json" "$dest/"
  sed -i "s/theme_name/$theme/g" "$dest/metadata.desktop" "$dest/metadata.json"
done
mkdir -p /usr/share/doc/vantah-appearance
cp "$build_root/MacTahoe-icon-theme/COPYING" /usr/share/doc/vantah-appearance/icons-LICENSE
cp "$build_root/MacTahoe-icon-theme/AUTHORS" /usr/share/doc/vantah-appearance/icons-AUTHORS
cp "$build_root/MacTahoe-gtk-theme/COPYING" /usr/share/doc/vantah-appearance/gtk-LICENSE
cp "$build_root/MacTahoe-kde/LICENSE" /usr/share/doc/vantah-appearance/decoration-LICENSE
printf 'icons=%s\ngtk=%s\ndecoration=%s\n' "$icons_revision" "$gtk_revision" "$kde_revision" > /usr/share/doc/vantah-appearance/REVISIONS
