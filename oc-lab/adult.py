# 10-10 成人模式（测试版）：8 类成人向类型卡 → 剧情列表 → 互动剧情播放器（视频 + 台词 + 选项分支）
# 搬家约定：剧情 = 一个 manifest JSON（adult/stories/<id>.json，按 char.type 归类），媒体在 adult/media/<id>/，
# 类型卡封面/悬停视频在 adult/cards/。正式版只需按这里的输入输出重写；登录闸门沿用 app.before_request。
# 🔴成人内容不进「大家创建的角色」/api/chars 等公开列表，也不写 chars/。
import os,json,glob,re
from flask import Blueprint,request,jsonify,send_file,abort
bp=Blueprint('adult',__name__)
HERE=os.path.dirname(os.path.abspath(__file__))
AD=os.path.join(HERE,'adult'); STORIES=os.path.join(AD,'stories'); MEDIA=os.path.join(AD,'media'); CARDS=os.path.join(AD,'cards')
MOCK='/tmp/cl8/adult_mock.json'   # 开发用：/adult/stories?mock=1 才会出现，id=mock
# 已立项的剧情：manifest 还没产出时也在列表里占位（点进去显示「这段还在制作中」）
PLANNED=[dict(id='grace_office',type='御姐',title='加班后的办公室',desc='深夜只剩你们两个人……',name_zh='格蕾丝')]

def _safe(root,rel):
  p=os.path.normpath(os.path.join(root,rel))
  if not p.startswith(root+os.sep) or not os.path.isfile(p): abort(404)
  return p
def _load(p):
  try: return json.load(open(p))
  except Exception as e: print('adult manifest',p,e); return None
def _brief(m,ready=True):
  ch=m.get('char') or {}; sc=m.get('scenario') or {}
  return dict(id=m.get('id'),type=ch.get('type'),title=sc.get('title'),desc=sc.get('desc'),cover=sc.get('cover') or ch.get('cover'),
              name=ch.get('name_zh') or ch.get('name'),nodes=len(m.get('nodes') or {}),ready=ready)
def manifests(mock=False):
  out={}
  for p in sorted(glob.glob(os.path.join(STORIES,'*.json'))):
    fid=os.path.basename(p)[:-5]
    if '_bak' in fid or fid.endswith('_persona'): continue   # 备份 / 人设文件不算剧情
    m=_load(p)
    if m and m.get('nodes') and m.get('id',fid)==fid: m['id']=fid; out[fid]=m
  if mock and os.path.exists(MOCK):
    m=_load(MOCK)
    if m: m['id']='mock'; out['mock']=m
  return out

@bp.get('/adult/stories')
def stories():
  ms=manifests(request.args.get('mock')=='1'); rows=[_brief(m) for m in ms.values()]
  for p in PLANNED:
    if p['id'] not in ms: rows.append(dict(p,cover=None,nodes=0,ready=False))
  r=jsonify(stories=rows); r.headers['Cache-Control']='no-store'; return r
@bp.get('/adult/story/<sid>')
def story(sid):
  sid=os.path.basename(sid); m=manifests(sid=='mock').get(sid)
  if not m: return jsonify(error='missing',id=sid),404
  r=jsonify(m); r.headers['Cache-Control']='no-store'; return r
@bp.get('/adult/media/<path:rel>')
def media(rel): return send_file(_safe(MEDIA,rel),max_age=3600,conditional=True)   # conditional → 支持 Range，iOS 播视频要
@bp.get('/adult/cards/<name>')
def cards(name): return send_file(_safe(CARDS,os.path.basename(name)),max_age=86400,conditional=True)
@bp.post('/adult/custom')
def adult_custom():   # 10-10 木木夕：自定义剧情（会员专属）——先收需求进队列，Mari 后面按队列做
  import json as _j,time as _t
  from flask import request,jsonify
  d=request.get_json(silent=True) or {}
  rec={k:str(d.get(k,''))[:200] for k in ('type','name','place','relation','note')}; rec['moods']=[str(x)[:8] for x in (d.get('moods') or [])][:6]
  if not rec['place'] or not rec['relation']: return jsonify(error='缺少场景或关系'),400
  rec['created']=_t.strftime('%Y-%m-%d %H:%M:%S')
  with open(os.path.join(HERE,'adult','custom_requests.jsonl'),'a') as f: f.write(_j.dumps(rec,ensure_ascii=False)+'\n')
  return jsonify(ok=True)
