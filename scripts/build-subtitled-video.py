#!/usr/bin/env python3
"""Create a silent 15-second story export for viewers to choose their own music."""
import argparse
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
root = Path(__file__).resolve().parents[1]
media = root / 'docs/social'
parser = argparse.ArgumentParser()
parser.add_argument('--font', default='/System/Library/Fonts/Supplemental/Arial Bold.ttf')
args = parser.parse_args()
font = Path(args.font)
if not font.is_file():
    parser.error('Use --font with the path to a bold TrueType font.')
cues = [
    'I took Alpine Linux.\nNot built from scratch.',
    'iOS-inspired glass.\nMy own workspace.',
    'English and Arabic.\nMade for how I work.',
    'Next goal:\nRaspberry Pi robotics.',
    'vAntah • Open source\nUp-to-code/vantah\non GitHub',
]
subtitle = media / 'vantah-story-subtitles-en.srt'
subtitle.write_text(''.join(f'{i+1}\n00:00:{i*3:02d},000 --> 00:00:{(i+1)*3:02d},000\n{text}\n\n' for i,text in enumerate(cues)))
# Preserve the full desktop and place legible timed text in the black space above it.
output = media / 'vantah-story-subtitles-en.mp4'
with tempfile.TemporaryDirectory() as directory:
    command = ['ffmpeg', '-y', '-v', 'error', '-i', str(media/'vantah-original-15s-silent.mp4')]
    for i,text in enumerate(cues):
        canvas = Image.new('RGBA',(1080,1920))
        draw = ImageDraw.Draw(canvas)
        face = ImageFont.truetype(str(font),64)
        lines = text.splitlines()
        for line_index,line in enumerate(lines):
            draw.text((540,350+line_index*85),line,font=face,anchor='mt',fill='white',stroke_width=2,stroke_fill='black')
        path = Path(directory)/f'{i}.png'
        canvas.save(path)
        command += ['-loop','1','-i',str(path)]
    filters = ['[0:v]scale=1080:648,pad=1080:1920:0:636:black[v0]']
    for i in range(len(cues)):
        filters.append(f"[v{i}][{i+1}:v]overlay=0:0:enable='gte(t,{i*3})*lt(t,{(i+1)*3})'[v{i+1}]")
    command += ['-filter_complex',';'.join(filters),'-map','[v5]','-an','-t','15','-r','30','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
    subprocess.run(command,check=True)
subprocess.run(['ffmpeg','-y','-v','error','-ss','1.5','-i',str(output),'-frames:v','1','-update','1',str(media/'vantah-story-subtitles-poster.jpg')],check=True)
print(output)
