# Full-system journey

The latest video is the **40-second full-system tour**: [English](vantah-system-tour-en.mp4) · [Arabic subtitles](vantah-system-tour-ar.mp4). It keeps the whole desktop visible and tells the project story with simple subtitles. [Recording details and rebuilding instructions](system-tour.md).

The earlier short close-up edits are preserved below.

# White / blue desktop promos

Two clean 15-second portrait edits, starting in the real Appearance settings:

- [English](vantah-tiktok-en.mp4) · [SRT](vantah-tiktok-en.srt) · [WebVTT](vantah-tiktok-en.vtt)
- [Arabic captions](vantah-tiktok-ar.mp4) · [SRT](vantah-tiktok-ar.srt) · [WebVTT](vantah-tiktok-ar.vtt)

Each video is 1080×1920 at 30 fps, H.264 with AAC stereo music. The edit uses a white canvas, an original blue desktop wallpaper, a smooth zoom into Settings, a close-up of the native glass sidebar, and a close-up of the centered dock. Shots dissolve over 450 ms. There are only three large 96-pixel labels: Settings, Glass and Dock. The previous slogans, branding header, website footer, progress marks and explanatory copy have been removed.

Both versions use the same real English desktop recording; the Arabic version translates the three captions. This opening is Appearance setup in the installed desktop, not an installation wizard. The camera crops and magnifies the recording without replacing any native UI. Fine details depend on the source recording's 1280×768 resolution.

## Footage and music

[vAntah blue session](vantah-blue-session.mp4) is the new uncut 75-second, 30 fps `x11grab` recording. The live desktop was switched to light appearance and the bundled [blue wallpaper](../../assets/wallpaper-blue.svg). Settings adjusts the actual glass tint; its native window is moved across the wallpaper and closed to expose the dock. The promotional edit samples three real sections, then adds eased camera zooms and crossfades. The original longer walkthrough remains in [recording.md](../recording.md).

`vantah-original-music.wav` is a new original ambient soundtrack with sustained chords, continuous oscillator phase, overlapping soft envelopes, stereo width and gentle fades. The previous arpeggio and percussion have been removed. It uses no third-party samples or songs and is provided under the repository license. There is no narration. SRT and WebVTT contain the labels as logical Unicode text; Arabic video captions are shaped and ordered for display.

## Rebuild

Install FFmpeg, then create a Python virtual environment with `Pillow`, `arabic-reshaper`, and `python-bidi`. From the repository root:

```sh
python scripts/build-social-videos.py
```

The script uses the committed blue session, regenerates the soundtrack, renders three crops with cosine-eased zooms, dissolves the shots, exports both videos and subtitle files, and refreshes their posters.

Default fonts are local macOS fonts used only during rendering. Fonts are not distributed. On Linux, supply installed font paths:

```sh
python scripts/build-social-videos.py \
  --font /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf \
  --arabic-font /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
```