@bp.get('/adult.js')
def adult_js(): return send_file(os.path.join(HERE,'adult.js'),max_age=0)
@bp.get('/adult.css')
def adult_css(): return send_file(os.path.join(HERE,'adult.css'),max_age=0)

# ---------- 10-10 木木夕：角色资料「＋自定义」——从 tag 库（adult/pose_tags.json）选姿势/穿着/尺度/场景… 用这个角色的配方出一张
# 角色部分（外貌 + 成年锚点）和负面词直接取 album.json 第一张图的配方，保证是同一个人；结果存 adult/gen/，配方写 works.jsonl。
import threading,time,uuid,io,requests
A=None
def init(app_mod):
  global A; A=app_mod
GEN=os.path.join(AD,'gen'); os.makedirs(GEN,exist_ok=True); WORKS=os.path.join(GEN,'works.jsonl')
MALE={'型男','熟男','兽人'}; GJOBS={}
def _tags(): return json.load(open(os.path.join(AD,'pose_tags.json')))
def _album(): return json.load(open(os.path.join(CARDS,'album.json')))
@bp.get('/adult/pose_tags')
def pose_tags(): r=jsonify(_tags()); r.headers['Cache-Control']='no-store'; return r
def _picks_en(picks,g,cats=None):
  cats={c['id']:c for c in _tags()['cats']}; en=[]; used=[]
  for pk in picks:
    c=cats.get(pk.get('cat'))
    if not c: continue
    t=next((t for t in c['tags'] if t['zh']==pk.get('zh') and t.get('g',g)==g),None)
    if not t or sum(1 for u in used if u['cat']==c['id'])>=c.get('max',1): continue
    used.append(dict(cat=c['id'],cat_name=c['name'],zh=t['zh'])); en.append(t['en'])
  if not used: raise ValueError('至少选一个 tag')
  if not any(u['cat']=='scene' for u in used): en.append('dim boudoir background')
  return en,used
def _body(base,en,neg,sid,w,h,furry):
  s=', '.join(en)
  if furry: s=s.replace('penis','animal penis, sheath')
  prompt=f"{base}, {s}. A single adult character alone in one seamless illustration."
  if sid.startswith('anima_'):
    body={"task_type":"ANIMA_TEXT_TO_IMAGE","params":{"prompt":prompt,"negative_prompt":neg,"width":w,"height":h,"amount":1,"turbo":True,"use_layer_replay":True,"use_aesthetic":True,"style_ids":[sid],"is_public":False,"watermark":False}}
  else:
    body={"task_type":"TEXT_TO_IMAGE","params":{"prompt":prompt,"negative_prompt":neg,"style_id":sid,"width":w,"height":h,"amount":1,"is_public":False,"watermark":False}}
  return body,prompt
def _build(typ,picks):
  a=_album().get(typ)
  if not a: raise ValueError('没有这个类型')
  rc=a['imgs'][0]['recipe']; p=rc['prompt']; i=p.find('years old')
  if i<0: raise ValueError('角色配方缺成年锚点')
  base=p[:i+len('years old')]; g='m' if typ in MALE else 'f'
  en,used=_picks_en(picks,g)
  sid=str(rc.get('style_id')); w,h=(int(x) for x in (rc.get('size') or '832x1216').split('x'))
  body,prompt=_body(base,en,rc['negative_prompt'],sid,w,h,typ=='兽人')
  recipe=dict(model=rc.get('model'),style_name=rc.get('style_name'),style_id=sid,size=f'{w}x{h}',prompt=prompt,negative_prompt=rc['negative_prompt'],source='角色资料 · 自定义 tag')
  return body,recipe,used,a

