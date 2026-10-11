# TikTok story: Linux, iOS style and robotics

[English 40-second video](vantah-system-tour-en.mp4) · [Arabic subtitles version](vantah-system-tour-ar.mp4)

This is a 9:16 TikTok edit of the real white/blue vAntah desktop journey. The complete desktop sits in the center over a full-screen blurred duplicate of the same footage. First-person subtitles describe wanting Linux for Raspberry Pi robotics, loving the iOS look, reshaping a Linux workspace, wanting it small, and making the native desktop work in Arabic. Small pinned robot and penguin emoji stickers sit above the desktop. vAntah is a custom desktop running on Alpine Linux. The Raspberry Pi robotics and compact-system lines describe intended goals. This video was recorded in the Alpine sandbox; Raspberry Pi hardware, robotics integrations and Raspberry Pi sizing have not been tested. The Arabic changes cover the native desktop and its Files/Settings views; third-party apps retain their own language configuration. The subtitles do not describe vAntah as an Apple product or a separate newly built Linux distribution.

The recording shows:

1. Appearance settings and an actual glass tint adjustment.
2. Installing `tree` with `apk add tree` from an administrator terminal, then running `tree /home/sandbox/Documents`.
3. Opening native Files, browsing Documents and opening the demo document in Mousepad.
4. Typing `My system. My style.` and saving the file; the saved text was verified on disk.
5. Switching from English to Arabic and showing the mirrored native Files view.
6. Opening the application launcher and filtering for Terminal.

The package installation succeeded: `tree 2.3.2` is installed in the demo container. Alpine's `apk` is the existing package manager; the tour demonstrates installing an app from its repositories. The administrator terminal was launched separately inside the container. The container's `no-new-privileges` protection was retained; ordinary `sudo` in this sandbox is unavailable.

## Recording and edit

[vantah-system-session.mp4](vantah-system-session.mp4) contains the 120-second main desktop capture plus a 20-second launcher ending, recorded at 1280×768, 30 fps with FFmpeg `x11grab`. The 140 seconds are sped up uniformly 3.5× to exactly 40 seconds. No desktop pixels are cropped or replaced. The full recording is scaled proportionally to 1040×624 and centered at (20, 648) in a 1080×1920 canvas. A separate duplicate fills the background, is blurred at reduced resolution, scaled up, muted and darkened for contrast. Only the blurred background is cropped to fill portrait; the clear foreground desktop is complete. Large outlined white captions sit below it. There is no white footer or title card. Exports are 1080×1920, 30 fps, H.264/AAC with fast-start metadata.

The original ambient soundtrack, [vantah-system-music.wav](vantah-system-music.wav), uses soft overlapping chords, continuous oscillator phase, stereo width and a fade out. It contains no narration, arpeggios, percussion or third-party samples. It is provided under the repository license.

Subtitle text:

- [English SRT](vantah-system-tour-en.srt) · [English WebVTT](vantah-system-tour-en.vtt)
- [Arabic SRT](vantah-system-tour-ar.srt) · [Arabic WebVTT](vantah-system-tour-ar.vtt)

Both exports show the same journey, including real English and Arabic UI. Their story subtitles differ by language. Arabic video text is shaped for display; subtitle sidecars preserve logical Unicode order.

## Rebuild

Install FFmpeg and FFprobe, and Python packages `Pillow`, `arabic-reshaper`, and `python-bidi`. From the repository root:

```sh
python scripts/build-system-tour.py
```

The script reads the committed session duration, computes the speed, synthesizes the 40-second soundtrack, renders transparent subtitles and stickers, creates the live blurred background, and exports both videos, SRT/WebVTT files and preview posters. Default text and emoji fonts are installed macOS fonts used only for rendering; font files are not distributed. An alternative emoji font must support Pillow color rendering at 96 pixels. On Linux, use installed fonts:

```sh
python scripts/build-system-tour.py \
  --font /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf \
  --arabic-font /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf \
  --emoji-font /path/to/a/compatible-color-emoji-font.ttf
```
