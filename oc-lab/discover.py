# 发现页只读取已有角色和素材；浏览不触发生图或角色档案补写。
import json, os
from pathlib import Path
from flask import Blueprint, jsonify, send_file
ROOT=Path(__file__).resolve().parent
bp=Blueprint('discover',__name__)

def read(path,default):
    try: return json.loads(path.read_text())
    except (OSError,ValueError): return default

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
    covers={}
    path=ROOT/'adult/gen/works.jsonl'
    if path.exists():
        for line in path.read_text().splitlines():
            try: w=json.loads(line)
            except ValueError: continue
            if w.get('cid') and w.get('src'): covers[str(w['cid'])]=w['src']
    rows=[]
    for path in sorted((ROOT/'chars').glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True):
        c=read(path,{})
        if not c.get('id'): continue
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
        rows.append(dict(adult_only=bool(c.get('adult_album_type')),id=cid,name=c.get('name') or '未命名',img=c.get('img'),cutout=cut,category=category,type=kind,role=c.get('role') or '',summary=p.get('summary') or c.get('bio') or '',greeting=greeting or '',accent=p.get('accent') or '#ef6595',images=images,nsfw_cover=nsfw,works=len(c.get('works') or [])))
    return jsonify(characters=rows)
