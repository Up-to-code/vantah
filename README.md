<p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/logo-light.svg"><img src="assets/logo.svg" width="112" alt="Qentrah logo"></picture></p>

# vAntah

A native glass desktop shell for Alpine Linux: translucent desktop chrome,
a live-blurred dock, application search, dark mode, and motion controls.

Fresh Docker demo:

![Fresh dark desktop](docs/screenshots/fresh-demo.jpg)

Application search in the themed sandbox:

![Application search](docs/screenshots/applications.jpg)

Download the source, logo, wallpaper, and screenshots from the
[public v0.1.0 release](https://github.com/Up-to-code/vantah/releases/tag/v0.1.0).

## One-command installer

Requires Docker with a running Linux engine, `curl`, `tar`, and `shasum` or
`sha256sum`. On macOS use Docker Desktop or Colima; on Linux use Docker Engine.
Windows users can run the command inside WSL with Docker integration.

```sh
curl -fsSL https://raw.githubusercontent.com/Up-to-code/vantah/v0.1.0/try.sh | sh
```

The installer downloads the versioned release, checks its SHA-256 checksum,
builds the image for your machine, and starts a localhost-only desktop. Open the
URL it prints. Running it again restarts the same container. Set `VANTAH_PORT`,
`VANTAH_CONTAINER`, or `VANTAH_INSTALL_DIR` to customize it. It requires no sudo and
does not install Docker or change your host desktop. Stop it with
`docker stop vantah-demo`. Your container files remain available.

## Build from source

Requires Docker with a running Linux engine. On macOS, Docker Desktop or Colima
can provide that engine.

```sh
git clone https://github.com/Up-to-code/vantah.git
cd alpine-glass-shell
sh sandbox/run.sh
```

Open <http://127.0.0.1:6081/vnc.html?autoconnect=true&resize=remote>.
The demo runs without host mounts as a non-root user, drops Linux capabilities,
and binds its browser port to localhost. It has no VNC password, so keep the
port on localhost. The container is named `vantah-demo`; stop and restart
it with `docker stop vantah-demo` and `docker start vantah-demo`.

The source is baked into the image. Rebuild after editing it. `run.sh` refuses to
replace an existing container; use a different name and port to keep its files:
`sh sandbox/run.sh vantah-demo-v2 6082`.

The fresh demo uses Adwaita app and window themes. The application-search screenshot shows the
existing sandbox with separately installed WhiteSur themes and icons. If those
are already installed, the shell selects them; otherwise it uses Adwaita.
The wallpaper and dock icons are original project assets. vAntah uses the
Qentrah logo supplied by the project owner.

## Native implementation

A custom native desktop shell for the Alpine Linux sandbox. The shell replaces
Xfce's panels with a glass menu bar, application search, and an application dock.
GTK 3 draws the UI, libwnck controls real windows, and Picom 13 renders live blur
and scale/fade animations. Xfwm remains the underlying window manager.

## Controls

- Click the magnifier, app-grid dock icon, or press **Super+Space** to search installed applications.
- Type a name, use arrow keys, and press Enter to launch. Escape closes search.
- Click a dock app to open it or cycle through its windows. Dots show running apps.
- Right-click a pinned app for a new window. Additional windows appear in the dock or its overflow menu.
- Click the sun/moon to switch dark and light appearance. The appearance also applies to GTK apps and window frames.
- Use the Qentrah logo menu to enable **Reduce Motion**, change wallpaper, or restore Xfce panels.
- Click the clock for a calendar. Time is shown in Africa/Cairo.

Dark mode is the default. Preferences are saved in `~/.config/alpine-shell/settings.json`.
The shell starts automatically with the Alpine desktop.

## Source and installation

`shell.py` is the native shell, `shell.css` defines its UI, and the two Picom
configuration files define compositor behavior with and without animation.
The original glass dock icons are editable SVGs in `icons/`; `icons/generate.py`
regenerates them. Dock hover zoom uses cached images and native animation timers.
The source installed in Alpine is `~/.local/share/alpine-shell`.

`fix-vnc.py` patches the sandbox's noVNC client so Mac Command stays Linux
Super, releases modifiers after an intercepted host shortcut, and clears
remote modifier state when reconnecting. This prevents ordinary letters from
becoming menu accelerators. Reload the noVNC browser after installation.
Upstream JavaScript backups are retained beside the modified files with the
suffix `.before-alpine-shell`. The modified noVNC files retain their upstream
MPL-2.0-or-later license; that license is separate from this shell's MIT license.

From this directory on the Mac:

```sh
sh install.sh alpine-gui
```

Optional WhiteSur themes and icons are not redistributed here and keep their
upstream licenses. The shell code, wallpaper, and dock icons are MIT licensed. The Qentrah logo
is project-owner branding, excluded from the artwork license. This is an original Linux shell inspired by Apple
design, not Apple's iOS or macOS code and not an official 2027 Apple theme.

## Restore

Choose **Restore Xfce Panels** in the Qentrah logo menu. To stop automatic startup,
rename `~/.config/autostart/alpine-shell.desktop` to an extension other than `.desktop`.
The shell does not delete your Xfce configuration or sandbox files.

## Current scope

This version targets the sandbox's single VNC display. It provides desktop
chrome, app search, window activation, live glass blur, and window animations.
It does not replace application UI, implement a global application menu, or
provide Apple's proprietary Liquid Glass refraction or minimize-to-dock engine.
GTK accessibility labels and keyboard navigation are included. Rams quick_review
was attempted, but the account's review credit limit prevented a result.

## Development checks

```sh
python3 -m py_compile shell.py fix-vnc.py
python3 sandbox/test-installer.py
sh -n try.sh install.sh run-shell.sh sandbox/run.sh sandbox/start-desktop.sh
# Test the patched client exported from the running demo:
docker cp vantah-demo:/usr/share/novnc/core/input/keyboard.js /tmp/alpine-keyboard.js
node sandbox/test-vnc-keyboard.cjs /tmp/alpine-keyboard.js
```

The keyboard regression simulates a swallowed Mac Command release and checks
that it is released before the next `e` key, without sending Linux Alt.

The Docker image was built and booted from this source; the native shell and
Picom started successfully, and the patched noVNC keyboard regression passed.
