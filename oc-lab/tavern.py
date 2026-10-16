# 酒馆 PNG 角色卡导入：解析元数据，不调用模型重写原设定。
import base64,hashlib,io,json,os,time,uuid,re
from pathlib import Path
from PIL import Image,UnidentifiedImageError
from card_text import clean_data
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
    data=clean_data(data)
    # 将源文件中英文字段拆入统一档案，不推测缺失的年龄与经历。
    aliases={
      '名字':['name','姓名','名字'], '年龄感':['age','年龄','年龄感'],
      '性别':['gender','sex','性别'], '身份':['occupation','identity','role','身份','职业'],
      '所属':['affiliation','world','所属','阵营','世界观'],
      '形态':['species','race','种族','形态','物种'],
      '性格':['personality','character traits','性格','性格特点'],
      '外貌':['appearance','外貌','外观','容貌'],
      '发型':['hair','发型','头发','发色'], '瞳色':['eyes','瞳色','眼睛'],
      '嘴唇':['lips','嘴唇'], '肤色':['skin','肤色','皮肤'],
      '面容':['face','面容','脸型'], '特征':['features','特征','特点'],
      '穿着':['clothing','outfit','服装','穿着'],
      '经历':['background','backstory','history','背景','身世','经历','背景故事'],
      '关系':['relationship','relationships','关系','人际关系'],
      '动机':['motivation','goal','动机','目标'],
      '喜好':['likes','喜好','喜欢'], '厌恶':['dislikes','厌恶','讨厌'],
      '说话方式':['speech style','speaking style','说话方式','语言风格'],
      '初始场景':['scenario','场景','初始场景'],
    }
    description=data.get('description') or ''
    def display(text):
        text=re.sub(r'\{\{(?:user|char)\}\}',lambda m:'你' if 'user' in m.group() else data.get('name','角色'),str(text))
        return text.strip()
    # Markdown、引号与中英文冒号只影响展示，不修改保存的原始文本。
    plain=re.sub(r'\*\*|__','',description)
    reverse={a.casefold():label for label,items in aliases.items() for a in items}
    names='|'.join(re.escape(a) for a in sorted(reverse,key=len,reverse=True))
    pattern=r'(?<![A-Za-z])(?:["\'【\[])?('+names+r')(?:["\'])?\s*(?:[:：]|[】\]])\s*'
    marks=list(re.finditer(pattern,plain,re.I));fields={}
    for i,m in enumerate(marks):
        value=plain[m.end():marks[i+1].start() if i+1<len(marks) else len(plain)]
        # 独立的未识别标题也截断当前字段，避免整段落进一个属性。
        value=re.split(r'\n\s*(?:#{1,4}\s*)?(?:[A-Za-z][A-Za-z _-]{1,30}|[\u4e00-\u9fff]{2,10})\s*[:：]\s*',value,maxsplit=1)[0]
        value=display(value).strip(' \n\r,，;；\"\'[]{}')
        if value:fields.setdefault(reverse[m.group(1).casefold()],value)
    for label,key in [('性格','personality'),('初始场景','scenario')]:
        if data.get(key):fields[label]=display(data[key])
    def short(value,limit=64):
        value=re.sub(r'\s+',' ',value).strip()
        return value if len(value)<=limit else value[:limit].rstrip('，,、;；')+'…'
    identity=fields.get('身份','');personality=re.sub(r'^(?:tags?|关键词|标签)\s*[:：]\s*','',fields.get('性格',''),flags=re.I)
    if personality:fields['性格']=personality
    appearance='\n'.join(k+'：'+fields[k] for k in ('外貌','发型','瞳色','嘴唇','肤色','面容','特征','穿着') if fields.get(k))
    overview=[]
    if identity:overview.append((data.get('name') or '')+'，'+short(identity,70)+'。')
    if personality:overview.append(short(personality,110))
    elif fields.get('特征'):overview.append(short(fields['特征'],110))
    elif fields.get('外貌'):overview.append(short(fields['外貌'],110))
    # 无字段的自然语言保留为人物简介；不把面向模型的指令挪到首屏。
    narrative=display(plain) if not marks else display(plain[:marks[0].start()])
    if not overview and narrative and not re.search(r'\{\{|system|instruction|不要|禁止|扮演|你是',narrative,re.I):overview.append(short(narrative,160))
    attributes=[dict(label=k,value=short(fields[k],65)) for k in ('所属','身份','形态','年龄感','性格','性别') if fields.get(k)]
    attributes.append(dict(label='画风',value='保持原图画风'))
    files=[]
    for title,body in [('外貌与辨识特征',appearance),('性格与习惯',personality),('人物经历',fields.get('经历','')),('人物关系',fields.get('关系','')),('愿望与动机',fields.get('动机','')),('喜好',fields.get('喜好','')),('不喜欢的事',fields.get('厌恶','')),('说话方式',fields.get('说话方式','')),('初始场景',fields.get('初始场景','')),('对话示例',data.get('mes_example','')),('作者补充',data.get('creator_notes',''))]:
        if body:files.append(dict(title=title,body=display(body)))
    # 无法可靠拆分的设定仍有完整入口，原始角色卡始终另行保留。
    if description:files.append(dict(title='完整人物设定',body=display(description)))
    greeting=data.get('first_mes') or ''
    voices=([dict(context='初次见面',line=__import__('card_text').spoken_line(display(greeting)))] if greeting else [])
    voices.extend(dict(context='其他开场',line=__import__('card_text').spoken_line(display(x))) for x in data.get('alternate_greetings',[]) if isinstance(x,str) and x)
    return dict(summary=''.join(overview),epithet=short(identity,48) if identity else '',
      world=fields.get('所属',''),story=[],voice=[v for v in voices if v['line']],
      dossier=[dict(label=k,value=fields[k]) for k in ('经历','关系','动机','喜好','厌恶','说话方式') if fields.get(k)],
      attributes=attributes,files=files,signatures=[])

