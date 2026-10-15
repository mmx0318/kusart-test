# 10-10 木木夕：角色主页「延展玩法」测试版 —— 服装抽卡机 / 运势表情包抽卡机 / 角色出场 PV
# 搬家约定：抽卡本身（/draw）免费、纯随机；只有 /make 才真正出图/出视频，异步 job，产物挂回角色的 works[]。
# 正式版只需要按这里的输入输出重写：素材池（outfit / fortune / pv 模板）+ 三个 make 执行器。
import glob,os,io,re,json,time,random,hashlib,base64,subprocess,requests
from flask import Blueprint,request,jsonify,abort
from PIL import Image
from asset_store import update_character
bp=Blueprint('plays',__name__)
HERE=os.path.dirname(os.path.abspath(__file__))
A=None   # app 模块（llm / POOL 等），init() 时注入
PJOBS={}
def init(app_mod):
  global A,SIGN_P; A=app_mod
  SIGN_P='你是角色本人，给用户念今天的运势签文。'+A.LANG+'只输出 JSON：{"sign":"..."}。sign 18~36 字（绝不超过 40 字），用角色的口吻和性格，把三个关键词自然揉进去；凶也要可爱、带一点安慰，不说教。'

def char(cid):
  p=os.path.join(HERE,'chars',os.path.basename(cid)+'.json')
  if not os.path.exists(p): abort(404)
  return p,json.load(open(p))
def add_work(cid,w):
  update_character(cid,lambda c:c.setdefault('works',[]).insert(0,dict(w,created=time.strftime('%Y-%m-%d %H:%M'))))
def load_bytes(src):
  if src.startswith('http'): return requests.get(src,timeout=60).content
  return open(os.path.join(HERE,src.split('?')[0]),'rb').read()
def char_png(c):
  """角色参考图：优先抠图（铺白底），没有就用原图"""
  src=(c.get('cutout') or {}).get('src') or c.get('img')
  im=Image.open(io.BytesIO(load_bytes(src)))
  if im.mode in ('RGBA','LA','P'):
    im=im.convert('RGBA'); bg=Image.new('RGB',im.size,'white'); bg.paste(im,mask=im.getchannel('A')); im=bg
  im=im.convert('RGB'); im.thumbnail((1024,1024)); b=io.BytesIO(); im.save(b,'PNG'); return b.getvalue()
def char_ref(c,cid):
  """10-10 木木夕：每个玩法作品都存「配方」——用的哪个角色（快照）、哪张参考图、什么风格"""
  return dict(cid=cid,name=c.get('name'),type=c.get('type'),gender=c.get('gender') or gender(c),style=c.get('style'),style_name=c.get('style_name'),
              ref=(c.get('cutout') or {}).get('src') or c.get('img'),img=c.get('img'))
GPT=lambda size:dict(name='gpt-image-2',api='OpenAI images/edits',quality='medium',size=size)
def gender(c):
  g=c.get('gender') or {'少女':'女','御姐':'女','假小子':'女','少年':'男','熟男':'男','男娘':'男'}.get(c.get('type'),'')
  return g

# ---------- GPT Image 2 edits（同表情包大盗；公司 OpenAI 账号，不扣站内积分）
OAI=lambda:open('/home/admin/.openclaw/openai_key.txt').read().strip()
def gpt_edit(prompt,images,size='1024x1536'):
  files=[('image[]',(f'i{i}.png',b,'image/png')) for i,b in enumerate(images)]
  for k in range(3):
    r=requests.post('https://api.openai.com/v1/images/edits',headers={'Authorization':'Bearer '+OAI()},
      data={'model':'gpt-image-2','prompt':prompt,'size':size,'quality':'medium','n':'1'},files=files,timeout=300)
    j=r.json()
    if j.get('data'): return base64.b64decode(j['data'][0]['b64_json'])
    err=(j.get('error') or {}).get('message') or str(j)[:200]
    if 'safety' in err.lower() or 'moderation' in err.lower(): raise RuntimeError('被内容审核拦了：'+err[:120])
    time.sleep(3)
  raise RuntimeError('出图失败：'+err[:160])
