# 捏角色 v0.6 真实测试站：原型 UI + Kimi 写描述/设定 + prod Kusa-Anima 真出图（10-08 木木夕要的）
import os,io,re,json,time,hmac,hashlib,base64,subprocess,threading,requests
from concurrent.futures import ThreadPoolExecutor
from flask import Flask,request,jsonify,send_file,redirect,make_response,abort
from PIL import Image
HERE=os.path.dirname(os.path.abspath(__file__))
ENV=dict(l.strip().split('=',1) for l in open(os.path.join(HERE,'.env')) if '=' in l)
OR_KEY=ENV['OPENROUTER_API_KEY']; KIMI='moonshotai/kimi-k2.6'; VISION='google/gemini-2.5-flash'; FAST='google/gemini-2.5-flash'   # 10-08：写提示词这步要快，Kimi 2.5~20s 不稳
ANSWER=ENV.get('TEAM_ANSWER','kusart'); SECRET=hashlib.sha256(('oc-lab:'+ANSWER).encode()).digest()
B="https://api.kusa.pics/api/go"; BASE='/oc-lab/'
app=Flask(__name__); POOL=ThreadPoolExecutor(8)
app.config['MAX_CONTENT_LENGTH']=12*1024*1024

# ---------- 画风：按角色类型推荐（10-08 木木夕：复用风格 Jev = style-lab 的 router_v8 + 精选池 tblDUKN4，只取 Anima）
SD='/home/admin/kusa-bot/.tmp/style_demo'; TMP='/home/admin/kusa-bot/.tmp'
AID={}; ANAME={}
for l in open(os.path.join(SD,'anima_db.tsv')):
  p=l.rstrip('\n').split('\t')
  if len(p)>2: AID.setdefault(p[2],p[0]); ANAME.setdefault(p[2],p[1])
AID['A-303']='anima_1787750254900877169'
XLNAME={}
IDNAME={l.split('\t')[0]:l.split('\t')[1] for l in open(os.path.join(SD,'anima_db.tsv')) if '\t' in l}
def sname(c):
  if isinstance(c,str) and c[:1]=='S' and c[1:].isdigit():
    if not XLNAME:
      try: XLNAME.update({p['编号']:'Kusa-XL · '+str(p.get('名称') or '') for p in router().P if p.get('模型')=='Kusa-XL'})
      except Exception: pass
    return XLNAME.get(c,'Kusa-XL · style'+c[1:])
  return (IDNAME.get(c,'') if str(c).startswith('anima_') else ANAME.get(c,'')) if c else ''
