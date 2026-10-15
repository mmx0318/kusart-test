# 互动角色卡独立保存，用户原始设定优先于自动补充。
# 清水卡沿用谨慎语气；成人向（分级 nsfw / 成人图集）保留尖锐性格并维持或加强色气。
import json

_BASE_KEYS=('name','age','gender','type','role','traits','bio','lore','line')
_RP_KEYS=('personality','motivation','boundaries','speech_style','behavior_rules','description','scenario','initial_relationship','first_mes','mes_example')
_TAVERN_KEYS=('description','personality','scenario','first_mes','mes_example')
_LIMIT=2500

_SYSTEM_SAFE=(
  '你是原创角色互动设定编辑。只输出中文 JSON：'
  '{"personality":"具体性格与矛盾","motivation":"愿望和动机","boundaries":"性格底线",'
  '"speech_style":"措辞、句长、幽默与情绪表达方式","behavior_rules":["4~6条具体行为习惯"],'
  '"scenario":"初次相遇的场景","initial_relationship":"初始关系",'
  '"first_mes":"仅角色口头台词，1~3句",'
  '"mes_example":[{"user":"用户台词或动作","reply":"角色口头台词","action":"可选第三人称短动作或空"}]}。'
  '生成4~6组不同情境的对话示例，覆盖沉默、夸奖、质疑、分歧等，体现角色差异。'
  '用户给定姓名、年龄、身份、性格、bio、lore不可改写或冲突。只补未明确的内容，不更改外观。'
  '角色台词自然简短，不描述自己行动，不每轮反问、不复读口头禅、不突然亲密。动作第三人称，最多一句；可以没有动作。'
  '示例只示范语气，不新增重大经历或人物关系。')

_SYSTEM_NSFW=(
  '你是原创角色互动设定编辑。这份角色资料是成人向（rating=nsfw，或成人图集/露骨人设）。只输出中文 JSON：'
  '{"personality":"具体性格与矛盾，保留源性格里尖锐、阴暗或淫靡的一面","motivation":"愿望和动机","boundaries":"性格底线",'
  '"speech_style":"措辞、句长、幽默与情绪表达方式","behavior_rules":["4~6条具体行为习惯"],'
  '"scenario":"延续源设定的场景，写入已有关系与色气","initial_relationship":"延续源设定的关系，不要改成陌生人",'
  '"first_mes":"仅角色口头台词，1~3句，带入关系温度与性张力",'
  '"mes_example":[{"user":"用户台词或动作","reply":"角色口头台词","action":"可选第三人称短动作或空"}]}。'
  '硬性要求：'
  '1. 性格、动机、说话方式、关系动力学必须贴合源设定，把原有性格写得更具体、更尖锐。禁止洗成无害甜宠、软萌路人或治愈系好人。'
  '2. 源设定里的性张力、色气、支配或臣服、肉体细节和露骨偏好，要在 scenario、initial_relationship、first_mes、mes_example 里保留并加强，写成成人之间清楚的感官与情欲。不要改成纯暧昧、纯治愈或客套寒暄，不要拒绝，不要说教，不要把露骨内容弱化。'
  '3. 源设定若已有确立关系（包养、地下情人、夫妻、夫君、强制爱、病娇占有、主仆等），scenario 与 initial_relationship 必须延续该关系。禁止改写成初次偶遇陌生人，除非源设定自己写的就是初次相遇。'
  '4. 对话示例写 4~6 组。其中至少 2 组是亲密或性互动：身体接触、露骨调情、前戏或性行为中的语气，reply 要像这个角色在那种场合会说的话。不能只用沉默、夸奖、质疑、分歧、吃醋、收钱这类情绪对白凑数。其余几组可以覆盖这些日常情境。不要换成与该角色无关的通用色情腔。'
  '5. first_mes 只用角色口头台词 1~3 句，带入源卡的关系温度和性张力。若已有 first_mes 是授权声明、倒卖警告或模板套话而不是角色开口，忽略那段，改从 description、scenario 和人设写开场。'
  '6. 姓名、年龄、身份以及与源设定冲突的外观不要改。源材料已经写明的身体与性征细节要保留，不要当成多余外观删掉。'
  '7. existing_roleplay 与 tavern_snippets 里的露骨段落优先提炼保留，不要删掉 NSFW 只留人格标签。同一件事若有一段更软、一段更尖锐或更露骨，采用更尖锐、更露骨的那一段；酒馆原文优先于已经被写软的旧稿。'
  '输出的 mes_example 必须是上述 JSON 数组，不要原样粘贴酒馆的 {{char}} 长文本。'
  '角色台词自然简短，不在 reply 里描述自己行动，不每轮反问、不复读口头禅。动作放在 action，第三人称，最多一句；可以没有动作。')

