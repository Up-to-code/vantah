#!/usr/bin/env python3
"""Speed the entire original desktop journey to 15s, without visual overlays."""
import json
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / 'docs/social'
source = MEDIA / 'vantah-system-session.mp4'
duration = float(json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format', '-of', 'json', str(source)]))['format']['duration'])
silent = MEDIA / 'vantah-original-15s-silent.mp4'
video = MEDIA / 'vantah-original-15s.mp4'
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(source), '-vf', f'setpts={15/duration:.12f}*PTS,fps=30,setsar=1', '-an', '-t', '15', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(silent)], check=True)
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(silent), '-i', str(MEDIA / 'vantah-system-music.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', '15', '-movflags', '+faststart', str(video)], check=True)
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', '5.5', '-i', str(video), '-frames:v', '1', '-update', '1', str(MEDIA / 'vantah-original-poster.jpg')], check=True)
print(f'Entire {duration:g}s recording sped to 15s: {video}')
