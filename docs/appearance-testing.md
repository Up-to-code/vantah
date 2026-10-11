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

Native-resolution screenshots: [launcher](screenshots/kwin-glass.jpg) and
[window frames](screenshots/window-tahoe.jpg). The browser was temporarily tested
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
