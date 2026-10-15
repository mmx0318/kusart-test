# 成人剧情快照与「动起来」：性内容、羞辱、恋物可以生成；未成年 / 幼态仍拒绝。
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def load(path, names):
    text = (ROOT / path).read_text()
    tree = ast.parse(text)
    chunks = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if any(name in names for name in targets):
                chunks.append(ast.get_source_segment(text, node))
        elif isinstance(node, ast.FunctionDef) and node.name in names:
            chunks.append(ast.get_source_segment(text, node))
    ns = {'__builtins__': __builtins__}
    exec('import re\n' + '\n\n'.join(chunks), ns)
    return ns

motion = load('snapshot_motion.py', {'MINOR_MARK', 'MOTION_REVIEW', 'motion_block_reason', 'sexual_block_can_retry'})
snap = load('snapshots.py', {'snapshot_brief', 'snapshot_image_prompt', 'snapshot_block_reason'})

def test_adult_nsfw_motion_is_not_refused():
    scenes = [
        '她按着你的后脑，把精液射进嘴里。',
        '公开场合的性化羞辱：跪好，把项圈戴上。',
        '恋物：皮手套和高跟鞋抵在你身上。',
    ]
    for scene in scenes:
        reason = motion['motion_block_reason'](scene, {'allowed': False, 'minor': False, 'motion': scene})
        assert reason is None, scene
        # 旧审核用 allowed!=true 拒绝。成人内容即使没带 minor 字段也不能再走这条拒绝。
        assert motion['motion_block_reason'](scene, {'allowed': False}) is None

def test_minor_and_childlike_motion_still_blocked():
    assert motion['motion_block_reason']('日常散步', {'minor': True})
    for word in ('未成年', '幼态', '萝莉', '正太', 'loli', 'shota'):
        assert motion['motion_block_reason'](f'画面里是{word}', {'minor': False})
    # 「少女」在本站是成年类型，不能被这条硬拒绝误伤。
    assert motion['motion_block_reason']('少女漫风格的成年角色', {'minor': False}) is None

def test_motion_prompt_allows_adult_sex_and_keeps_minor_rule():
    text = motion['MOTION_REVIEW']
    for phrase in ('性行为', '裸露', '性化羞辱', '恋物', '必须放行', '未成年', '幼态'):
        assert phrase in text
    assert '均不允许' not in text
    assert '请选择日常、风景或其他非性化剧情' not in (ROOT / 'snapshot_motion.py').read_text()

def test_nsfw_snapshot_brief_keeps_explicit_scene():
    brief = snap['snapshot_brief'](True)
    for phrase in ('性行为', '裸露', '性化羞辱', '恋物', '不要改成非性化'):
        assert phrase in brief
    assert '不生成露骨性内容' not in brief
    safe = snap['snapshot_brief'](False)
    assert '不生成露骨性内容' in safe
    assert '幼态' in safe

def test_nsfw_image_prompt_follows_nudity():
    visual = '成年人之间的露骨画面'
    nsfw = snap['snapshot_image_prompt'](visual, True)
    assert '裸露程度跟随这段成人剧情' in nsfw
    assert '服饰与参考图一致' not in nsfw
    assert visual in nsfw
    assert '服饰与参考图一致' in snap['snapshot_image_prompt'](visual, False)

def test_snapshot_block_only_for_minors():
    adult = {'minor': False, 'visual': '性化羞辱与恋物'}
    assert snap['snapshot_block_reason'](True, adult) is None
    assert snap['snapshot_block_reason'](True, {'allowed': False, 'visual': '口交'}) is None
    assert snap['snapshot_block_reason'](True, {'minor': True, 'visual': ''})

def test_old_sexual_block_can_be_confirmed_again():
    old = {'status': 'blocked', 'error': '此片段不适合生成视频，请选择日常、风景或其他非性化剧情。'}
    assert motion['sexual_block_can_retry'](old)
    assert not motion['sexual_block_can_retry']({'status': 'blocked', 'error': '此片段涉及未成年或幼态，不能生成动画。'})
    assert not motion['sexual_block_can_retry'](dict(old, task_id='already-paid'))

def test_taxonomy_does_not_block_adult_humiliation():
    text = (ROOT / 'character_taxonomy.py').read_text()
    assert '性化羞辱、恋物' in text
    assert '明确非自愿性行为标blocked' not in text
    assert '幼态、儿童体貌的性内容标blocked' in text

if __name__ == '__main__':
    failed = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith('test_'): continue
        try: fn()
        except Exception as e:
            failed += 1
            print('FAIL', name, e)
        else: print('PASS', name)
    raise SystemExit(failed)
