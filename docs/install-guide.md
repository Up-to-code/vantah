# Install and use vAntah

vAntah is a Linux desktop shell, not an Apple operating system. Settings and Files are native GTK applications; KWin samples the live backdrop for blur and refraction. The English/Arabic switch translates vAntah views and mirrors their layout. Applications such as Terminal and Mousepad retain their own translations and menus.

## Choose an installation route

| Route | Status | What changes |
|---|---|---|
| Existing Alpine Docker sandbox | Tested on this project's ARM64 sandbox | Updates the desktop inside the named container; keeps its files |
| Fresh Docker source build | Build scripts provided; clean build has not been revalidated for this update | Creates a separate container and localhost browser port |
| Old PC running Linux + Docker | Same source route; x86_64 and physical hardware not yet validated | Runs a virtual desktop in the browser; leaves your host desktop in place |
| Replace the PC's installed desktop or OS | Not packaged or tested | Do not use this project as a disk installer |

The validated session uses two virtual CPUs, 2 GiB VM RAM, ARM64 Alpine, a 1280×768 display and Mesa software OpenGL. Source compilation installs several GB of development dependencies. Allow roughly 20 GB free disk and prefer 4 GiB or more RAM for a first build. These are practical build allowances, not a benchmarked minimum. An old machine may render glass slowly with software graphics. Try it in the browser before considering it for daily use.

## 1. Prepare Docker

Install [Docker Engine on Linux](https://docs.docker.com/engine/install/) or [Docker Desktop](https://docs.docker.com/desktop/). On Mac, [Colima](https://github.com/abiosoft/colima) is another option. Verify:

```sh
docker info
git --version
```

Docker must report a running Linux engine. Do not run the installer until this works. A Windows PC can use WSL with Docker integration; this route has not been tested here.

## 2. Try the current source with one command

Requires Docker, Git, curl and a POSIX shell:

```sh
curl -fsSL https://raw.githubusercontent.com/Up-to-code/vantah/main/try-current.sh | sh
```

This command clones the current public source, builds KWin and its pinned effects, then launches `vantah-current`. It can take a substantial time on the first build. It is a source installer, not a prebuilt image download. Read [the script](../try-current.sh) first if desired. Repeating it starts the same project-labelled container and preserves your files; it does not silently replace another container. To keep multiple versions:

```sh
curl -fsSL https://raw.githubusercontent.com/Up-to-code/vantah/main/try-current.sh |
  VANTAH_CONTAINER=vantah-second VANTAH_PORT=6082 sh
```

Open the printed URL, normally <http://127.0.0.1:6081/vnc.html?autoconnect=true&resize=scale>. The port is bound to localhost and VNC is unauthenticated inside the container. There are no host folder mounts. Container files live separately from your PC's files.

The older tagged `v0.1.1/try.sh` installs the historical Picom demo. Use `main/try-current.sh` for the current Settings, Files and KWin desktop.

## 3. Upgrade an existing Alpine sandbox

```sh
git clone https://github.com/Up-to-code/vantah.git
cd vantah
sh install.sh alpine-gui
```

Replace `alpine-gui` with your existing project container name. This updates pinned appearance resources and shell source and restarts that container. It preserves your home files. It assumes the project's Alpine sandbox layout and user ID 1000; it is not an installer for arbitrary containers or a native host OS. If the pinned KWin version is absent it compiles it, which needs significant free disk.

## 4. Walk through the desktop

- **Dock:** Applications, Files, Terminal, Editor, Settings, followed by Trash. Running indicators occupy a bottom lane beneath each tile. Click a running app to activate it. Additional real windows can appear before Trash.
- **Launcher:** click Applications or press Super+Space. Search, arrow keys, Enter and Escape work with installed applications. Files and Settings open the coordinated vAntah views.
- **Settings → Appearance:** toggle Dark Mode, Reduce Motion and glass tint. Tint changes the translucent surface; the compositor supplies live blur/refraction. Clearer glass can reduce legibility over busy wallpaper.
- **Settings → Language:** choose English or العربية. Settings and Files mirror their sidebars and controls. Filesystem paths remain left-to-right. This is interface translation, not an Arabic keyboard layout installer or translation of third-party apps.
- **Settings → About:** read the actual filesystem capacity and available space.
- **Files:** browse Home, Desktop, Documents, Downloads or Trash. Double-click folders to navigate, files to open their registered application. Search filters the current folder's visible entries. Back follows navigation history.
- **New Folder:** enter a single folder name. Hidden files are omitted from this view. This first Files implementation is a list browser; it does not yet provide Finder's full preview, tags, column views or network sidebar.
- **Trash:** select a file and choose Move to Trash. Open Trash from the dock, select it and choose Restore. Restore refuses to overwrite an existing destination. No irreversible Empty Trash control is provided.
- **Editor / Terminal:** real Linux applications, with styled native menus and compositor-rounded windows. Their toolbars and menu arrangement remain their original GTK layouts.

## 5. Stop, restart, keep files

```sh
docker stop vantah-current
docker start vantah-current
```

These commands preserve container files. Before removing or replacing a container, copy out files you want to keep:

```sh
docker cp vantah-current:/home/sandbox/Documents ./vantah-documents-backup
```

Back up other folders separately as needed. `docker rm` discards that container's writable filesystem; the installer does not run it automatically.

## Troubleshooting

**Blank/disconnected noVNC:** wait for desktop startup, then reload. Inspect `docker logs CONTAINER` and `docker exec -u 1000 CONTAINER tail -60 /tmp/desktop.log`.

**No live glass:** the build must use KWin with its pinned Glass effect. `docs/kwin-glass.md` lists revisions and GLX requirements. Native GPU acceleration is not configured in this Docker demo; it uses software OpenGL. On unsupported or very slow hardware, do not expect Apple's rendering performance.

**Disk-full build:** stop the build, free space and retry. Do not delete unrelated Docker volumes or containers. This update was validated by upgrading the existing sandbox; a fresh source image remains to be validated.

**Trash unavailable:** `gvfs` must be installed and its services run on the same desktop DBus session. Current Dockerfile and upgrade installer include it. Files displays service errors rather than inventing a Trash listing.

**Arabic text but no Arabic typing:** the switch translates the shell's interface. Configure an Arabic keyboard layout separately in the underlying Linux keyboard settings. Arabic filenames are supported; the integration test creates, searches, trashes and restores an Arabic-named file.

## Design resources and limits

[Apple iOS 27](https://www.apple.com/os/ios/), [Apple design resources](https://developer.apple.com/design/resources/), [Language & Region](https://support.apple.com/guide/mac-help/change-language-region-settings-on-mac-intl163/mac), [Finder settings](https://support.apple.com/en-ie/guide/mac-help/mchlp2803/27/mac/27), and [right-to-left layout guidance](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPInternational/SupportingRight-To-LeftLanguages/SupportingRight-To-LeftLanguages.html) inform the comparison. Apple's native Liquid Glass implementation is not available as a Linux package. vAntah uses open-source KWin Glass and editable original SVG dock tiles, with MacTahoe resources for external GTK applications and window decoration. See the [comparison](visual-comparison.html) and [source/license catalog](kwin-glass.md).
