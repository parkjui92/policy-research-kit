#!/usr/bin/env python3
"""Render a 30-second terminal/file walkthrough from intro.json.

Requires Python 3.9+, Pillow, FFmpeg and Korean fonts. No network calls.
INTRO_FONT, INTRO_FONT_BOLD and INTRO_FONT_MONO override font paths.
"""
from __future__ import annotations
import argparse
from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
S=1.5
W,H=1920,1080
DURATION=30
TIMES=[0,7,14,23,30]
C={'paper':'#F6F8FB','ink':'#171722','muted':'#5B5B60','line':'#D9DFEA','pale':'#EEF5FB',
   'blue':'#0071BC','indigo':'#1B1464','terminal':'#161B22','termtext':'#E6EDF3','termmuted':'#A8B3C4','accent':'#79C0FF'}

def sc(v): return round(v*S)
def xy(v): return tuple(sc(x) for x in v)
def ease(t): return 1-(1-max(0,min(1,t)))**3

@lru_cache(maxsize=40)
def font(size,bold=False,mono=False):
    env='INTRO_FONT_MONO' if mono else 'INTRO_FONT_BOLD' if bold else 'INTRO_FONT'
    files=[os.getenv(env,''),str(Path.home()/'Library/Fonts'/('Pretendard-Bold.otf' if bold else 'Pretendard-Regular.otf')),
           '/System/Library/Fonts/AppleSDGothicNeo.ttc','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']
    if mono:
        files.insert(1,'/System/Library/Fonts/Menlo.ttc')
    for p in files:
        if p and Path(p).is_file(): return ImageFont.truetype(p,sc(size))
    raise RuntimeError('Set INTRO_FONT and INTRO_FONT_BOLD to Korean-capable font files.')

def tw(value,size,bold=False,mono=False):
    return font(size,bold,mono).getlength(value)/S

def text(im,x,y,value,size=24,color=None,bold=False,maxw=None,mono=False):
    if maxw and tw(value,size,bold,mono)>maxw+1:
        raise ValueError(f'Text overflow ({maxw}): {value}')
    ImageDraw.Draw(im).text(xy((x,y)),value,font=font(size,bold,mono),fill=color or C['ink'],anchor='lt')

def rect(im,bounds,fill,outline=None,r=0,width=1):
    ImageDraw.Draw(im).rounded_rectangle(xy(bounds),sc(r),fill,outline,sc(width))

def line(im,points,color,width=1):
    ImageDraw.Draw(im).line([xy(x) for x in points],fill=color,width=sc(width))

def wrap(value,width,size,bold=False):
    result=[]
    for part in value.split('\n'):
        current=''
        for ch in part:
            if current and tw(current+ch,size,bold)>width:
                result.append(current.rstrip()); current=ch.lstrip()
            else: current+=ch
        result.append(current)
    return result

@lru_cache(maxsize=1)
def logo():
    im=Image.open(ROOT/'brand-logo.png').convert('RGBA')
    im=im.crop(im.getchannel('A').getbbox())
    return im.resize((144,round(im.height*144/im.width)),Image.Resampling.LANCZOS)

def chrome(im,s,idx,t):
    text(im,48,29,s['repo'],24,C['indigo'],True)
    text(im,48+tw(s['repo'],24,True)+23,34,s['category'],17,C['muted'])
    im.paste(logo(),xy((1136,27)),logo())
    line(im,[(48,69),(1232,69)],C['line'])
    text(im,48,92,f'{idx+1:02}',24,C['blue'],True)
    text(im,96,88,s['scenes'][idx]['title'],30,C['ink'],True,maxw=1136)
    text(im,48,639,s['scenes'][idx]['caption'],23,C['indigo'],True,maxw=1184)
    text(im,48,688,s['provenance'],16,C['muted'])
    text(im,936,688,'30초 소개 · 실제 실행시간과 무관',16,C['muted'])
    rect(im,(0,716,1280,720),C['line'])
    if t>0: rect(im,(0,716,max(1,1280*t/DURATION),720),C['blue'])