def apply_card_identity(c, data, profile):
    # 年龄只从明确字段映射，不能用画风或「公子」等称谓猜成年。
    attrs={x['label']:x['value'] for x in profile.get('attributes',[])}
    if c.get('role') in ('导入角色','酒馆导入角色','',None):c['role']=attrs.get('身份','')
    if c.get('gender') in ('不详','',None):
        value=attrs.get('性别','').lower()
        if value in ('男','男性','male','man'):c['gender']='男'
        elif value in ('女','女性','female','woman'):c['gender']='女'
    if c.get('age') in ('不详','',None):
        age=attrs.get('年龄感','').strip()
        if re.fullmatch(r'\d{1,3}(?:岁| years old| years|yo)?',age,re.I):
            years=int(re.search(r'\d+',age).group());c['age']='成年' if years>=18 else '未成年'
        elif age in ('成年','成年人','adult'):c['age']='成年'
    if c.get('bio')==data.get('description','')[:140]:c['bio']=profile.get('summary','')

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
    data=clean_data(data)
    cid=uuid.uuid4().hex[:10];src='u/'+cid+'_tavern.png'
    rp={k:data.get(k,'') for k in ('description','personality','scenario','first_mes','mes_example')}
    c=dict(id=cid,name=data['name'].strip(),img=src,images=[src],type='其他',age='不详',gender='不详',role='导入角色',traits=[],bio=data.get('description','')[:140],lore=data.get('description',''),created=time.strftime('%Y-%m-%d %H:%M'),works=[],roleplay=rp,tavern_card=card,tavern_import_hash=digest,profile=profile_from_card(data))
    apply_card_identity(c,data,c['profile'])
    # 未识别字段和世界书原样保存；外部系统指令不覆盖本站提示词。
    (ROOT/'u').mkdir(exist_ok=True);(ROOT/'chars').mkdir(exist_ok=True)
    (ROOT/src).write_bytes(cover)
    p=ROOT/'chars'/(cid+'.json');tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(c,ensure_ascii=False,indent=1));os.replace(tmp,p)
    return jsonify(id=cid,name=c['name'],duplicate=False)
