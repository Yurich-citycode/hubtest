"""Render the YuRich digital-city editorial loop (no generated-image dependency).
Run from repository root: .venv/bin/python video/projects/digital-city/render.py
Dependencies: pillow, numpy, imageio-ffmpeg. Outputs to video/renders/digital-city/.
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'video' / 'renders' / 'digital-city'
OUT.mkdir(parents=True, exist_ok=True)
W,H,FPS,SECONDS = 1600,640,30,8
PINK=(255,79,163); LIME=(216,255,62); WHITE=(240,239,232); MUTED=(145,149,151)
fonts=ROOT/'brand/covers/fonts'
def font(size,weight='700'):
    return ImageFont.truetype(str(fonts/f'inter-{weight}.ttf'),size)
def smooth(x):
    x=max(0,min(1,x));return x*x*(3-2*x)
# A restrained, fixed graphite atmosphere: no grid and no moving texture noise.
y,x=np.mgrid[0:H,0:W]
haze=np.exp(-(((x-1120)/680)**2+((y-360)/300)**2))
base=np.zeros((H,W,3),dtype=np.uint8)
for c,v in enumerate((14,15,17)):base[:,:,c]=(v+8*haze).astype(np.uint8)
base=Image.fromarray(base)
def txt(d,xy,s,size=20,color=WHITE,weight='400'):
    d.text(xy,s,font=font(size,weight),fill=color)
def pathdraw(d,points,progress,color,width=3):
    lengths=[math.dist(a,b) for a,b in zip(points,points[1:])]
    remain=sum(lengths)*max(0,min(1,progress))
    for a,b,l in zip(points,points[1:],lengths):
        if remain<=0:break
        q=min(1,remain/l)
        e=(a[0]+(b[0]-a[0])*q,a[1]+(b[1]-a[1])*q)
        d.line([a,e],fill=color,width=width)
        remain-=l

def frame(t):
    im=base.copy();d=ImageDraw.Draw(im)
    txt(d,(86,46),'YuRich / DIGITAL CITIES',15,MUTED,'600')
    txt(d,(86,96),'A CITY IS NOT A TOKEN',70,WHITE,'700')
    end=86+d.textlength('A CITY IS NOT A TOKEN',font=font(70,'700'))
    d.ellipse((end+8,150,end+19,161),fill=PINK)
    txt(d,(90,198),'Useful services. Real businesses. Enforceable rights.',24,MUTED)
    txt(d,(90,302),'THE PROMISE',16,PINK,'600')
    txt(d,(555,302),'THE WORKING CITY',16,LIME,'600')
    # Baseline paths are visible throughout. Rights branch explicitly separate.
    route=[(306,394),(450,394),(450,374),(630,374),(970,374)]
    rights=[(970,374),(1050,374),(1100,424),(1340,424)]
    d.line(route,fill=(51,56,43),width=2)
    d.line(rights,fill=(51,56,43),width=2)
    d.ellipse((200,365,258,423),outline=PINK,width=2)
    txt(d,(219,377),'?',24,PINK,'600')
    # Dashed speculation, animated in rather than sliding continuously.
    active=smooth((t-.15)/1.2)*(1-smooth((t-6.6)/1.4))
    motion=Image.new('RGBA',(W,H));md=ImageDraw.Draw(motion)
    for i in range(7):
        a=270+i*23
        md.line((a,394,a+11,394),fill=(*PINK,int(230*active)),width=3)
    for i in range(4):
        a=254+i*23
        md.line((a,353-i*4,a+11,351-i*4),fill=(*PINK,int(100*active)),width=2)
    p=smooth((t-1.3)/3.2)
    fade=1-smooth((t-6.5)/1.5)
    pathdraw(md,route,p,(*LIME,int(255*fade)),4)
    pathdraw(md,rights,smooth((t-3.9)/1.1),(*LIME,int(255*fade)),3)
    nodes=[(630,374,2.1),(970,374,3.3),(1340,424,4.7)]
    for nx,ny,start in nodes:
        v=smooth((t-start)/.5)*fade
        d.ellipse((nx-8,ny-8,nx+8,ny+8),fill=(26,29,24),outline=(90,103,52),width=2)
        md.ellipse((nx-8,ny-8,nx+8,ny+8),fill=(*LIME,int(255*v)))
        pulse=max(0,1-abs(t-start-.4)/.7)*fade
        if pulse:
            r=10+23*(1-pulse)
            md.ellipse((nx-r,ny-r,nx+r,ny+r),outline=(*LIME,int(140*pulse)),width=2)
    # Restrained local bloom only around the active lines; text stays crisp.
    glow=motion.filter(ImageFilter.GaussianBlur(9))
    im=Image.alpha_composite(im.convert('RGBA'),glow)
    im=Image.alpha_composite(im,motion).convert('RGB');d=ImageDraw.Draw(im)
    txt(d,(90,450),'A story about the future',17,MUTED)
    txt(d,(555,409),'01 / USE',24,LIME,'600')
    txt(d,(555,447),'Book a service',20,WHITE)
    txt(d,(875,409),'02 / RETURN',24,LIME,'600')
    txt(d,(875,447),'Get partner benefits',20,WHITE)
    txt(d,(1190,458),'03 / HOLD A RIGHT',22,LIME,'600')
    txt(d,(1190,493),'Know who owes you',19,WHITE)
    txt(d,(1113,376),'Separate legal structure',14,MUTED)
    d.line((90,550,1510,550),fill=(47,49,51),width=1)
    txt(d,(90,580),'ACCESS IS NOT AN INVESTMENT RIGHT',16,MUTED,'600')
    txt(d,(1380,576),'by YuRich',21,WHITE,'600')
    return im

writer=imageio_ffmpeg.write_frames(str(OUT/'digital-city-loop.mp4'),(W,H),fps=FPS,
    codec='libx264',pix_fmt_in='rgb24',pix_fmt_out='yuv420p',quality=8,
    output_params=['-movflags','+faststart','-an','-profile:v','high'])
writer.send(None)
gif=[]
for i in range(FPS*SECONDS):
    f=frame(i/FPS);writer.send(np.asarray(f))
    if i%3==0:gif.append(f.resize((1000,400),Image.Resampling.LANCZOS))
writer.close()
# Shared palette avoids flashing in the GIF.
palette=frame(5.8).resize((1000,400)).quantize(colors=128)
frames=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in gif]
frames[0].save(OUT/'digital-city-loop.gif',save_all=True,append_images=frames[1:],duration=100,loop=0,optimize=True)
frame(5.8).save(OUT/'digital-city-cover.png')
print(OUT)
for p in OUT.iterdir():print(p.name,p.stat().st_size)
