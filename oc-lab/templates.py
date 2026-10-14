# 模板库：角色参考图自动带入；作品保存配方，支持重新生成与换角色做同款。
import base64, io, json, os, time, uuid, threading
from pathlib import Path
import requests
from PIL import Image
from flask import Blueprint, request, jsonify, send_file, abort
from asset_store import ROOT, LOCK, write_json, update_character
bp=Blueprint('templates',__name__)
CATALOG=json.loads((ROOT/'templates.json').read_text())
TOOLS={x['id']:x for x in CATALOG['items']}
JOBS=ROOT/'template_jobs'
A=None; P=None

def init(app_mod,plays_mod):
    global A,P
    A=app_mod; P=plays_mod
    JOBS.mkdir(exist_ok=True)
    # 服务重启后只继续查询已提交的上游任务，绝不重复付费提交。
    for path in JOBS.glob('*.json'):
        j=json.loads(path.read_text())
        if j['status']=='running':
            if j.get('task_id'): A.POOL.submit(resume,j)
            else:
                j.update(status='error',error='服务重启中断了任务，请手动重试。'); persist(j)

def persist(j):
    with LOCK: write_json(JOBS/(j['id']+'.json'),j)

def public_tool(t): return {k:t[k] for k in ('id','name','category','size','cover')}

def reference(c,saved=None):
    if saved: return saved
    return (c.get('reference_sheet') or {}).get('src') or c.get('img')

def png64(src):
    im=Image.open(io.BytesIO(P.load_bytes(src))).convert('RGBA')
    im.thumbnail((1536,1536)); bg=Image.new('RGB',im.size,'white'); bg.paste(im,mask=im.getchannel('A'))
    out=io.BytesIO(); bg.save(out,'PNG'); return base64.b64encode(out.getvalue()).decode()

def card_fields(c):
    p=c.get('profile') or {}; at={a.get('label'):a.get('value') for a in p.get('attributes') or []}
    voice=p.get('voice') or []
    line=next((v.get('line') for v in voice if '初次' in v.get('context','')),None)
    traits=c.get('traits'); traits='、'.join(traits) if isinstance(traits,list) else traits
    fields={'Name':c.get('name'),'Affiliation':at.get('所属') or at.get('阵营') or p.get('world'),'Role':c.get('role') or at.get('身份'),'Personality':traits,'Signature line':line,'Club':at.get('社团')}
    return '\n'.join(k+': '+(str(v) if v else '(leave blank)') for k,v in fields.items())

def prompt_for(t,c,options,composition_index=None):
    guide='Image 1 is the authoritative character reference. Preserve recognizable identity, face, hairstyle, outfit colors, proportions, and signature accessories while creating the requested new composition.'
    if t['layout']: guide+=' Image 2 is the hidden built-in layout reference; use its composition and typography system without copying leftover text, logos, or watermarks.'
    if t['category']=='换装': guide='Image 1 is the authoritative character reference. Preserve identity, face, hairstyle, species, proportions, and signature accessories. Change only the clothing as requested.'
    user=t['default_prompt']
    if t['category']=='换装': user=options.get('outfit','Change clothing to a modern casual outfit.')
    if composition_index:
        guide+=' Image '+str(composition_index)+" is the previous completed work, used ONLY for composition, background, color palette, pose and typography placement. Follow its visual layout closely. Replace its character completely with Image 1's character. Do not copy the previous character's face, species, hair or personal accessories, or their name and biography. Replace character-specific copy with the supplied target character fields; keep missing fields blank. For outfit tools apply the selected clothing instruction."
    parts=[t['system_prompt'],guide,'Uploaded image count: '+str(composition_index or (2 if t['layout'] else 1))+'.','User request: '+user]
    if t['category'] in ('角色卡','明信片'):
        parts+=['Use only these character card fields for text:\n'+card_fields(c),'Leave any card field that is not provided blank; do not invent values.']
    if options.get('request'): parts+=['Additional request: '+options['request']]
    parts+=['Keep character identity consistent; visual appearance comes only from Image 1, not from character biography text. Render only intentional functional copy. Avoid random text, watermarks, logos, extra main characters, duplicated body parts, or warped anatomy.']
    return '\n\n'.join(parts)

