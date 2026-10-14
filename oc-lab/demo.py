# OC Lab demo：剧情树工作台 + 角色素材聊天。数据仅写入 demo_data/，不改角色原始档案。
import os, json, glob, uuid, time
from flask import Blueprint, request, jsonify, send_file, abort

bp = Blueprint('demo', __name__)
HERE = os.path.dirname(os.path.abspath(__file__))
CHARS = os.path.join(HERE, 'chars')
DATA = os.path.join(HERE, 'demo_data')
STORIES = os.path.join(DATA, 'stories')
A = None

def init(app_mod):
  global A
  A = app_mod
  os.makedirs(STORIES, exist_ok=True)

def _j(path, default=None):
  try:
    with open(path) as f: return json.load(f)
  except Exception: return default

def _char(cid):
  cid = os.path.basename(str(cid or ''))
  c = _j(os.path.join(CHARS, cid + '.json'))
  if not c: abort(404, '角色不存在')
  return c

def _assets(c):
  """只枚举此角色已有作品；素材内容与角色描述交给模型做语义匹配。"""
  cid = c.get('id'); rows = []
  for i, src in enumerate(c.get('images') or [c.get('img')]):
    if isinstance(src, str) and src:
      rows.append(dict(id=f'ill_{i}', kind='立绘', title=f'角色立绘 {i+1}', src=src, hint='角色外观、日常、登场'))
  for i, w in enumerate(c.get('works') or []):
    if isinstance(w, dict) and w.get('src'):
      rows.append(dict(id=f'work_{i}', kind=w.get('kind') or '角色作品', title=w.get('title') or w.get('kind') or '角色作品', src=w['src'], hint=w.get('title') or w.get('kind') or '角色作品'))
  gen = os.path.join(HERE, 'adult', 'gen')
  for file, key, kind in [('works.jsonl', 'src', '角色图片'), ('videos.jsonl', 'src', '角色视频')]:
    p = os.path.join(gen, file)
    if not os.path.isfile(p): continue
    try:
      for line in open(p):
        try: item = json.loads(line)
        except Exception: continue
        if str(item.get('cid') or '') != str(cid) or not item.get(key): continue
        rows.append(dict(id=f'{kind}_{item.get("id")}', kind=kind, title=item.get('label') or item.get('kind_name') or kind,
                         src=item[key], hint=item.get('label') or item.get('kind_name') or kind))
    except OSError: pass
  uniq = {}
  for row in rows: uniq.setdefault(row['src'], row)
  return list(uniq.values())[:80]

def _story_file(sid):
  sid = os.path.basename(sid)
  p = os.path.join(STORIES, sid + '.json')
  if not os.path.isfile(p): abort(404, '剧情不存在')
  return p

@bp.get('/demo')
def page(): return send_file(os.path.join(HERE, 'demo.html'), max_age=0)
@bp.get('/demo.js')
def js(): return send_file(os.path.join(HERE, 'demo.js'), max_age=0)
@bp.get('/demo.css')
def css(): return send_file(os.path.join(HERE, 'demo.css'), max_age=0)

@bp.get('/demo/api/characters')
def characters():
  rows=[]
  for p in glob.glob(os.path.join(CHARS, '*.json')):
    c=_j(p)
    if c: rows.append(dict(id=c.get('id'), name=c.get('name') or '未命名角色', img=c.get('img'), type=c.get('type'), role=c.get('role')))
  return jsonify(characters=sorted(rows, key=lambda x:x['name']))

@bp.get('/demo/api/assets/<cid>')
def assets(cid): return jsonify(assets=_assets(_char(cid)))

@bp.get('/demo/api/stories')
def story_list():
  rows=[]
  for p in sorted(glob.glob(os.path.join(STORIES, '*.json')), key=os.path.getmtime, reverse=True):
    d=_j(p)
    if d: rows.append(dict(id=d.get('id'), title=d.get('title'), character=d.get('character_name'), updated=d.get('updated')))
  return jsonify(stories=rows)

@bp.post('/demo/api/stories/generate')
def story_generate():
  d=request.get_json(silent=True) or {}; c=_char(d.get('cid')); brief=str(d.get('brief') or '').strip()[:1200]
  if not brief: return jsonify(error='先写一句剧情想法'),400
  profile=c.get('profile') or {}; assets=_assets(c)
  asset_text=[dict(id=x['id'],kind=x['kind'],title=x['title'],hint=x['hint']) for x in assets]
  system=('你是互动角色剧本编排器。只输出 JSON，结构为 {"title":"","synopsis":"","start":"n1","nodes":[{"id":"n1","title":"","text":"","asset_id":"素材id或空","choices":[{"text":"选项","next":"n2"}]}]}。'
          '生成 4 到 6 个节点的短互动故事，至少有一个分支结局；所有 next 必须指向存在的节点；节点文本 30~90 字，选项 2~3 个。角色必须符合设定。素材只能从给定清单选，按节点情境匹配；没有合适素材就 asset_id 留空，不要编造素材。')
  user={'角色':{'name':c.get('name'),'type':c.get('type'),'role':c.get('role'),'traits':c.get('traits'),'bio':c.get('bio'),'lore':c.get('lore'),'profile':profile},'剧情想法':brief,'可用角色素材':asset_text}
  try: story=A.llm(system,json.dumps(user,ensure_ascii=False))
  except Exception as e: return jsonify(error='剧本生成失败：'+str(e)[:180]),502
  nodes=story.get('nodes') or []
  if not 2 <= len(nodes) <= 10: return jsonify(error='生成的节点数量不合要求，请重试'),502
  for n in nodes: n['id']=str(n.get('id') or uuid.uuid4().hex[:6])
  valid={n['id'] for n in nodes}
  for n in nodes:
    n['choices']=[x for x in n.get('choices',[]) if str(x.get('next')) in valid][:3]
    asset=next((a for a in assets if a['id']==n.get('asset_id')),None)
    n['asset']=asset
  story.update(id=uuid.uuid4().hex[:12], character_id=c['id'], character_name=c.get('name'), start=story.get('start') if story.get('start') in valid else nodes[0]['id'], nodes=nodes, created=time.strftime('%Y-%m-%d %H:%M:%S'), updated=time.strftime('%Y-%m-%d %H:%M:%S'))
  return jsonify(story=story)

