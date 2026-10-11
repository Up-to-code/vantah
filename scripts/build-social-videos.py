#!/usr/bin/env python3
"""Render real desktop footage into bilingual portrait videos with original music.
Requires: ffmpeg, Pillow, arabic-reshaper, python-bidi; local system fonts.
"""
from pathlib import Path
import argparse, math, subprocess, tempfile, wave
from array import array
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/social'
CUES = {
'en': [('Make Linux feel different', 'Real glass. Your own desktop.'),
       ('Open. Edit. Save.', 'Native Files and a real text editor.'),
       ('Trash that actually works', 'Move a file to Trash, then restore it.'),
       ('English or العربية', 'Switch languages with mirrored Arabic layouts.'),
       ('Search. Launch. Create.', 'A real Alpine Linux desktop. Try vAntah.')],
'ar': [('سطح مكتب لينكس مختلف', 'زجاج حقيقي. وسطح مكتب يناسبك.'),
       ('افتح. عدّل. احفظ.', 'تصفّح الملفات وحرّر مستنداتك فعليًا.'),
       ('سلة مهملات تعمل فعليًا', 'انقل ملفًا إلى السلة ثم استعده.'),
       ('العربية أو الإنجليزية', 'بدّل اللغة مع واجهة عربية من اليمين لليسار.'),
       ('ابحث. افتح. أنشئ.', 'سطح مكتب ألباين لينكس حقيقي. جرّب vAntah.')]
}

def run(*args):
    subprocess.run(args, check=True)

def music(path):
    """Original A-minor ambient loop; no samples or third-party composition."""
    rate = 44100
    samples = array('h')
    notes = [220, 261.6256, 329.6276, 391.9954, 293.6648, 349.2282, 440, 329.6276]
    for i in range(rate * 15):
        t = i / rate
        fade = min(1, t / .6, (15-t) / 1.2)
        step = int(t / .46875)
        age = t % .46875
        n = notes[step % len(notes)]
        chime = .14 * math.exp(-age * 9) * (math.sin(2*math.pi*n*2*t) + .25*math.sin(2*math.pi*n*4*t))
        pad = .07 * sum(math.sin(2*math.pi*f*t) for f in [110, 130.8128, 164.8138]) / 3
        beat = t % .9375
        kick = .16 * math.exp(-beat * 22) * math.sin(2*math.pi*(52*beat + 2.8*(1-math.exp(-beat*20))))
        value = int(32767 * fade * (chime + pad + kick))
        samples.extend([value, value])
    with wave.open(str(path), 'wb') as w:
        w.setparams((2, 2, rate, 0, 'NONE', 'not compressed'))
        w.writeframes(samples.tobytes())

def clock(sec, srt=True):
    return f'00:00:{sec:02d}' + (',000' if srt else '.000')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--font', default='/System/Library/Fonts/Helvetica.ttc')
    parser.add_argument('--arabic-font', default='/System/Library/Fonts/SFArabic.ttf')
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    music(OUT / 'vantah-original-music.wav')
    def text(draw, label, y, size, color, arabic=False):
        rendered = get_display(arabic_reshaper.reshape(label)) if arabic else label
        fontpath = args.arabic_font if arabic or any('\u0600' <= c <= '\u06ff' for c in label) else args.font
        while True:
            font = ImageFont.truetype(fontpath, size)
            bounds = draw.textbbox((0,0), rendered, font=font)
            if bounds[2]-bounds[0] <= 900 or size <= 22: break
            size -= 1
        draw.text((540, y), rendered, font=font, fill=color, anchor='mt')
    with tempfile.TemporaryDirectory(prefix='vantah-social-') as scratch:
        scratch = Path(scratch)
        for lang, cues in CUES.items():
            entries = []
            for idx, (headline, caption) in enumerate(cues):
                img = Image.new('RGB', (1080,1920))
                pix = img.load()
                for y in range(1920):
                    for x in range(1080):
                        glow = math.exp(-(((x-900)/700)**2 + ((y-600)/750)**2))
                        pix[x,y] = (int(10+29*glow), int(13+23*glow), int(25+65*glow))
                d = ImageDraw.Draw(img)
                text(d, 'vAntah', 195, 110, '#ffffff')
                text(d, 'YOUR LINUX. REIMAGINED.' if lang=='en' else 'لينكس بطريقتك', 335, 32, '#b7beee', lang=='ar')
                d.rounded_rectangle((32, 492,1048,1116), radius=26, fill='#161d34', outline='#7580ac', width=2)
                text(d, headline, 1215, 58, '#ffffff', lang=='ar')
                text(d, caption, 1310, 34, '#d4d8ec', lang=='ar')
                for j in range(5):
                    x = 380+j*66
                    d.rounded_rectangle((x,1435,x+48,1440),radius=2,fill='#a8b5ff' if j==idx else '#38415d')
                text(d, 'OPEN SOURCE / REAL DESKTOP' if lang=='en' else 'مفتوح المصدر / سطح مكتب حقيقي', 1550, 27, '#b7beee', lang=='ar')
                text(d, 'github.com/Up-to-code/vantah', 1610, 28, '#ffffff')
                frame = scratch / f'{lang}-{idx}.png'
                img.save(frame)
                entries.append(f"file '{frame}'\nduration 3\n")
            entries.append(f"file '{frame}'\n")
            timeline = scratch / f'{lang}.txt'
            timeline.write_text(''.join(entries))
            (OUT / f'vantah-tiktok-{lang}.srt').write_text('\n\n'.join(f'{i+1}\n{clock(i*3)} --> {clock((i+1)*3)}\n{h}\n{c}' for i,(h,c) in enumerate(cues))+'\n')
            (OUT / f'vantah-tiktok-{lang}.vtt').write_text('WEBVTT\n\n'+'\n\n'.join(f'{clock(i*3,False)} --> {clock((i+1)*3,False)}\n{h}\n{c}' for i,(h,c) in enumerate(cues))+'\n')
            run('ffmpeg','-hide_banner','-loglevel','warning','-y','-f','concat','-safe','0','-i',str(timeline),
                '-i',str(ROOT/'docs/vantah-tour.mp4'),'-i',str(OUT/'vantah-original-music.wav'),
                '-filter_complex','[0:v]fps=30,format=yuv420p[bg];[1:v]scale=1000:600[demo];[bg][demo]overlay=40:504:shortest=1[v]',
                '-map','[v]','-map','2:a','-t','15','-c:v','libx264','-preset','medium','-crf','20',
                '-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart',str(OUT/f'vantah-tiktok-{lang}.mp4'))
if __name__ == '__main__':
    main()