# ---------- 10-10 木木夕：普通角色主页的「成人模式」按钮 → 用这个用户角色进成人出图页；作品按 cid 存，只在成人模式下的角色主页显示
# 🔴 年龄闸门：只有年龄感是成年/成熟/年长、且类型不是少女/少年/萝莉/正太/甜妹/奶系 的角色才能进；外形标签由视觉模型从立绘读，不读服装。
ADULT_AGE={'成年','成熟','年长'}; MINOR_T={'少女','少年','少男','萝莉','正太','甜妹','奶系'}
MALE_OC={'熟男','成男','少年','少男','正太','男娘','奶系'}
OCD=os.path.join(AD,'oc'); os.makedirs(OCD,exist_ok=True)
def _oc(cid):
  p=os.path.join(HERE,'chars',os.path.basename(cid)+'.json')
  if not os.path.exists(p): abort(404)
  return json.load(open(p))
MINOR_W=re.compile(r'少女|少年|萝莉|正太|小女孩|小男孩|幼|童|学生|初中|高中|JK|DK|小学|未成年')
def _look(c):   # 10-10 🔴 立绘看起来像不像小孩/Q版比例 —— 年龄感字段是用户自己选的，不可信，必须再看图（按立绘缓存）
  f=os.path.join(OCD,(c.get('id') or 'x')+'_age.json')
  if os.path.exists(f):
    d=json.load(open(f))
    if d.get('img')==c.get('img'): return d
  r=A.llm('You are a strict safety reviewer for an adult-content feature. Look at the character illustration and judge whether the character clearly reads as an ADULT. '
          'Output JSON {"adult":true|false,"reason":"简体中文一句话"}. Answer false if ANY of: childlike or teen face, chibi / super-deformed or big-head proportions (head taller than about 1/5 of body height), short child-like body, school uniform, or the character could plausibly be a minor. '
          'For furry/anthro characters judge by body proportions and build the same way. When unsure, answer false.',
          '判断这个角色是否明确是成年人。',model=A.VISION,img=_imgurl(c.get('img','')))
  d=dict(img=c.get('img'),adult=bool(r.get('adult')) and r.get('adult') is not False,reason=str(r.get('reason',''))[:80]); json.dump(d,open(f,'w'),ensure_ascii=False); return d
def _oc_ok(c,look=True):
  txt=' '.join(str(c.get(k,'')) for k in ('name','bio','desc','role'))
  m=MINOR_W.search(txt)
  if m: return False,f"{c.get('name')} 的设定里写着「{m.group(0)}」，成人模式只对明确成年的角色开放"
  if c.get('age') not in ADULT_AGE: return False,f"{c.get('name')} 的年龄感是「{c.get('age') or '未填'}」，只有成年人设能进成人模式"
  if c.get('type') in MINOR_T: return False,f"{c.get('name')} 的类型是「{c.get('type')}」，只有成年人设能进成人模式"
  if look:
    d=_look(c)
    if not d['adult']: return False,f"{c.get('name')} 的立绘看起来不像成年人（{d['reason']}），成人模式只对明确成年的角色开放"
  return True,''
def _oc_g(c): return 'm' if (c.get('gender')=='男' or (not c.get('gender') and c.get('type') in MALE_OC)) else 'f'
def _imgurl(u):
  if u.startswith('http'): return u
  import base64; f=os.path.join(HERE,u.lstrip('./'))
  return 'data:image/png;base64,'+base64.b64encode(open(f,'rb').read()).decode()
