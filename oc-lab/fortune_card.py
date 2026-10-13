# 10-10 木木夕：运势表情包生成后同步出一张「今日运势签」（含表情包），用户下载分享
# 10-10 v2（木木夕定稿，v3 纸张版在 bak_v3）：按 KusArt VI v1.2 手绘层重做——纯白纸、墨线手绘框、小赖手写体、朱印只用一处品牌粉、胶带贴图、蓝色横格线，不用发光和模糊投影
import os,math,random,datetime
from PIL import Image,ImageDraw,ImageFont
HERE=os.path.dirname(os.path.abspath(__file__))
HAND=os.path.expanduser('~/.fonts/Xiaolai-Regular.ttf')
SERIF='/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc'
if not os.path.exists(SERIF): SERIF='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
SANS_B='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
F=lambda p,s:ImageFont.truetype(p,s,index=2 if p.endswith('.ttc') else 0)   # ttc 第 3 个是 SC 字形
INK=(11,11,13); INK2=(100,100,109); PINK=(216,27,96); BLUE=(85,155,255); TAPE=(255,227,238,200)
MARIQ='/var/www/kusart-lib/mariq/mari-q_{}.png'
FACE={'大吉':'face-star-eyes-sticker','吉':'face-happy-sticker','小吉':'face-peace-sticker','平':'face-think-sticker','凶':'face-cry-sticker'}
LOGO='/var/www/kusart-lib/brand/pack/kit/logo/kusart-logo-L1-fullcolor-tight.png'
W,H=1080,1720
S=2   # 超采样，手绘线更顺

def wrap(d,text,font,maxw):
  lines,cur=[],''
  for ch in text:
    if d.textlength(cur+ch,font=font)>maxw and cur:
      if ch in '，。！？、…」）': cur+=ch; continue   # 标点不放行首
      lines.append(cur); cur=ch
    else: cur+=ch
  if cur: lines.append(cur)
  return lines

def rough(d,pts,fill,w,rnd,jit=2.2,closed=False,passes=2):
  """手绘线：沿折线加细抖动，画两遍略错开，像笔描了两次"""
  if closed: pts=pts+[pts[0]]
  for k in range(passes):
    out=[]
    for i in range(len(pts)-1):
      (x0,y0),(x1,y1)=pts[i],pts[i+1]; n=max(2,int(math.hypot(x1-x0,y1-y0)/(18*S)))
      for t in range(n):
        f=t/n; out.append((x0+(x1-x0)*f+rnd.uniform(-jit,jit)*S,y0+(y1-y0)*f+rnd.uniform(-jit,jit)*S))
    out.append((pts[-1][0]+rnd.uniform(-jit,jit)*S,pts[-1][1]+rnd.uniform(-jit,jit)*S))
    d.line(out,fill=fill,width=int(w*S*(1 if k==0 else .6)),joint='curve')

def rrect_pts(x0,y0,x1,y1,r):
  pts=[]
  for cx,cy,a0 in((x1-r,y0+r,-90),(x1-r,y1-r,0),(x0+r,y1-r,90),(x0+r,y0+r,180)):
    for a in range(a0,a0+91,15): pts.append((cx+r*math.cos(math.radians(a)),cy+r*math.sin(math.radians(a))))
  return pts

def circle_pts(cx,cy,r,rnd,turns=1.08):
  a0=rnd.uniform(0,360); n=int(60*turns)
  return [(cx+r*(1+rnd.uniform(-.015,.015))*math.cos(math.radians(a0+360*turns*i/n)),cy+r*(1+rnd.uniform(-.015,.015))*math.sin(math.radians(a0+360*turns*i/n))) for i in range(n+1)]

def tape(w,h,rnd):
  t=Image.new('RGBA',(w,h),(0,0,0,0)); d=ImageDraw.Draw(t)
  jag=lambda x:[(x+rnd.uniform(-5,5)*S,y) for y in range(0,h+1,6*S)]
  l=jag(0); r=jag(w)[::-1]; d.polygon(l+r,fill=TAPE)
  for y in range(8*S,h,14*S): d.line([(10*S,y),(w-10*S,y)],fill=(255,255,255,70),width=S)
  return t