def trim(im,pad=0.03):
  """裁掉四周近白留白（换装前后对比时人物比例才一致）"""
  from PIL import ImageChops
  g=im.convert('L').point(lambda v:255 if v<240 else 0); bb=g.getbbox()
  if not bb: return im
  w,h=im.size; px=int((bb[2]-bb[0])*pad); py=int((bb[3]-bb[1])*pad)
  return im.crop((max(0,bb[0]-px),max(0,bb[1]-py),min(w,bb[2]+px),min(h,bb[3]+py)))
def save_png(data,name,crop=False):
  im=Image.open(io.BytesIO(data)).convert('RGB')
  if crop: im=trim(im)
  fn=f'u/{name}.webp'; im.save(os.path.join(HERE,fn),'WEBP',quality=90); return fn

def job(kind,cid,fn,*a):
  jid=hashlib.md5(f'{time.time()}{cid}{kind}'.encode()).hexdigest()[:12]
  PJOBS[jid]=dict(status='running',kind=kind,cid=cid,t=time.time())
  def run():
    j=PJOBS[jid]
    try: j.update(status='done',**fn(j,*a))
    except Exception as e: j.update(status='error',err=str(e)[:300])
    j['sec']=round(time.time()-j['t'])
  A.POOL.submit(run); return jid
@bp.get('/api/play/job/<jid>')
def pjob(jid):
  j=PJOBS.get(jid) or abort(404); return jsonify({k:v for k,v in j.items() if k!='t'})

# ========== 1. 服装抽卡机
# R  = 本类型的 5 个日常穿着（tag 例图）；SR = 同性别其他类型的穿着；SSR = oc-editor 的万圣节 / 圣诞整套（金框）
OUT=[json.loads(l) for l in open(os.path.join(HERE,'plays','outfits.jsonl')) if l.strip()]
SSR=[o for o in OUT if o['theme'] in ('christmas','halloween')]
FEM=re.compile(r'lolita|dress|skirt|princess|witch|qipao',re.I)
G_TYPES={'女':['少女','御姐','假小子'],'男':['少年','熟男'],'':['Furry']}
def tag_outfits(t):
  import tags_def
  return [(l,w) for g,it in tags_def.TAGS.get(t,[]) if g=='穿着' for l,w in it]
def tag_img(t,l):
  import tags_def; return tags_def.imgkey(t,'穿着',l) if hasattr(tags_def,'imgkey') else ''
# 10-10 木木夕：卡池扩到 oc-editor 全部服装 / 配饰素材（248 个，缩略图缓存在 plays/thumbs）
ED=json.load(open(os.path.join(HERE,'plays','editor_items.json')))
FULL_CATS=('clothing_casual','clothing_formal','clothing_traditional','clothing_uniform','clothing_sportswear','clothing_dress')
CAT_CN={'hats':'帽子','hair_ornaments':'发饰','earrings':'耳饰','gloves':'手套','neck_accessories':'颈饰','accessories_wrists':'腕饰','accessories_torso':'腰饰','accessories_legs':'腿饰',
  'special_features':'特殊部件','socks':'袜子','stockings':'长袜','footwear':'鞋子','clothing_top':'上衣','clothing_bottom':'下装','clothing_casual':'休闲','clothing_formal':'正装',
  'clothing_traditional':'传统服饰','clothing_uniform':'制服','clothing_sportswear':'运动服','clothing_dress':'裙装'}
