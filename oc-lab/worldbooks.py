# 世界观展示、可编辑世界书与聊天按需读取；原卡内容不被覆盖。
import json,hashlib,re,time,threading,uuid
from pathlib import Path
from flask import Blueprint,jsonify,request,send_file,abort
from asset_store import write_json
from card_text import clean
ROOT=Path(__file__).resolve().parent;STORE=ROOT/'world_data';DOCS=STORE/'worlds';BIND=STORE/'bindings.json';LOCK=threading.RLock()
bp=Blueprint('worldbooks',__name__)
DOCS.mkdir(parents=True,exist_ok=True)
def read(path,default):
 try:return json.loads(Path(path).read_text())
 except (OSError,ValueError):return default

def char(cid):
 if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',str(cid)):abort(400)
 c=read(ROOT/'chars'/(cid+'.json'),None)
 if not c:abort(404)
 return c

def doc(wid):
 if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',str(wid)):abort(400)
 d=read(DOCS/(wid+'.json'),None)
 if not d:abort(404)
 return d

# 现有库的世界观初始副本只在目标文件不存在时建立，不覆盖用户编辑。
for seed in read(ROOT/'world_seed.json',[]):
 if not (DOCS/(seed['id']+'.json')).exists():write_json(DOCS/(seed['id']+'.json'),seed)

def number(value,default=0,lo=-100000,hi=100000):
 try:return max(lo,min(hi,int(value)))
 except (ValueError,TypeError):return default

def normalize(entry,index):
 ext=entry.get('extensions') or {}
 keys=entry.get('keys') or []
 secondary=entry.get('secondary_keys') or []
 if not isinstance(keys,list):keys=[]
 if not isinstance(secondary,list):secondary=[]
 return {'id':str(entry.get('id',index))[:100],'title':str(entry.get('title') or entry.get('comment') or entry.get('name') or '设定条目')[:120],
 'keys':[str(x)[:100] for x in keys[:50]],'secondary_keys':[str(x)[:100] for x in secondary[:50]],
 'content':clean(str(entry.get('content') or ''))[:30000], 'enabled':entry.get('enabled',True) is not False,
 'constant':entry.get('constant') is True,'selective':entry.get('selective') is True,
 'logic':number(entry.get('logic',ext.get('selectiveLogic',0)),0,0,3),
 'priority':number(entry.get('priority',ext.get('order',entry.get('insertion_order',100))),100),
 'use_regex':entry.get('use_regex') is True,'case_sensitive':entry.get('case_sensitive',ext.get('case_sensitive',False)) is True,
 'probability':number(ext.get('probability',entry.get('probability',100)),100,0,100),
 'position':str(entry.get('position','after_char'))[:50]}

