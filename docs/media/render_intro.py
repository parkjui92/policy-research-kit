#!/usr/bin/env python3
"""Render a silent 30-second introduction from intro.json using Pillow and FFmpeg.

Requires Python 3.9+, Pillow, FFmpeg and a Korean-capable font.
Set INTRO_FONT_DIR to a directory containing Pretendard-{Regular,Bold}.otf,
or set INTRO_FONT and INTRO_FONT_BOLD to font file paths.
Usage: python3 docs/media/render_intro.py [--stills] [--fps 30]
"""
from __future__ import annotations
import argparse
import functools
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

W, H, DURATION = 1280, 720, 30
BG, INK, MUTED, LINE = '#F5F3EE', '#172A34', '#687779', '#D7DED9'
TIMES = [0, 4, 11, 20, 26, 30]

def find_font(bold=False):
    override = os.environ.get('INTRO_FONT_BOLD' if bold else 'INTRO_FONT')
    if override:
        if not Path(override).is_file():
            raise FileNotFoundError(override)
        return override
    base = Path(os.environ.get('INTRO_FONT_DIR', str(Path.home() / 'Library/Fonts')))
    paths = [base / ('Pretendard-Bold.otf' if bold else 'Pretendard-Regular.otf'),
             Path('/System/Library/Fonts/AppleSDGothicNeo.ttc'),
             Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')]
    for p in paths:
        if p.exists():
            return str(p)
    raise RuntimeError('Set INTRO_FONT and INTRO_FONT_BOLD to Korean-capable font files.')

@functools.lru_cache(maxsize=100)
def font(size, bold=False):
    return ImageFont.truetype(find_font(bold), int(size))

def ease(x):
    x = max(0, min(1, x))
    return 1 - (1 - x)**3

def mix(a, b, k):
    def rgb(s):
        return tuple(int(s[i:i+2], 16) for i in (1,3,5))
    return tuple(round(x+(y-x)*k) for x,y in zip(rgb(a),rgb(b)))

def text(im, xy, value, size=24, color=INK, bold=False, maxw=None):
    d = ImageDraw.Draw(im)
    f = font(size, bold)
    if maxw:
        while d.textlength(value, font=f) > maxw and size > 16:
            size -= 1
            f = font(size, bold)
    if d.textlength(value, font=f) + xy[0] > W-20:
        raise ValueError('Text overflow: ' + value)
    d.text(xy, value, font=f, fill=color, anchor='lt')

def wrap(value, width, size):
    lines=[]
    d=ImageDraw.Draw(Image.new('RGB',(1,1)))
    for paragraph in value.split('\n'):
        current=''
        for char in paragraph:
            if current and d.textlength(current+char,font=font(size)) > width:
                lines.append(current.rstrip())
                current=char.lstrip()
            else:
                current += char
        lines.append(current)
    return lines

def paragraph(im, xy, value, width, size=24, color=INK, bold=False, gap=12):
    y=xy[1]
    for line in wrap(value,width,size):
        text(im,(xy[0],y),line,size,color,bold)
        y += size+gap
    return y

def box(im, coords, fill='white', outline=None, radius=16, width=1):
    ImageDraw.Draw(im).rounded_rectangle(tuple(map(round,coords)), radius, fill, outline, width)

def rule(im, xy, color=LINE, width=2):
    ImageDraw.Draw(im).line(xy, fill=color, width=width)

def arrow(im, x1, y, x2, color, progress=1):
    x=x1+(x2-x1)*max(0,min(1,progress))
    rule(im,[(x1,y),(x,y)],color,3)
    ImageDraw.Draw(im).polygon([(x,y),(x-9,y-5),(x-9,y+5)],fill=color)

def reveal(im, painter, amount, dy=20):
    a=ease(amount)
    if a <= 0:
        return
    layer=Image.new('RGBA',(W,H),(0,0,0,0))
    painter(layer)
    layer.putalpha(layer.getchannel('A').point(lambda p: round(p*a)))
    im.paste(layer,(0,round(dy*(1-a))),layer)

def header(im,s,t,dark=False):
    c='#DDE9E2' if dark else MUTED
    text(im,(64,38),'PARKJUI92  /  RESEARCH TOOLS',17,c,True)
    text(im,(855,38),s['category']+'  ·  30초 소개',17,c,maxw=360)
    rule(im,[(64,76),(1216,76)],'#36504F' if dark else LINE,1)
    text(im,(64,668),'사용 흐름 예시 · 실제 UI 녹화 아님',16,c)
    text(im,(955,668),s['repo'],16,c,maxw=260)
    ImageDraw.Draw(im).rectangle((0,714,round(W*t/DURATION),720),fill=s['color'])

def kicker(im,number,label,color):
    box(im,(64,108,110,139),color,radius=7)
    text(im,(73,113),number,17,'white',True)
    text(im,(124,112),label,19,MUTED)

def title(im,value,color=INK):
    text(im,(64,166),value,46,color,True,maxw=1152)

def mini_document(im,s,t):
    col=s['color']
    for i in (2,1,0):
        x,y=757+i*14,184-i*12
        box(im,(x,y,x+405,y+350),mix('#E1E7E1','#FFFFFF',1-i*.23),LINE,14)
    text(im,(786,211),'INPUT  →  OUTPUT',16,col,True)
    for i,line in enumerate(s['output']):
        a=ease((t-.8-i*.42)/.7)
        yy=272+i*75
        box(im,(783,yy,1132,yy+53),mix('#EEF2ED','#FFFFFF',i/3),radius=8)
        def draw_row(layer, line=line, yy=yy):
            text(layer,(799,yy+15),line,21,INK,i==0,maxw=315)
        reveal(im,draw_row,a,10)
    box(im,(780,553,1140,596),col,radius=8)
    text(im,(803,565),s['category']+'에 맞춘 작업 흐름',20,'white',True,maxw=325)

def workflow(im,s,u):
    col=s['color']
    for i,label in enumerate(s['steps']):
        x=64+i*291
        a=ease((u-i*.85)/.6)
        active=a>.5
        box(im,(x,263,x+261,323),col if active else '#E8ECE5',radius=9)
        text(im,(x+17,283),f'{i+1:02d}',18,'white' if active else MUTED,True)
        text(im,(x+58,281),label,22,'white' if active else MUTED,True,maxw=192)
        if i<3:
            arrow(im,x+268,293,x+282,col,ease((u-.5-i*.85)/.4))
    box(im,(64,353,1216,581),'#FFFFFF',LINE,16)
    text(im,(87,372),'OUTPUT  /  '+s['result'],17,col,True,maxw=1085)
    p=ease((u-2.8)/1.2)
    if s['kind']=='proof':
        for i in range(7):
            x=90+i*64
            box(im,(x,414,x+52,430),col if i<=int(u*.85) else '#E6ECE5',radius=4)
        text(im,(562,411),'문단 경계로 분할 → 순차 점검',18,MUTED)
        text(im,(100,460),'분석되어지고',37,INK,True)
        rule(im,[(99,481),(99+225*p,481)],'#D57158',3)
        arrow(im,370,480,483,col,p)
        reveal(im,lambda l:text(l,(528,460),'분석되고',37,col,True),p,0)
        rule(im,[(91,519),(1184,519)],LINE,1)
        text(im,(102,540),'위치  §2.1 / C3',19,MUTED)
        text(im,(465,540),'유형  이중피동',19,MUTED)
        text(im,(830,540),'사유  피동 표현 중복',19,MUTED)
    elif s['kind']=='privacy':
        text(im,(99,419),'원문 · 가상 예시',17,MUTED)
        text(im,(724,419),'가명본',17,MUTED)
        text(im,(101,456),'홍길동 교수',34,INK,True)
        text(im,(101,505),'홍길동 교수가 검토함',24,MUTED)
        arrow(im,479,478,663,col,p)
        reveal(im,lambda l:text(l,(724,456),'[연구자A] 교수',34,col,True),p,0)
        reveal(im,lambda l:text(l,(724,505),'[연구자A] 교수가 검토함',24,col),p,0)
        # Route the sensitive mapping away from the released output.
        text(im,(85,603),'_private/  원값 매핑',20,MUTED)
        text(im,(740,603),'out/  검증 게이트 통과분',20,col,True)
    else:
        text(im,(97,418),'집필',17,MUTED)
        text(im,(97,452),'보고서 초안',32,INK,True)
        text(im,(97,505),'주장 · 수치 · 인용',23,MUTED)
        arrow(im,369,474,529,col,p)
        box(im,(562,414,889,550),'#EDF4EF',radius=10)
        text(im,(584,430),'별도 검토 역할 · 읽기 전용',21,col,True)
        for i,v in enumerate(['원문과 수치 대조','위치·문제·수정안 반환']):
            reveal(im,lambda l,i=i,v=v:text(l,(584,474+i*35),v,21,INK), (u-3.1-i*.7)/.5,8)
        arrow(im,907,477,963,col,ease((u-5)/.7))
        text(im,(988,451),'검수',28,col,True)
        text(im,(988,490),'기록',28,col,True)

def frame(s,t):
    index=max(i for i in range(5) if t>=TIMES[i])
    u=t-TIMES[index]
    col=s['color']
    dark=index==4
    im=Image.new('RGB',(W,H),'#172D32' if dark else BG)
    header(im,s,t,dark)
    if index==0:
        text(im,(64,120),s['repo'],26,col,True)
        for i,line in enumerate(s['hook']):
            reveal(im,lambda l,i=i,line=line:text(l,(64,216+i*73),line,53,INK,True,maxw=635),(u-i*.18)/.6)
        reveal(im,lambda l:paragraph(l,(67,406),s['tagline'],565,27,MUTED),(u-.65)/.6)
        text(im,(67,564),'입력부터 결과까지, 30초로 보기',21,col,True)
        mini_document(im,s,u)
    elif index==1:
        kicker(im,'01','실제 업무에서 시작하기',col)
        title(im,'무엇을 넣고, 어떻게 요청할까요?')
        for i,label in enumerate(s['inputs']):
            yy=292+i*113
            def painter(layer,i=i,yy=yy,label=label):
                box(layer,(64,yy,432,yy+88),'white',LINE,12)
                text(layer,(86,yy+18),f'INPUT {i+1:02d}',14,col,True)
                text(layer,(86,yy+46),label,25,INK,True,maxw=325)
            reveal(im,painter,(u-.2-i*.35)/.6)
        arrow(im,447,402,495,col,ease((u-.8)/.65))
        box(im,(516,274,1216,561),'#FFFFFF',LINE,16)
        text(im,(548,301),'REQUEST / 사용 예시',17,col,True)
        def prompt(layer):
            paragraph(layer,(548,355),s['prompt'],630,30,INK,gap=19)
        reveal(im,prompt,(u-1)/.7)
        text(im,(65,606),s['scenario'],21,MUTED,maxw=1150)
    elif index==2:
        kicker(im,'02','처리와 결과',col)
        title(im,'입력은 이렇게 결과로 이어집니다')
        workflow(im,s,u)
    elif index==3:
        kicker(im,'03','이 도구의 강점',col)
        title(im,s['feature_title'])
        for i,(name,body) in enumerate(s['features']):
            y=267+i*97
            def painter(layer,i=i,y=y,name=name,body=body):
                box(layer,(64,y,1216,y+80),'white',LINE,12)
                box(layer,(81,y+19,123,y+60),col,radius=8)
                text(layer,(91,y+28),str(i+1),23,'white',True)
                text(layer,(146,y+26),name,27,INK,True,maxw=320)
                text(layer,(505,y+29),body,24,MUTED,maxw=675)
            reveal(im,painter,(u-i*.65)/.5)
        paragraph(im,(66,588),s['note'],1140,18,MUTED,gap=6)
    else:
        text(im,(64,127),'START WITH YOUR OWN WORK',19,'#A6C4B6',True)
        reveal(im,lambda l:text(l,(64,206),s['repo'],65,'#F5F3EE',True,maxw=1150),u/.55)
        paragraph(im,(66,317),s['cta'],1140,35,'#F5F3EE',True)
        box(im,(64,421,1216,518),'#244047',radius=12)
        text(im,(87,443),'첫걸음',15,'#A6C4B6',True)
        text(im,(87,474),s['start_short'],24,'#F5F3EE',maxw=1100)
        text(im,(66,571),'github.com/parkjui92/'+s['repo'],25,'#B7D3C4',maxw=1140)
    # Quick neutral dissolve at scene boundaries; no black flash.
    if index>0 and u<.22:
        previous=frame(s,TIMES[index]-.001)
        im=Image.blend(previous,im,ease(u/.22))
    return im

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec',type=Path,default=Path(__file__).with_name('intro.json'))
    parser.add_argument('--output',type=Path)
    parser.add_argument('--fps',type=int,default=30)
    parser.add_argument('--stills',action='store_true')
    a=parser.parse_args()
    if not 1<=a.fps<=60:
        parser.error('--fps must be between 1 and 60')
    spec=json.loads(a.spec.read_text())
    out=a.output or a.spec.parent
    out.mkdir(parents=True,exist_ok=True)
    points=[3.4,9.5,19.0,25.5,29.2]
    frames=[frame(spec,t) for t in points]
    frames[0].save(out/'intro-poster.png')
    sheet=Image.new('RGB',(1280,1140),BG)
    for i,im in enumerate(frames):
        x,y=(i%2)*640,(i//2)*380
        sheet.paste(im.resize((640,360),Image.Resampling.LANCZOS),(x,y))
        text(sheet,(x+14,y+362),f'{TIMES[i]:02d}–{TIMES[i+1]:02d}s',14,MUTED)
    sheet.save(out/'intro-storyboard.png')
    if a.stills:
        return
    if not shutil.which('ffmpeg'):
        raise RuntimeError('FFmpeg is required to render MP4 and GIF.')
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo',
         '-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}',
         '-r',str(a.fps),'-i','-','-an','-c:v','libx264','-threads','2',
         '-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'intro.mp4')]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(DURATION*a.fps):
            proc.stdin.write(frame(spec,i/a.fps).tobytes())
        proc.stdin.close()
        if proc.wait():
            raise RuntimeError('MP4 encoding failed.')
    except BaseException:
        proc.kill()
        proc.wait()
        raise
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss','11','-t','9',
                    '-i',str(out/'intro.mp4'),'-filter_complex',
                    'fps=10,scale=768:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=80[p];[b][p]paletteuse=dither=bayer:bayer_scale=5',
                    '-loop','0',str(out/'intro-preview.gif')],check=True)
    print(f'{spec["repo"]}: 30s MP4, 9s GIF, poster and storyboard created',flush=True)

if __name__=='__main__':
    main()