MALE_SKIP=re.compile(r'dress|gown|skirt|bikini|lolita|maid|stocking|legwear|garter|bra|camisole|tube top|crop|kimono_furisode|high heels|uchikake|qipao|cheongsam|bunny',re.I)
def outfit_pool(c):
  t=c.get('type') or '少女'; g=gender(c); male=(g=='男')
  ok=lambda txt:not (male and MALE_SKIP.search(txt))
  R=[dict(id='r:'+x['cat']+':'+x['name_en'],rarity='R',kind='item',cat=CAT_CN.get(x['cat'],''),name=x['name_cn'],name_en=x['name_en'],prompt=x['prompt'],thumb=x['thumb_local'])
     for x in ED if x['cat'] not in FULL_CATS and ok(x['name_en']+' '+x['cat'])]
  SR=[dict(id='sr:'+x['cat']+':'+x['name_en'],rarity='SR',kind='outfit',cat=CAT_CN.get(x['cat'],''),name=x['name_cn'],name_en=x['name_en'],prompt=x['prompt'],thumb=x['thumb_local'])
     for x in ED if x['cat'] in FULL_CATS and ok(x['name_en']+' '+x['cat'])]
  seen={x['name'] for x in SR}
  for tt in [t]+[x for x in G_TYPES.get(g,['少女']) if x!=t]:   # 本类型 / 同性别类型的 tag 穿着也进 SR
    for l,w in tag_outfits(tt):
      if l in seen: continue
      seen.add(l); th=f'tags_v3/{tt}/big/穿着_{l}.webp'
      if not os.path.exists(os.path.join(HERE,th)): th=th.replace('/big/','/')
      SR.append(dict(id=f'sr:{tt}:{l}',rarity='SR',kind='outfit',cat='日常',name=l,prompt=w,thumb=th))
  S=[dict(id='ssr:'+o['id'],rarity='SSR',kind='outfit',cat='节日限定',name=o['name_cn'],name_en=o['name_en'],prompt=o['prompt'],thumb=o.get('thumb_local') or o['thumb_url'],theme=o['theme'])
     for o in SSR if g=='女' or not FEM.search(o['prompt'])]
  return R,SR,S
@bp.get('/api/play/outfit/pool/<cid>')
def outfit_pool_api(cid):
  _,c=char(cid); R,SR,S=outfit_pool(c); return jsonify(R=R,SR=SR,SSR=S,rate=dict(R=.6,SR=.3,SSR=.1))
@bp.post('/api/play/outfit/draw')
def outfit_draw():
  d=request.json; _,c=char(d['cid']); R,SR,S=outfit_pool(c)
  n=max(1,min(10,int(d.get('n') or 1))); out=[]
  for i in range(n):
    r=random.random(); pool=S if r<.1 and S else SR if r<.4 and SR else R
    if n==10 and i==9 and not any(x['rarity']!='R' for x in out): pool=SR or R   # 十连保底 SR
    out.append(random.choice(pool))
  return jsonify(cards=out)
OUTFIT_P=('Image 1 is the character. Image 2 shows an outfit. Redraw the SAME character from Image 1 — same face, hairstyle, hair color, eye color, '
  'skin tone, body proportions, species features (ears, tail, fur, horns), glasses and personal accessories — now wearing the outfit from Image 2. '
  'Copy the outfit from Image 2 faithfully (design, colors, layers, materials, shoes, hat/hair ornaments that belong to the outfit). '
  'Keep the art style, line weight and coloring of Image 1 exactly; do not use the art style of Image 2. '
  'Body features come ONLY from Image 1: if the character in Image 1 has no animal ears, tail, horns or wings, do NOT add them even if the model in Image 2 has them (outfit hats and headbands are fine). '
  'Full body from head to toe, standing, centered, plain white background, single character only, no text, no watermark. Outfit notes: {p}')
ITEM_P=('Image 1 is the character. Image 2 shows a model wearing a {cat} item: "{name}". Redraw the SAME character from Image 1 — same face, hairstyle, hair color, eye color, '
  'skin tone, body proportions, species features, glasses, AND the same outfit — and only add or swap in that one item ({p}), copied faithfully from Image 2 (shape, color, material). '
  'Everything else on the character stays exactly as in Image 1. Ignore the model in Image 2 (her pink hair, cat ears, tail and clothes are NOT part of this item, unless the item itself is ears/tail/wings). '
  'Keep the art style of Image 1 exactly. Full body from head to toe, standing, centered, plain white background, single character only, no text, no watermark.')