def make(meme_path,level,keywords,sign,name,out_path):
  rnd=random.Random(f'{name}{level}{sign}')
  im=Image.new('RGBA',(W*S,H*S),'#FFFFFF'); d=ImageDraw.Draw(im)
  # 手绘外框
  rough(d,rrect_pts(46*S,46*S,(W-46)*S,(H-46)*S,40*S),INK,3.2,rnd,jit=1.6,closed=True)
  # 顶部：日期 + 手写标题 + 波浪下划线
  t=datetime.datetime.now(); wk='一二三四五六日'[t.weekday()]
  d.text((W//2*S,150*S),'今日运势签',font=F(HAND,76*S),fill=INK,anchor='mm')
  d.text((W//2*S,222*S),f'{t:%Y.%m.%d}  星期{wk}',font=F(SANS,26*S),fill=INK2,anchor='mm')
  wave=[((W//2-150+i*6)*S,(190+4*math.sin(i/2.2))*S) for i in range(51)]
  rough(d,wave,INK,2.4,rnd,jit=.6,passes=1)
  # 朱印：全图唯一一处品牌粉，微微转一下像盖上去的
  st=Image.new('RGBA',(340*S,340*S),(0,0,0,0)); sd=ImageDraw.Draw(st); c=170*S
  rough(sd,circle_pts(c,c,138*S,rnd),PINK,5,rnd,jit=1.4,passes=1)
  rough(sd,circle_pts(c,c,124*S,rnd,turns=1.03),PINK,2.2,rnd,jit=1.2,passes=1)
  sd.text((c,c+6*S),level,font=F(SERIF,(170 if len(level)==1 else 108)*S),fill=PINK,anchor='mm')
  st=st.rotate(rnd.uniform(-9,-4),resample=Image.BICUBIC); im.alpha_composite(st,(W//2*S-c,(415-170)*S))
  # 三个关键词：手写 + 手绘下划线
  kf=F(HAND,46*S); gap=46*S; ky=640*S
  ws=[d.textlength(k,font=kf) for k in keywords]; x=(W*S-sum(ws)-gap*(len(ws)-1))/2
  for i,(k,w) in enumerate(zip(keywords,ws)):
    d.text((x+w/2,ky),k,font=kf,fill=INK,anchor='mm')
    rough(d,[(x-6*S,ky+34*S),(x+w+6*S,ky+30*S+rnd.uniform(-3,3)*S)],INK,2.6,rnd,jit=.8,passes=1)
    if i<len(ws)-1: d.text((x+w+gap/2,ky),'·',font=kf,fill=INK2,anchor='mm')
    x+=w+gap
  # 表情包：白边相纸 + 手绘框 + 两条胶带，微微歪
  m=Image.open(meme_path).convert('RGB'); boxw,boxh=700*S,500*S
  sc=min(boxw/m.width,boxh/m.height); m=m.resize((int(m.width*sc),int(m.height*sc)),Image.LANCZOS)
  pad=22*S; ph=Image.new('RGBA',(m.width+pad*2,m.height+pad*2),(0,0,0,0)); pd=ImageDraw.Draw(ph)
  pd.rectangle((0,0,ph.width-1,ph.height-1),fill='#FFFFFF'); ph.paste(m,(pad,pad))
  rough(pd,[(4*S,4*S),(ph.width-4*S,4*S),(ph.width-4*S,ph.height-4*S),(4*S,ph.height-4*S)],INK,2.6,rnd,jit=1.2,closed=True)
  ph=ph.rotate(rnd.uniform(-2.2,-1),resample=Image.BICUBIC,expand=True)
  mx=(W*S-ph.width)//2; my=712*S+(boxh+pad*2-ph.height)//2; im.alpha_composite(ph,(mx,my))
  tw,th=170*S,46*S
  for ang,(tx,ty) in((32,(mx-30*S,my+8*S)),(-28,(mx+ph.width-tw+34*S,my+4*S))):
    tp=tape(tw,th,rnd).rotate(ang,resample=Image.BICUBIC,expand=True); im.alpha_composite(tp,(int(tx),int(ty-tp.height/3)))
  # 签文：手写体压在蓝色横格线上
  sf=F(HAND,48*S); txt='「'+(sign or '今天也会是不错的一天。')+'」'; lines=wrap(d,txt,sf,(W-240)*S)
  if len(lines)>1: lines=wrap(d,txt,sf,min((W-240)*S,d.textlength(txt,font=sf)/len(lines)+60*S))   # 均分行长，避免最后一行只剩两三个字
  lines=lines[:3]
  y0=1335 if len(lines)<=2 else 1318; lh=68
  for i,ln in enumerate(lines):
    yy=(y0+i*lh)*S; d.text((W//2*S,yy),ln,font=sf,fill=INK,anchor='mm')
  for i in range(max(len(lines),2)):
    yy=(y0+i*lh+33)*S; d.line([(120*S,yy),((W-120)*S,yy)],fill=BLUE+(128,),width=int(1.5*S))
  # 署名（10-10 木木夕：去掉茉莉表情）
  ny=1548
  d.text(((W-120)*S,ny*S),f'—— {name}',font=F(HAND,44*S),fill=INK,anchor='rm')
  # 页脚：logo 放深色胶囊（VI：白底上 logo 进 rgba(7,8,11,.72) 胶囊）+ 网址
  lg=Image.open(LOGO).convert('RGBA'); lh_=40*S; lg=lg.resize((int(lg.width*lh_/lg.height),lh_),Image.LANCZOS); pp=10*S
  cap=Image.new('RGBA',(lg.width+pp*2+lh_//2,lh_+pp*2),(0,0,0,0)); ImageDraw.Draw(cap).rounded_rectangle((0,0,cap.width-1,cap.height-1),cap.height//2,fill=(7,8,11,184))
  cap.alpha_composite(lg,((cap.width-lg.width)//2,pp)); im.alpha_composite(cap,(96*S,(H-78)*S-cap.height))
  d.text(((W-96)*S,(H-78)*S-cap.height//2),'和你的角色一起抽今日运势 · kusart.com',font=F(SANS,24*S),fill=INK2,anchor='rm')
  im.convert('RGB').resize((W,H),Image.LANCZOS).save(out_path,quality=92)
  return out_path