# 10-08 木木夕：第一步类型卡片用角色库（Bitable RQRXbBVs / 随机角色库）里的角色，该类型推荐的第一个画风 = 卡片角色用的 Anima 风格
TYPE_CARDS=json.load(open(os.path.join(HERE,'type_cards.json')))
_rt={'m':None,'mt':0}; _lk=threading.Lock()
def router():   # router_v8.py 改了就自动重载，和 style-lab 共用一份规则
  p=os.path.join(SD,'router_v8.py'); mt=os.path.getmtime(p)
  with _lk:
    if _rt['m'] is None or mt!=_rt['mt']:
      import importlib.util
      cwd=os.getcwd(); os.chdir(SD)
      try:
        spec=importlib.util.spec_from_file_location('rt',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
      finally: os.chdir(cwd)
      _rt.update(m=m,mt=mt)
    return _rt['m']
# 类型 → 问 Jev 的话、Jev 失败时兜底的 char_type、例图用哪套（young/uncle = maletest 男性例图）
# 10-08 木木夕扩成 8 类（和角色库分类对齐）；Jev 的 char_type 正好有这 7 个：萝莉/美少女/御姐/正太/美少年/成熟男性/非人
TYPE_Q={'甜妹':('帮我创建一个甜妹原创角色（成年、娇小甜美），全身立绘','萝莉',''),'少女':('帮我捏一个美少女原创角色，全身立绘','美少女',''),
  '御姐':('帮我捏一个成熟御姐原创角色，全身立绘','御姐',''),'奶系':('帮我创建一个奶系原创角色（成年男性、软萌清秀），全身立绘','正太','young'),
  '少年':('帮我捏一个美少年原创角色，全身立绘','美少年','young'),'熟男':('帮我捏一个成熟帅大叔原创角色，全身立绘','成熟男性','uncle'),
  '假小子':('帮我创建一个假小子原创角色（成年女性、中性帅气），全身立绘','美少女',''),'男娘':('帮我创建一个男娘原创角色（成年男性、女装可爱），全身立绘','美少年','young'),
  '赛博格':('帮我创建一个赛博格原创角色（成年、半机械身体、义体关节），全身立绘','非人',''),
  'Furry':('帮我捏一个 furry 兽人原创角色（全身毛茸茸的兽人），全身立绘','非人',''),'异种':('帮我捏一个异种原创角色（人外、怪物拟人、机械、恶魔），全身立绘','非人','')}
# 每种类型的画风大类顺序：前 4 类各取 Jev 精选池排第一的 Anima 风格做主推，其余进「查看更多」
ORDER={'甜妹':['Q版','清新·少女漫','日系赛璐珞','水彩·淡彩','半厚涂·光影','厚涂','复古·90s','古风','暗黑·哥特'],
  '少女':['清新·少女漫','日系赛璐珞','Q版','半厚涂·光影','水彩·淡彩','厚涂','复古·90s','古风','暗黑·哥特','赛博朋克'],
  '御姐':['半厚涂·光影','厚涂','日系赛璐珞','暗黑·哥特','水彩·淡彩','古风','复古·90s','赛博朋克','清新·少女漫'],
  '奶系':['Q版','日系赛璐珞','清新·少女漫','水彩·淡彩','半厚涂·光影','厚涂','复古·90s','古风'],
  '少年':['日系赛璐珞','清新·少女漫','韩漫·半写实','半厚涂·光影','水彩·淡彩','厚涂','复古·90s','古风','赛博朋克','暗黑·哥特'],
  '熟男':['韩漫·半写实','厚涂','日系赛璐珞','半厚涂·光影','暗黑·哥特','古风','复古·90s','赛博朋克','水彩·淡彩'],
  '假小子':['日系赛璐珞','清新·少女漫','半厚涂·光影','韩漫·半写实','水彩·淡彩','厚涂','复古·90s','赛博朋克'],
  '男娘':['清新·少女漫','日系赛璐珞','Q版','水彩·淡彩','半厚涂·光影','暗黑·哥特','复古·90s','古风'],
  '赛博格':['赛博朋克','日系赛璐珞','半厚涂·光影','厚涂','暗黑·哥特','清新·少女漫','韩漫·半写实','复古·90s'],
  'Furry':['Q版','日系赛璐珞','清新·少女漫','厚涂','水彩·淡彩','半厚涂·光影','复古·90s','暗黑·哥特'],
  '异种':['半厚涂·光影','暗黑·哥特','赛博朋克','厚涂','古风','日系赛璐珞','水彩·淡彩','清新·少女漫','复古·90s']}
# 10-07 扫图：不写身材时容易画夸张的 Anima 风格，捏角色不推荐（GinkgoWM 是官方茉莉画风，保留）
LEAN={'A-44','A-2','A-12','A-159','A-161','A-58','A-304','A-1','A-53','A-226','A-13','A-79','A-117','A-210'}
SHORT={'清新·少女漫':'清新少女漫','日系赛璐珞':'日系动画','半厚涂·光影':'半厚涂光影','韩漫·半写实':'韩漫半写实','水彩·淡彩':'水彩淡彩','Q版':'Q 版','复古·90s':'复古 90s','暗黑·哥特':'暗黑哥特'}
STYC={}
def ex_rel(c,mk):
  if mk and os.path.exists(os.path.join(TMP,f'maletest/img/{AID.get(c,"")}__{mk}.jpg')): return os.path.join(TMP,f'maletest/img/{AID[c]}__{mk}.jpg')
  if os.path.exists(f'/home/admin/style-lab/uni/{c}.jpg'): return f'/home/admin/style-lab/uni/{c}.jpg'
  p=os.path.join(TMP,f'anima_styles/img/{AID.get(c,"")}.jpg'); return p if os.path.exists(p) else None
# 10-08 木木夕：推荐要按类型拉开（少女≠萝莉、少年≠正太），Jev 精选池只有 29 个 Anima 风格、按大类取第一必撞，
# 改成人工排序：mkstyles8.py 8 类 × 29 风格各用类型提示词实跑一张（sx8/），茉莉逐类看图排出 curated8.json。
# 例图：Furry / 异种用 sx8 的类型提示词图（要看得出兽头/恶魔）；其余类型按木木夕 10-08 口径继续用原例图（女=uni 统一提示词，男=maletest）
CURATED=json.load(open(os.path.join(HERE,'curated8.json')))
IDCODE={l.split('\t')[0]:l.rstrip('\n').split('\t')[2] for l in open(os.path.join(SD,'anima_db.tsv')) if l.count('\t')>=2}
SX8_TYPES=tuple(TYPE_Q)   # 10-08：萝莉配原 uni 例图会出成年大胸女、正太配美少年例图像高中生，推荐拉不开 → 8 类全用 sx8 类型提示词图（同类同一句提示词，第一张卡也一样）
def ex_id(sid,typ,mk):
  if typ in SX8_TYPES:
    p=os.path.join(HERE,'sx8',f'{typ}_{sid}.webp')   # 带 mtime，换图后不命中旧缓存
    return f'sx8/{typ}_{sid}.webp?v=%d'%(os.path.getmtime(p) if os.path.exists(p) else 0)
  if mk and os.path.exists(os.path.join(TMP,f'maletest/img/{sid}__{mk}.jpg')): return f'exi/{sid}?mk={mk}'
  c=IDCODE.get(sid,''); 
  if c and AID.get(c)==sid and os.path.exists(f'/home/admin/style-lab/uni/{c}.jpg'): return f'exi/{sid}'
  if os.path.exists(os.path.join(TMP,f'anima_styles/img/{sid}.jpg')): return f'exi/{sid}'
  return f'sx8/{typ}_{sid}.webp'
def recommend(typ):
  if typ in STYC and time.time()-STYC[typ]['t']<3600: return STYC[typ]
  msg,fb,mk=TYPE_Q.get(typ,TYPE_Q['少女']); t0=time.time()
  ids=list(CURATED.get(typ,CURATED['少女']))
  card=TYPE_CARDS.get(typ); card=dict(card,anima_id=card.get('anima_id') or card.get('xl_id')) if card and (card.get('anima_id') or card.get('xl_id')) else None
  rows=[dict(code=s,name=typ+'推荐',sub=sname(s),cat='人工精选',img=ex_id(s,typ,mk)) for s in ids if not card or s!=card['anima_id']]
  if card:   # 第一张 = 角色卡同款风格，例图和同类其他例图同一套提示词
    ci=ex_id(card['anima_id'],typ,mk) if typ in SX8_TYPES else next((f for f in (f"a/cs_{card['anima_id']}__{mk}.jpg",f"a/cs_{card['anima_id']}.jpg") if os.path.exists(os.path.join(HERE,f))),card['img'])
    rows=[dict(code=card['anima_id'],name='角色卡同款',sub=card['style_name'],cat='角色库',img=ci)]+rows
  out=dict(main=rows[:4],more=rows[4:],src='人工精选（sx8 实跑排序）',char=typ,t=time.time(),sec=round(time.time()-t0,1))
  STYC[typ]=out; return out
@app.route('/exi/<sid>')
def exi(sid):
  sid=os.path.basename(sid); mk=request.args.get('mk',''); c=IDCODE.get(sid,'')
  for p in ([os.path.join(TMP,f'maletest/img/{sid}__{mk}.jpg')] if mk else [])+([f'/home/admin/style-lab/uni/{c}.jpg'] if c and AID.get(c)==sid else [])+[os.path.join(TMP,f'anima_styles/img/{sid}.jpg')]:
    if os.path.exists(p): return send_file(p,max_age=86400)
  abort(404)
@app.route('/lab/<name>')   # 10-09 视觉方案对比页（魔法阵等）
def labpage(name):
  p=os.path.join(HERE,'lab',os.path.basename(name)); r=send_file(p,max_age=0) if os.path.exists(p) else abort(404); r.headers['Cache-Control']='no-store'; return r
@app.route('/sx8/<name>')
def sx8img(name): p=os.path.join(HERE,'sx8',os.path.basename(name)); return send_file(p,max_age=3600) if os.path.exists(p) else abort(404)

# ---------- 文字模型
def llm(system,user,model=KIMI,img=None,tries=2,max_tokens=None,usage_sink=None):
  content=user if not img else [{'type':'text','text':user},{'type':'image_url','image_url':{'url':img}}]
  body={'model':model,'response_format':{'type':'json_object'},'messages':[{'role':'system','content':system},{'role':'user','content':content}]}
  if max_tokens is not None: body['max_tokens']=max_tokens
  if model==KIMI: body.update(provider={'order':['Fireworks','Together','Inceptron','DeepInfra'],'allow_fallbacks':True},reasoning={'enabled':False})
  err=None
  for _ in range(tries):
    try:
      r=requests.post('https://openrouter.ai/api/v1/chat/completions',headers={'Authorization':'Bearer '+OR_KEY},json=body,timeout=60).json()
      if usage_sink is not None: usage_sink.update(r.get('usage') or {})
      t=r['choices'][0]['message']['content']
      return json.loads(t[t.find('{'):t.rfind('}')+1])
    except Exception as e: err=f'{type(e).__name__}: {e}'
  raise RuntimeError('文字模型没返回：'+err)

TYPE_HINT={'甜妹':'petite adult woman with a sweet cute look (1girl, petite, adult, cute face, fully clothed)','少女':'young adult woman (1girl, adult, 18+)','御姐':'adult woman (1girl, mature female)',
  '奶系':'young adult man with a soft cute look (1boy, adult, slim, soft cute face, fully clothed)','少年':'young adult man (1boy, adult, 18+)','熟男':'adult man (1boy, mature male)',
  '假小子':'tomboy adult woman (1girl, adult, tomboy, boyish short hair, casual boyish clothes)','男娘':'adult man with a feminine cute look (1boy, adult, otoko no ko, androgynous, crossdressing, flat chest)',
  '赛博格':'adult cyborg character (cyborg, mechanical parts, robot joints, android, mechanical arms or legs)',
  'Furry':'anthropomorphic furry character, full animal head and fur body (anthro, furry), not a human with animal ears',
  '异种':'non-human character such as monster girl, slime, jellyfish, naga, android, demon, object-head'}
LANG='用户界面是中文，所有给用户看的字段都用简体中文。'
def write_desc(mode,typ,style,text):
  sty=sname(style)
  sysm=('你是 KusArt 捏角色流程里的写作助手。'+LANG+'只输出 JSON：{"desc":"..."}。desc 是一段 40~80 字的角色外形描述，'
        '依次写：性别年龄感、发色发型、眼睛、服装、一两个辨识特征、一句性格。不要写背景和镜头，不写身材和性感描写，不用 tilde（～ 或 ~）。')
  if mode=='polish': u=f'把用户写的描述补全成好出图的描述，保留用户写过的每个点，只补缺的部分。\n角色类型：{typ}\n画风：{sty}\n用户写的：{text or "（空）"}'
  elif mode=='random': u=f'随机构思一个有记忆点的原创角色。角色类型：{typ or "随你"}。不要粉发猫耳这种最常见组合。'
  else: u=f'根据前两步的选择写一个原创角色。角色类型：{typ}\n画风：{sty}'+(f'\n用户已经写了一点，可以参考：{text}' if text else '')
  return llm(sysm,u).get('desc','').strip()

def to_prompt(typ,desc,n=4,model=None):
  sysm=('你把中文角色描述转成 Kusa-Anima（Danbooru 标签系模型）的英文提示词，并给每张候选图写一句角色台词。只输出 JSON：'
        '{"tags":"1girl, solo, ...","nl":"one English sentence","lines":["...x%d"],"subject":"girl|boy|woman|man"}。'
        'tags 规则：小写 Danbooru 标签，逗号分隔；必须含 solo、full body、standing、simple background、white background、looking at viewer；'
        '必须写出完整服装（上衣、下装、鞋）；男性角色用 1boy 且不得出现 1girl；不写身材相关标签，不加权重括号。'
        'nl 是一句英文自然语言补充，描述角色外形和神态。lines 是 %d 句不同语气的中文台词，每句 8~18 字，像角色第一次和用户打招呼，不用 tilde。')%(n,n)
  return llm(sysm,f"角色类型：{typ}（{TYPE_HINT.get(typ,'')}）\n描述：{desc}",model=model or FAST)

def read_image(url):
  return llm('你是角色设定助手。'+LANG+'只输出 JSON：{"desc":"...","type":"少女|御姐|少年|熟男|假小子|男娘|赛博格|Furry|异种"}。'
             'desc 只写角色本身的外形设定，用中文短语、逗号分隔，20~50 字，顺序：年龄感、发色发型、眼睛、服装、配饰/辨识特征。'
             '不要写「图中」「这是」「她/他」「一位」这种叙述；不写表情、动作、姿势、闭眼睁眼、气质氛围、画风、背景、图里的文字排版。'
             '例：少女，银白色及腰长发，两侧垂发，蓝眼睛，银色头戴式耳机，白衬衫，黑色蝴蝶结',
             '读出这张角色图里角色的外形。',model=VISION,img=url)

# ---------- 出图（走木木夕的 prod 账号，同 style-lab）
H=lambda:{"Authorization":"Bearer "+open('/home/admin/.mmx_id_token').read().strip(),"Content-Type":"application/json"}
NEG='worst quality, low quality, blurry, jpeg artifacts, watermark, text, signature, multiple views, split screen, extra arms, extra legs, nsfw, nude, topless, cleavage, cropped, close-up, upper body, portrait, cowboy shot, out of frame, cut off feet, multiple views, character sheet, multiple girls, multiple boys, 2girls, 3girls, 2boys, 3boys, clone, logo, english text, chinese text'
# 10-08 木木夕：强制全身立绘（主页首屏舞台要全身，半身会像被切掉）
FULL='full body, standing, solo, from head to toe, shoes, feet visible, wide shot, centered character, simple background, white background'
CROP=re.compile(r'\s*(upper body|close-up|portrait|cowboy shot|bust|headshot|face focus|from below|from above)\s*',re.I)
def full_body(tags):
  return ', '.join(t for t in (x.strip() for x in tags.split(',')) if t and not CROP.fullmatch(t))
SLIM_SKIP=('甜妹','奶系','Furry')   # 10-08 木木夕嫌全身显矮：改 768x1344(≈4:7)，非萝莉/正太/Furry 加细长腿、负面压Q版大头
XL_COMP={'solo','full body','standing','simple background','white background','looking at viewer','fully clothed'}
def is_xl(style): return isinstance(style,str) and len(style)>1 and style[0]=='S' and style[1:].isdigit()
def anima_body(style,tags,nl,n,typ=''):
  if is_xl(style):   # 10-08 木木夕：XL 和 Anima 画风混着推荐；XL 风格码 S<id> 走 Kusa-XL TEXT_TO_IMAGE（10 积分/张）
    # 10-11 木木夕：XL 只读前 ~75 个词，原来的长拼法（重复构图词+长腿词+英文长句）把「全身」冲淡 → 切头/腿特写；改短 tag 版（男娘 S70/S207 实测 6/6 头完整）
    sub=', '.join(t for t in (x.strip() for x in full_body(tags).split(',')) if t and t.lower() not in XL_COMP)
    return {"task_type":"TEXT_TO_IMAGE","params":{"prompt":'masterpiece, best quality, full body, standing, solo, '+sub+', looking at viewer, simple background, white background, fully clothed',
      "negative_prompt":NEG+('' if typ in SLIM_SKIP else ', chibi, super deformed, big head'),"style_id":style[1:],"width":768,"height":1344,"amount":n,"is_public":False,"watermark":False}}
  slim='' if typ in SLIM_SKIP else ', slender, long legs'
  p={"prompt":'masterpiece, best quality, '+FULL+', '+full_body(tags)+slim+', fully clothed, modest. A single character shown in full body, the whole figure from head to feet is visible. '+nl,"negative_prompt":NEG+('' if typ in SLIM_SKIP else ', chibi, super deformed, big head'),"width":768,"height":1344,"amount":n,
     "turbo":True,"use_layer_replay":True,"use_aesthetic":True,"is_public":False,"watermark":False}
  if str(style).startswith("anima_"): p["style_ids"]=[style]
  elif style in AID: p["style_ids"]=[AID[style]]
  return {"task_type":"ANIMA_TEXT_TO_IMAGE","params":p}
# 10-11 木木夕：测试账号积分用完 → 改走 KusArt B2B 接口（X-API-Key，key 在 ~/.kusa_b2b_key，扣 API 账户积分，价格=站内价）；没有 key 文件才回退木木夕账号
B2B_KEY=(open(os.path.expanduser('~/.kusa_b2b_key')).read().strip() if os.path.exists(os.path.expanduser('~/.kusa_b2b_key')) else '')
HB=lambda:{'X-API-Key':B2B_KEY,'Content-Type':'application/json','User-Agent':'Mozilla/5.0'}
def tget(tid):   # 查任务：先 B2B，查不到（旧任务是木木夕账号建的）再用她的 token
  if B2B_KEY:
    try:
      d=requests.post(f"{B}/b2b/tasks/get",headers=HB(),json={"task_id":tid},timeout=60).json().get('data')
      if d: return d
    except Exception: pass
  return requests.post(f"{B}/tasks/get",headers=H(),json={"task_id":tid},timeout=60).json().get('data') or {}
def create(b):
  r={}
  if B2B_KEY:
    for _ in range(2):
      try: r=requests.post(f"{B}/b2b/tasks/create",headers=HB(),json=b,timeout=60).json()
      except Exception as e: r={'message':str(e)}
      tid=(r.get('data') or {}).get('task_id')
      if tid: return tid,None
      time.sleep(2)
    return None,str(r.get('message') or r.get('error') or r)[:200]
  for _ in range(3):
    try: r=requests.post(f"{B}/tasks/create",headers=H(),json=b,timeout=60).json()
    except Exception as e: r={'message':str(e)}
    tid=(r.get('data') or {}).get('task_id')
    if tid: return tid,None
    subprocess.run(["python3","/home/admin/kusa-bot/debug/mint_mmx_token.py"],capture_output=True); time.sleep(2)
  return None,str(r.get('message') or r)[:200]
def wait(tid):
  for _ in range(480):
    time.sleep(1.5)
    try: d=tget(tid)
    except Exception: continue
    if d.get('status')=='COMPLETED': return [i['display_url'] for i in d['result']['images']],None
    if d.get('status') in ('FAILED','ERROR','CANCELLED'): return None,str(d.get('error_message') or d.get('error') or d.get('status'))[:200]
  return None,'超时（12 分钟）'

JOBS={}
def runjob(jid):
  j=JOBS[jid]; t=time.time()
  try:
    j['phase']='写提示词'; p=to_prompt(j['type'],j['desc'],j['n'])
    j.update(tags=p.get('tags',''),nl=p.get('nl',''),subject=p.get('subject',''),lines=(p.get('lines') or [])[:j['n']])
    j['phase']='排队出图'; tid,err=create(anima_body(j['style'],j['tags'],j['nl'],j['n'],j.get('type','')))
    if not tid: raise RuntimeError('创建任务失败：'+err)
    j['phase']='出图中'; imgs,err=wait(tid)
    if not imgs and 'Read-only file system' in (err or '') and j['style']!='A-4':   # 10-08：GinkgoWM 等 LoRA 在部分 GPU 节点只读挂载写不了锁，换 A-4 兜底
      j['note']=f"{j['style']} 的 GPU 节点故障（Read-only file system），已自动换 A-4 画风重出"; j['style']='A-4'
      tid,err=create(anima_body(j['style'],j['tags'],j['nl'],j['n'],j.get('type',''))); imgs,err=wait(tid) if tid else (None,err)
    if not imgs and 'Serverless' in (err or ''):
      j['note']='第一次 GPU 节点报错，已自动重试'; tid,err=create(anima_body(j['style'],j['tags'],j['nl'],j['n'],j.get('type',''))); imgs,err=wait(tid) if tid else (None,err)
    if not imgs: raise RuntimeError('出图失败：'+str(err))
    j.update(status='done',images=imgs,task_id=tid)
  except Exception as e: j.update(status='error',err=str(e))
  j['sec']=round(time.time()-t)

# ---------- 登录（问题同 image-router-lab / style-lab）
def sign(v): return v+'.'+hmac.new(SECRET,v.encode(),hashlib.sha256).hexdigest()
def authed():
  c=request.cookies.get('ol','')
  if '.' not in c: return False
  v,_=c.rsplit('.',1)
  return hmac.compare_digest(sign(v),c) and time.time()<float(v)
@app.before_request
def gate():
  if request.path.rstrip('/').endswith('/login'): return
  if not authed():
    if request.path.startswith('/api'): abort(401)
    return redirect(BASE+'login')
@app.route('/login',methods=['GET','POST'])
def login():
  if request.method=='POST' and request.form.get('a','').strip().lower()==ANSWER:
    r=make_response(redirect(BASE)); r.set_cookie('ol',sign(str(time.time()+43200)),httponly=True,secure=True,samesite='Lax',max_age=43200,path=BASE); return r
  return f'''<meta name=viewport content="width=device-width,initial-scale=1"><title>创建角色 · 测试</title><body style="font-family:sans-serif;display:flex;height:90vh;align-items:center;justify-content:center;background:#F8F7F7">
<form method=post style="background:#fff;padding:28px;border-radius:16px;border:1px solid #E0E2E6">
<div style="margin-bottom:12px">我们的产品名字叫什么？（全小写）</div><input name=a autofocus style="font-size:16px;padding:8px;width:220px"> <button style="padding:8px 14px">进入</button>
{'<div style="color:#c00;margin-top:8px">不对哦</div>' if request.method=='POST' else ''}</form>'''

# ---------- 页面和静态
@app.route('/')
def index():   # 10-08：飞书内置浏览器会缓存旧页面，首页强制不缓存
  if request.args.get('adult_oc'): return redirect(BASE+'create?'+request.query_string.decode())
  r=send_file(os.path.join(HERE,'home.html'),max_age=0); r.headers['Cache-Control']='no-store'; return r
@app.route('/create')
def create_page():
  r=send_file(os.path.join(HERE,'index.html'),max_age=0); r.headers['Cache-Control']='no-store'; return r
@app.route('/base.css')
def css(): return send_file(os.path.join(HERE,'base.css'))
@app.route('/a/<name>')
def asset(name): p=os.path.join(HERE,'a',os.path.basename(name)); return send_file(p,max_age=86400) if os.path.exists(p) else abort(404)
@app.route('/u/<name>')
def upl(name): p=os.path.join(HERE,'u',os.path.basename(name)); return send_file(p,max_age=86400) if os.path.exists(p) else abort(404)
@app.route('/ex/<code>')
def ex(code): p=ex_rel(os.path.basename(code),request.args.get('mk','')); return send_file(p,max_age=86400) if p else abort(404)
@app.get('/api/styles')
def styles():
  typ=request.args.get('type') or '少女'; r=recommend(typ); ti=list(TYPE_Q).index(typ) if typ in TYPE_Q else 0
  allx=r['main']+r['more']; card=allx[:1] if r['main'] and r['main'][0].get('cat')=='角色库' else []
  rest=allx[len(card):]; main=card+rest[:4-len(card)]   # 10-08：撤掉 sx/ 同提示词重跑图，其余画风继续用原例图
  try:   # 10-09 木木夕：每类 4 个画风按她在 Tag 库文档里定的来（style_main.json，改文件即生效）
    O=json.load(open(os.path.join(HERE,'style_main.json'))); codes=O['main'].get(typ)
    if codes:
      byc={x.get('code'):x for x in allx}; nm=O.get('names',{})
      def mk(i,c):
        x=dict(byc.get(c) or {}); f=f'sx8/{typ}_{c}.webp'
        x.update(code=c,cat='角色库' if i==0 else '人工精选',name='角色卡同款' if i==0 else typ+'推荐',sub=x.get('sub') or nm.get(c) or sname(c) or c)
        if os.path.exists(os.path.join(HERE,f)): x['img']=f+'?v=%d'%os.path.getmtime(os.path.join(HERE,f))
        return x
      main=[mk(i,c) for i,c in enumerate(codes)]; rest=[x for x in rest if x.get('code') not in codes]
  except Exception as e: print('style_main',e)
  return jsonify(main=main,more=rest[4-len(card):],src=r['src'],char=r['char'],sec=r['sec'])
@app.route('/sx/<name>')
def sximg(name): p=os.path.join(HERE,'sx',os.path.basename(name)); return send_file(p,max_age=3600) if os.path.exists(p) else abort(404)

# ---------- 第 3 步灵感词：按类型（tags_def.py；例图 mktags.py 跑在 tags/）
import importlib, tags_def
@app.get('/api/tags')
def api_tags():
  importlib.reload(tags_def); typ=request.args.get('type') or '少女'
  if typ not in tags_def.TAGS: typ='少女'
  out=[]
  for g,items in tags_def.TAGS[typ]:
    row=[]
    for l,w in items:
      sh=getattr(tags_def,'TYPE_IMG',{}).get((typ,g,l)) or tags_def.SHARED_IMG.get((g,l))
      if sh:
        fp=os.path.join(HERE,sh); v='?v=%d'%os.path.getmtime(fp) if os.path.exists(fp) else ''
        row.append(dict(label=l,img=sh+v,big=(sh.replace('/eye/','/eye/big/') if '/eye/' in sh else sh.rsplit('/',1)[0]+'/big/'+sh.rsplit('/',1)[1])+v)); continue
      k=tags_def.imgkey(typ,g,l)
      k2=tags_def.imgkey(typ,g,l,tags_def.type_style(typ)); v2=os.path.join(HERE,'tags_v2',k2+'.webp')
      if (typ,g,l) not in tags_def.OCREUSE and os.path.exists(v2):   # 10-09 细节特写版（脸部/头肩构图，512 缩略 + 1024 大图）
        row.append(dict(label=l,img='tags_v2/'+k2+'.webp?v=%d'%os.path.getmtime(v2),big='tags_v2/big/'+k2+'.webp?v=%d'%os.path.getmtime(v2))); continue
      img=tags_def.OCREUSE.get((typ,g,l)) or ('tags/'+k+'.webp?v=%d'%os.path.getmtime(os.path.join(HERE,'tags',k+'.webp')) if os.path.exists(os.path.join(HERE,'tags',k+'.webp')) else '')
      row.append(dict(label=l,img=img,big=img))
    out.append(dict(group=g,items=row))
  return jsonify(type=typ,groups=out)
@app.route('/tags_v3/<path:name>')
def tagimg3(name):
  p=os.path.normpath(os.path.join(HERE,'tags_v3',name))
  return send_file(p,max_age=3600) if p.startswith(os.path.join(HERE,'tags_v3')) and os.path.exists(p) else abort(404)
@app.route('/tags_v2/<path:name>')
def tagimg2(name):
  p=os.path.normpath(os.path.join(HERE,'tags_v2',name))
  return send_file(p,max_age=3600) if p.startswith(os.path.join(HERE,'tags_v2')) and os.path.exists(p) else abort(404)
@app.route('/tags/<name>')
def tagimg(name): p=os.path.join(HERE,'tags',os.path.basename(name)); return send_file(p,max_age=3600) if os.path.exists(p) else abort(404)

@app.post('/api/classify')   # 10-09 木木夕：第一屏加「自定义」卡 → 用户写一句，归到最接近的类型（只用来推荐画风和外形 tag，原话照样进描述）
def api_classify():
  text=(request.json or {}).get('text','').strip()[:200]
  if not text: return jsonify(error='先写一句你的角色是什么样的')
  ts=[t for t in TYPE_Q if t not in ('甜妹','奶系','赛博格','异种')]   # 10-09 木木夕：赛博格、异种先去掉
  j=llm('你是角色分类助手。只输出 JSON：{"type":"'+'|'.join(ts)+'"}。按用户描述选外形最接近的一类：成熟男性/大叔选熟男，兽头兽身选 Furry；看不出性别默认少女。',text)
  t=j.get('type'); return jsonify(type=t if t in ts else '少女')
@app.post('/api/write')
def api_write():
  d=request.json; return jsonify(desc=write_desc(d.get('mode','write'),d.get('type',''),d.get('style',''),d.get('text','')))
@app.post('/api/upload')
def api_upload():
  f=request.files['f']; im=Image.open(f.stream).convert('RGB'); im.thumbnail((1024,1024))
  name=hashlib.md5(im.tobytes()).hexdigest()[:12]+'.jpg'; im.save(os.path.join(HERE,'u',name),quality=88)
  buf=io.BytesIO(); im.save(buf,'JPEG',quality=85); data='data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode()
  r=read_image(data) if request.form.get('read','1')=='1' else {}
  return jsonify(url='u/'+name,desc=r.get('desc',''),type=r.get('type',''))
@app.post('/api/gen')
def api_gen():
  d=request.json; desc=d.get('desc','').strip()
  if not desc: desc=write_desc('random',d.get('type',''),d.get('style',''),'')
  jid=hashlib.md5(f"{time.time()}{desc}".encode()).hexdigest()[:12]
  JOBS[jid]=dict(status='running',phase='准备',type=d.get('type') or '少女',style=d.get('style') or 'A-303',desc=desc,n=max(1,min(4,int(d.get('n') or 4))))
  POOL.submit(runjob,jid); return jsonify(job=jid,desc=desc)
@app.get('/api/job/<jid>')
def job(jid):
  j=JOBS.get(jid) or abort(404); return jsonify({k:j.get(k) for k in ('status','phase','images','lines','tags','nl','subject','err','note','sec','desc')})
@app.post('/api/profile')
def api_profile():
  d=request.json
  r=llm('你给刚捏好的原创角色预填设定。'+LANG+'只输出 JSON：{"names":["5 个候选名字"],"age":"少女|少年|成年|不详","roles":["3 个贴合外形的身份"],'
        '"traits":["从这 8 个里选 1~3 个：温柔治愈,开朗活力,傲娇毒舌,内向软萌,冷酷无情,沉稳可靠,腹黑心机,搞怪幽默"],"bio":"一句话介绍，15~25 字"}。'
        '名字要好记，可以是日系、西式或中文名，和外形气质贴合。年龄只能从给的四个里选：少女=未成年女性，少年=未成年男性，成年，不详；必须和性别一致，女性角色绝不能选少年；角色看起来未成年时不能选成年。',
        f"角色类型：{d.get('type')}\n性别（以出图为准）：{ {'girl':'女','woman':'女','boy':'男','man':'男'}.get(d.get('subject'),'按描述判断')}\n画风：{sname(d.get('style'))}\n外形描述：{d.get('desc')}\n候选台词：{d.get('line','')}")
  return jsonify(r)

# 10-08 木木夕：设定页加「粘贴已有设定」入口，用户直接贴自己写好的角色介绍，Mari 拆成表单字段自动填；原文存 lore 给主页用
@app.post('/api/parse_profile')
def api_parse_profile():
  d=request.json; text=(d.get('text') or '').strip()[:4000]
  if not text: return jsonify(error='没有内容'),400
  r=llm('你把用户粘贴的原创角色设定拆成表单字段。'+LANG+'只输出 JSON：{"name":"角色名，原文没有就给空字符串","age":"少女|少年|成年|不详","role":"身份，2~10 字",'
        '"traits":["从这 8 个里选最贴近原文的 1~3 个：温柔治愈,开朗活力,傲娇毒舌,内向软萌,冷酷无情,沉稳可靠,腹黑心机,搞怪幽默"],"bio":"一句话介绍，15~25 字，概括原文"}。'
        '只根据原文提取，不要编造原文没有的设定；原文写了名字就原样保留。年龄：少女=未成年女性，少年=未成年男性；必须和角色性别一致，原文没说年龄就按外形判断，判断不了填不详。',
        f"角色类型：{d.get('type')}\n出图外形：{d.get('desc','')}\n用户粘贴的设定原文：\n{text}")
  return jsonify(r)

# ---------- 登场：存角色 + AI 写主页内容
# 10-08 木木夕：主页按 feat/library-asset-pages-v2 的角色页（CharacterTopicLayout）来做，文案按它的 profile 结构写（只出中文）
def page_copy(c):
  return llm('你为用户刚捏好的原创角色写角色主页，结构照 KusArt 官方角色页。'+LANG+'只输出 JSON：{'
    '"epithet":"称号，格式「世界观 · 职业」，如「霓虹屋顶乐园 · 街机主播」",'
    '"world":"角色所在的世界观/地点，4~8 字",'
    '"accent":"角色主色的十六进制色值，取发色或服装主色，如 #dc97aa",'
    '"attributes":[{"label":"所属","value":"…"},{"label":"身份","value":"…"},{"label":"形态","value":"…"},{"label":"年龄感","value":"…"},{"label":"性格","value":"…"},{"label":"画风","value":"…"}],'
    '"summary":"档案简介 70~110 字：先交代清楚是谁、在哪、做什么，最后一句是钩子",'
    '"hook":"悬念句，一句话，25 字内",'
    '"scene_title":"故事这一幕的标题，4~8 字",'
    '"story":["故事第一段 100~150 字","故事第二段 100~150 字"],'
    '"signatures":[{"title":"辨识特征名 4~8 字","body":"具体描述 20~40 字"}]（4 条，只写立绘里看得见的外形）,'
    '"voice":[{"context":"场景，如 初次见面","line":"台词"}]（5 句：初次见面、闲聊、开心、生气或失落、告别）,'
    '"dossier":[{"label":"喜欢","value":"…"},{"label":"讨厌","value":"…"},{"label":"习惯","value":"…"},{"label":"秘密","value":"…"}],'
    '"files":[{"title":"档案故事标题 2~6 字","body":"80~140 字的小片段"}]（3 篇）}。'
    '写法：具体、有画面、有小动作，像游戏官网角色页；不用 tilde，不写身材和性感描写；所有内容和给定的设定、外形一致；画风一栏填给定的画风。',
    json.dumps({k:c.get(k) for k in ('name','type','age','role','traits','bio','desc','style_name','line','lore')},ensure_ascii=False)+('\n用户自己粘贴的完整设定（lore）优先，主页内容要和它一致，不要编造冲突的信息。' if c.get('lore') else ''))

_rb={}
def make_cutout(c):
  """透明底立绘：rembg isnet-anime，裁到人物边框"""
  from rembg import remove,new_session
  if 'ses' not in _rb: _rb['ses']=new_session('isnet-anime')
  src=c['img']; data=requests.get(src,timeout=60).content if src.startswith('http') else open(os.path.join(HERE,src),'rb').read()
  im=remove(Image.open(io.BytesIO(data)).convert('RGB'),session=_rb['ses'])
  a=im.getchannel('A').point(lambda v:0 if v<24 else 255 if v>110 else int((v-24)*255/86)); im.putalpha(a)   # 10-09 浅色衣服抠成半透明会透出背后影子 → 硬化 alpha
  bb=im.getbbox()
  if bb: im=im.crop(bb)
  im.thumbnail((900,1600)); fn=f"u/{c['id']}_cutout.webp"; im.save(os.path.join(HERE,fn),'WEBP',quality=88)
  return dict(src=fn,width=im.width,height=im.height)

_CUT={}   # 改了抠图算法就重启清缓存
@app.post('/api/cutout')   # 10-09 设定页提前抠图：全身立绘透明底，放在大卡里配去色影子
def api_cutout():
  src=(request.json or {}).get('img','')
  if not src: return jsonify(error='no img'),400
  k=hashlib.md5(src.encode()).hexdigest()[:12]
  if k not in _CUT: _CUT[k]=make_cutout(dict(img=src,id='pre_'+k))
  return jsonify(_CUT[k])

def build_page(c):
  f1=POOL.submit(page_copy,c); f2=POOL.submit(make_cutout,c)
  try: c['profile']=f1.result()
  except Exception as e: c['profile']={}; c['page_err']=str(e)
  try: c['cutout']=f2.result()
  except Exception as e: c['cutout_err']=str(e)
  return c

@app.post('/api/save')
def api_save():
  c=request.json; c['id']=hashlib.md5(f"{time.time()}{c.get('name')}".encode()).hexdigest()[:10]; c['created']=time.strftime('%Y-%m-%d %H:%M')
  c['style_name']=sname(c.get('style')) or '保持原图画风'
  build_page(c)
  from roleplay import generate
  try: c['roleplay']=generate(c,llm)
  except Exception as e: c['roleplay_err']=str(e)[:160]
  json.dump(c,open(os.path.join(HERE,'chars',c['id']+'.json'),'w'),ensure_ascii=False,indent=1)
  # 新建角色完成互动设定后立即分类，让聊天入口读取到同一份角色。
  try:
    import character_taxonomy,sys
    character_taxonomy.classify(c,sys.modules[__name__])
  except Exception:
    app.logger.exception('新建角色分类暂未完成：%s',c['id'])
  vo=(c.get('profile') or {}).get('voice') or []   # 10-09 木木夕：登场气泡用按性格写的「初次见面」台词
  hello=(c.get('roleplay') or {}).get('first_mes') or next((v.get('line') for v in vo if '初次' in (v.get('context') or '')),None) or (vo[0].get('line') if vo else '')
  return jsonify(id=c['id'],url='c/'+c['id'],hello=hello)
@app.get('/api/chars')
def api_chars():
  out=[]
  for f in sorted(os.listdir(os.path.join(HERE,'chars')),key=lambda f:-os.path.getmtime(os.path.join(HERE,'chars',f)))[:60]:
    c=json.load(open(os.path.join(HERE,'chars',f)))
    from character_taxonomy import read as read_classification
    if read_classification(c)['rating']!='safe': continue
    out.append(dict(id=c['id'],name=c.get('name'),img=c.get('img'),cutout=(c.get('cutout') or {}).get('src'),created=c.get('created')))
  return jsonify(out)
@app.get('/c/<cid>')
def char_page(cid):
  p=os.path.join(HERE,'chars',os.path.basename(cid)+'.json')
  if not os.path.exists(p): abort(404)
  return send_file(os.path.join(HERE,'char.html'))
@app.get('/api/char/<cid>')
def api_char(cid):
  p=os.path.join(HERE,'chars',os.path.basename(cid)+'.json')
  if not os.path.exists(p): abort(404)
  c=json.load(open(p))
  if 'profile' not in c:   # 10-08 之前存的角色：按新主页结构补一次
    build_page(c); json.dump(c,open(p,'w'),ensure_ascii=False,indent=1)
  if c.get('tavern_card'):
    from card_text import clean_tree
    # 只净化返回的展示字段，原始卡和磁盘资料保留，避免改写用户人设。
    c=dict(c)
    for field in ('bio','role','profile','roleplay'):
      if field in c:c[field]=clean_tree(c[field])
  # 台词展示与原始剧情分开：每项只保留可识别的一句口头台词。
  if isinstance(c.get('profile'),dict):
    from card_text import spoken_line
    c=dict(c,profile=dict(c['profile']))
    c['profile']['voice']=[dict(v,line=line) for v in c['profile'].get('voice',[]) if isinstance(v,dict) and (line:=spoken_line(v.get('line')))]
  return jsonify(c)

# 10-09 木木夕：作者可以编辑主页上的所有内容（测试站不分作者，正式版只给创建者）
EDIT_KEYS=('epithet','world','accent','attributes','summary','hook','scene_title','story','signatures','voice','dossier','files')
@app.post('/api/char/<cid>')
def api_char_edit(cid):
  p=os.path.join(HERE,'chars',os.path.basename(cid)+'.json')
  if not os.path.exists(p): abort(404)
  c=json.load(open(p)); d=request.json or {}
  if (d.get('name') or '').strip(): c['name']=d['name'].strip()[:40]
  if d.get('bio') is not None: c['bio']=str(d['bio'])[:200]
  pr=c.setdefault('profile',{})
  for k in EDIT_KEYS:
    if k in (d.get('profile') or {}): pr[k]=d['profile'][k]
  if d.get('img') and d['img']!=c.get('img') and d['img'] in (c.get('images') or []):   # 换主立绘 → 重新抠图
    c['img']=d['img']
    try: c['cutout']=make_cutout(c); c.pop('cutout_err',None)
    except Exception as e: c['cutout']=None; c['cutout_err']=str(e)
  c['edited']=time.strftime('%Y-%m-%d %H:%M')
  json.dump(c,open(p,'w'),ensure_ascii=False,indent=1)
  return jsonify(c)
REWRITE={'summary':'"epithet":"称号，格式「世界观 · 职业」","summary":"档案简介 70~110 字：先交代清楚是谁、在哪、做什么，最后一句是钩子","attributes":[{"label":"所属","value":"…"},{"label":"身份","value":"…"},{"label":"形态","value":"…"},{"label":"年龄感","value":"…"},{"label":"性格","value":"…"},{"label":"画风","value":"保持原值"}]',
 'story':'"hook":"悬念句，一句话，25 字内","story":["故事第一段 100~150 字","故事第二段 100~150 字"]',
 'voice':'"voice":[{"context":"场景","line":"台词，40 字内"}]（5 句：初次见面、闲聊、开心、生气或失落、告别）',
 'dossier':'"dossier":[{"label":"喜欢","value":"…"},{"label":"讨厌","value":"…"},{"label":"习惯","value":"…"},{"label":"秘密","value":"…"}]',
 'files':'"files":[{"title":"档案故事标题 2~6 字","body":"80~140 字的小片段"}]（3 篇）',
 'signatures':'"signatures":[{"title":"辨识特征名 4~8 字","body":"具体描述 20~40 字"}]（4 条，只写立绘里看得见的外形）'}
@app.route('/api/char/<cid>/roleplay',methods=['POST','PUT'])
def roleplay_card(cid):
  p=os.path.join(HERE,'chars',os.path.basename(cid)+'.json')
  if not os.path.exists(p): abort(404)
  c=json.load(open(p))
  if request.method=='PUT':
    card=(request.json or {}).get('roleplay')
    if not isinstance(card,dict): return jsonify(error='角色卡必须为对象'),400
  else:
    from roleplay import generate
    card=generate(c,llm)
  c['roleplay']=card
  json.dump(c,open(p,'w'),ensure_ascii=False,indent=1)
  return jsonify(roleplay=card)

@app.post('/api/char/<cid>/rewrite')
def api_char_rewrite(cid):
  p=os.path.join(HERE,'chars',os.path.basename(cid)+'.json')
  if not os.path.exists(p): abort(404)
  c=json.load(open(p)); d=request.json or {}; sec=d.get('section')
  if sec not in REWRITE: abort(400)
  cur={**(c.get('profile') or {}),**(d.get('profile') or {})}; cur['name']=d.get('name') or c.get('name')
  hint=(d.get('hint') or '').strip()
  r=llm('你在帮作者重写原创角色主页里的一个板块。'+LANG+'只输出 JSON：{'+REWRITE[sec]+'}。写法：具体、有画面、有小动作，像游戏官网角色页；不用 tilde，不写身材和性感描写；必须和角色其他设定一致，不要和现有内容重复。',
        json.dumps({'角色':{k:cur.get(k) for k in ('name','epithet','world','attributes','summary','hook','story','dossier')},'外形':c.get('desc'),'性格':c.get('traits'),'作者原设定':c.get('lore'),'要重写的板块现在是':{k:cur.get(k) for k in (['hook','story'] if sec=='story' else ['epithet','summary','attributes'] if sec=='summary' else [sec])},'作者的要求':hint or '换一种写法'},ensure_ascii=False))
  if sec=='summary':   # 画风一栏不让模型改
    old={a.get('label'):a.get('value') for a in (cur.get('attributes') or [])}
    for a in r.get('attributes') or []:
      if a.get('label')=='画风': a['value']=old.get('画风') or c.get('style_name') or a.get('value')
  return jsonify(r)
@app.errorhandler(Exception)
def oops(e):
  from werkzeug.exceptions import HTTPException
  if isinstance(e,HTTPException): return e
  import traceback; traceback.print_exc()
  return jsonify(error=f'{type(e).__name__}: {e}'),500
# 10-10 木木夕：角色主页延展玩法（服装抽卡 / 运势表情包 / 出场 PV）
import sys as _sys, plays; plays.init(_sys.modules[__name__]); app.register_blueprint(plays.bp)
import adult; adult.init(_sys.modules[__name__]); app.register_blueprint(adult.bp)   # 10-10 成人模式（类型卡 / 剧情列表 / 互动剧情播放器）
import templates; templates.init(_sys.modules[__name__],plays); app.register_blueprint(templates.bp)
import discover; app.register_blueprint(discover.bp)
import tavern; app.register_blueprint(tavern.bp)
import demo; demo.init(_sys.modules[__name__]); app.register_blueprint(demo.bp)   # demo：剧情工作台与角色聊天
import worldbooks; app.register_blueprint(worldbooks.bp)
import snapshots; app.register_blueprint(snapshots.bp)
import snapshot_motion; app.register_blueprint(snapshot_motion.bp)
if __name__=='__main__': app.run('127.0.0.1',8791,threaded=True)