def shell(im,p,bounds):
    x,y,x2,y2=bounds
    term=p['kind']=='terminal'
    bg=C['terminal'] if term else '#FFFFFF'
    rect(im,bounds,bg,C['line'],r=10)
    rect(im,(x+1,y+1,x2-1,y+43),'#222933' if term else '#EDF0F5',r=9)
    rect(im,(x+1,y+29,x2-1,y+43),'#222933' if term else '#EDF0F5')
    for i,c in enumerate(['#F17C79','#E8BE63','#7DBA80']):
        ImageDraw.Draw(im).ellipse(xy((x+17+i*18,y+17,x+26+i*18,y+26)),fill=c)
    text(im,x+87,y+14,p['title'],16,C['termmuted'] if term else C['muted'],maxw=x2-x-105)
    if not term:
        line(im,[(x+48,y+55),(x+48,y2-16)],'#EDF0F5')
    return term

def rows(im,p,bounds,u):
    x,y,x2,y2=bounds
    term=shell(im,p,bounds)
    size=24 if x2-x>800 else 21
    left=x+26 if term else x+66
    width=x2-left-24
    gap=39 if x2-x>800 else 38
    top=y+76
    # Lines appear in order, then remain long enough to read.
    for i,item in enumerate(p['lines']):
        value=item['text']; style=item['style']
        start=(1.3+i*.19) if i>0 and p['lines'][0]['style']=='command' else .25+i*.19
        if u<start: continue
        alpha=ease((u-start)/.3)
        dark=C['termtext'] if term else C['ink']
        colors={'accent':C['accent'] if term else C['blue'],'heading':C['accent'] if term else C['indigo'],
                'command':'#FFFFFF' if term else C['ink'],'muted':C['termmuted'] if term else C['muted'],
                'success':'#7EE2A8' if term else C['blue'],'highlight':dark}
        color=colors.get(style,dark)
        bold=style in ['heading','accent','success']
        yy=top+i*gap
        if yy+size>y2-16: raise ValueError('Vertical overflow: '+value)
        layer=Image.new('RGBA',(W,H))
        if style=='highlight':
            rect(layer,(left-7,yy-6,x2-19,yy+size+9),'#273544' if term else '#EDF5FD',r=3)
            rect(layer,(left-7,yy-6,left-4,yy+size+9),C['blue'])
        # Animate command typing; all other rows reveal quickly.
        shown=value
        if style=='command' and i==0:
            count=int(len(value)*min(1,max(0,(u-start)/1.1)))
            shown=value[:count]
            if count<len(value): shown+='|'
        # Keep command line lengths reproducible, wrapping only where needed.
        parts=wrap(shown,width,size,bold)
        if len(parts)>1:
            # Long commands get a modest local font reduction; never below 18px.
            local=size
            while tw(shown,local,bold)>width and local>18: local-=.5
            text(layer,left,yy,shown,local,color,bold,maxw=width)
        else:
            text(layer,left,yy,shown,size,color,bold,maxw=width)
        if not term:
            text(layer,x+17,yy,str(i+1),15,'#939DAA')
        if alpha<1: layer.putalpha(layer.getchannel('A').point(lambda a:round(a*alpha)))
        im.paste(layer,(0,0),layer)

