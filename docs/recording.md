# Real desktop tour

`vantah-tour.mp4` is a 15.000-second H.264 video, 1280×768 at 30 fps. It was recorded directly from this Alpine X11 session with FFmpeg `x11grab`, not generated from a mockup. The main recording is 240 seconds. A second capture supplies 45 seconds of launcher filtering and Terminal interaction; the combined 285 seconds are sped up 19×. There is no audio.

The walkthrough opens native Settings, changes light/dark appearance and glass tint, browses Documents, opens a real text file in Mousepad, types and saves an edit, moves the document to Trash and restores it, switches to Arabic, browses mirrored Files, filters application search and executes `echo vAntah` in Terminal. The edited document was checked on disk after saving and restoring.

## Reproduce a recording

With the project desktop already running, capture a manual walkthrough inside its container:

```sh
docker exec -u 0 alpine-gui apk add --no-cache ffmpeg
docker exec -u 1000 alpine-gui sh -c '
  . /tmp/vantah-session.env
  ffmpeg -y -f x11grab -framerate 15 -video_size 1280x768 -i :1 \
    -t 120 -an -c:v libx264 -threads 1 -preset ultrafast \
    -crf 25 -pix_fmt yuv420p /tmp/tour.mp4
'
```

Interact in noVNC while that capture runs. The geometry must match the desktop; replace 1280×768 if using a different size. After it finishes:

```sh
docker cp alpine-gui:/tmp/tour.mp4 ./tour.mp4
ffmpeg -i tour.mp4 -vf 'setpts=15/120*PTS,fps=30' -t 15 \
  -an -c:v libx264 -crf 20 -pix_fmt yuv420p -movflags +faststart tour-15s.mp4
```

That example assumes a 120-second source. Read the actual duration with `ffprobe` and use `15 / SOURCE_DURATION` for other lengths. Capture only the demo files and windows you intend to publish.