def _oc_tags(cid,c):
  f=os.path.join(OCD,cid+'.json')
  if os.path.exists(f):
    d=json.load(open(f))
    if d.get('img')==c.get('img') and 'style' in d and 'breasts' in d: return d
  furry=c.get('type') in ('Furry','兽耳 / 兽人')
  sysm=('You turn a character illustration into English Danbooru appearance tags for an ADULT version of the same character. Output JSON only: {"tags":"..."}. '
        'Start with '+('"anthro, furry, <species>"' if furry else ('"1boy, solo, male focus"' if _oc_g(c)=='m' else '"1girl, solo"'))+'. '
        'Then ONLY body-independent identity features: hair colour and style, eye colour, species/ears/tail/horns/wings, skin or fur colour, facial marks (mole, scar, eyepatch, freckles), earrings and hair accessories. '
        'NO clothing, NO pose, NO expression, NO background, NO body size or age words, no weights or brackets. 8-20 tags, lowercase, comma separated.')
  r=A.llm(sysm,f"角色外形描述：{c.get('desc','')}",model=A.VISION,img=_imgurl(c.get('img','')))
  t=re.sub(r'\b(child|loli|shota|teen|young|petite|small|flat chest|kid)\w*\b','',r.get('tags','')).strip(' ,')
  # 10-10 木木夕：成人图画风跑偏（夜景/裸露场景会把画风拉成油亮厚涂）→ 再让视觉模型读一次立绘的「渲染方式」补进提示词；颜色类词去掉（会把发色洗掉）
  st=A.llm('You describe ONLY the art style (rendering) of an anime illustration as English Danbooru-style tags. Output JSON {"style":"...","avoid":"..."}. '
           'style: 6-12 tags about line art, colouring, shading, texture (e.g. sketch, thin lineart, flat color, cel shading, watercolor). '
           'avoid: 4-8 tags of rendering looks this image clearly does NOT have (e.g. shiny skin, glossy, 3d, realistic, heavy shading). No subject, clothing or background words.',
           'Describe the rendering style.',model=A.VISION,img=_imgurl(c.get('img','')))
  sty=', '.join(x for x in (y.strip() for y in st.get('style','').split(',')) if x and not re.search(r'colou?r|hair|palette|saturat|gradient|background',x))
  avoid=st.get('avoid','').strip(' ,')+', shiny skin, glossy skin, oily skin'
  # 10-10 木木夕：非巨乳角色被画成巨乳 → 从立绘读胸型和体型，写进正面，负面压掉更大的尺寸
  bd=A.llm('Look at the character illustration and judge body build as drawn. Output JSON {"breasts":"flat|small|medium|large|huge|none","build":"slim|average|curvy|muscular|chubby"}. '
           'breasts=none for male characters. Judge what is drawn: flat = flat chest, small = clearly small chest, medium = average adult woman (use this when clothing makes it hard to tell), large = clearly big, huge = exaggerated. Do not exaggerate either way.','判断立绘里的胸型和体型。',model=A.VISION,img=_imgurl(c.get('img','')))
  br=bd.get('breasts') if bd.get('breasts') in BR else 'medium'
  d=dict(img=c.get('img'),tags=t,style=sty,avoid=avoid,breasts=br,build=bd.get('build') if bd.get('build') in ('slim','average','curvy','muscular','chubby') else 'average')
  json.dump(d,open(f,'w'),ensure_ascii=False); return d