def table(im,scene,bounds,u):
    x,y,x2,y2=bounds
    shell(im,scene['panels'][0],bounds)
    left=x+25; top=y+78
    widths=[165,215,478,250]
    cols=[left]
    for w in widths: cols.append(cols[-1]+w)
    rect(im,(left,top,cols[-1],top+48),C['indigo'])
    for i,value in enumerate(scene['table']['headers']):
        text(im,cols[i]+12,top+14,value,20,'#FFFFFF',True,maxw=widths[i]-24)
    for j,row in enumerate(scene['table']['rows']):
        if u<.4+j*.55: continue
        yy=top+48+j*83
        rect(im,(left,yy,cols[-1],yy+83),C['pale'] if j%2==0 else '#FFFFFF')
        for i,value in enumerate(row):
            parts=wrap(value,widths[i]-26,21,i==2)
            for k,part in enumerate(parts):
                text(im,cols[i]+12,yy+20+k*28,part,21,C['blue'] if i==2 else C['ink'],i==2,maxw=widths[i]-24)
        line(im,[(left,yy+83),(cols[-1],yy+83)],C['line'])
    text(im,left,top+333,scene['footnote'],21,C['muted'],maxw=1108)

@lru_cache(maxsize=40)
def content_frame(spec_json,idx,u):
    s=json.loads(spec_json)
    im=Image.new('RGB',(W,H),C['paper'])
    scene=s['scenes'][idx]
    if 'table' in scene:
        table(im,scene,(48,151,1232,616),u)
    else:
        panels=scene['panels']
        bounds=[(48,151,1232,616)] if len(panels)==1 else [(48,151,630,616),(650,151,1232,616)]
        for panel,box in zip(panels,bounds): rows(im,panel,box,u)
    return im

def frame(s,t):
    idx=max(i for i in range(4) if t>=TIMES[i])
    u=t-TIMES[idx]
    # After the reveal, reuse the stable screen and animate only progress.
    im=content_frame(json.dumps(s,ensure_ascii=False),idx,round(min(u,3),3)).copy()
    chrome(im,s,idx,t)
    if idx and u<.22:
        before=content_frame(json.dumps(s,ensure_ascii=False),idx-1,3).copy()
        chrome(before,s,idx-1,t)
        im=Image.blend(before,im,ease(u/.22))
    return im

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--spec',type=Path,default=ROOT/'intro.json')
    ap.add_argument('--output',type=Path)
    ap.add_argument('--fps',type=int,default=30)
    ap.add_argument('--stills',action='store_true')
    args=ap.parse_args()
    if not 1<=args.fps<=60: ap.error('--fps must be between 1 and 60')
    s=json.loads(args.spec.read_text())
    tokens=json.loads((ROOT/'brand-tokens.json').read_text())
    if hashlib.sha256((ROOT/'brand-logo.png').read_bytes()).hexdigest()!=tokens['source']['logo_png_sha256']:
        raise RuntimeError('Logo differs from the supplied original.')
    out=args.output or args.spec.parent
    out.mkdir(parents=True,exist_ok=True)
    times=[5.5,12,20,28]
    stills=[frame(s,t) for t in times]
    stills[2].save(out/'intro-poster.png')
    board=Image.new('RGB',(1920,1140),'#FFFFFF')
    for i,im in enumerate(stills):
        x,y=(i%2)*960,(i//2)*570
        board.paste(im.resize((960,540),Image.Resampling.LANCZOS),(x,y))
        ImageDraw.Draw(board).text((x+20,y+547),f'{TIMES[i]:02d}–{TIMES[i+1]:02d}s',font=font(13),fill=C['muted'])
    board.save(out/'intro-storyboard.png')
    if args.stills: return
    if not shutil.which('ffmpeg'): raise RuntimeError('FFmpeg is required.')
    proc=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}',
        '-r',str(args.fps),'-i','-','-an','-c:v','libx264','-threads','2','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'intro.mp4')],stdin=subprocess.PIPE)
    try:
        for i in range(DURATION*args.fps): proc.stdin.write(frame(s,i/args.fps).tobytes())
        proc.stdin.close()
        if proc.wait(): raise RuntimeError('Encoding failed.')
    except BaseException:
        proc.kill(); proc.wait(); raise
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(out/'intro.mp4'),'-filter_complex',
        'fps=8,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4',
        '-loop','0',str(out/'intro-preview.gif')],check=True)
    print(s['repo']+': 30s screen walkthrough rendered',flush=True)

if __name__=='__main__': main()
