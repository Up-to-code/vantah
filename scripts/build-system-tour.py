#!/usr/bin/env python3
"""Speed the entire long recording into a 15-second TikTok story: centered full desktop over live blur.
Requires ffmpeg, ffprobe, Pillow, arabic-reshaper and python-bidi.
"""
from pathlib import Path
import argparse, json, math, subprocess, tempfile, wave
from array import array
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/social'
DURATION=15
RANGES=[(0,3),(3,6),(6,9),(9,12),(12,15)]
LINES={
'en': [ ["I didn't build an OS", 'from scratch.'],
        ['I took Linux', 'and edited it my way.'],
        ['iOS style.', 'Raspberry Pi robotics goals.'],
        ['My workspace.', 'Now with Arabic support.'],
        ['vAntah.', 'Up-to-code/vantah on GitHub.'] ],
'ar': [ ['لم أبنِ نظام تشغيل', 'من الصفر.'],
        ['أخذت لينكس', 'وعدّلته بطريقتي.'],
        ['أسلوب iOS.', 'وهدفي روبوتات راسبيري باي.'],
        ['مساحة عملي.', 'والآن تدعم العربية.'],
        ['vAntah.', 'Up-to-code/vantah على GitHub.'] ]}

def run(*args): subprocess.run(args,check=True)

def stamp(sec,srt): return f'00:00:{sec:02d}'+(',000' if srt else '.000')

def soundtrack(path):
    rate=44100; samples=array('h')
    chords=[[130.8128,164.8138,195.9977,246.9417],
            [146.8324,174.6141,220,261.6256],
            [130.8128,164.8138,195.9977,261.6256],
            [123.4708,146.8324,195.9977,246.9417],
            [130.8128,164.8138,195.9977,261.6256]]
    for i in range(rate*DURATION):
        t=i/rate
        for channel in range(2):
            sound=0
            for k,notes in enumerate(chords):
                age=t-k*8
                if 0 <= age < 10:
                    env=math.sin(math.pi*age/10)**2
                    for n,f in enumerate(notes):
                        phase=channel*.19+n*.27
                        sound+=.07*env*(math.sin(2*math.pi*f*t+phase)+.12*math.sin(2*math.pi*f*2*t+phase))
            fade=min(1,t/1.2,(DURATION-t)/2)
            samples.append(int(sound*fade*32767))
    with wave.open(str(path),'wb') as w:
        w.setparams((2,2,rate,0,'NONE','not compressed')); w.writeframes(samples.tobytes())

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--font',default='/System/Library/Fonts/Supplemental/Arial Bold.ttf')
    p.add_argument('--arabic-font',default='/System/Library/Fonts/SFArabic.ttf')
    p.add_argument('--emoji-font',default='/System/Library/Fonts/Apple Color Emoji.ttc')
    args=p.parse_args()
    source=OUT/'vantah-system-session.mp4'
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(source)]))
    duration=float(info['format']['duration'])
    ratio=DURATION/duration
    soundtrack(OUT/'vantah-system-music.wav')
    with tempfile.TemporaryDirectory(prefix='vantah-full-tour-') as temp:
        temp=Path(temp)
        for lang,captions in LINES.items():
            timeline=[]
            for i,((a,b),lines) in enumerate(zip(RANGES,captions)):
                card=Image.new('RGBA',(1080,1920),(0,0,0,0)); d=ImageDraw.Draw(card)
                fontpath=args.arabic_font if lang=='ar' else args.font
                font=ImageFont.truetype(fontpath,58)
                for j,line in enumerate(lines):
                    if lang=='ar': line=get_display(arabic_reshaper.reshape(line))
                    while d.textbbox((0,0),line,font=font)[2] > 890:
                        font=ImageFont.truetype(fontpath,font.size-1)
                    d.text((500,1390+j*76),line,fill='white',font=font,anchor='mt',stroke_width=3,stroke_fill=(0,0,0,190))
                # Small pinned emoji stickers stay outside the unobscured desktop.
                emoji_font=ImageFont.truetype(args.emoji_font,96)
                for x,y,glyph,angle in [(94,480,'🤖',-10),(824,480,'🐧',8)]:
                    sticker=Image.new('RGBA',(132,132),(0,0,0,0))
                    pen=ImageDraw.Draw(sticker)
                    pen.rounded_rectangle((4,4,128,128),radius=30,fill=(255,255,255,225))
                    pen.text((18,18),glyph,font=emoji_font,embedded_color=True)
                    sticker=sticker.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True)
                    card.alpha_composite(sticker,(x,y))
                png=temp/f'{lang}-{i}.png'; card.save(png)
                timeline.append(f"file '{png}'\nduration {b-a}\n")
            timeline.append(f"file '{png}'\n")
            listing=temp/f'{lang}.txt'; listing.write_text(''.join(timeline))
            run('ffmpeg','-hide_banner','-loglevel','warning','-y','-i',str(source),
                '-f','concat','-safe','0','-i',str(listing),'-i',str(OUT/'vantah-system-music.wav'),
                '-filter_complex',f'[0:v]setpts={ratio}*PTS,fps=30,setsar=1,split=2[screen][back];'
                '[back]scale=324:576:force_original_aspect_ratio=increase,crop=324:576,'
                'boxblur=18:3,scale=1080:1920,eq=brightness=-0.20:saturation=0.80[blur];'
                '[screen]scale=1040:624[desktop];'
                '[blur][desktop]overlay=20:648[scene];'
                '[1:v]fps=30,format=rgba[labels];'
                '[scene][labels]overlay=0:0:shortest=1,format=yuv420p[v]',
                '-map','[v]','-map','2:a','-t',str(DURATION),'-c:v','libx264','-preset','medium','-crf','18',
                '-c:a','aac','-b:a','192k','-movflags','+faststart',str(OUT/f'vantah-system-tour-{lang}.mp4'))
            for ext in ['srt','vtt']:
                srt=ext=='srt'
                rows=[(f'{i+1}\n' if srt else '')+f'{stamp(a,srt)} --> {stamp(b,srt)}\n'+'\n'.join(lines)
                      for i,((a,b),lines) in enumerate(zip(RANGES,captions))]
                (OUT/f'vantah-system-tour-{lang}.{ext}').write_text(('' if srt else 'WEBVTT\n\n')+'\n\n'.join(rows)+'\n')
            run('ffmpeg','-v','error','-y','-ss','5.5','-i',str(OUT/f'vantah-system-tour-{lang}.mp4'),
                '-frames:v','1',str(OUT/f'vantah-system-tour-{lang}-poster.jpg'))
if __name__=='__main__': main()