BR=('flat','small','medium','large','huge','none'); BU=('slim','average','curvy','muscular','chubby')
BR_EN={'flat':'flat chest','small':'small breasts','medium':'medium breasts','large':'large breasts','huge':'huge breasts'}
BU_EN={'slim':'slender','curvy':'curvy','muscular':'muscular','chubby':'plump'}
BR_NEG={'flat':', medium breasts, large breasts, huge breasts, gigantic breasts','small':', large breasts, huge breasts, gigantic breasts, big breasts','medium':', huge breasts, gigantic breasts','large':', gigantic breasts'}
def _oc_build(cid,picks,body=None):
  body=body or {}
  c=_oc(cid); ok,why=_oc_ok(c)
  if not ok: raise ValueError(why)
  g=_oc_g(c); furry=c.get('type') in ('Furry','兽耳 / 兽人')
  ref=_album()['兽人' if furry and g=='m' else ('型男' if g=='m' else '御姐')]['imgs'][0]['recipe']
  anchor='adult man, mature masculine face, adult male body, adult, mature, 30+ years old' if g=='m' else 'adult woman, mature adult face, womanly figure, adult, mature, 25+ years old'
  ot=_oc_tags(cid,c)
  # 10-10 木木夕：进成人出图页时先按立绘把体型写进默认提示词（成年角色也有贫乳）；页面上可改（body 参数），只认白名单值
  br=body.get('breasts') if body.get('breasts') in BR else ot.get('breasts','medium'); bu=body.get('build') if body.get('build') in BU else ot.get('build','average')
  if g=='m': br='none'
  if g=='f': anchor=anchor.replace('womanly figure, ',('womanly figure, ' if br in ('large','huge') else '')+(BR_EN[br]+', ' if BR_EN.get(br) else ''))
  if BU_EN.get(bu): anchor+=', '+BU_EN[bu]
  base='masterpiece, best quality, very aesthetic, highres, uncensored, face visible, nsfw, explicit, '+ot['tags']+', '+anchor
  en,used=_picks_en(picks,g)
  cols=[x.strip() for x in ot['tags'].split(',') if re.search(r'(hair|eyes|fur)$',x.strip()) and not x.strip().startswith(('long','short','medium','very'))]
  en+= [x for x in [ot.get('style',''),', '.join(cols)] if x]   # 画风词 + 发色/瞳色收尾再强调一次
  st=str(c.get('style') or ''); sid=st if st.startswith('anima_') else (st[1:] if A.is_xl(st) else A.AID.get(st,'anima_1785572045772130975'))
  neg=ref['negative_prompt']+(', human, human face, kemonomimi' if furry else '')+(', '+ot['avoid'] if ot.get('avoid') else '')+(BR_NEG.get(br,'') if g=='f' else '')+(', visible ribs, skinny, emaciated' if bu=='slim' else '')
  if br=='flat': neg=neg.replace(', flat chest','').replace('flat chest, ','')   # 贫乳是她本来的样子；成年锚点和防幼态负面词照留
  body,prompt=_body(base,en,neg,sid,832,1216,furry)
  recipe=dict(body=dict(breasts=br,build=bu),model='Kusa-Anima ANIMA_TEXT_TO_IMAGE turbo+aesthetic' if sid.startswith('anima_') else 'Kusa-XL TEXT_TO_IMAGE',style_name=c.get('style_name'),style_id=sid,size='832x1216',
              prompt=prompt,negative_prompt=neg,source=f"用户角色 {c.get('name')}（{cid}）· 成人模式 · 外形标签由视觉模型从立绘读出",character=dict(cid=cid,name=c.get('name'),type=c.get('type'),age=c.get('age'),img=c.get('img')))
  return body,recipe,used,c
@bp.get('/adult/oc/<cid>')
def adult_oc(cid):
  c=_oc(cid); ok,why=_oc_ok(c); ot=_oc_tags(cid,c) if ok else {}
  return jsonify(ok=ok,why=why,body=dict(breasts=ot.get('breasts'),build=ot.get('build')),cid=cid,name=c.get('name'),type=c.get('type'),age=c.get('age'),g=_oc_g(c),img=c.get('img'),cutout=(c.get('cutout') or {}).get('src'),style=c.get('style'),style_name=c.get('style_name'))
def _run(jid):
  j=GJOBS[jid]; t0=time.time()
  try:
    tid,err=A.create(j['body'])
    if not tid: raise RuntimeError('创建任务失败：'+str(err))
    j['phase']='出图中'; imgs,err=A.wait(tid)
    if not imgs: raise RuntimeError('出图失败：'+str(err))
    from PIL import Image
    im=Image.open(io.BytesIO(requests.get(imgs[0],timeout=120).content)).convert('RGB')
    name=f"{jid}.webp"; im.save(os.path.join(GEN,name),quality=90); th=im.copy(); th.thumbnail((360,520)); th.save(os.path.join(GEN,jid+'_s.webp'),quality=82)
    rec=dict(id=jid,type=j['type'],cid=j.get('cid'),cdn=imgs[0],src='adult/gen/img/'+name,thumb=f'adult/gen/img/{jid}_s.webp',label=' · '.join(u['zh'] for u in j['used']),picks=j['used'],recipe=dict(j['recipe'],task_id=tid),created=time.strftime('%Y-%m-%d %H:%M:%S'))
    with open(WORKS,'a') as f: f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    j.update(status='done',work=rec)
  except Exception as e: j.update(status='error',err=_nice(e))
  j['sec']=round(time.time()-t0)
