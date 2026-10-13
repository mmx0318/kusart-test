# Ask Agent：成人向剧情 / 出图提示词钩子。
# 优先转发 ASK_AGENT_URL（可选 ASK_AGENT_BEARER）；否则用已有的 OpenRouter llm()；都没有就返回带 source=mock 的演示稿，本地预览仍能走通。
import json, re
import requests
from flask import Blueprint, request, jsonify

bp = Blueprint('ask_agent', __name__)
A = None
MINOR = re.compile(
    r'(未成年|萝莉|正太|幼女|幼男|小学生|初中生|高中生|\bJK\b|\bDK\b|loli|shota|underage|\bminor\b|\bchild\b|preteen|little girl|little boy)',
    re.I)
KEYS = ('story_beats', 'dialogue', 'image_prompt', 'negative_prompt', 'notes')

def init(app_mod):
    global A
    A = app_mod

def _clip(v, n):
    return str(v or '').strip()[:n]

def _context(d):
    character = d.get('character', d.get('character_summary', ''))
    if isinstance(character, (dict, list)):
        character = json.dumps(character, ensure_ascii=False)
    dialogue = d.get('dialogue', d.get('existing_dialogue', ''))
    dialogue_s = json.dumps(dialogue, ensure_ascii=False) if isinstance(dialogue, (dict, list)) else _clip(dialogue, 4000)
    ctx = dict(
        character=_clip(character, 4000),
        scene_goal=_clip(d.get('scene_goal', d.get('goal', '')), 2000),
        nsfw=bool(d.get('nsfw')),
        dialogue=dialogue if isinstance(dialogue, (dict, list)) else dialogue_s,
    )
    for k in ('story_id', 'node_id', 'type'):
        if d.get(k):
            ctx[k] = _clip(d.get(k), 80)
    age = d.get('age')
    try:
        if age is not None and str(age).strip() != '' and float(age) < 18:
            ctx['_minor'] = True
    except (TypeError, ValueError):
        pass
    return ctx

def _blob(ctx):
    dlg = ctx['dialogue']
    if not isinstance(dlg, str):
        dlg = json.dumps(dlg, ensure_ascii=False)
    return '\n'.join([ctx['character'], ctx['scene_goal'], dlg])

def _as_list(v):
    if v is None or v == '':
        return []
    if isinstance(v, str):
        return [v]
    if isinstance(v, list):
        return v
    return [v]

def _dialogue(v):
    rows = []
    for item in _as_list(v)[:24]:
        if isinstance(item, dict):
            rows.append(dict(speaker=_clip(item.get('speaker') or item.get('name') or '', 40),
                             line=_clip(item.get('line') or item.get('text') or item.get('zh') or '', 400)))
        else:
            rows.append(dict(speaker='', line=_clip(item, 400)))
    return rows

def _pick(data):
    if not isinstance(data, dict):
        return {'notes': _clip(data, 2000)}
    for k in ('result', 'data', 'output', 'response'):
        inner = data.get(k)
        if isinstance(inner, dict) and any(x in inner for x in KEYS):
            return inner
        if isinstance(inner, str) and '{' in inner:
            try:
                j = json.loads(inner[inner.find('{'):inner.rfind('}') + 1])
                if isinstance(j, dict):
                    return j
            except Exception:
                pass
    ch = (data.get('choices') or [None])[0]
    if isinstance(ch, dict):
        msg = (ch.get('message') or {}).get('content')
        if isinstance(msg, str) and '{' in msg:
            try:
                j = json.loads(msg[msg.find('{'):msg.rfind('}') + 1])
                if isinstance(j, dict):
                    return j
            except Exception:
                pass
    return data

def normalize(data, source):
    d = _pick(data)
    if not isinstance(d, dict):
        d = {'notes': _clip(d, 2000)}
    return dict(
        story_beats=[_clip(x, 300) for x in _as_list(d.get('story_beats'))[:8]],
        dialogue=_dialogue(d.get('dialogue')),
        image_prompt=_clip(d.get('image_prompt'), 2000),
        negative_prompt=_clip(d.get('negative_prompt'), 800),
        notes=_clip(d.get('notes'), 800),
        source=source,
    )