def _taxonomy(c):
  try: from character_taxonomy import read as read_classification
  except ImportError: return {}
  if not c.get('id'): return {}
  try: tax=read_classification(c) or {}
  except Exception: return {}
  return tax if isinstance(tax, dict) else {}

def _rating_is_nsfw(value):
  return str(value or '').strip().lower()=='nsfw'

def is_nsfw(c):
  """成人向：分级 nsfw、成人图集，或角色上已有的同类 rating。blocked/pending/safe 仍走清水提示。"""
  if not isinstance(c, dict): return False
  if c.get('adult_album_type'): return True
  if _rating_is_nsfw(c.get('rating')): return True
  embedded=c.get('classification')
  if isinstance(embedded, dict) and _rating_is_nsfw(embedded.get('rating')): return True
  return _rating_is_nsfw(_taxonomy(c).get('rating'))

def _clip(v, limit=_LIMIT):
  if isinstance(v, str):
    text=v.strip()
    if not text: return None
    if len(text)<=limit: return text
    head=limit//2; tail=limit-head-1
    return text[:head]+'…'+text[-tail:]
  if isinstance(v, list):
    if not v: return None
    if len(json.dumps(v, ensure_ascii=False))<=limit: return v
    kept=[v[0]]+( [v[-1]] if len(v)>1 else [])
    for item in v[1:-1]:
      trial=kept[:-1]+[item]+kept[-1:]
      if len(json.dumps(trial, ensure_ascii=False))>limit: break
      kept=trial
    return kept
  if isinstance(v, dict):
    if not v: return None
    raw=json.dumps(v, ensure_ascii=False)
    return v if len(raw)<=limit else _clip(raw, limit)
  if v in (None,''): return None
  return v

def tavern_data(c):
  raw=c.get('tavern_card') or {}
  if not isinstance(raw, dict): return {}
  data=raw.get('data') if raw.get('spec') else raw
  return data if isinstance(data, dict) else {}

def _picked(src, keys):
  out={}
  if not isinstance(src, dict): return out
  for k in keys:
    clipped=_clip(src.get(k))
    if clipped is not None: out[k]=clipped
  return out

def user_payload(c, nsfw):
  payload={k:c.get(k) for k in _BASE_KEYS}
  if not nsfw: return payload
  tax=_taxonomy(c)
  payload['rating']='nsfw'
  if c.get('adult_album_type'): payload['adult_album_type']=c.get('adult_album_type')
  themes=tax.get('themes') if isinstance(tax.get('themes'), list) else []
  if not themes and isinstance(c.get('classification'), dict):
    embedded=c['classification'].get('themes')
    themes=embedded if isinstance(embedded, list) else []
  if themes: payload['themes']=themes
  existing=_picked(c.get('roleplay'), _RP_KEYS)
  snippets=_picked(tavern_data(c), _TAVERN_KEYS)
  if existing: payload['existing_roleplay']=existing
  if snippets: payload['tavern_snippets']=snippets
  return payload

def generate(c, llm):
  nsfw=is_nsfw(c)
  return llm(_SYSTEM_NSFW if nsfw else _SYSTEM_SAFE, json.dumps(user_payload(c, nsfw), ensure_ascii=False))

def fallback(c):
  p=c.get('profile') or {}
  return dict(personality=c.get('traits'),speech_style=c.get('line'),scenario=c.get('lore') or c.get('bio'),mes_example=[dict(user=v.get('context',''),reply=v.get('line',''),action='') for v in p.get('voice',[])],initial_relationship='初次相遇')
