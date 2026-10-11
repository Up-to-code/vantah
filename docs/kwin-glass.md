# KWin Glass backend

vAntah uses KWin X11 6.5.6 and the real compositor effect from
[4v3ngR/kwin-effects-glass](https://github.com/4v3ngR/kwin-effects-glass).
Glass is pinned to its last supported X11 revision,
`0ae94cf5e709a894a9f1f54544cb17deb7f77d58`; KWin is pinned to
`f53992fd00bd446c478adda5d4cf8b588cb32b75`.

The shader samples the live composited scene behind each surface, applies
blur, convex refraction, and RGB dispersion. GTK draws the controls and a
thin tint. `FakeBlur=false` prevents wallpaper imitation. The shell declares
its shaped blur regions, including the gap between search and applications.
The ordinary KWin Blur effect is disabled.

The container uses Xvfb with Mesa GLX software rendering, exposed through
x11vnc and noVNC. Alpine Qt omits its GLX plugin, so a small patch allows
KWin to create its own GLX context while QtQuick uses software rendering.
`patch-kwin-x11.py` records this compatibility change. Picom and Xfwm are
not started by the KWin session.

The X11 effect has convex refraction; newer Wayland-only Snell refraction
and rim-specular controls are not available in this pinned version. Software
rendering depends on CPU and desktop size. The framebuffer defaults to
1280 × 800; noVNC uses local scaling. Set VANTAH_WIDTH and VANTAH_HEIGHT
on the container to choose another size.

The effect is GPL-2.0-or-later. KWin retains its upstream component licenses.
Sources are downloaded at the pinned revisions; installed license files,
revision identifiers, and the patch are in `/usr/share/doc/vantah-glass/`.
The vAntah shell retains its separate MIT license.

The existing Alpine sandbox was built, booted, and visually checked with
`glass_x11` loaded. The revised multistage Docker build has not yet been
tested from a clean image. Building KWin requires several GB of free disk
space and takes considerably longer than installing the shell itself.

## Native window corners and GTK menus

The compositor also loads [KDE-Rounded-Corners](https://github.com/matinlotfali/KDE-Rounded-Corners),
pinned to `c1178d94ff2ec0db8d4d9a9782a3eb06aec13ce6` and built for KWin X11.
It rounds the rendered window texture, including opaque GTK client content.
The profile uses a 16px squircle radius, native decoration shadows, no added
outlines, and disables rounding for maximized, tiled and fullscreen windows.
The shell class is excluded so its separate launcher shapes stay intact.
This avoids relying on X server masks that KWin's composited scene can bypass.
The effect is separately licensed GPL-3.0; its license and revision are installed
in `/usr/share/doc/vantah-corners/`.

`gtk-menus.css` is installed as an overlay in the six MacTahoe GTK 3 variants.
The installer also appends a marked import to user GTK CSS, retaining existing
rules, loading the shared menu rules at GTK user-style priority.
Native application menus use compact rows, rounded corners and blue selection.
`gtk_menu_glass.py` requests a shaped live blur region inside GTK's
`_GTK_FRAME_EXTENTS`, leaving the invisible client shadow margins transparent.
An application's existing blur property takes precedence. Whole-window forced
blur uses an empty whitelist and is disabled to prevent the large extra surround. The shell's own
launcher, dock and menus continue to declare their own shaped blur regions.