def outfit_make(j,cid,card,reference_src=None):
  _,c=char(cid); j['phase']='换装中'
  if reference_src: c=dict(c,cutout={'src':reference_src})
  pr=ITEM_P.format(cat=card.get('cat') or 'accessory',name=card.get('name_en') or card['name'],p=card['prompt'][:300]) if card.get('kind')=='item' else OUTFIT_P.format(p=card['prompt'][:600])
  data=gpt_edit(pr,[char_png(c),load_bytes(card['thumb'])],'1024x1536')
  fn=save_png(data,f"{cid}_outfit_{int(time.time())}",crop=True)
  rc=dict(play='outfit',play_name='服装抽卡机',character=char_ref(c,cid),model=GPT('1024x1536'),prompt=pr,
          inputs=[dict(role='Image 1 角色参考图',src=char_ref(c,cid)['ref']),dict(role='Image 2 服装参考图',src=card['thumb'])],
          params=dict(card={k:card.get(k) for k in ('id','rarity','kind','cat','name','name_en','prompt','theme')}),post='裁白边')
  add_work(cid,dict(kind='outfit',src=fn,title=card['name'],rarity=card['rarity'],recipe=rc))
  return dict(src=fn,card=card)
@bp.post('/api/play/outfit/make')
def outfit_make_api():
  d=request.json; char(d['cid']); return jsonify(job=job('outfit',d['cid'],outfit_make,d['cid'],d['card']))

# ========== 2. 运势表情包抽卡机：三个关键词 → 运势档位 → 表情包大盗模板 → 和角色融合
FM=json.load(open(os.path.join(HERE,'plays','meme_fortune_map.json')))
LV=[('大吉',.12),('吉',.23),('小吉',.25),('平',.22),('凶',.18)]
KW={'大吉':['暴富','桃花朵朵','灵感爆棚','万事顺遂','好运加满','被夸夸','心想事成','欧气冲天','贵人相助','满分发挥'],
    '吉':['小确幸','有人请客','奶茶自由','顺风顺水','被偏爱','好消息','状态在线','宜出门','摸鱼成功','好吃的'],
    '小吉':['慢慢变好','意外惊喜','偶遇','小进步','宜早睡','新发现','温柔以待','轻松一点','被理解','宜摸猫'],
    '平':['平平无奇','按部就班','宜发呆','先观望','佛系','多喝热水','原地待机','无事发生','慢半拍','稳住'],
    '凶':['水逆','踩坑','社死预警','钱包瘦身','忘带东西','排队最长','手滑','宜躺平','咖啡洒了','被放鸽子']}
SIGN_P=None   # init 时拼（要用 A.LANG）
@bp.post('/api/play/fortune/draw')
def fortune_draw():
  d=request.json; _,c=char(d['cid']); r=random.random(); acc=0
  for lv,p in LV:
    acc+=p
    if r<acc: break
  kws=random.sample(KW[lv],3); tpl=random.choice(FM[lv])
  sign=''
  try:
    sign=A.llm(SIGN_P,
      f"角色：{c.get('name')}；性格：{'、'.join(c.get('traits') or [])}；一句话：{c.get('bio','')}\n运势：{lv}\n关键词：{'、'.join(kws)}",model=A.FAST).get('sign','')
  except Exception: pass
  return jsonify(level=lv,keywords=kws,template=dict(id=tpl['id'],url=tpl['file_or_url'],desc=tpl['desc']),sign=sign,
                 reels={k:random.sample(sum(KW.values(),[]),8) for k in range(3)})
