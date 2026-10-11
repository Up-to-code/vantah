#!/usr/bin/env python3
"""Speed the real full-system recording to 40 seconds, without UI crops.
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
DURATION=40
RANGES=[(0,5),(5,10),(10,16),(16,20),(20,25),(25,34),(34,40)]
LINES={
'en': [ ['vAntah.', 'My take on a Linux operating system.'],
        ['I love the macOS style.', 'I wanted a system I could change.'],
        ['Install an app.', 'Use it right from the terminal.'],
        ['A Finder-inspired Files app.', 'For the work I actually do.'],
        ['Write. Edit. Save.', 'A system I can make my own.'],
        ['Glass. Settings. Arabic.', 'Built on Alpine Linux.'],
        ['Up-to-code/vantah', 'The source is on GitHub.'] ],
'ar': [ ['vAntah.', 'رؤيتي لنظام تشغيل مبني على لينكس.'],
        ['أحب أسلوب macOS.', 'وأريد نظامًا أستطيع تغييره.'],
        ['ثبّت تطبيقًا.', 'واستخدمه مباشرة من الطرفية.'],
        ['تطبيق ملفات مستوحى من Finder.', 'للعمل الذي أقوم به فعلًا.'],
        ['اكتب. عدّل. احفظ.', 'نظام أستطيع أن أجعله يناسبني.'],
        ['زجاج. إعدادات. عربية.', 'مبني على ألباين لينكس.'],
        ['Up-to-code/vantah', 'المصدر متاح على GitHub.'] ]}

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
    p.add_argument('--font',default='/System/Library/Fonts/Helvetica.ttc')
    p.add_argument('--arabic-font',default='/System/Library/Fonts/SFArabic.ttf')
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
                card=Image.new('RGB',(1280,896),'#fafcff'); d=ImageDraw.Draw(card)
                font=ImageFont.truetype(args.arabic_font if lang=='ar' else args.font,36)
                for j,line in enumerate(lines):
                    if lang=='ar': line=get_display(arabic_reshaper.reshape(line))
                    d.text((640,782+j*46),line,fill='#172b46',font=font,anchor='mt')
                png=temp/f'{lang}-{i}.png'; card.save(png)
                timeline.append(f"file '{png}'\nduration {b-a}\n")
            timeline.append(f"file '{png}'\n")
            listing=temp/f'{lang}.txt'; listing.write_text(''.join(timeline))
            run('ffmpeg','-hide_banner','-loglevel','warning','-y','-i',str(source),
                '-f','concat','-safe','0','-i',str(listing),'-i',str(OUT/'vantah-system-music.wav'),
                '-filter_complex',f'[0:v]setpts={ratio}*PTS,fps=30,setsar=1[desktop];'
                '[1:v]fps=30,format=yuv420p[paper];[paper][desktop]overlay=0:0:shortest=1,format=yuv420p[v]',
                '-map','[v]','-map','2:a','-t',str(DURATION),'-c:v','libx264','-preset','medium','-crf','18',
                '-c:a','aac','-b:a','192k','-movflags','+faststart',str(OUT/f'vantah-system-tour-{lang}.mp4'))
            for ext in ['srt','vtt']:
                srt=ext=='srt'
                rows=[(f'{i+1}\n' if srt else '')+f'{stamp(a,srt)} --> {stamp(b,srt)}\n'+'\n'.join(lines)
                      for i,((a,b),lines) in enumerate(zip(RANGES,captions))]
                (OUT/f'vantah-system-tour-{lang}.{ext}').write_text(('' if srt else 'WEBVTT\n\n')+'\n\n'.join(rows)+'\n')
            run('ffmpeg','-v','error','-y','-ss','14','-i',str(OUT/f'vantah-system-tour-{lang}.mp4'),
                '-frames:v','1',str(OUT/f'vantah-system-tour-{lang}-poster.jpg'))
if __name__=='__main__': main()
