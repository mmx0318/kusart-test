# 酒馆 PNG 角色卡导入：解析元数据，不调用模型重写原设定。
import base64,hashlib,io,json,os,time,uuid
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
    c=dict(id=cid,name=data['name'].strip(),img=src,images=[src],type='其他',age='不详',gender='不详',role='导入角色',traits=[],bio=data.get('description','')[:140],lore=data.get('description',''),created=time.strftime('%Y-%m-%d %H:%M'),works=[],roleplay=rp,tavern_card=card,tavern_import_hash=digest,profile=dict(summary=data.get('description',''),voice=[],story=[],dossier=[],attributes=[],files=[],signatures=[]))
    # 未识别字段和世界书原样保存；外部系统指令不覆盖本站提示词。
    (ROOT/'u').mkdir(exist_ok=True);(ROOT/'chars').mkdir(exist_ok=True)
    (ROOT/src).write_bytes(cover)
    p=ROOT/'chars'/(cid+'.json');tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(c,ensure_ascii=False,indent=1));os.replace(tmp,p)
    return jsonify(id=cid,name=c['name'],duplicate=False)