MEME_P=open(os.path.join(HERE,'plays','meme_v2_prompt.txt')).read()
def fortune_make(j,cid,tpl,lv,kws=None,sign='',reference_src=None):
  _,c=char(cid); j['phase']='表情包融合中'
  if reference_src: c=dict(c,cutout={'src':reference_src})
  tb=load_bytes(tpl['url']); w,h=Image.open(io.BytesIO(tb)).size; r=w/h
  size='1536x1024' if r>=1.25 else '1024x1536' if r<=.8 else '1024x1024'
  data=gpt_edit(MEME_P,[tb,char_png(c)],size)
  ts=int(time.time()); fn=save_png(data,f"{cid}_meme_{ts}")
  rc=dict(play='fortune',play_name='运势表情包',character=char_ref(c,cid),model=GPT(size),prompt=MEME_P,
          inputs=[dict(role='Image 1 表情包模板',src=tpl['url'],template=tpl['id']),dict(role='Image 2 角色参考图',src=char_ref(c,cid)['ref'])],
          params=dict(level=lv,keywords=kws or [],template=tpl,sign=sign),
          text_model=dict(name=A.FAST,api='OpenRouter',use='签文',prompt=SIGN_P))
  add_work(cid,dict(kind='meme',src=fn,title=f'今日运势 · {lv}',template=tpl['id'],recipe=rc))
  # 10-10 木木夕：同步出一张「今日运势签」（含表情包），给用户下载分享
  j['phase']='排运势签'; import fortune_card; card=f"u/{cid}_fsign_{ts}.jpg"
  fortune_card.make(os.path.join(HERE,fn),lv,(kws or [])[:3],sign,c.get('name') or '',os.path.join(HERE,card))
  add_work(cid,dict(kind='fsign',src=card,title=f'运势签 · {lv}',recipe=dict(rc,play_name='运势签',model=dict(name='本地排版 fortune_card.py v2（手绘白底）',api='PIL'),
    inputs=[dict(role='表情包',src=fn)],from_meme=fn)))
  return dict(src=fn,card=card)
@bp.post('/api/play/fortune/make')
def fortune_make_api():
  d=request.json; char(d['cid']); return jsonify(job=job('meme',d['cid'],fortune_make,d['cid'],d['template'],d.get('level',''),d.get('keywords') or [],d.get('sign') or ''))

# ========== 3. 角色出场 PV（H3-max T04：13 镜头 15s，参考图模式，768P）
T04=open(os.path.join(HERE,'plays','t04_skeleton.txt')).read()
H3K=lambda:open('/home/admin/.openclaw/minimax_h3max_key2.txt').read().strip()
def public_url(c):
  src=c.get('img') or ''
  if src.startswith('http'): return src
  data=char_png(c); k=hashlib.md5(data).hexdigest()[:12]; tmp=f'/tmp/cl8/pvref_{k}.png'
  open(tmp,'wb').write(data)
  subprocess.run(['gsutil','-q','cp',tmp,f'gs://animemodel-cdn/tmp/oclab_{k}.png'],check=True,capture_output=True,timeout=120)
  return f'https://storage.googleapis.com/animemodel-cdn/tmp/oclab_{k}.png'
def pv_params(c):
  p=c.get('profile') or {}
  return A.llm('你给原创角色的 15 秒游戏式「角色登场 PV」填文字参数。只输出 JSON：{"CHARACTER_NAME":"","STATUS_TEXT_1":"","STATUS_TEXT_2":"","INTERSTITIAL_TEXT_1":"","INTERSTITIAL_TEXT_2":"","INTERSTITIAL_TEXT_3":"","SUBTITLE":"","ability":""}。'
    '画面字卡只能用英文大写短语：CHARACTER_NAME=角色名的英文或罗马音（≤16 字符）；STATUS_TEXT_1=身份/阵营（≤18 字符）；STATUS_TEXT_2 固定写成 "MODE: XXX"（XXX 是角色特质，≤12 字符）；'
    'INTERSTITIAL_TEXT_1~3 = 三张招式/特质卡（每张 ≤16 字符，可以是能力名、口头禅、标志物）；SUBTITLE=一句副标题（≤24 字符）。'
    'ability 用中文写角色最标志的能力或气质（12~30 字），环境与特效会围绕它展开；日常系角色就写日常里的标志动作和氛围。不要出现任何真实作品、品牌和名人的名字。',
    json.dumps({k:c.get(k) for k in ('name','type','role','traits','bio','desc','lore')}|{k:p.get(k) for k in ('epithet','world','summary','hook')},ensure_ascii=False))