def materialize(c):
 # 仅首次导入建立独立编辑副本，相同世界书复用同一世界文档。
 with LOCK:
  bindings=read(BIND,{})
  if c['id'] in bindings:return bindings[c['id']]
  raw=c.get('tavern_card') or {};data=raw.get('data',{}) if raw.get('spec') else raw;book=(data or {}).get('character_book')
  if not isinstance(book,dict) or not isinstance(book.get('entries'),list):return []
  digest=hashlib.sha256(json.dumps(book,ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:16];wid='card-'+digest
  if not (DOCS/(wid+'.json')).exists():
   entries=[normalize(e,i) for i,e in enumerate(book['entries']) if isinstance(e,dict)]
   write_json(DOCS/(wid+'.json'),{'id':wid,'name':str(book.get('name') or c.get('name')+'的世界观')[:120], 'tagline':'','story':[],'scene':'','accent':'#ef6595','entries':entries,'scan_depth':number(book.get('scan_depth'),8,1,50),'budget':4096,'revision':1,'source':'角色卡附带世界书','source_book':book,'updated':time.time()})
  bindings[c['id']]=[wid];write_json(BIND,bindings);return [wid]

def linked(c):
 b=read(BIND,{})
 return b[c['id']] if c['id'] in b else materialize(c)

def catalog():
 bindings=read(BIND,{});members={}
 for cid,ids in bindings.items():
  for wid in ids:members.setdefault(wid,[]).append(cid)
 rows=[]
 for p in DOCS.glob('*.json'):
  d=read(p,{})
  if d.get('id'):rows.append({k:d.get(k) for k in ('id','name','tagline','scene','accent')}|{'entries':len(d.get('entries',[])),'members':members.get(d['id'],[])})
 return sorted(rows,key=lambda d:d.get('name') or '')

def hit(key,text,sensitive=False):
 if not key:return False
 if not sensitive:key=key.casefold();text=text.casefold()
 if re.fullmatch(r'[a-zA-Z0-9_ ]+',key):return bool(re.search(r'(?<!\w)'+re.escape(key)+r'(?!\w)',text))
 return key in text

def activate(c,messages):
 budget=6144;used=0;selected=[];trace=[]
 for wid in linked(c)[:8]:
  d=read(DOCS/(wid+'.json'),{});spent=0;limit=min(number(d.get('budget'),4096,0,6144),budget)
  overview='\n'.join(x for x in [d.get('name',''),d.get('tagline',''),*(d.get('story') or [])] if x)
  if overview:
   cost=len(overview.encode('utf-8'))+100
   ok=cost<=limit and used+cost<=budget
   if ok:selected.append({'world':d.get('name'),'entry':'世界观简介','content':overview});spent+=cost;used+=cost
   trace.append({'world':d.get('name'),'id':'overview','title':'世界观简介','keys':[],'active':ok,'reason':'关联世界观常驻背景' if ok else '简介超出注入预算'})
  recent=messages[-number(d.get('scan_depth'),8,1,50):];text='\n'.join(str(m.get('content','')) for m in recent)
  for e in sorted(d.get('entries',[]),key=lambda x:number(x.get('priority'),100)):
   reason='';matches=[k for k in e.get('keys',[]) if hit(k,text,e.get('case_sensitive'))]
   if not e.get('enabled',True):reason='已停用'
   elif e.get('use_regex'):reason='正则触发暂不支持'
   elif e.get('probability',100)!=100:reason='概率触发暂不支持'
   elif not e.get('constant') and not matches:continue
   elif e.get('selective') and not e.get('constant'):
    secondary=e.get('secondary_keys',[]);flags=[hit(k,text,e.get('case_sensitive')) for k in secondary];logic=e.get('logic',0)
    ok=bool(secondary) and (any(flags) if logic==0 else not all(flags) if logic==1 else not any(flags) if logic==2 else all(flags))
    if not ok:continue
   content=e.get('content','');cost=len(content.encode('utf-8'))+len(str(e.get('title','')).encode('utf-8'))+100
   # UTF-8字节数作为保守预算单位；不把估算冒称精确token。
   if not reason and not content.strip():reason='正文为空'
   if not reason and (spent+cost>limit or used+cost>budget):reason='超出本轮注入预算'
   if not reason:
    selected.append({'world':d.get('name'),'entry':e.get('title'),'content':content,'position':e.get('position')});spent+=cost;used+=cost
   if e.get('enabled',True):trace.append({'world':d.get('name'),'id':e.get('id'),'title':e.get('title'),'keys':matches,'active':not bool(reason),'reason':reason or ('常驻' if e.get('constant') else '关键词命中')})
 return selected,{'used_bytes':used,'budget_bytes':budget,'entries':trace[:200]}

@bp.get('/worlds')
def page():return send_file(ROOT/'worlds.html',max_age=0)
@bp.get('/worlds.js')
def js():return send_file(ROOT/'worlds.js',max_age=0)
@bp.get('/worlds.css')
def css():return send_file(ROOT/'worlds.css',max_age=0)
@bp.get('/api/worlds')
def list_worlds():
 cid=request.args.get('cid');ids=linked(char(cid)) if cid else []
 return jsonify(worlds=catalog(),linked=ids)
@bp.post('/api/worlds')
def create():
 data=request.get_json(silent=True) or {};wid='world-'+uuid.uuid4().hex[:12]
 d={'id':wid,'name':str(data.get('name') or '新世界观')[:120],'tagline':'','story':[],'scene':'','accent':'#ef6595','entries':[],'scan_depth':8,'budget':4096,'revision':1,'updated':time.time()}
 write_json(DOCS/(wid+'.json'),d);return jsonify(world=d)
@bp.get('/api/worlds/<wid>')
def get(wid):
 d=dict(doc(wid));d.pop('source_book',None)
 members=[]
 for cid,ids in read(BIND,{}).items():
  if wid in ids:
   c=read(ROOT/'chars'/(cid+'.json'),{})
   if c.get('id'):members.append({'id':cid,'name':c.get('name'),'img':c.get('img')})
 return jsonify(world=d,members=members)
@bp.put('/api/worlds/<wid>')
def update(wid):
 data=request.get_json(silent=True) or {}
 with LOCK:
  d=doc(wid)
  if data.get('revision')!=d.get('revision',1):return jsonify(error='此世界观刚被修改，请重新打开后再保存。'),409
  if not isinstance(data.get('entries'),list) or len(data['entries'])>2000:return jsonify(error='条目格式错误，单个世界最多2000条。'),400
  if any(not isinstance(e,dict) for e in data['entries']):return jsonify(error='条目格式错误'),400
  if len(json.dumps(data,ensure_ascii=False).encode())>3000000:return jsonify(error='世界观内容过大'),400
  backup=STORE/'backups'/wid;backup.mkdir(parents=True,exist_ok=True);write_json(backup/(str(d.get('revision',1))+'.json'),d)
  for k,limit in [('name',120),('tagline',300)]:d[k]=clean(str(data.get(k,d.get(k,''))))[:limit]
  d['story']=[clean(str(x))[:10000] for x in (data.get('story') or [])[:20]]
  d['entries']=[normalize(e,i) for i,e in enumerate(data['entries'])]
  d['scan_depth']=number(data.get('scan_depth'),8,1,50);d['budget']=number(data.get('budget'),4096,0,6144)
  d['revision']=d.get('revision',1)+1;d['updated']=time.time();write_json(DOCS/(wid+'.json'),d)
  result=dict(d);result.pop('source_book',None);return jsonify(world=result)
@bp.put('/api/char/<cid>/worlds')
def bind(cid):
 char(cid);data=request.get_json(silent=True) or {};ids=data.get('world_ids')
 if not isinstance(ids,list) or len(ids)>8 or not all(isinstance(x,str) for x in ids):return jsonify(error='最多关联8个世界观'),400
 for wid in ids:doc(wid)
 with LOCK:
  b=read(BIND,{});b[cid]=list(dict.fromkeys(ids));write_json(BIND,b)
 return jsonify(linked=b[cid])
@bp.post('/api/worlds/preview')
def preview():
 data=request.get_json(silent=True) or {};c=char(data.get('cid'));text=str(data.get('text',''))[:10000]
 entries,trace=activate(c,[{'role':'user','content':text}]);return jsonify(trace=trace)