def mock_payload(ctx):
    who = (ctx['character'] or '成年角色').split('\n')[0][:40]
    goal = ctx['scene_goal'] or '把这一幕接着演下去'
    beats = [
        f'{who} 对准这一幕的目标：{goal}',
        '先给一个能被看见的动作，再留一个让对方接话的停顿。',
        '停在还没说完的一句上，下一段可以从这里接。',
    ]
    if ctx['nsfw']:
        beats.insert(2, '亲密戏只发生在已经成年、并且这一幕里彼此同意的角色之间。')
    prompt = 'masterpiece, best quality, solo, adult, 25 years old, mature, looking at viewer, cinematic lighting'
    if ctx['nsfw']:
        prompt += ', nsfw, explicit'
    else:
        prompt += ', fully clothed'
    return dict(
        story_beats=beats,
        dialogue=[
            dict(speaker=who[:12] or '角色', line='今晚按你说的来。你想从哪一句开始？'),
            dict(speaker='你', line=(goal[:80] or '靠近一点。')),
        ],
        image_prompt=prompt,
        negative_prompt='child, loli, shota, underage, teen, minor, low quality, blurry, watermark, text',
        notes='本地演示稿：没有设置 ASK_AGENT_URL，也没有 OPENROUTER_API_KEY。接上任意一个就会换成真实写作。',
        source='mock',
    )

def _system(nsfw):
    tone = ('这一幕可以写成人向亲密戏，直接、具体。' if nsfw else '这一幕不要露骨：衣着完整，不写性行为。')
    return ('你是成人向互动小说的写作助手。所有角色必须是成年人。只输出 JSON：'
            '{"story_beats":["3 到 6 条节拍，每条一句"],"dialogue":[{"speaker":"角色名或你","line":"台词"}],'
            '"image_prompt":"英文 Danbooru 风格提示词，必须含 adult","negative_prompt":"英文负面词，必须含 child, loli, shota, underage","notes":"给作者的一句中文备注"}。'
            'story_beats 和 dialogue 用简体中文。' + tone)

def from_llm(ctx):
    user = json.dumps({k: ctx[k] for k in ('character', 'scene_goal', 'nsfw', 'dialogue') if k in ctx}, ensure_ascii=False)
    return normalize(A.llm(_system(ctx['nsfw']), user, model=A.FAST), 'openrouter')

def forward(url, bearer, ctx):
    headers = {'Content-Type': 'application/json'}
    if bearer:
        headers['Authorization'] = 'Bearer ' + bearer
    body = {k: v for k, v in ctx.items() if not k.startswith('_')}
    try:
        r = requests.post(url, headers=headers, json=body, timeout=60)
    except Exception as e:
        return jsonify(error='Ask Agent 连不上：' + str(e)[:200]), 502
    try:
        data = r.json()
    except Exception:
        data = {'notes': (r.text or '')[:2000]}
    if r.status_code >= 400:
        msg = ''
        if isinstance(data, dict):
            msg = data.get('error') or data.get('message') or ''
        return jsonify(error=f'Ask Agent 返回 {r.status_code}：{msg or (r.text or "")[:200]}'), 502
    return jsonify(normalize(data, 'webhook'))

@bp.post('/api/ask-agent')
def ask_agent():
    d = request.get_json(silent=True) or {}
    if not isinstance(d, dict):
        return jsonify(error='需要 JSON 对象'), 400
    ctx = _context(d)
    if ctx.get('_minor') or MINOR.search(_blob(ctx)):
        return jsonify(error='只接受明确成年角色的场景。涉及未成年的描述不能生成。'), 400
    if not ctx['character'] and not ctx['scene_goal']:
        return jsonify(error='需要 character（角色摘要）或 scene_goal（这一幕要发生什么）'), 400
    url = A.envget('ASK_AGENT_URL').strip()
    bearer = (A.envget('ASK_AGENT_BEARER') or A.envget('ASK_AGENT_TOKEN')).strip()
    if url:
        return forward(url, bearer, ctx)
    if A.OR_KEY:
        try:
            return jsonify(from_llm(ctx))
        except Exception as e:
            return jsonify(error='文字模型失败：' + str(e)[:300]), 502
    return jsonify(mock_payload(ctx))