def pv_make(j,cid,params=None,template_id='t04'):
  if template_id=='lp':
    import lp_animation,sys
    return lp_animation.make(sys.modules[__name__],j,cid)
  _,c=char(cid); j['phase']='写分镜参数'; pr=params or pv_params(c)
  txt=T04
  for k in ('CHARACTER_NAME','STATUS_TEXT_1','STATUS_TEXT_2','INTERSTITIAL_TEXT_1','INTERSTITIAL_TEXT_2','INTERSTITIAL_TEXT_3','SUBTITLE'):
    txt=txt.replace('{'+k+'}',str(pr.get(k,'')).upper().replace('"',''))
  txt=txt.replace('{PROJECT_TEXT}','')   # 模型分不清副标题和 PROJECT_TEXT，会渲染两遍 → 留空
  txt=txt.replace('{角色中文名}',c.get('name') or '').replace('{作品}','KusArt 原创角色').replace('{标志能力}',pr.get('ability') or (c.get('role') or ''))
  selected=None
  if template_id!='t04':
    selected=next((t for t in pv_catalog() if t['id']==template_id),None)
    if not selected: raise ValueError('模板不存在')
    variants=selected['variants'];preferred='male' if c.get('gender')=='男' else 'female'
    key=next((k for k in variants if ('furry' in k if c.get('type')=='Furry' else k==preferred)),next(iter(variants)))
    v=variants[key]
    values=A.llm('为原创角色视频模板填槽。只输出JSON：{"vals":["按槽位顺序的字符串"]}。不得引用其他IP；name填当前角色名，work填原创世界，const填空，其余按前后分镜语义填写场景、配色、动作与性格。参考图锁定角色外观，不得更换角色或服装。',json.dumps({'角色':{k:c.get(k) for k in ('name','role','traits','bio','lore')},'片段':v['frags'],'槽位':v['slots']},ensure_ascii=False)).get('vals')
    if not isinstance(values,list) or len(values)!=len(v['frags'])+1: raise ValueError('模板参数不完整，请重试')
    txt=''.join(str(values[i])+frag for i,frag in enumerate(v['frags']))+str(values[-1])
    pr['template_id']=template_id;pr['template_name']=selected['name']
  duration=selected['duration'] if selected else 15
  ratio=selected['ratio'] if selected else '16:9'
  j['phase']='上传立绘'; url=public_url(c)
  body={"model":"MiniMax-H3-max","content":[{"type":"text","text":txt},{"type":"image_url","role":"reference_image","image_url":{"url":url}}],
        "resolution":"768P","duration":duration,"ratio":ratio,"aigc_watermark":False}
  hd={'Authorization':'Bearer '+H3K(),'Content-Type':'application/json'}
  j['phase']='排队生成'; tid=None
  for k in range(3):
    r=requests.post('https://api.minimax.io/v2/video_generation',headers=hd,json=body,timeout=60).json()
    tid=r.get('task_id') or (r.get('data') or {}).get('task_id')
    if tid: break
    err=str(r)[:200]; time.sleep(15)
  if not tid: raise RuntimeError('创建视频任务失败：'+err)
  j.update(phase='生成中（约 1 分钟）',task_id=tid)
  for _ in range(180):
    time.sleep(15)
    try: q=requests.get(f'https://api.minimax.io/v2/query/video_generation/{tid}',headers=hd,timeout=60).json()
    except Exception: continue
    t=q.get('task') or {}; s=str(t.get('status','')).lower()
    if s=='succeeded':
      v=requests.get(t['content']['url'],timeout=300).content; fn=f'u/{cid}_pv_{int(time.time())}.mp4'; open(os.path.join(HERE,fn),'wb').write(v)
      rc=dict(play='pv',play_name='出场 PV',character=char_ref(c,cid),model=dict(name='MiniMax-H3-max',api='api.minimax.io v2/video_generation',mode='reference_image',resolution='768P',duration=duration,ratio=ratio),
              prompt=txt,template=selected['name'] if selected else 'H3-max T04（plays/t04_skeleton.txt）',inputs=[dict(role='参考图',src=url)],params=pr,
              text_model=dict(name=A.KIMI,api='OpenRouter',use='填 T04 字卡参数'),task_id=tid)
      add_work(cid,dict(kind='pv',src=fn,title='出场 PV',params=pr,recipe=rc)); return dict(src=fn,params=pr)
    if s in ('failed','cancelled'): raise RuntimeError('视频生成失败：'+str(t.get('error'))[:200])
  raise RuntimeError('视频生成超时')
