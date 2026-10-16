# 发现页只读取已有角色和素材；浏览不触发生图或角色档案补写。
import json, os, threading, re, hashlib
from pathlib import Path
from flask import Blueprint, jsonify, send_file, request
import character_taxonomy as taxonomy
ROOT=Path(__file__).resolve().parent
bp=Blueprint('discover',__name__)
# 目录变化时才重读原卡；缓存按成年访问权限与响应类型隔离。
_catalog_cache={}
_catalog_lock=threading.Lock()
def catalog_stamp():
    return tuple((str(p.relative_to(ROOT)),p.stat().st_mtime_ns,p.stat().st_size) for folder in ('chars','classification','adult/oc') for p in sorted((ROOT/folder).glob('*.json'))) + ((ROOT/'adult/gen/works.jsonl').stat().st_mtime_ns if (ROOT/'adult/gen/works.jsonl').exists() else 0,)


def read(path,default):
    try: return json.loads(path.read_text())
    except (OSError,ValueError): return default

def opening_line(c,greeting):
    # 优先取原卡开场中的对白，不调用模型改写。
    from card_text import clean
    text=clean(str((c.get('roleplay') or {}).get('first_mes') or greeting or ''))
    text=text.replace('{{char}}',str(c.get('name') or '角色')).replace('{{user}}','你')
    quoted=re.search(r'[“「「\"]([^”」\"\n]{2,240})[”」\"]',text)
    if quoted:return quoted.group(1).strip()[:100]
    lines=[re.sub(r'\*[^*]*\*','',line).strip(' *') for line in text.splitlines()]
    return next((line[:100] for line in lines if line),'')

@bp.get('/chat')
def chat_page(): return send_file(ROOT/'chat.html',max_age=0)
@bp.get('/shell.css')
def shell_css(): return send_file(ROOT/'shell.css',max_age=0)
@bp.get('/shell.js')
def shell_js(): return send_file(ROOT/'shell.js',max_age=0)
@bp.get('/discover.js')
def discover_js(): return send_file(ROOT/'discover.js',max_age=0)
@bp.get('/chat.css')
def chat_css(): return send_file(ROOT/'chat.css',max_age=0)
@bp.get('/chat.js')
def chat_js(): return send_file(ROOT/'chat.js',max_age=0)

@bp.get('/discover/api/characters')
def characters():
    if request.args.get('cid'):
        return build_characters()
    adult=request.args.get('adult')=='1' and request.cookies.get('oc_adult')=='1'
    view=request.args.get('view','')
    cards=view in ('cards','chat')
    stamp=catalog_stamp(); cache_key=(adult,view)
    stamp=('import-format-1016',stamp)
    fingerprint=hashlib.sha256(repr(stamp).encode()).hexdigest()
    disk=ROOT/'catalog_cache'/('adult' if adult else 'safe')
    disk=disk.with_name(disk.name+'-'+('chat' if view=='chat' else 'cards' if cards else 'full')+'.json')
    with _catalog_lock:
        cached=_catalog_cache.get(cache_key)
        if cached and cached[0]==stamp:return jsonify(characters=cached[1])
        saved=read(disk,{})
        if saved.get('stamp')==fingerprint:
            _catalog_cache[cache_key]=(stamp,saved['rows'])
            return jsonify(characters=saved['rows'])
        response=build_characters()
        rows=response.get_json()['characters']
        if cards:
            fields={'id','name','img','category','type','role','summary','classification','adult_only','nsfw_cover','opening'}
            rows=[{k:v for k,v in row.items() if k in fields} for row in rows]
        if view=='chat':
            rows=[{k:v for k,v in row.items() if k in ('id','name','img','role')} for row in rows]
        from asset_store import write_json
        disk.parent.mkdir(exist_ok=True)
        write_json(disk,{'stamp':fingerprint,'rows':rows})
        _catalog_cache[cache_key]=(stamp,rows)
        return jsonify(characters=rows)

def build_characters():
    covers={}
    path=ROOT/'adult/gen/works.jsonl'
    if path.exists():
        for line in path.read_text().splitlines():
            try: w=json.loads(line)
            except ValueError: continue
            if w.get('cid') and w.get('src'): covers[str(w['cid'])]=w['src']
    include_adult=request.args.get('adult')=='1' and request.cookies.get('oc_adult')=='1'
    rows=[]
    requested=request.args.get('cid','')
    paths=[ROOT/'chars'/(requested+'.json')] if requested and requested==os.path.basename(requested) else list((ROOT/'chars').glob('*.json'))
    for path in sorted((p for p in paths if p.exists()),key=lambda p:p.stat().st_mtime,reverse=True):
        c=read(path,{})
        if not c.get('id'): continue
        classification=taxonomy.read(c)
        if classification['rating'] not in (('safe','nsfw') if include_adult else ('safe',)):continue
        cid=c['id']; p=c.get('profile') or {}; kind=c.get('type','')
        gender=c.get('gender') or {'少女':'女','御姐':'女','假小子':'女','少年':'男','熟男':'男','成男':'男','男娘':'男'}.get(kind,'')
        category='Furry' if kind=='Furry' else '异种' if kind in ('异种','异种族','非人') else '男性' if gender in ('男','男性','male') else '女性' if gender in ('女','女性','female') else '其他'
        check=read(ROOT/'adult/oc'/(cid+'_age.json'),{})
        # 成人封面沿用此前成功生成素材时的年龄与外观核验，不把普通立绘当作成人封面。
        approved=c.get('age') in ('成年','成熟','年长') and check.get('adult') is True and check.get('img')==c.get('img')
        nsfw=c.get('img') if c.get('adult_album_type') else covers.get(cid) if approved else None
        voice=p.get('voice') or []
        greeting=next((v.get('line') for v in voice if '初次' in v.get('context','')),None)
        cut=(c.get('cutout') or {}).get('src')
        images=list(dict.fromkeys([s for s in [cut,c.get('img'),*(c.get('images') or []),*[w.get('src') for w in c.get('works') or [] if w.get('kind')!='pv']] if isinstance(s,str) and s]))
        motion_key={'御姐':'yujie','甜心':'tianxin','辣妹':'lamei','熟女':'shunv','型男':'xingnan','熟男':'shunan','魅魔':'meimo','兽人':'shouren'}.get(c.get('adult_album_type'))
        motion='adult/cards/'+motion_key+'.mp4' if motion_key and (ROOT/'adult/cards'/(motion_key+'.mp4')).exists() else None
        if not include_adult:nsfw=None;images=[c.get('img')];motion=None
        rows.append(dict(opening=opening_line(c,greeting),motion=motion,classification=classification,adult_only=classification['rating']=='nsfw',id=cid,name=c.get('name') or '未命名',img=c.get('img'),cutout=cut,category=category,type=kind,role=c.get('role') or '',summary=p.get('summary') or c.get('bio') or '',greeting=__import__('card_text').clean((c.get('roleplay') or {}).get('first_mes') or greeting or ''),accent=p.get('accent') or '#ef6595',images=images,nsfw_cover=nsfw,works=len(c.get('works') or [])))
    return jsonify(characters=rows)

@bp.post('/discover/api/adult-access')
def adult_access():
    data=request.get_json(silent=True) or {}
    response=jsonify(ok=True)
    if data.get('confirmed') is True:response.set_cookie('oc_adult','1',max_age=12*3600,httponly=True,samesite='Lax',path='/oc-lab/',secure=request.headers.get('X-Forwarded-Proto')=='https')
    else:response.delete_cookie('oc_adult',path='/oc-lab/')
    return response
