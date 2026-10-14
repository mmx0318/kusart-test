# 酒馆 PNG 角色卡导入：解析元数据，不调用模型重写原设定。
import base64,hashlib,io,json,os,time,uuid,re
from pathlib import Path
from PIL import Image,UnidentifiedImageError
from flask import Blueprint,request,jsonify
ROOT=Path(__file__).resolve().parent
bp=Blueprint('tavern',__name__)

def decode_card(raw):
    if not raw.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('请上传原始 PNG 角色卡，不支持截图或 JPG。')
    with Image.open(io.BytesIO(raw)) as im:
        if im.width*im.height>24000000:raise ValueError('角色封面尺寸过大。')
        im.load()
        text=im.info.get('ccv3') or im.info.get('chara')
        if not isinstance(text,str):raise ValueError('图片没有角色卡数据，请使用酒馆导出的原始 PNG。')
        if len(text)>2000000:raise ValueError('角色卡设定过大。')
        try:card=json.loads(base64.b64decode(text,validate=True).decode('utf-8'))
        except Exception:raise ValueError('角色卡数据损坏，无法读取。')
        if not isinstance(card,dict):raise ValueError('角色卡格式不正确。')
        spec=card.get('spec')
        if spec and spec not in ('chara_card_v2','chara_card_v3'):raise ValueError('暂不支持该角色卡版本。')
        data=card.get('data') if spec else card
        if not isinstance(data,dict) or not isinstance(data.get('name'),str) or not data['name'].strip():raise ValueError('角色卡缺少角色名字。')
        for k in ('description','personality','scenario','first_mes','mes_example'):
            if k in data and not isinstance(data[k],str):raise ValueError('角色卡字段格式不正确：'+k)
        cover=im.convert('RGBA');cover.thumbnail((1600,2400));out=io.BytesIO();cover.save(out,'PNG')
    return card,data,out.getvalue()

def profile_from_card(data):
    # 只映射源文件已有字段，不生成新的角色经历。
    description=data.get('description') or ''
    personality=data.get('personality') or ''
    scenario=data.get('scenario') or ''
    greeting=data.get('first_mes') or ''
    def display_text(text):
        text=re.sub(r'\{\{(?:user|char)\}\}',lambda m:'你' if 'user' in m.group() else data.get('name','角色'),text)
        return text.strip()
    def field(labels):
        pattern=r'(?:^|[\n;；]|\s)(?:'+labels+r')\s*[:：]\s*([^\n;；]+)'
        m=re.search(pattern,description,re.I)
        return m.group(1).strip()[:48] if m else ''
    identity=field('身份|职业|occupation|role')
    age=field('年龄|age')
    gender=field('性别|gender')
    # 首屏展示已有结构信息；不把面向模型的指令当作人物简介。
    overview=(display_text(personality)[:100] if personality else '通过酒馆角色卡导入。完整人物设定、初始场景和对话内容可在下方档案查看。')
    attributes=[dict(label=k,value=v or '未填写') for k,v in [
      ('所属',field('所属|世界观|world')),('身份',identity),
      ('形态',field('种族|形态|species')),('年龄感',age),
      ('性格',display_text(personality)[:60]),('画风','保持原图画风')]]
    if gender: attributes.append(dict(label='性别',value=gender))
    voices=([dict(context='初次见面',line=display_text(greeting))] if greeting else [])
    voices += [dict(context='其他开场',line=x) for x in data.get('alternate_greetings',[]) if isinstance(x,str) and x]
    return dict(summary=overview,epithet=identity or '原创角色 · 酒馆导入',
      story=[],voice=voices,
      dossier=[dict(label='性格',value=personality)] if personality else [],
      attributes=attributes,
      files=[dict(title=k,body=display_text(v)) for k,v in [('角色描述',description),('性格设定',personality),('初始场景',scenario),('对话示例',data.get('mes_example') or ''),('作者说明',data.get('creator_notes') or '')] if v],signatures=[])

@bp.post('/api/tavern/import')
def import_card():
    f=request.files.get('file')
    if not f:return jsonify(error='请选择 PNG 角色卡。'),400
    try:raw=f.read();card,data,cover=decode_card(raw)
    except (ValueError,UnidentifiedImageError,OSError,Image.DecompressionBombError) as e:return jsonify(error=str(e),no_card=str(e).startswith('图片没有角色卡数据')),400
    digest=hashlib.sha256(raw).hexdigest()
    for p in (ROOT/'chars').glob('*.json'):
        try:c=json.loads(p.read_text())
        except (ValueError,OSError):continue
        if c.get('tavern_import_hash')==digest:return jsonify(id=c['id'],name=c['name'],duplicate=True)
    cid=uuid.uuid4().hex[:10];src='u/'+cid+'_tavern.png'
    rp={k:data.get(k,'') for k in ('description','personality','scenario','first_mes','mes_example')}
    c=dict(id=cid,name=data['name'].strip(),img=src,images=[src],type='其他',age='不详',gender='不详',role='导入角色',traits=[],bio=data.get('description','')[:140],lore=data.get('description',''),created=time.strftime('%Y-%m-%d %H:%M'),works=[],roleplay=rp,tavern_card=card,tavern_import_hash=digest,profile=profile_from_card(data))
    # 未识别字段和世界书原样保存；外部系统指令不覆盖本站提示词。
    (ROOT/'u').mkdir(exist_ok=True);(ROOT/'chars').mkdir(exist_ok=True)
    (ROOT/src).write_bytes(cover)
    p=ROOT/'chars'/(cid+'.json');tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(c,ensure_ascii=False,indent=1));os.replace(tmp,p)
    return jsonify(id=cid,name=c['name'],duplicate=False)