@bp.post('/api/play/pv/make')
def pv_make_api():
  d=request.json; char(d['cid']); template_id=d.get('template_id','t04')
  if template_id not in ['t04','lp']+[t['id'] for t in pv_catalog()]: return jsonify(error='模板不存在'),400
  return jsonify(job=job('pv',d['cid'],pv_make,d['cid'],None,template_id))

@bp.get('/api/play/recipes')
def recipes():
  """所有玩法作品的配方存档（之后给别人复用）；?play=outfit|fortune|pv 过滤"""
  pl=request.args.get('play'); out=[]
  for f in sorted(glob.glob(os.path.join(HERE,'chars','*.json'))):
    try: c=json.load(open(f))
    except Exception: continue
    for w in c.get('works') or []:
      r=w.get('recipe')
      if r and (not pl or r.get('play')==pl): out.append(dict(src=w['src'],kind=w['kind'],title=w.get('title'),created=w.get('created'),recipe=r))
  out.sort(key=lambda x:x.get('created') or '',reverse=True); return jsonify(count=len(out),items=out)
@bp.get('/plays/thumbs/<name>')
def plays_thumb(name):
  from flask import send_file; p=os.path.join(HERE,'plays','thumbs',os.path.basename(name)); return send_file(p,max_age=86400) if os.path.exists(p) else abort(404)
@bp.get('/plays.js')
def plays_js():
  from flask import send_file; return send_file(os.path.join(HERE,'plays.js'),max_age=0)
@bp.get('/plays.css')
def plays_css():
  from flask import send_file; return send_file(os.path.join(HERE,'plays.css'),max_age=0)

# 已归档样片按需播放，模板骨架只留在服务端。
def pv_catalog():
  p=os.path.join(HERE,'plays','pv_catalog.json')
  return json.load(open(p)) if os.path.exists(p) else []
@bp.get('/api/play/pv/templates')
def pv_templates():
  return jsonify(templates=[dict(id='t04',name='游戏角色登场',family='字卡快剪',duration=15,ratio='16:9',sample=None),dict(id='lp',name='角色 LP 动画',family='剧情演出 · 落回角色卡 · 试用',duration=15,ratio='16:9',sample='plays/pv_samples/lp.mp4' if os.path.exists(os.path.join(HERE,'plays','pv_samples','lp.mp4')) else None)]+[{k:t[k] for k in ('id','name','family','duration','ratio','sample')} for t in pv_catalog()])
@bp.get('/plays/pv_samples/<name>')
def pv_sample(name):
  from flask import send_file
  p=os.path.join(HERE,'plays','pv_samples',os.path.basename(name))
  if not os.path.isfile(p):abort(404)
  return send_file(p,conditional=True,max_age=3600)