@bp.post('/adult/gen')
def adult_gen():
  d=request.get_json(silent=True) or {}
  cid=os.path.basename(str(d.get('cid') or ''))
  try: body,recipe,used,a=_oc_build(cid,d.get('picks') or [],d.get('body') if isinstance(d.get('body'),dict) else None) if cid else _build(str(d.get('type','')),d.get('picks') or [])
  except ValueError as e: return jsonify(error=str(e)),400
  except Exception as e: return jsonify(error='准备提示词失败：'+str(e)[:120]),500
  jid=uuid.uuid4().hex[:12]; GJOBS[jid]=dict(status='run',phase='排队出图',type=d.get('type'),cid=cid or None,body=body,recipe=recipe,used=used)
  threading.Thread(target=_run,args=(jid,),daemon=True).start(); return jsonify(id=jid)
@bp.get('/adult/gen/job/<jid>')
def adult_gen_job(jid):
  j=GJOBS.get(jid)
  if not j: return jsonify(status='error',err='任务不存在（服务可能重启过）'),404
  return jsonify({k:j.get(k) for k in ('status','phase','err','work','sec')})
@bp.get('/adult/gen/list')
def adult_gen_list():
  typ=request.args.get('type',''); cid=request.args.get('cid',''); out=[]
  if os.path.exists(WORKS):
    for l in open(WORKS):
      try: r=json.loads(l)
      except Exception: continue
      if (cid and r.get('cid')==cid) or (not cid and typ and r.get('type')==typ and not r.get('cid')): out.append(r)
  r=jsonify(works=out[::-1][:30]); r.headers['Cache-Control']='no-store'; return r
@bp.get('/adult/gen/img/<name>')
def adult_gen_img(name): return send_file(_safe(GEN,os.path.basename(name)),max_age=86400)


# ---------- 10-11 木木夕：成人作品「做成视频」（闭环第一步）——三种：剧情向 H3 / 无声动态 Seedance 1.0 Pro Fast / SEX 动态 LTX
# 只能从 works.jsonl 里的作品做（用户角色还要再过一次 _oc_ok 年龄闸门）；不收外部上传图。价格=官网扣费规则（task/pricing/calculator.go）。
import subprocess
VID=os.path.join(GEN,'vid'); os.makedirs(VID,exist_ok=True); VIDS=os.path.join(GEN,'videos.jsonl'); VJOBS={}
VKINDS={
 'h3':dict(name='剧情向',model='H3（MiniMax H3）',task='IMAGE_TO_VIDEO_MINIMAX_H3',secs=[5,6,8,10,15],res={'768P':120,'480P':50},dres='768P',eta='约 30 秒~3 分钟',audio=True,
   desc='有镜头运动和情绪表演，可以写她说什么、做什么',
   base='Keep the exact same character, face, art style, colours and line work as the first frame. A single adult character alone. Slow cinematic camera push-in, she looks at the viewer with a seductive expression, natural subtle body movement, hair sways gently, soft breathing.'),
 'live':dict(name='无声动态',model='Seedance 1.0 Pro Fast',task='IMAGE_TO_VIDEO',secs=[3,5,8,10,12],res={'720p':20},dres='720p',eta='约 30 秒',audio=False,
   desc='像 Live2D 一样的轻微动态：呼吸、眨眼、头发飘，适合做封面和待机',
   base='Live2D style subtle idle animation of the exact same illustration, camera completely fixed, no scene change, no new objects. Gentle breathing, slow blinking, hair and loose clothing sway slightly, small soft body sway.'),
 'ltx':dict(name='SEX 动态',model='LTX2.3-10Eros',task='LTX_IMAGE_TO_VIDEO',secs=[4,6,8,10],res={'720p':20},dres='720p',eta='约 1~10 分钟（后台生成）',audio=True,
   desc='成人向身体动态，带喘息声，自动去底噪',
   base='2D anime illustration in motion, the exact same art style, colors and line work as the first frame. A single adult woman alone in the scene. She breathes heavily, her body trembles and sways slowly, flushed face, half-closed eyes, looking at the viewer, soft breathy moans and sighs. Camera fixed. Crisp clear image.'),
}
LTX_NEG=('phasing, captions, subtitles, text, watermark, logo, still image, static, frozen, bad quality, blur, noise, white noise, hiss, background music, film grain, haze, fog, washed out, '
         'style change, photorealistic, real person, child, loli, shota, teen, underage, schoolgirl, school uniform, childlike face, baby face, 2girls, multiple girls')