def archive(j,url):
    # 下载到测试站，避免作品依赖临时的生成链接。
    r=requests.get(url,timeout=90); r.raise_for_status()
    src=P.save_png(r.content,j['cid']+'_template_'+j['id'])
    work=dict(id=j['id'],kind='template',src=src,title=j['title'],created=time.strftime('%Y-%m-%d %H:%M'),recipe=j['recipe'])
    def add(c):
        works=c.setdefault('works',[])
        if not any(w.get('id')==j['id'] for w in works): works.insert(0,work)
    update_character(j['cid'],add)
    j.update(status='done',phase='已保存到角色作品库',src=src,work=work); persist(j)

def poll(j):
    for _ in range(180):
        r=requests.post(A.B+'/b2b/tasks/get',headers=A.HB(),json={'task_id':j['task_id']},timeout=60)
        r.raise_for_status(); payload=r.json(); d=payload.get('data') or {}
        status=str(d.get('status','')).upper()
        if status=='COMPLETED':
            images=(d.get('result') or {}).get('images') or []
            if not images: raise RuntimeError('生成任务完成但没有返回图片。')
            url=images[0].get('display_url') or images[0].get('url')
            if not url: raise RuntimeError('生成任务未返回图片地址。')
            archive(j,url); return
        if status in ('FAILED','FAILURE','ERROR','CANCELLED'): raise RuntimeError('生成失败：'+str(d.get('error') or d.get('message') or status)[:160])
        time.sleep(5)
    raise RuntimeError('生成等待超时，上游任务号已保留。')

def resume(j):
    try: poll(j)
    except Exception as e: j.update(status='error',error=str(e)[:250]); persist(j)

def execute(j):
    try:
        t=TOOLS[j['template_id']]; _,c=P.char(j['cid'])
        src=j.get('reference') or reference(c)
        inputs=[dict(role='角色参考图',src=src)]
        if t['layout']: inputs.append(dict(role='版式参考',src=t['layout']))
        composition_index=None
        if j.get('source') and j['source']['cid']!=j['cid']:
            inputs.append(dict(role='原作品构图参考',src=j['source']['src']))
            composition_index=len(inputs)
        if j.get('saved_inputs'): inputs=j['saved_inputs']; src=inputs[0]['src']
        images=[png64(i['src']) for i in inputs]
        pr=j.get('saved_prompt') or prompt_for(t,c,j['options'],composition_index)
        j['recipe']=dict(version=1,play='template',play_name=t['name'],template_id=t['id'],character=dict(P.char_ref(c,j['cid']),ref=src),inputs=inputs,prompt=pr,model=dict(name='gpt-image-2',quality='low',size=j.get('saved_size') or t['size']),options=j['options'],source=j.get('source'),config_commit=CATALOG['commit'])
        j.update(phase='生成中'); persist(j)
        body={'task_type':'API_TEXT_TO_IMAGE_GPT_IMAGE_2','params':{'prompt':pr,'size':j.get('saved_size') or t['size'],'quality':'low','model':'gpt-image-2','amount':1,'b64_images':images,'watermark':False}}
        r=requests.post(A.B+'/b2b/tasks/create',headers=A.HB(),json=body,timeout=90); r.raise_for_status()
        data=r.json(); tid=(data.get('data') or {}).get('task_id')
        if not tid: raise RuntimeError('任务未创建：'+str(data.get('message') or data.get('error') or '接口没有返回任务号')[:180])
        j['task_id']=tid; j['recipe']['task_id']=tid; persist(j); poll(j)
    except Exception as e: j.update(status='error',error=str(e)[:250]); persist(j)

@bp.get('/templates')
def page(): return send_file(ROOT/'templates.html',max_age=0)
@bp.get('/templates.js')
def js(): return send_file(ROOT/'templates.js',max_age=0)
@bp.get('/templates.css')
def css(): return send_file(ROOT/'templates.css',max_age=0)
@bp.get('/api/templates')
def catalog(): return jsonify(items=[public_tool(t) for t in TOOLS.values()])
@bp.get('/api/templates/characters')
def characters():
    out=[]
    for f in sorted((ROOT/'chars').glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True):
        c=json.loads(f.read_text()); out.append(dict(id=c['id'],name=c.get('name'),img=c.get('img'),reference_sheet=c.get('reference_sheet')))
    return jsonify(items=out)
@bp.get('/api/templates/works')
def works():
    out=[]
    for f in (ROOT/'chars').glob('*.json'):
        c=json.loads(f.read_text())
        for w in c.get('works') or []:
            out.append(dict(w,source_cid=c['id'],character_name=c.get('name'),reusable=bool((w.get('recipe') or {}).get('play') in ('template','outfit','fortune','pv'))))
    out.sort(key=lambda w:w.get('created',''),reverse=True)
    return jsonify(items=out)
