# Appearance and desktop checks

Checked on 2026-10-11 in the existing `alpine-gui` sandbox at 1280 × 768,
using KWin X11 6.5.6, Mesa software rendering and noVNC in the Codex browser.

## Passed

- Ran the complete `install.sh alpine-gui` upgrade: downloaded pinned Linux
  theme sources, installed light/dark GTK themes, icon themes, cursors and
  Aurorae decorations, preserved license/revision files, then booted the session.
- KWin's DBus `isEffectLoaded glass_x11` returned true after the upgrade and
  appearance/motion switching. Picom and Xfwm were absent from active processes.
- All eight visible installed application desktop entries resolved their icons
  to `/usr/share/icons/MacTahoe-dark/`. Dock, wallpaper and accessibility icon
  names were also checked; none of the audited names were missing.
- Searched for `term` through the GUI and launched Terminal with Enter.
- Typed `e` in Terminal: the letter appeared at the prompt; Edit stayed closed.
- Used traffic-light controls to maximize, minimize and close Terminal.
  Clicking its dock icon restored the minimized window.
- Opened Files and Settings from the dock; inspected their themed controls.
- Toggled light mode with Files open: GTK changed to `MacTahoe-Light`, icons to
  `MacTahoe-light`, and Aurorae to `MacTahoe-Light`. Visually confirmed the white
  content/window frame, then returned to dark mode.
- Opened Mousepad, typed `e`, and discarded only that temporary test document.
  This exposed its newer `org.xfce.mousepad` window class; the shell now matches
  it to the pinned Text Editor icon and friendly app label. After rebooting the
  fixed shell, visually verified five dock icons, the correct pinned running dot
  and the Text Editor label, with no duplicate Mousepad icon.
- Enabled Reduce Motion in the desktop menu; saved preference became true and
  KWin `AnimationDurationFactor` became 0. Disabled it again; factor returned to 1.
- Opened the clock calendar and dismissed it by clicking outside.
- Python syntax checks and shell installer syntax checks passed.
- Five installer regressions passed. The actual patched noVNC keyboard test
  passed (lost Command release cleared before `e`, no Alt sent); viewport tests
  passed (remote/scale fit, off preserves native size).

## Limits

Native-resolution screenshots: [launcher](screenshots/launcher.jpg) and
[window frames](screenshots/editor.jpg). The browser was temporarily tested
at the framebuffer resolution to check clipping without VNC scaling, then reset.

These are smoke checks of the existing sandbox, not exhaustive testing of every
Linux application. The new multistage Docker image has not been clean-built.
The published v0.1.1 installer still targets the earlier Picom release; current
MacTahoe/KWin changes are on the main source branch. Apple 27 screenshot references
were inspected, but no pixel-diff or full Figma component measurement was done.
The installed MacTahoe packages are Tahoe-inspired Linux artwork, not official
macOS 27 assets. Software-rendered glass and VNC updates visibly lag input.

Rams quick_review was requested with `via: rules` in its review context (the tool
has no separate `via` parameter). It returned an exhausted review-credit error,
so there is no Rams score or successful automated review to report.

## Reference comparison follow-up

Compared the running shell against Apple's macOS 27 search capsule, Siri desktop
window/dock, and official component-kit preview. A side-by-side HTML page links
Apple-hosted images alongside native-resolution vAntah screenshots. The references
use different content and scale; no numeric pixel-diff equivalence is claimed.

Applied a 28px menu bar, 24px search text, larger 56px launcher icons, two-line
application labels and fewer grid columns. Menus now use shorter rows and a blue
selection. Dock/glass saturation is neutral, edge lighting is disabled and
refraction is narrower. Aurorae uses a 28px title strip and smaller 12px buttons.

The running shell was rebooted with these changes. Visually verified full launcher
labels, menu spacing, live glass, and window controls. Python syntax, shell syntax
and the five installer regressions passed. Rams again returned an exhausted-credit
error. Exact native app layouts, bottom client corners, Apple typography/icons and
optics remain different; these changes do not certify an exact macOS reproduction.

## Native corners and menu glass follow-up