@bp.post('/demo/api/stories/save')
def story_save():
  s=request.get_json(silent=True) or {}; sid=os.path.basename(str(s.get('id') or ''))
  if not sid: sid=uuid.uuid4().hex[:12]; s['id']=sid
  if not s.get('title') or not isinstance(s.get('nodes'),list) or not s['nodes']: return jsonify(error='剧情标题和节点不能为空'),400
  c=_char(s.get('character_id')); valid={str(n.get('id')) for n in s['nodes']}
  for n in s['nodes']:
    n['choices']=[x for x in n.get('choices',[]) if str(x.get('next')) in valid]
    if n.get('asset_id'):
      n['asset']=next((a for a in _assets(c) if a['id']==n['asset_id']),None)
  s['character_name']=c.get('name'); s['updated']=time.strftime('%Y-%m-%d %H:%M:%S')
  with open(os.path.join(STORIES,sid+'.json'),'w') as f: json.dump(s,f,ensure_ascii=False,indent=2)
  return jsonify(ok=True,id=sid)

@bp.get('/demo/api/stories/<sid>')
def story_get(sid):
  d=_j(_story_file(sid)); return jsonify(story=d)

@bp.post('/demo/api/chat')
def chat():
  d=request.get_json(silent=True) or {}; c=_char(d.get('cid')); messages=d.get('messages') or []
  if not messages: return jsonify(error='请先发一条消息'),400
  messages=[{'role':'assistant' if x.get('role')=='assistant' else 'user','content':str(x.get('content') or '')[:1000]} for x in messages[-12:]]
  assets=_assets(c); shortlist=[dict(id=x['id'],kind=x['kind'],title=x['title'],hint=x['hint']) for x in assets]
  style=d.get('style') or {}; pov=style.get('pov','second'); length=style.get('length','medium'); pace=style.get('pace','natural')
  style_hint=f"叙事要求：视角={ {'second':'用第二人称称呼用户','first':'角色用第一人称叙述','third':'用第三人称旁白'} .get(pov,'用第二人称称呼用户')}；回复长度={ {'short':'1~3句','medium':'3~6句','long':'6~10句'} .get(length,'3~6句')}；推进节奏={ {'slow':'慢热，留空间给用户回应','natural':'自然推进','fast':'主动推动事件发展'} .get(pace,'自然推进')}。"
  system=('你正在扮演用户原创角色，与用户进行自然中文 Story Chat。严格依照角色设定和说话风格；不替用户决定用户的动作或想法。'
          '根据对话生成 2~3 条简短、方向不同的后续选项供用户点选，同时保留用户自由输入。'
          '只输出 JSON：{"reply":"角色回复","asset_id":"素材id或空","choices":["选项一","选项二"],"state":{"scene":"当前地点/场景","mood":"角色情绪","relationship":"关系进展"}}。'
          '当某个已有素材能自然回应当前话题时选择它；不必每轮发送素材。只能选素材清单里的 id，不可编造。'+style_hint)
  persona={'name':c.get('name'),'role':c.get('role'),'type':c.get('type'),'traits':c.get('traits'),'bio':c.get('bio'),'lore':c.get('lore'),'voice':(c.get('profile') or {}).get('voice')}
  try:
    result=A.llm(system,json.dumps({'角色设定':persona,'叙事设置':{'视角':pov,'回复长度':length,'推进节奏':pace},'素材清单':shortlist,'对话':messages},ensure_ascii=False),model='deepseek/deepseek-v4.1-flash')
  except Exception as e: return jsonify(error='角色暂时没接上话：'+str(e)[:160]),502
  asset=next((a for a in assets if a['id']==result.get('asset_id')),None)
  state=result.get('state') if isinstance(result.get('state'),dict) else {}
  choices=[str(x)[:100] for x in (result.get('choices') or [])[:3] if str(x).strip()]
  return jsonify(reply=str(result.get('reply') or '')[:1200],asset=asset,choices=choices,
                 state={k:str(state.get(k) or '')[:80] for k in ('scene','mood','relationship')},
                 model='DeepSeek V4.1 Flash')
