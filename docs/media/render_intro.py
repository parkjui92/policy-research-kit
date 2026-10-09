#!/usr/bin/env python3
"""Render the 정책한걸음 introduction, following ../../DESIGN.md.

Python 3.9+, Pillow, FFmpeg, and a Korean font are required for regeneration.
The original logo PNG and brand-tokens.json stay beside this script.
INTRO_FONT / INTRO_FONT_BOLD can override local font paths.
"""
from __future__ import annotations
import argparse
import functools
import hashlib
import json
import math
import os
import re
from pathlib import Path
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
TOKENS=json.loads((ROOT/'brand-tokens.json').read_text(encoding='utf-8'))
C=TOKENS['colors']
S=1.5
VW,VH=1280,720
W,H=int(VW*S),int(VH*S)
DURATION=30
TIMES=[0,4,11,20,26,30]

def coords(values):
    return tuple(round(v*S) for v in values)

def rgb(value):
    return tuple(int(value[i:i+2],16) for i in (1,3,5))

def mix(a,b,t):
    return tuple(round(x+(y-x)*t) for x,y in zip(rgb(a),rgb(b)))

def ease(t):
    return 1-(1-max(0,min(1,t)))**3

@functools.lru_cache(maxsize=80)
def font(size,bold=False):
    override=os.environ.get('INTRO_FONT_BOLD' if bold else 'INTRO_FONT')
    directory=Path(os.environ.get('INTRO_FONT_DIR',str(Path.home()/'Library/Fonts')))
    choices=([Path(override)] if override else [])+[
        directory/('Pretendard-ExtraBold.otf' if bold else 'Pretendard-Regular.otf'),
        directory/('Pretendard-Bold.otf' if bold else 'Pretendard-Regular.otf'),
        Path('/System/Library/Fonts/AppleSDGothicNeo.ttc'),
        Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')]
    for p in choices:
        if p.is_file():
            return ImageFont.truetype(str(p),round(size*S))
    raise RuntimeError('Set INTRO_FONT and INTRO_FONT_BOLD to Korean-capable font files.')

def text(im,xy,value,size=24,color=None,bold=False,maxw=None):
    d=ImageDraw.Draw(im)
    f=font(size,bold)
    if maxw:
        while d.textlength(value,font=f)>maxw*S and size>16:
            size-=1
            f=font(size,bold)
    extent=d.textlength(value,font=f)/S
    if xy[0]+extent>VW-20:
        raise ValueError('Text overflow: '+value)
    d.text(coords(xy),value,font=f,fill=color or C['ink'],anchor='lt')

def paragraph(im,xy,value,width,size=24,color=None,bold=False,gap=10):
    d=ImageDraw.Draw(im)
    lines=[]
    for part in value.split('\n'):
        line=''
        for ch in part:
            if line and d.textlength(line+ch,font=font(size,bold))>width*S:
                lines.append(line.rstrip())
                line=ch.lstrip()
            else:
                line+=ch
        lines.append(line)
    y=xy[1]
    for line in lines:
        text(im,(xy[0],y),line,size,color,bold)
        y+=size+gap
    return y

def box(im,xy,fill=None,outline=None,radius=0,width=1):
    ImageDraw.Draw(im).rounded_rectangle(coords(xy),round(radius*S),fill or C['white'],outline,round(width*S))

def line(im,points,color=None,width=1):
    ImageDraw.Draw(im).line([coords(p) for p in points],fill=color or C['line'],width=max(1,round(width*S)),joint='curve')

def dot(im,x,y,r,color):
    ImageDraw.Draw(im).ellipse(coords((x-r,y-r,x+r,y+r)),fill=color)

@functools.lru_cache(maxsize=40)
def gradient(w,h,left,right):
    row=Image.new('RGB',(w,1))
    row.putdata([mix(left,right,x/max(1,w-1)) for x in range(w)])
    return row.resize((w,h))

def band(im,xy,left=None,right=None,slant=12):
    x,y,x2,y2=coords(xy)
    w,h=x2-x,y2-y
    mask=Image.new('L',(w,h),0)
    ImageDraw.Draw(mask).polygon([(0,0),(w,0),(w-round(slant*S),h),(0,h)],fill=255)
    im.paste(gradient(w,h,left or C['blue'],right or C['indigo']),(x,y),mask)

def logo(im,x=64,y=22,width=235):
    im.paste(logo_asset(width),coords((x,y)),logo_asset(width))

@functools.lru_cache(maxsize=8)
def logo_asset(width):
    original=Image.open(ROOT/'brand-logo.png').convert('RGBA')
    # Trim transparent layout margins only; the logo artwork is unmodified.
    original=original.crop(original.getchannel('A').getbbox())
    w=round(width*S)
    return original.resize((w,round(original.height*w/original.width)),Image.Resampling.LANCZOS)

def reveal(im,painter,amount,dx=0,dy=12):
    a=ease(amount)
    if a<=0:
        return
    layer=Image.new('RGBA',(W,H),(0,0,0,0))
    painter(layer)
    if a<1:
        layer.putalpha(layer.getchannel('A').point(lambda p:round(p*a)))
    im.paste(layer,coords((dx*(1-a),dy*(1-a))),layer)

def arrow(im,x1,y,x2,amount=1,color=None):
    p=max(0,min(1,amount))
    if p<=0:
        return
    col=color or C['blue']
    x=x1+(x2-x1)*p
    line(im,[(x1,y),(x,y)],col,2.5)
    ImageDraw.Draw(im).polygon([coords((x,y)),coords((x-8,y-5)),coords((x-8,y+5))],fill=col)

def bezier(a,b,c,d,n=40):
    result=[]
    for i in range(n+1):
        t=i/n
        result.append(tuple((1-t)**3*a[j]+3*(1-t)**2*t*b[j]+3*(1-t)*t*t*c[j]+t**3*d[j] for j in (0,1)))
    return result

def route(im,points,amount=1,width=6,track=True):
    if track:
        line(im,points,C['line'],width)
    n=min(len(points)-1,round((len(points)-1)*max(0,min(1,amount))))
    for i in range(n):
        color=mix(C['blue'],C['indigo'],i/max(1,len(points)-1))
        line(im,points[i:i+2],color,width)
        # Round overlapping joins avoid hairline seams between gradient segments.
        dot(im,*points[i],width/2,color)
    if n:
        x,y=points[n]
        dot(im,x,y,width/2+1,mix(C['blue'],C['indigo'],n/(len(points)-1)))

def header(im,s,t):
    logo(im)
    text(im,(958,40),s['category'],22,C['indigo'],True,maxw=258)
    text(im,(958,71),'30 SEC / WORKFLOW',13,C['muted'])
    line(im,[(64,103),(1216,103)])
    text(im,(64,677),'기능 설명용 모션그래픽 · 실제 UI 녹화 아님',16,C['muted'])
    text(im,(954,677),s['repo'],16,C['muted'],maxw=262)
    if t>0:
        band(im,(0,715,VW*t/DURATION,720),slant=0)

def heading(im,num,overline,title):
    text(im,(64,134),num,18,C['blue'],True)
    text(im,(105,134),overline,18,C['muted'])
    text(im,(64,178),title,42,C['ink'],True,maxw=1152)

def hero(im,s,u):
    text(im,(64,147),s['repo'],25,C['indigo'],True)
    for i,value in enumerate(s['hook']):
        reveal(im,lambda layer,i=i,value=value:text(layer,(64,238+72*i),value,53,C['black'],True,maxw=690),(u-.15*i)/.6,dx=-18,dy=0)
    paragraph(im,(66,424),s['tagline'],640,27,C['muted'])
    band(im,(64,532,417,579))
    text(im,(85,548),'내 업무에 쓰는 방법, 30초',23,'white',True)
    # A connected double path is derived from the logo's rounded turns.
    points=[(787,230),(1120,230)]
    points+=bezier((1120,230),(1235,230),(1235,354),(1120,354))
    points+=[(870,354)]
    points+=bezier((870,354),(769,354),(769,486),(870,486))
    points+=[(1190,486)]
    line(im,[(x,y+19) for x,y in points],C['line'],7)
    route(im,points,ease((u-.25)/2.9),9)
    for i,label in enumerate(s['output']):
        label=re.sub(r'^\d{2}\s+', '', label)
        y=[174,291,423][i]
        x=[789,869,869][i]
        def draw(layer,i=i,label=label,x=x,y=y):
            text(layer,(x,y),f'0{i+1}',16,C['blue'],True)
            text(layer,(x,y+24),label,21,C['ink'],True,maxw=1205-x)
        reveal(im,draw,(u-.5-i*.65)/.55,dy=8)
    text(im,(795,552),'INPUT  /  PROCESS  /  OUTPUT',15,C['muted'])

def inputs(im,s,u):
    heading(im,'01','업무에서 시작하기','무엇을 넣고, 어떻게 요청할까요?')
    for i,value in enumerate(s['inputs']):
        y=301+i*119
        def draw(layer,i=i,value=value,y=y):
            line(layer,[(64,y),(403,y)],C['gray'],3)
            text(layer,(64,y+20),f'INPUT {i+1:02d}',15,C['blue'],True)
            text(layer,(64,y+53),value,27,C['ink'],True,maxw=345)
        reveal(im,draw,(u-.2-i*.35)/.6,dx=-15,dy=0)
    route(im,bezier((431,386),(457,386),(470,386),(496,386)),ease((u-.7)/.7),3)
    box(im,(522,274,1216,565),C['pale'])
    band(im,(522,274,1216,280),slant=0)
    text(im,(552,307),'REQUEST / 사용 예시',16,C['blue'],True)
    reveal(im,lambda layer:paragraph(layer,(552,367),s['prompt'],620,29,C['ink'],gap=21),(u-.9)/.65,dx=16,dy=0)
    paragraph(im,(64,607),s['scenario'],1145,20,C['muted'],gap=7)

def stepper(im,s,u):
    for i,value in enumerate(s['steps']):
        x=64+i*291
        p=ease((u-i*.75)/.6)
        line(im,[(x,291),(x+246,291)],C['line'],3)
        if p>0:
            band(im,(x,289,x+max(1,246*p),293),slant=0)
        dot(im,x+12,291,12,C['indigo'] if p>.85 else C['gray'])
        text(im,(x+8,284),str(i+1),14,'white',True)
        text(im,(x,324),value,24,C['indigo'] if p>.5 else C['muted'],True,maxw=250)

def result(im,s,u):
    heading(im,'02','처리에서 결과까지',s['feature_title'])
    stepper(im,s,u)
    box(im,(64,390,1216,592),C['pale'])
    text(im,(87,408),'OUTPUT / '+s['result'],17,C['blue'],True,maxw=1095)
    p=ease((u-2.6)/1.2)
    if s['kind']=='privacy':
        text(im,(97,451),'가상 원문',16,C['muted'])
        text(im,(744,451),'가명본',16,C['muted'])
        text(im,(97,483),'홍길동 교수',33,C['charcoal'],True)
        text(im,(97,536),'홍길동 교수가 검토함',23,C['muted'])
        arrow(im,462,511,679,p)
        reveal(im,lambda layer:text(layer,(744,483),'[연구자A] 교수',33,C['indigo'],True),p,dx=16,dy=0)
        reveal(im,lambda layer:text(layer,(744,536),'[연구자A] 교수가 검토함',23,C['indigo']),p,dx=16,dy=0)
        text(im,(65,621),'_private/  원값 매핑',19,C['muted'])
        text(im,(744,621),'out/  검증 게이트 통과분',19,C['indigo'],True)
    elif s['kind']=='proof':
        for i in range(7):
            x=98+i*43
            box(im,(x,455,x+31,464),C['blue'] if i<=int(u*.9) else C['line'],radius=4)
        text(im,(476,448),'문단 경계로 나누어 순차 점검',18,C['muted'])
        text(im,(97,495),'분석되어지고',35,C['charcoal'],True)
        line(im,[(96,516),(96+220*p,516)],C['gray'],2)
        arrow(im,407,515,605,p)
        reveal(im,lambda layer:text(layer,(687,495),'분석되고',35,C['indigo'],True),p,dx=12,dy=0)
        line(im,[(88,547),(1188,547)],C['line'])
        text(im,(98,563),'위치  §2.1 / C3',17,C['muted'])
        text(im,(484,563),'유형  이중피동',17,C['muted'])
        text(im,(841,563),'사유  피동 표현 중복',17,C['muted'])
    else:
        text(im,(97,458),'집필',16,C['muted'])
        text(im,(97,489),'보고서 초안',30,C['charcoal'],True)
        text(im,(97,541),'주장 · 수치 · 인용',22,C['muted'])
        arrow(im,351,521,490,p)
        line(im,[(529,452),(529,568)],C['blue'],4)
        text(im,(552,458),'별도 검토 역할',25,C['indigo'],True)
        text(im,(552,495),'읽기 전용 · 원문과 수치 대조',20,C['muted'])
        reveal(im,lambda layer:text(layer,(552,536),'위치·문제·수정안 반환',22,C['ink']),p,dy=8)
        arrow(im,882,521,958,ease((u-4.8)/.7))
        text(im,(1003,485),'검수',29,C['indigo'],True)
        text(im,(1003,528),'기록',29,C['indigo'],True)

def strengths(im,s,u):
    heading(im,'03','이 도구의 강점',s['feature_title'])
    for i,(name,body) in enumerate(s['features']):
        y=271+i*96
        def draw(layer,i=i,name=name,body=body,y=y):
            text(layer,(64,y),f'0{i+1}',43,C['blue'],True)
            text(layer,(156,y+3),name,27,C['ink'],True,maxw=330)
            text(layer,(540,y+7),body,24,C['muted'],maxw=670)
            line(layer,[(156,y+66),(1216,y+66)],C['line'])
        reveal(im,draw,(u-.6*i)/.6,dx=10,dy=0)
    paragraph(im,(64,592),s['note'],1148,19,C['muted'],gap=8)

def ending(im,s,u):
    text(im,(64,146),'한 걸음, 내 업무에서 시작하세요.',25,C['blue'],True)
    reveal(im,lambda layer:text(layer,(64,227),s['repo'],63,C['black'],True,maxw=1152),u/.6,dx=-18,dy=0)
    paragraph(im,(66,335),s['cta'],1142,31,C['muted'],True)
    band(im,(64,429,1216,537),slant=22)
    text(im,(91,450),'FIRST STEP',15,'white',True)
    text(im,(91,488),s['start_short'],26,'white',True,maxw=1060)
    text(im,(66,586),'github.com/parkjui92/'+s['repo'],24,C['indigo'],maxw=1130)

def frame(s,t,transition=True):
    i=max(k for k in range(5) if t>=TIMES[k])
    u=t-TIMES[i]
    im=Image.new('RGB',(W,H),'white')
    header(im,s,t)
    [hero,inputs,result,strengths,ending][i](im,s,u)
    if transition and i>0 and u<.3:
        im=Image.blend(frame(s,TIMES[i]-.001,False),im,ease(u/.3))
    return im

def brand_sheet(out):
    im=Image.new('RGB',(W,H),'white')
    logo(im,64,38,335)
    text(im,(64,169),'로고에서 출발하는 소개자료',42,C['black'],True)
    text(im,(64,242),'색 · 연결된 곡선 · 굵은 제목 · 넓은 흰 여백',25,C['muted'])
    for i,key in enumerate(['blue','indigo','gray','charcoal','tagline_gray']):
        x=64+i*230
        box(im,(x,325,x+207,435),C[key])
        text(im,(x,457),C[key],25,C['ink'],True)
        text(im,(x,498),key,19,C['muted'])
    band(im,(64,566,1216,584),slant=12)
    text(im,(64,625),'DESIGN.md  /  정책한걸음 · The Step in Public Policy',23,C['indigo'])
    im.save(out/'brand-board.png')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--spec',type=Path,default=ROOT/'intro.json')
    ap.add_argument('--output',type=Path)
    ap.add_argument('--fps',type=int,default=30)
    ap.add_argument('--stills',action='store_true')
    args=ap.parse_args()
    if not 1<=args.fps<=60:
        ap.error('--fps must be between 1 and 60')
    expected=TOKENS['source']['logo_png_sha256']
    if hashlib.sha256((ROOT/'brand-logo.png').read_bytes()).hexdigest()!=expected:
        raise RuntimeError('The original logo checksum does not match brand-tokens.json.')
    s=json.loads(args.spec.read_text(encoding='utf-8'))
    out=args.output or args.spec.parent
    out.mkdir(parents=True,exist_ok=True)
    points=[3.5,9.5,19,25.5,29.3]
    stills=[frame(s,t) for t in points]
    stills[0].save(out/'intro-poster.png')
    sheet=Image.new('RGB',(1920,1710),'white')
    for i,im in enumerate(stills):
        x,y=(i%2)*960,(i//2)*570
        sheet.paste(im.resize((960,540),Image.Resampling.LANCZOS),(x,y))
        ImageDraw.Draw(sheet).text((x+20,y+545),f'{TIMES[i]:02d}–{TIMES[i+1]:02d}s',font=font(14),fill=C['muted'])
    sheet.save(out/'intro-storyboard.png')
    brand_sheet(out)
    if args.stills:
        return
    if not shutil.which('ffmpeg'):
        raise RuntimeError('FFmpeg is required to render video.')
    command=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24',
             '-s',f'{W}x{H}','-r',str(args.fps),'-i','-','-an','-c:v','libx264','-threads','2',
             '-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'intro.mp4')]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE)
    try:
        for i in range(DURATION*args.fps):
            proc.stdin.write(frame(s,i/args.fps).tobytes())
        proc.stdin.close()
        if proc.wait():
            raise RuntimeError('Video encoding failed.')
    except BaseException:
        proc.kill()
        proc.wait()
        raise
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss','11','-t','9','-i',str(out/'intro.mp4'),
                    '-filter_complex','fps=10,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4',
                    '-loop','0',str(out/'intro-preview.gif')],check=True)
    print(s['repo']+': branded 1920x1080 / 30s MP4 and 9s GIF rendered',flush=True)

if __name__=='__main__':
    main()