MINOR_EN=re.compile(r'\b(child|kid|loli|shota|teen|underage|minor|schoolgirl|schoolboy|little girl|little boy)\w*\b',re.I)
def vprice(k,sec,res): v=VKINDS[k]; return v['res'][res]*sec
@bp.get('/adult/vid/opts')
def vid_opts():   # 10-11 木木夕：卡片里放对应类型的样本动图（adult/cards/vs_<kind>.webp，从已做好的内容截的；没有就不显示）
  return jsonify({k:dict({x:v[x] for x in ('name','secs','res','dres','eta','audio','desc')},sample=f'adult/cards/vs_{k}.webp' if os.path.exists(os.path.join(CARDS,f'vs_{k}.webp')) else None) for k,v in VKINDS.items()})
def _work(wid):
  for l in open(WORKS):
    try: r=json.loads(l)
    except Exception: continue
    if r.get('id')==wid: return r
def _work_url(w):
  if w.get('cdn'): return w['cdn']
  tid=(w.get('recipe') or {}).get('task_id')
  d=A.tget(tid)
  return d['result']['images'][0]['display_url']
def _vwait(tid):
  for _ in range(600):
    time.sleep(3)
    try: d=A.tget(tid)
    except Exception: continue
    if d.get('status')=='COMPLETED':
      vs=(d.get('result') or {}).get('videos') or []
      return (vs[0].get('display_url') or vs[0].get('url')) if vs else None,None if vs else '结果里没有视频'
    if d.get('status') in ('FAILED','ERROR','CANCELLED'): return None,str(d.get('error_message') or d.get('status'))[:200]
  return None,'超时（30 分钟）'
def _nice(e):   # 积分不足给人话
  m=re.search(r'Insufficient credits: need (\d+), available (\d+)',str(e))
  return f'测试账号积分不够：这次要 {m.group(1)}，账号里还剩 {m.group(2)}' if m else str(e)[:200]
def _vrun(vid):
  j=VJOBS[vid]; t0=time.time()
  try:
    tid,err=A.create(j['body'])
    if not tid: raise RuntimeError('创建任务失败：'+str(err))
    j['phase']='生成中'; url,err=_vwait(tid)
    if not url: raise RuntimeError('生成失败：'+str(err))
    raw=os.path.join(VID,vid+'_raw.mp4'); out=os.path.join(VID,vid+'.mp4')
    open(raw,'wb').write(requests.get(url,timeout=300).content)
    if j['kind']=='ltx':   # LTX 固定底噪 → 去噪 + 响度统一
      r=subprocess.run(['bash',os.path.join(AD,'work','clean_audio.sh'),raw,out],capture_output=True)
      if r.returncode!=0: os.replace(raw,out)
      else: os.remove(raw)
    else: os.replace(raw,out)
    subprocess.run(['ffmpeg','-v','error','-y','-i',out,'-frames:v','1','-vf','scale=360:-2','-q:v','4',os.path.join(VID,vid+'.jpg')])
    rec=dict(id=vid,kind=j['kind'],kind_name=VKINDS[j['kind']]['name'],work=j['work']['id'],type=j['work'].get('type'),cid=j['work'].get('cid'),sec=j['sec'],res=j['res'],credits=j['credits'],
             src='adult/gen/vid/'+vid+'.mp4',poster='adult/gen/vid/'+vid+'.jpg',label=f"{VKINDS[j['kind']]['name']} · {j['sec']}秒 · {j['work'].get('label','')}",
             recipe=dict(model=VKINDS[j['kind']]['model'],task_type=j['body']['task_type'],params={k:v for k,v in j['body']['params'].items()},task_id=tid,source_work=j['work']['id'],source_image=j['work'].get('src')),
             created=time.strftime('%Y-%m-%d %H:%M:%S'),sec_used=round(time.time()-t0))
    with open(VIDS,'a') as f: f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    j.update(status='done',video=rec)
  except Exception as e: j.update(status='error',err=_nice(e))
  j['used']=round(time.time()-t0)