@bp.get('/api/templates/job/<jid>')
def get_job(jid):
    if not all(x in '0123456789abcdef' for x in jid) or len(jid)!=32: abort(404)
    path=JOBS/(jid+'.json')
    if not path.exists(): abort(404)
    return jsonify(json.loads(path.read_text()))

@bp.post('/api/templates/generate')
def generate():
    d=request.get_json() or {}; cid=d.get('cid',''); _,c=P.char(cid)
    source=None; saved=None; saved_prompt=None; saved_size=None; saved_inputs=None; options=d.get('options') or {}; tid=d.get('template_id'); legacy=None
    if d.get('source_cid') and d.get('source_src'):
        _,sc=P.char(d['source_cid']); w=next((w for w in sc.get('works',[]) if w.get('src')==d['source_src']),None)
        if not w or not w.get('recipe'): return jsonify(error='这件作品没有可复用的配方。'),400
        r=w['recipe']; source={'cid':d['source_cid'],'src':w['src'],'title':w.get('title')}
        if r.get('play')=='template':
            tid=r['template_id']; options=r.get('options') or {}
            if cid==d['source_cid']:
                saved=(r.get('inputs') or [{}])[0].get('src'); saved_prompt=r.get('prompt'); saved_size=(r.get('model') or {}).get('size'); saved_inputs=r.get('inputs')
        elif r.get('play') in ('outfit','fortune','pv'): legacy=r
        else: return jsonify(error='这件作品的配方暂不支持复用。'),400
    if not legacy and tid not in TOOLS: return jsonify(error='请选择有效模板。'),400
    if not legacy and not A.B2B_KEY: return jsonify(error='模板生成的 B2B 接口尚未配置。'),503
    if not isinstance(options,dict): return jsonify(error='参数格式不正确。'),400
    options={k:str(v)[:1500] for k,v in options.items() if k in ('request','outfit')}
    j=dict(id=uuid.uuid4().hex,status='running',phase='准备角色参考图',cid=cid,template_id=tid,title=(TOOLS[tid]['name'] if not legacy else legacy.get('play_name','同款作品')),options=options,reference=saved,saved_prompt=saved_prompt,saved_size=saved_size,saved_inputs=saved_inputs,source=source,created=time.strftime('%Y-%m-%d %H:%M'))
    persist(j)
    if legacy: A.POOL.submit(execute_legacy,j,legacy)
    else: A.POOL.submit(execute,j)
    return jsonify(job=j['id'])

def execute_legacy(j,r):
    try:
        params=r.get('params') or {}; play=r['play']; cid=j['cid']
        if play=='outfit':
            card=dict(params.get('card') or {})
            card['thumb']=next((i['src'] for i in r.get('inputs',[]) if '服装' in i.get('role','')),None)
            if not card.get('thumb'): raise RuntimeError('旧换装作品缺少服装参考图。')
            result=P.outfit_make(j,cid,card,(r.get('character') or {}).get('ref') if cid==j['source']['cid'] else None)
        elif play=='fortune':
            sign=params.get('sign','')
            if cid!=j['source']['cid']:
                _,c=P.char(cid)
                sign=A.llm(P.SIGN_P,json.dumps({'name':c.get('name'),'traits':c.get('traits'),'level':params.get('level'),'keywords':params.get('keywords')},ensure_ascii=False),model=A.FAST).get('sign','')
            result=P.fortune_make(j,cid,params['template'],params.get('level',''),params.get('keywords',[]),sign,(r.get('character') or {}).get('ref') if cid==j['source']['cid'] else None)
        else: result=P.pv_make(j,cid,params if cid==j['source']['cid'] else None)
        def annotate(c):
            for w in c.get('works',[]):
                if w.get('src') in (result.get('src'),result.get('card')):
                    w.setdefault('recipe',{})['source']=j['source']
        update_character(cid,annotate)
        j.update(status='done',phase='已保存到角色作品库',**result); persist(j)
    except Exception as e: j.update(status='error',error=str(e)[:250]); persist(j)

@bp.post('/api/templates/reference')
def set_reference():
    d=request.get_json() or {}; cid=d.get('cid',''); _,c=P.char(cid)
    w=next((w for w in c.get('works',[]) if w.get('src')==d.get('src')),None)
    if not w or (w.get('recipe') or {}).get('template_id')!='character-sheet-generator': return jsonify(error='请选择这个角色生成的设定图。'),400
    update_character(cid,lambda c:c.update(reference_sheet=dict(src=w['src'],work_id=w.get('id'))))
    return jsonify(ok=True)
