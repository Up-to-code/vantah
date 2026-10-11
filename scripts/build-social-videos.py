#!/usr/bin/env python3
"""Build clean bilingual portrait promos from the real white/blue desktop.
Requires ffmpeg, Pillow, arabic-reshaper and python-bidi. Fonts remain local.
"""
from pathlib import Path
import argparse, math, subprocess, tempfile, wave
from array import array
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/social'
DURATION = 15
SHOT_DURATION = 5.3
TRANSITION = .45
# Start, crop width/height/x/y, output width/height, top placement.
# First shot starts inside the real Appearance setup, followed by glass and dock.
SHOTS = [(0, (880,600,216,48), (1040,710), 540),
         (30, (230,570,390,74), (460,1140), 250),
         (60, (600,170,340,598), (1040,294), 740)]
CAPTIONS = {'en': ['Settings', 'Glass', 'Dock'],
            'ar': ['الإعدادات', 'الزجاج', 'الشريط']}

def run(*args):
    subprocess.run(args, check=True)

def music(path):
    """Smooth original ambient chords, with continuous phase and soft envelopes.
    No arpeggio, percussion, samples, hard note changes, or external recording.
    """
    rate = 44100
    samples = array('h')
    chords = [(0, [130.8128,164.8138,195.9977,246.9417]),
              (5, [146.8324,174.6141,220,261.6256]),
              (10,[130.8128,164.8138,195.9977,261.6256])]
    for i in range(rate*DURATION):
        t = i/rate
        channels = []
        for channel in range(2):
            sound = 0
            for start, notes in chords:
                age = t-start
                if 0 <= age < 7:
                    envelope = math.sin(math.pi*age/7)**2
                    for n,f in enumerate(notes):
                        # Static stereo phase offset; every chord fades from zero.
                        phase = channel*.19 + n*.27
                        sound += .070*envelope*(math.sin(2*math.pi*f*t+phase)+.12*math.sin(2*math.pi*f*2*t+phase))
            fade = min(1, t/1.2, (DURATION-t)/1.6)
            channels.append(int(32767*sound*fade))
        samples.extend(channels)
    with wave.open(str(path),'wb') as w:
        w.setparams((2,2,rate,0,'NONE','not compressed'))
        w.writeframes(samples.tobytes())

def stamp(seconds, srt=True):
    whole = int(seconds)
    ms = round((seconds-whole)*1000)
    return f'00:00:{whole:02d}' + (',' if srt else '.') + f'{ms:03d}'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--font',default='/System/Library/Fonts/Helvetica.ttc')
    parser.add_argument('--arabic-font',default='/System/Library/Fonts/SFArabic.ttf')
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    source = OUT/'vantah-blue-session.mp4'
    if not source.exists():
        raise SystemExit('Missing real desktop source: docs/social/vantah-blue-session.mp4')
    music(OUT/'vantah-original-music.wav')
    with tempfile.TemporaryDirectory(prefix='vantah-promo-') as temp:
        temp = Path(temp)
        for lang, captions in CAPTIONS.items():
            clips=[]
            for i, (start,crop,size,top) in enumerate(SHOTS):
                card=Image.new('RGB',(1080,1920),'#fafcff')
                draw=ImageDraw.Draw(card)
                label=captions[i]
                if lang=='ar': label=get_display(arabic_reshaper.reshape(label))
                font=ImageFont.truetype(args.arabic_font if lang=='ar' else args.font, 96)
                draw.text((540,1470),label,font=font,fill='#172b46',anchor='mt')
                background=temp/f'{lang}-{i}.png'; card.save(background)
                cw,ch,cx,cy=crop; ow,oh=size
                # Cosine easing avoids a sudden camera start/stop. Overscan is
                # derived from the native pixels, with all important controls retained.
                ease='(0.5-0.5*cos(PI*on/158))'
                zoom=f'1+0.04*{ease}'
                vf=(f'[0:v]crop={cw}:{ch}:{cx}:{cy},'
                    f'zoompan=z=\'{zoom}\':x=\'iw/2-iw/zoom/2\':y=\'ih/2-ih/zoom/2\':'
                    f'd=1:s={ow}x{oh}:fps=30,setsar=1[detail];'
                    f'[1:v]fps=30,format=yuv420p[paper];'
                    f'[paper][detail]overlay={(1080-ow)//2}:{top}:shortest=1,format=yuv420p[v]')
                clip=temp/f'{lang}-{i}.mp4'; clips.append(clip)
                run('ffmpeg','-hide_banner','-loglevel','warning','-y','-ss',str(start),'-t',str(SHOT_DURATION),'-i',str(source),
                    '-loop','1','-i',str(background),'-filter_complex',vf,'-map','[v]',
                    '-t',str(SHOT_DURATION),'-an','-c:v','libx264','-preset','fast','-crf','19',str(clip))
            run('ffmpeg','-hide_banner','-loglevel','warning','-y',
                '-i',str(clips[0]),'-i',str(clips[1]),'-i',str(clips[2]),'-i',str(OUT/'vantah-original-music.wav'),
                '-filter_complex','[0:v][1:v]xfade=transition=fade:duration=0.45:offset=4.85[first];'
                '[first][2:v]xfade=transition=fade:duration=0.45:offset=9.7,format=yuv420p[v]',
                '-map','[v]','-map','3:a','-t','15','-c:v','libx264','-preset','medium','-crf','19',
                '-c:a','aac','-b:a','192k','-movflags','+faststart',str(OUT/f'vantah-tiktok-{lang}.mp4'))
            ranges=[(0,4.85),(5.3,9.7),(10.15,15)]
            for ext in ['srt','vtt']:
                srt=ext=='srt'
                rows=[(f'{i+1}\n' if srt else '')+f'{stamp(a,srt)} --> {stamp(b,srt)}\n{label}'
                      for i,((a,b),label) in enumerate(zip(ranges,captions))]
                (OUT/f'vantah-tiktok-{lang}.{ext}').write_text(('' if srt else 'WEBVTT\n\n')+'\n\n'.join(rows)+'\n')
            run('ffmpeg','-hide_banner','-loglevel','error','-y','-ss','1','-i',str(OUT/f'vantah-tiktok-{lang}.mp4'),
                '-frames:v','1',str(OUT/f'vantah-tiktok-{lang}-poster.jpg'))
if __name__=='__main__': main()