Built and installed pinned KDE-Rounded-Corners against the running KWin X11
6.5.6. D-Bus reports both `kwin4_effect_shapecorners` and `glass_x11` loaded;
the corner shaders report successful loading. Visually checked rounded opaque
GTK bottom corners, maximized square edges, restored rounded edges, and light
and dark appearance. Typing `e` in Mousepad entered text normally.

GTK menus now request blur only within their visible content bounds. The prior
large blurred surround came from including `_GTK_FRAME_EXTENTS` shadow margins.
Four tests against the real X server pass: excluding shadow extents, preserving
existing nonempty and empty app blur regions, and removing a closed menu from
tracking. Five installer regressions, Python syntax, shell syntax, CSS parsing,
and preservation/idempotence of the user CSS import pass. Existing CSS is kept;
a marked import loads the shared menu overlay at user-style priority.

The upgrade installer completed and rebooted the existing sandbox. Docker's VM
needed a restart after a filesystem I/O error during dependency installation;
both previously running Alpine containers were restored. The clean multistage
image is still untested. Rams `quick_review` was requested with `via: rules` but
remains unavailable because its review credits are exhausted. The screenshots
record actual results; exact Apple layout, menu placement, typography, icon art,
selection rendering and optical equivalence remain unproven.

The final launcher check also verified explicit visible-region blur with an
empty force-blur whitelist, and a shell-class exclusion in the corner effect.
This prevents filling the gap between the search capsule and application grid.

## Native Settings / Files / dock follow-up

- Replaced the icon-plus-dot vertical stack with an overlay: a 72px icon target is centered inside an 88px cell, and the dot is independently bottom-aligned. Dock top/bottom padding is symmetric. Added a separated final Trash slot and regenerated all original SVG dock tiles.
- Added native Settings sections for Appearance, Language and About. Dark mode, reduced motion, glass tint and English/Arabic selection persist in the existing preference file. Storage reads the actual home filesystem. Tint was exercised live in both appearance modes.
- Added native Files browsing, current-directory search, default-app opening, new folders, real Gio/GVfs Trash and no-overwrite restoration. Selection is retained when Trash refreshes. GVfs Trash discovery is asynchronous; the view refreshes while visible, and the integration test waits for the real service rather than assuming immediate cache updates.
- Arabic labels are shaped by GTK/Pango. Settings and Files mirror their navigation, controls and file list. Paths remain left-to-right. The native titlebar controls mirror in Arabic too. External applications and app metadata retain their own language configuration.
- Replaced the external frame on vAntah Settings/Files with a 32px native titlebar, traffic-light buttons, dragging, maximizing/minimizing and a bottom-right resize target. The entire client is clipped to 16px corners and requests a matching compositor blur region. This removes the white rectangular lower frame seen in light-mode testing. Maximized native windows use square corners.
- Hid the old Xfce desktop icons. Files navigation and the new dock remain available. The previous screenshots were removed and replaced by actual current captures. The wallpaper and owner-supplied logo remain original project assets.
- Automated checks: 2 real-display desktop integration tests, 4 GTK menu region tests and 8 installer orchestration tests passed; Python compilation, GTK stylesheet loading, shell syntax and diff whitespace checks passed. Installer tests mock Docker/network operations; they do not prove a clean image build.
- Manual walkthrough: opened and edited a real document, saved it, moved it to Trash and restored it. Confirmed its saved contents on disk. Application filtering opened Terminal; `echo vAntah` ran with ordinary `e` typing. Light/dark and Arabic/English switching were observed live.
- Exported and probed the actual 15-second desktop tour; source footage and timing are described in `recording.md`.
- Rams quick_review was requested with `via: rules` context after the UI changes. The service rejected every attempt because this workspace's 15 review credits were exhausted. No Rams findings were returned or claimed fixed. Manual review covered layout, text direction, native actions and corner rendering.
- Fresh Docker image builds, x86_64/old-PC hardware and native host-desktop installation remain unvalidated. The source installer is provided; exact Apple pixel equality, complete Finder functionality and Apple's own Liquid Glass optics are not claimed.