@bp.post('/adult/vid')
def vid_make():
  d=request.get_json(silent=True) or {}; k=d.get('kind')
  if k not in VKINDS: return jsonify(error='没有这种视频类型'),400
  v=VKINDS[k]; w=_work(str(d.get('work','')))
  if not w: return jsonify(error='只能用已保存的成人作品做视频'),400
  if w.get('cid'):
    ok,why=_oc_ok(_oc(w['cid']))
    if not ok: return jsonify(error=why),403
  sec=int(d.get('sec') or v['secs'][1]); res=d.get('res') if d.get('res') in v['res'] else v['dres']
  if sec not in v['secs']: return jsonify(error='时长不支持'),400
  txt=str(d.get('text') or '').strip()[:300]
  if (MINOR_W.search(txt) or MINOR_EN.search(txt)): return jsonify(error='描述里有涉及未成年的词，不能生成'),400
  try: url=_work_url(w)
  except Exception as e: return jsonify(error='找不到这张图的原图地址：'+str(e)[:80]),500
  prompt=v['base']+((' '+txt) if txt else '')
  if k=='h3':
    body={"task_type":v['task'],"params":{"image_url":url,"prompt":prompt,"resolution":res,"duration":sec,"role_mode":"frame","ratio":"adaptive","watermark":False}}   # 首帧模式；不写 role_mode 会被当成参考图模式（ref2va）且不支持 adaptive
  elif k=='live':
    body={"task_type":v['task'],"params":{"image_url":url,"prompt":prompt,"model":"ProFast","resolution":res,"duration":sec,"source_width":832,"source_height":1216,"watermark":False}}
  else:
    body={"task_type":v['task'],"params":{"image_url":url,"last_image_url":url,"prompt":prompt,"negative_prompt":LTX_NEG,"width":832,"height":1216,"num_frames":sec*24+1,"fps":24,"resolution":res,"watermark":False}}
  vid=uuid.uuid4().hex[:12]; VJOBS[vid]=dict(status='run',phase='排队中',kind=k,work=w,sec=sec,res=res,credits=vprice(k,sec,res),body=body)
  threading.Thread(target=_vrun,args=(vid,),daemon=True).start(); return jsonify(id=vid,credits=vprice(k,sec,res))
@bp.get('/adult/vid/job/<vid>')
def vid_job(vid):
  j=VJOBS.get(vid)
  if not j: return jsonify(status='error',err='任务不存在（服务可能重启过）'),404
  return jsonify({k:j.get(k) for k in ('status','phase','err','video','used','kind')})
@bp.get('/adult/vid/list')
def vid_list():
  q={k:request.args.get(k) for k in ('cid','type','work') if request.args.get(k)}; out=[]
  if os.path.exists(VIDS):
    for l in open(VIDS):
      try: r=json.loads(l)
      except Exception: continue
      if q.get('work') and r.get('work')!=q['work']: continue
      if q.get('cid') and r.get('cid')!=q['cid']: continue
      if q.get('type') and (r.get('type')!=q['type'] or r.get('cid')): continue
      out.append(r)
  r=jsonify(videos=out[::-1][:40]); r.headers['Cache-Control']='no-store'; return r
@bp.get('/adult/gen/vid/<name>')
def vid_file(name): return send_file(_safe(VID,os.path.basename(name)),max_age=86400,conditional=True)
