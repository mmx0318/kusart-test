# 互动角色卡独立保存，用户原始设定优先于自动补充。
import json

def generate(c,llm):
    return llm('你是原创角色互动设定编辑。只输出中文 JSON：'
      '{"personality":"具体性格与矛盾","motivation":"愿望和动机","boundaries":"性格底线",'
      '"speech_style":"措辞、句长、幽默与情绪表达方式","behavior_rules":["4~6条具体行为习惯"],'
      '"scenario":"初次相遇的场景","initial_relationship":"初始关系",'
      '"first_mes":"仅角色口头台词，1~3句",'
      '"mes_example":[{"user":"用户台词或动作","reply":"角色口头台词","action":"可选第三人称短动作或空"}]}。'
      '生成4~6组不同情境的对话示例，覆盖沉默、夸奖、质疑、分歧等，体现角色差异。'
      '用户给定姓名、年龄、身份、性格、bio、lore不可改写或冲突。只补未明确的内容，不更改外观。'
      '角色台词自然简短，不描述自己行动，不每轮反问、不复读口头禅、不突然亲密。动作第三人称，最多一句；可以没有动作。'
      '示例只示范语气，不新增重大经历或人物关系。',json.dumps({k:c.get(k) for k in ('name','age','gender','type','role','traits','bio','lore','line')},ensure_ascii=False))

def fallback(c):
    p=c.get('profile') or {}
    return dict(personality=c.get('traits'),speech_style=c.get('line'),scenario=c.get('lore') or c.get('bio'),mes_example=[dict(user=v.get('context',''),reply=v.get('line',''),action='') for v in p.get('voice',[])],initial_relationship='初次相遇')
