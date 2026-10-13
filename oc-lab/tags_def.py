# 第 3 步灵感词：按第 1 步的角色类型分开（10-08 木木夕）
# 每条 = (中文标签, 出例图用的英文词)；例图由 mktags.py 用 Anima GinkgoWM 现跑，兽耳类优先复用 OC generator 的 tag 例图（本来就是猫耳角色）
OC='https://kusart.com/Oc-generator/oc-prompt-%20picture/'
OCC='https://kusart.com/Oc-generator/color-previews/hair-color/'

BASE={  # 每种类型的基础人设 + 各组默认值（换某一组时，其余组用默认）
 '甜妹':('1girl, solo, petite adult woman, short stature, cute face, fully clothed','brown hair','twintails','frilled dress'),
 '奶系':('1boy, solo, male focus, young adult man, slim, soft cute face, fully clothed','brown hair','short messy hair','t-shirt and shorts'),
 '假小子':('1girl, solo, tomboy, adult woman, boyish','black hair','short hair','oversized t-shirt and cargo shorts'),
 '男娘':('1boy, solo, otoko no ko, androgynous adult man, feminine face, flat chest','red hair','short messy hair','frilled black coat dress'),
 '赛博格':('1girl, solo, cyborg, adult woman, mechanical parts, robot joints, android','blue hair','short hair','white techwear jacket with high collar, cargo pants'),
 'Furry':('anthro, furry, solo, anthro fox, fox head, snout, fur body, fluffy tail','orange fur','','hoodie'),
 '少女':('1girl, solo, young adult woman, cute','brown hair','long straight hair','white blouse and pleated skirt'),
 '成女':('1girl, solo, adult woman, mature female, elegant','black hair','long wavy hair','white blouse'),
 '少男':('1boy, solo, young adult man, bishounen','black hair','short hair','white shirt'),
 '成男':('1boy, solo, adult man, mature male, older man, handsome, sharp jawline, 30s','black hair','short hair','white shirt'),
 '兽耳 / 兽人':('1girl, solo, kemonomimi, cat ears, cat tail','pink hair','long hair','light blue jacket and white dress'),
 '异种族':('1girl, solo, fantasy','silver hair','long hair','simple white robe'),
}
HAIRC=[('黑色头发','black hair'),('白色头发','white hair'),('金色头发','blonde hair'),('银色头发','silver hair'),('蓝色头发','blue hair'),('粉色头发','pink hair'),('红色头发','red hair'),('棕色头发','brown hair'),('紫色头发','purple hair'),('灰白头发','grey hair')]
H=dict(HAIRC)
def hc(*names): return [(n,H[n]) for n in names]

TAGS={
 '甜妹':[
  ('发色',hc('粉色头发','金色头发','白色头发','蓝色头发','黑色头发','棕色头发')),
  ('发型',[('双马尾','twintails'),('双丸子','double bun'),('齐刘海短发','bob cut, blunt bangs'),('侧马尾','side ponytail'),('长卷发','long curly hair'),('麻花辫','twin braids')]),
  ('穿着',[('洛丽塔裙','lolita fashion, frilled dress'),('背带裤','overalls'),('魔法少女服','magical girl outfit'),('黄色雨衣','single girl alone, yellow raincoat with hood, red rain boots, holding small umbrella'),('学院制服','school uniform, blazer'),('动物睡衣','animal hood pajamas')]),
  ('特征',[('大蝴蝶结','large hair bow'),('抱玩偶','holding stuffed bunny'),('星星发夹','star hair ornament'),('雀斑','freckles'),('圆眼镜','round glasses'),('虎牙','fang, smile')])],
 '奶系':[
  ('发色',hc('黑色头发','棕色头发','金色头发','白色头发','红色头发','蓝色头发')),
  ('发型',[('蘑菇头','bowl cut'),('呆毛短发','short hair, ahoge'),('刺猬头','spiked hair'),('小辫子','short ponytail'),('小卷毛','curly hair'),('寸头','buzz cut')]),
  ('穿着',[('背带短裤','suspenders, shorts, white shirt'),('水手服','sailor suit, boy'),('连帽卫衣','oversized hoodie'),('运动服','gym uniform'),('甚平','jinbei'),('小西装','suit, bow tie')]),
  ('特征',[('创可贴','bandaid on face'),('棒球帽','baseball cap'),('虎牙','fang, smile'),('双肩包','backpack'),('头戴耳机','headphones around neck'),('围巾','scarf')])],
 '假小子':[
  ('发色',hc('黑色头发','棕色头发','金色头发','银色头发','红色头发','蓝色头发')),
  ('发型',[('短发','short hair'),('狼尾','wolf cut'),('侧剃','undercut, short hair'),('低马尾','low ponytail'),('碎发','messy short hair'),('短卷发','short curly hair')]),
  ('穿着',[('宽松T恤','oversized graphic t-shirt, cargo shorts'),('连帽卫衣','oversized hoodie, jeans'),('运动服','track jacket, sweatpants'),('机车夹克','leather jacket, jeans'),('工装背带裤','overalls, t-shirt'),('篮球服','basketball uniform')]),
  ('特征',[('反戴棒球帽','backwards baseball cap'),('创可贴','bandaid on face'),('耳钉','stud earrings'),('虎牙','fang, smile'),('头戴耳机','headphones around neck'),('小麦肤色','tan skin')])],
 '男娘':[
  ('发色',hc('粉色头发','白色头发','黑色头发','金色头发','紫色头发','红色头发')),
  ('发型',[('双马尾','twintails'),('姬发式','hime cut'),('短发','bob cut'),('长直发','long straight hair'),('侧马尾','side ponytail'),('编发','braid')]),
  ('穿着',[('女仆装','maid outfit'),('水手服','serafuku, sailor uniform'),('哥特裙','gothic lolita dress'),('大码卫衣','oversized hoodie'),('和服','kimono'),('针织开衫','cardigan, pleated skirt')]),
  ('特征',[('大蝴蝶结','large hair bow'),('猫耳发箍','cat ear headband'),('颈圈','choker'),('泪痣','mole under eye'),('发夹','hairclip'),('围巾','scarf')])],
 '赛博格':[
  ('发色',hc('蓝色头发','白色头发','银色头发','粉色头发','黑色头发','红色头发')),
  ('发型',[('短发','short hair'),('双马尾','twintails'),('长直发','long straight hair'),('单马尾','ponytail'),('狼尾','wolf cut'),('姬发式','hime cut')]),
  ('机械部位',[('机械臂','mechanical arm, prosthetic arm'),('机械腿','mechanical legs, prosthetic legs'),('球形关节','doll joints, robot joints'),('机械耳','mechanical ears, headgear'),('面部线条','glowing lines on face, circuit tattoo'),('外露骨架','exposed mechanical frame, transparent skin panels')]),
  ('穿着',[('战术外套','tactical jacket, high collar, cargo pants'),('机能风外套','techwear jacket, straps'),('护士服','nurse uniform'),('女仆装','maid outfit'),('风衣','long coat'),('连帽卫衣','oversized hoodie')])],
 'Furry':[
  ('物种',[('狐','anthro fox, fox head, fox snout'),('狼','anthro wolf, wolf head, wolf snout, grey fur'),('猫','anthro cat, cat head, whiskers'),('兔','anthro rabbit, rabbit head, long rabbit ears'),('熊','anthro bear, bear head, round ears, brown fur'),('龙','anthro dragon, dragon head, scales, horns, reptile')]),
  ('毛色',[('橙色毛','orange fur'),('白色毛','white fur'),('灰色毛','grey fur'),('黑色毛','black fur'),('棕色毛','brown fur'),('蓝色毛','blue fur')]),
  ('穿着',[('连帽卫衣','hoodie'),('夹克','denim jacket'),('西装','business suit, necktie'),('和服','kimono'),('冒险者装','adventurer outfit, leather armor'),('围裙','apron, chef')]),
  ('特征',[('围巾','scarf'),('眼镜','glasses'),('头戴耳机','headphones'),('铃铛项圈','collar with bell'),('异色瞳','heterochromia'),('斜挎包','satchel')])],
 '少女':[
  ('发色',hc('粉色头发','黑色头发','白色头发','蓝色头发','金色头发','银色头发')),
  ('发型',[('双马尾','twintails'),('长直发','long straight hair'),('短发','bob cut'),('丸子头','hair bun'),('单马尾','ponytail'),('姬发式','hime cut')]),
  ('穿着',[('水手服','serafuku, sailor uniform'),('连帽卫衣','oversized hoodie'),('和服','kimono'),('荷叶边裙','frilled dress'),('女仆装','maid outfit'),('运动服','track jacket, sportswear')]),
  ('特征',[('红眼睛','red eyes'),('眼镜','glasses'),('小花发饰','hair flower'),('呆毛','ahoge'),('雀斑','freckles'),('发带','hair ribbon')])],
 '成女':[
  ('发色',hc('黑色头发','红色头发','银色头发','金色头发','棕色头发','紫色头发')),
  ('发型',[('大波浪','long wavy hair'),('长直发','long straight hair'),('低马尾','low ponytail'),('盘发','updo, hair bun'),('短发','short bob hair'),('侧编发','side braid')]),
  ('穿着',[('西装套裙','office lady, business suit, pencil skirt'),('旗袍','cheongsam, china dress, high collar'),('长风衣','trench coat'),('毛衣长裙','turtleneck sweater, long skirt'),('和服','kimono'),('晚礼服','elegant long evening gown, long sleeves')]),
  ('特征',[('泪痣','mole under eye'),('眼镜','glasses'),('耳环','earrings'),('红唇','red lips'),('发簪','hair stick, kanzashi'),('长睫毛','long eyelashes')])],
 '少男':[
  ('发色',hc('黑色头发','白色头发','金色头发','棕色头发','蓝色头发','红色头发')),
  ('发型',[('碎短发','messy short hair'),('刺猬头','spiked hair'),('狼尾','wolf cut, mullet'),('中分','center part hair'),('小辫子','short ponytail'),('长刘海','long bangs, hair over one eye')]),
  ('穿着',[('立领制服','gakuran, school uniform'),('连帽卫衣','hoodie'),('西装制服','school blazer, necktie'),('运动服','track jacket, sportswear'),('和服','kimono, hakama'),('夹克','denim jacket')]),
  ('特征',[('耳钉','stud earrings'),('创可贴','bandaid on face'),('眼镜','glasses'),('虎牙','fang, smile'),('头戴耳机','headphones around neck'),('围巾','scarf')])],
 '成男':[
  ('发色',hc('黑色头发','灰白头发','棕色头发','金色头发','银色头发','红色头发')),
  ('发型',[('背头','slicked back hair'),('短寸','buzz cut'),('中分','center part hair'),('低马尾','long hair, low ponytail'),('凌乱短发','messy short hair'),('武士髻','topknot, samurai hair')]),
  ('穿着',[('西装','black business suit, necktie'),('长风衣','long trench coat'),('军装','military uniform'),('皮夹克','leather jacket'),('和服','kimono, haori'),('白大褂','lab coat, doctor')]),
  ('特征',[('胡茬','stubble, beard stubble, five o\'clock shadow'),('伤疤','scar across eye'),('眼镜','glasses'),('眼罩','eyepatch'),('领带','necktie'),('络腮胡','full beard')])],
 '兽耳 / 兽人':[
  ('耳朵尾巴',[('猫耳','cat ears, cat tail'),('狐耳','fox ears, fox tail'),('狼耳','wolf ears, wolf tail'),('兔耳','rabbit ears, rabbit tail'),('犬耳','dog ears, dog tail'),('熊耳','bear ears, round ears')]),
  ('发色',hc('粉色头发','黑色头发','白色头发','蓝色头发','金色头发','银色头发')),
  ('穿着',[('连帽卫衣','oversized hoodie'),('水手服','serafuku, sailor uniform'),('和服','kimono'),('荷叶边裙','frilled dress'),('巫女服','miko, hakama'),('女仆装','maid outfit')]),
  ('特征',[('铃铛项圈','choker with bell'),('肉球手套','paw gloves'),('虎牙','fang, smile'),('异色瞳','heterochromia'),('蝴蝶结','hair bow'),('小花发饰','hair flower')])],
 '异种族':[
  ('种族',[('精灵','elf, pointy ears'),('恶魔','demon girl, demon horns, demon tail'),('天使','angel, glowing halo above head, large white feathered wings spread'),('机械人','android, robot girl, mechanical parts, robot joints, mechanical ears'),('龙人','dragon girl, dragon horns, dragon tail, scales'),('吸血鬼','vampire, red eyes, fangs')]),
  ('发色',hc('银色头发','黑色头发','白色头发','红色头发','蓝色头发','紫色头发')),
  ('穿着',[('法师长袍','mage robe, hood'),('盔甲','silver armor, knight'),('哥特裙','gothic lolita dress'),('赛博战衣','cyberpunk bodysuit jacket, techwear'),('神官服','priestess robe, white and gold'),('斗篷','dark cloak')]),
  ('特征',[('尖耳','pointy ears'),('角','large curved horns'),('翅膀','large feathered wings spread behind'),('机械臂','mechanical arm, prosthetic arm'),('光环','glowing halo above head'),('发光纹路','glowing tattoo, glowing runes')])],
}
# 兽耳类直接复用 OC generator 例图（猫耳粉发角色，和类型一致）
OCREUSE={('兽耳 / 兽人','发色','粉色头发'):OCC+'pink.png',('兽耳 / 兽人','发色','黑色头发'):OCC+'black.png',('兽耳 / 兽人','发色','白色头发'):OCC+'white.png',
 ('兽耳 / 兽人','发色','蓝色头发'):OCC+'blue.png',('兽耳 / 兽人','发色','金色头发'):OCC+'blonde.png',('兽耳 / 兽人','发色','银色头发'):OCC+'silver.png'}
GROUP_SLOT={'发色':1,'毛色':1,'发型':2,'穿着':3}   # 换这一组时替换 BASE 里对应的默认值
def prompt(typ,group,word):
  b=list(BASE[typ]); slot=GROUP_SLOT.get(group)
  if slot: b[slot]=('wearing '+word+', outfit clearly visible') if group=='穿着' else word
  else: b.append(word)
  if typ in ('兽耳 / 兽人',) and group=='耳朵尾巴': b[0]='1girl, solo, kemonomimi'
  if typ=='Furry' and group=='物种': b[0]='anthro, furry, solo, animal head, fur body, fluffy tail'
  frame='cowboy shot' if group=='穿着' or (typ=='异种族' and group in ('种族','特征')) else 'upper body'
  return ', '.join(x for x in b if x)+f', {frame}, looking at viewer, simple background, white background, fully clothed'
# 10-08 扩成 8 类：旧类型改名后例图沿用旧 key（不重跑）
IMGKEY={'御姐':'成女','少年':'少男','熟男':'成男','异种':'异种族'}
for _n,_o in IMGKEY.items(): TAGS[_n]=TAGS[_o]; BASE[_n]=BASE[_o]
def type_style(t):   # 10-09 木木夕：灵感词例图用该类型卡片的默认推荐画风（type_cards.json 的 anima_id / xl_id）
  import json,os
  c=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'type_cards.json'))).get(t) or {}
  return TAG_STYLE_OVERRIDE.get(t) or c.get('anima_id') or c.get('xl_id') or ''
# 卡片画风不适合做小例图的类型（10-09 实测：异种卡 Sharp Dusk Mood 糊成一团看不清标签差别）→ 换该类推荐里清晰的画风
# 10-09 木木夕：萝莉/正太改名甜妹/奶系，提示词全部改成年（petite adult / young adult man），例图重跑
TAG_STYLE_OVERRIDE={'假小子':'anima_1785572045772359975','男娘':'anima_1785572045772359975','赛博格':'anima_1785572045772359975','异种':'S14','奶系':'anima_1785572045772331975','御姐':'S211'}   # 正太卡画风小图总出双胞胎、御姐卡画风总出深V，换该类精选里排前的
def imgkey(t,g,l,style=None):
  import hashlib,os
  st=type_style(t) if style is None else style
  k=hashlib.md5(f'{t}|{g}|{l}|{st}'.encode()).hexdigest()[:12]
  if style is None and not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)),'tags',k+'.webp')):   # 新例图没跑完前沿用旧图
    return hashlib.md5(f'{IMGKEY.get(t,t)}|{g}|{l}'.encode()).hexdigest()[:12]
  return k
NEG_EXTRA={'赛博格':', nude, nsfw, cleavage, large breasts, bodysuit, twins, multiple girls','假小子':', 1boy, male, large breasts, cleavage, twins, siblings, multiple girls, multiple views','男娘':', 1girl, female, breasts, cleavage, twins, multiple boys','Furry':', human, human face, kemonomimi, 1girl','奶系':', 1girl, female, hair ornament, hair ribbon, twintails, ponytail, twins, siblings, multiple boys, 3boys, group, crowd','御姐':', cleavage, large breasts, huge breasts, twins, multiple girls, group','异种':', cleavage, large breasts, multiple girls'}
# 10-09 木木夕：瞳色组补上（所有类型共用，排在发色/毛色后面）。例图直接用通用 tag 库（Base TJ3ZbxOg）里的白素体眼睛图，不再跑图
EYE_F=[('蓝瞳','blue eyes'),('红瞳','red eyes'),('紫瞳','purple eyes'),('绿瞳','green eyes'),('棕瞳','brown eyes'),('金瞳','yellow eyes')]
EYE_M=[('蓝瞳','blue eyes'),('红瞳','red eyes'),('金瞳','yellow eyes'),('绿瞳','green eyes'),('紫瞳','purple eyes'),('棕瞳','brown eyes')]
SHARED_IMG={('瞳色',l):'tags_v2/eye/%s.webp'%f for l,f in [('蓝瞳','blue'),('红瞳','red'),('紫瞳','purple'),('绿瞳','green'),('棕瞳','brown'),('金瞳','yellow'),('黑瞳','black'),('粉瞳','pink')]}
for _t in list(TAGS):
  _g=[x for x in TAGS[_t] if x[0]!='瞳色']
  _i=next((i+1 for i,x in enumerate(_g) if x[0] in ('发色','毛色')),0)
  TAGS[_t]=_g[:_i]+[('瞳色',EYE_M if _t in ('少年','熟男','少男','成男','奶系') else EYE_F)]+_g[_i:]
# 少女特征里的「红眼睛」和瞳色组重复 → 换成虎牙
TAGS['少女']=[(g,[(('虎牙','fang, smile') if l=='红眼睛' else (l,w)) for l,w in it]) for g,it in TAGS['少女']]
# 10-09 木木夕：少女 tag 例图换成 GPT 2.5 套图版（卡片画风原图 + 画风锁定，3×3 裁切），每组 8 个，按 tag 库 v2；默认发色金发
TAGS['少女']=[
 ('发色',[('金发','blonde hair'),('棕发','brown hair'),('黑发','black hair'),('蓝发','blue hair'),('粉发','pink hair'),('银白发','silver white hair'),('紫发','purple hair'),('红发','red hair')]),
 ('瞳色',[('蓝瞳','blue eyes'),('红瞳','red eyes'),('紫瞳','purple eyes'),('绿瞳','green eyes'),('棕瞳','brown eyes'),('金瞳','yellow eyes'),('粉瞳','pink eyes'),('异色瞳','heterochromia')]),
 ('发型',[('长直发','long straight hair'),('短发','short hair'),('双马尾','twintails'),('编发','side braid'),('单马尾','ponytail'),('中长发','medium hair'),('公主切','hime cut'),('丸子头','hair bun')]),
 ('穿着',[('连衣裙','white dress'),('水手服','sailor school uniform'),('和服','kimono'),('毛衣','knit sweater and skirt'),('女仆装','maid outfit'),('中华服','qipao'),('卫衣','hoodie'),('魔法少女装','magical girl outfit')]),
 ('特征',[('呆毛','ahoge'),('蝴蝶结','hair bow'),('颈圈','choker'),('发卡','hairclip'),('虎牙','fang'),('发花','hair flower'),('猫耳','cat ear headband'),('眼镜','glasses')])]
TYPE_IMG={('少女',g,l):f'tags_v3/少女/{g}_{l}.webp' for g,it in TAGS['少女'] for l,_ in it}
# 10-09 木木夕：中间方案——tag 例图按性别共用。男性套 = 少年 D2 底图（Blue Veil Paint）+ GPT 2.5 套图，少年/熟男按 tag 库 v2 各挑 8 个
_HC_M=[('黑发','black hair'),('金发','blonde hair'),('棕发','brown hair'),('银白发','silver white hair'),('蓝发','blue hair'),('红发','red hair'),('紫发','purple hair'),('绿发','green hair')]
_EYE_M8=[('蓝瞳','blue eyes'),('红瞳','red eyes'),('金瞳','yellow eyes'),('绿瞳','green eyes'),('紫瞳','purple eyes'),('棕瞳','brown eyes'),('黑瞳','black eyes'),('异色瞳','heterochromia')]
TAGS['少年']=[('发色',_HC_M),('瞳色',_EYE_M8),
 ('发型',[('短发','short hair'),('长发','long hair'),('小辫子','short ponytail'),('刺猬头','spiked hair'),('中分','center part'),('单边遮眼','hair over one eye'),('编发','braid'),('碎发','messy hair')]),
 ('穿着',[('夹克','jacket'),('大衣','overcoat'),('和服','kimono'),('马甲','vest'),('学生制服','gakuran'),('西装','suit'),('高领毛衣','turtleneck'),('连帽卫衣','hoodie')]),
 ('特征',[('耳环','earrings'),('兽耳','animal ears'),('伤疤','scar'),('项链','necklace'),('眼镜','glasses'),('呆毛','ahoge'),('尖耳','pointy ears'),('围巾','scarf')])]
TAGS['熟男']=[('发色',_HC_M),('瞳色',_EYE_M8),
 ('发型',[('短发','short hair'),('长发','long hair'),('刺猬头','spiked hair'),('中长发','medium hair'),('小辫子','short ponytail'),('极短发','buzz cut'),('背头','slicked back hair'),('中分','center part')]),
 ('穿着',[('衬衫','dress shirt'),('夹克','jacket'),('领带','necktie'),('和服','kimono'),('大衣','overcoat'),('铠甲','armor'),('西装','suit'),('马甲','vest')]),
 ('特征',[('络腮胡','full beard'),('胡茬','stubble'),('伤疤','scar'),('小胡子','mustache'),('眼镜','glasses'),('纹身','tattoo'),('耳环','earrings'),('项链','necklace')])]
for _t in ('少年','熟男'):
  for g,it in TAGS[_t]:
    for l,_ in it: TYPE_IMG[(_t,g,l)]=f'tags_v3/男/{g}_{l}.webp'
# 10-09 木木夕：各类型元素 tag 配图按性别换成 GPT 2.5 套图版（女性套=tags_v3/少女，男性套=tags_v3/男）。
# 女性套里有的 tag 换新图（同义的旧标签直接改名），没有的先保留旧图，等女性补图套图跑完再换。
import os
_F='tags_v3/少女/{}_{}.webp'
_EN={'金发':'blonde hair','棕发':'brown hair','黑发':'black hair','蓝发':'blue hair','粉发':'pink hair','银白发':'silver white hair','紫发':'purple hair','红发':'red hair',
 '蓝瞳':'blue eyes','红瞳':'red eyes','紫瞳':'purple eyes','绿瞳':'green eyes','棕瞳':'brown eyes','金瞳':'yellow eyes','粉瞳':'pink eyes','异色瞳':'heterochromia',
 '长直发':'long straight hair','短发':'short hair','双马尾':'twintails','编发':'side braid','单马尾':'ponytail','中长发':'medium hair','公主切':'hime cut','丸子头':'hair bun','波波头':'bob cut',
 '连衣裙':'white dress','水手服':'sailor school uniform','和服':'kimono','毛衣':'knit sweater and skirt','女仆装':'maid outfit','中华服':'qipao','卫衣':'hoodie','魔法少女装':'magical girl outfit',
 '呆毛':'ahoge','蝴蝶结':'hair bow','颈圈':'choker','发卡':'hairclip','虎牙':'fang','发花':'hair flower','猫耳':'cat ear headband','眼镜':'glasses','耳饰':'earrings'}
# 显示标签 → 女性套图文件里的标签（同义）
_FIMG={'耳环':'耳饰','发饰':'发花','旗袍':'中华服'}
_FHC=[(l,_EN[l]) for l in ['金发','棕发','黑发','蓝发','粉发','银白发','紫发','红发']]
_FEYE=[(l,_EN[l]) for l in ['蓝瞳','红瞳','紫瞳','绿瞳','棕瞳','金瞳','粉瞳','异色瞳']]
def _old(t,g,labels):
  d=dict(next((it for gg,it in TAGS[t] if gg==g),[])); return [(l,d[l]) for l in labels if l in d]
def _new(*labels): return [(l,_EN.get(_FIMG.get(l,l),'')) for l in labels]
_PLAN={
 '御姐':{'发型':_new('长直发','短发','单马尾','编发','中长发')+_old('御姐','发型',['大波浪','盘发','低马尾']),
        '穿着':_new('连衣裙','毛衣','和服','旗袍')+_old('御姐','穿着',['西装套裙','长风衣','晚礼服']),
        '特征':_new('眼镜','耳环','颈圈','发饰')+_old('御姐','特征',['泪痣','红唇','发簪','长睫毛'])},
 '假小子':{'发型':_new('短发','单马尾','中长发')+_old('假小子','发型',['狼尾','侧剃','碎发','低马尾','短卷发']),
        '穿着':_new('卫衣')+_old('假小子','穿着',['宽松T恤','运动服','机车夹克','工装背带裤','篮球服']),
        '特征':_new('虎牙')+_old('假小子','特征',['反戴棒球帽','创可贴','耳钉','头戴耳机','小麦肤色'])},
 '男娘':{'发型':_new('双马尾','公主切','短发','长直发','编发','单马尾','波波头')+_old('男娘','发型',['侧马尾']),
        '穿着':_new('女仆装','水手服','和服','卫衣','连衣裙','魔法少女装')+_old('男娘','穿着',['哥特裙','针织开衫']),
        '特征':_new('蝴蝶结','猫耳','颈圈','发卡','发饰','耳环')+_old('男娘','特征',['泪痣','围巾'])},
 '赛博格':{'发型':_new('短发','双马尾','长直发','单马尾','公主切','波波头','中长发')+_old('赛博格','发型',['狼尾']),
        '穿着':_new('女仆装','卫衣')+_old('赛博格','穿着',['战术外套','机能风外套','护士服','风衣'])},
 '异种':{},
}
for _t,_gs in _PLAN.items():
  _gs=dict(_gs,**{'发色':_FHC,'瞳色':_FEYE})
  TAGS[_t]=[(g,_gs.get(g,it)) for g,it in TAGS[_t]]
  for g,it in TAGS[_t]:
    for l,_ in it:
      f=_F.format(g,_FIMG.get(l,l))
      if g in ('发色','瞳色') or l in _EN or l in _FIMG:
        if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)),f)): TYPE_IMG[(_t,g,l)]=f
# 10-09 木木夕：tag 全部按「创建角色 Tag 库 v1」文档（Nvc0dkcM）对齐 —— 每组 6 个、按热度排、第一个默认；
# 男娘过膝袜留、赛博格紧身作战服留。配图：女性套 / 男性套有的直接用（同义映射），其次复用该类型旧图，都没有的空着等补图。
_DOC_HC_F=[('黑发','black hair'),('金发','blonde hair'),('棕发','brown hair'),('蓝发','blue hair'),('粉发','pink hair'),('银白发','silver white hair')]
_DOC_HC_M=[('黑发','black hair'),('金发','blonde hair'),('棕发','brown hair'),('银白发','silver white hair'),('蓝发','blue hair'),('红发','red hair')]
_DOC_EYE_F=[('红瞳','red eyes'),('紫瞳','purple eyes'),('绿瞳','green eyes'),('金瞳','yellow eyes'),('蓝瞳','blue eyes'),('异色瞳','heterochromia')]
_DOC_EYE_M=[('蓝瞳','blue eyes'),('红瞳','red eyes'),('金瞳','yellow eyes'),('绿瞳','green eyes'),('紫瞳','purple eyes'),('异色瞳','heterochromia')]
_OLD_TAGS={k:list(v) for k,v in TAGS.items()}
TAGS.update({
 '少女':[('发色',_DOC_HC_F),('瞳色',_DOC_EYE_F),
  ('发型',[('短发','short hair'),('长直发','long straight hair'),('双马尾','twintails'),('编发','side braid'),('单马尾','ponytail'),('丸子头','hair bun')]),
  ('穿着',[('连衣裙','white dress'),('水手服','sailor school uniform'),('和服','kimono'),('女仆装','maid outfit'),('卫衣','hoodie'),('魔法少女装','magical girl outfit')]),
  ('特征',[('呆毛','ahoge'),('蝴蝶结','hair bow'),('虎牙','fang'),('发花','hair flower'),('猫耳','cat ear headband'),('眼镜','glasses')])],
 '御姐':[('发色',_DOC_HC_F),('瞳色',_DOC_EYE_F),
  ('发型',[('长发','long hair'),('短发','short hair'),('单马尾','ponytail'),('编发','side braid'),('单边遮眼','hair over one eye'),('盘发','updo, hair bun')]),
  ('穿着',[('连衣裙','dress'),('毛衣','knit sweater'),('高领毛衣','turtleneck sweater'),('和服','kimono'),('衬衫领带','dress shirt, necktie'),('大衣','long overcoat')]),
  ('特征',[('耳环','earrings'),('眼镜','glasses'),('项链','necklace'),('红唇','red lips'),('泪痣','mole under eye'),('颈圈','choker')])],
 '假小子':[('发色',_DOC_HC_F),('瞳色',_DOC_EYE_F),
  ('发型',[('短发','short hair'),('单马尾','ponytail'),('极短发','very short hair'),('碎发','messy short hair'),('单边遮眼','hair over one eye'),('低马尾','low ponytail')]),
  ('穿着',[('夹克','jacket'),('T恤短裤','t-shirt, shorts'),('连帽卫衣','hoodie'),('背心','tank top'),('牛仔','denim jacket, jeans'),('运动外套','track jacket')]),
  ('特征',[('小麦肤色','tan skin'),('棒球帽','baseball cap'),('虎牙','fang'),('耳洞','ear piercing'),('创可贴','bandaid on face'),('伤疤','scar')])],
 '少年':[('发色',_DOC_HC_M),('瞳色',_DOC_EYE_M),
  ('发型',[('短发','short hair'),('小辫子','short ponytail'),('刺猬头','spiked hair'),('中分','center part'),('单边遮眼','hair over one eye'),('碎发','messy hair')]),
  ('穿着',[('夹克','jacket'),('和服','kimono'),('学生制服','school uniform, blazer'),('高领毛衣','turtleneck'),('连帽卫衣','hoodie'),('学兰','gakuran')]),
  ('特征',[('耳环','earrings'),('伤疤','scar'),('眼镜','glasses'),('呆毛','ahoge'),('围巾','scarf'),('虎牙','fang')])],
 '熟男':[('发色',_DOC_HC_M),('瞳色',_DOC_EYE_M),
  ('发型',[('短发','short hair'),('长发','long hair'),('小辫子','short ponytail'),('极短发','buzz cut'),('背头','slicked back hair'),('中分','center part')]),
  ('穿着',[('夹克','jacket'),('衬衫领带','dress shirt, necktie'),('和服','kimono'),('大衣','overcoat'),('西装','suit'),('马甲','vest')]),
  ('特征',[('络腮胡','full beard'),('胡茬','stubble'),('伤疤','scar'),('小胡子','mustache'),('眼镜','glasses'),('纹身','tattoo')])],
 '男娘':[('发色',_DOC_HC_F),('瞳色',_DOC_EYE_F),
  ('发型',[('长发','long hair'),('短发','short hair'),('编发','side braid'),('双马尾','twintails'),('单马尾','ponytail'),('单边遮眼','hair over one eye')]),
  ('穿着',[('短裙','miniskirt'),('连衣裙','dress'),('校服','school uniform'),('女仆装','maid outfit'),('卫衣','hoodie'),('毛衣','knit sweater')]),
  ('特征',[('过膝袜','thighhighs'),('蝴蝶结','hair bow'),('发带','hairband'),('颈圈','choker'),('猫耳','cat ear headband'),('发卡','hairclip')])],
 '赛博格':[('发色',_DOC_HC_F),('瞳色',[(l,w) for l,w in _DOC_EYE_F if l!='异色瞳']+[('发光眼','glowing eyes')]),
  ('发型',[('短发','short hair'),('长直发','long straight hair'),('双马尾','twintails'),('编发','side braid'),('单马尾','ponytail'),('丸子头','hair bun')]),
  ('机械部位',[('机械臂','mechanical arms'),('单只机械臂','single mechanical arm'),('机械腿','mechanical legs'),('义肢','prosthesis'),('关节球','doll joints'),('头戴装置','headgear')]),
  ('穿着',[('夹克','jacket'),('紧身作战服','tactical bodysuit under jacket'),('大衣','long coat'),('军装','military uniform'),('连帽外套','hooded jacket'),('白大褂','lab coat')])],
 '异种':[('种族',[('恶魔','demon girl, demon horns, demon tail'),('精灵','elf, pointy ears'),('龙娘','dragon girl, dragon horns, dragon tail, scales'),('鬼','oni, oni horns'),('吸血鬼','vampire, red eyes, fangs'),('史莱姆','slime girl')]),
  ('发色',_DOC_HC_F),('瞳色',_DOC_EYE_F),
  ('非人部件',[('尾巴','tail'),('角','horns'),('翅膀','wings'),('尖耳','pointy ears'),('光环','halo'),('异色皮肤','colored skin')]),
  ('穿着',[('和服','kimono'),('铠甲','armor'),('女巫帽','witch hat'),('斗篷','cloak'),('修女服','nun habit'),('哥特洛丽塔','gothic lolita dress')])],
 'Furry':[('物种',[('狐','anthro fox, fox head, fox snout'),('龙','anthro dragon, dragon head, scales, horns, reptile'),('犬','anthro dog, dog head, dog snout'),('狼','anthro wolf, wolf head, wolf snout, grey fur'),('猫','anthro cat, cat head, whiskers'),('兔','anthro rabbit, rabbit head, long rabbit ears')]),
  ('毛色',[('白色毛','white fur'),('棕色毛','brown fur'),('黑色毛','black fur'),('蓝色毛','blue fur'),('灰色毛','grey fur'),('橙色毛','orange fur')]),
  ('瞳色',_DOC_EYE_F),
  ('穿着',[('衬衫','shirt'),('夹克','jacket'),('卫衣','hoodie'),('毛衣','sweater'),('西装','business suit, necktie'),('大衣','overcoat')]),
  ('特征',[('眼镜','glasses'),('耳洞','ear piercing'),('项圈','collar'),('帽子','hat'),('项链','necklace'),('围巾','scarf')])],
})
_HERE=os.path.dirname(os.path.abspath(__file__))
_MALE={'少年','熟男'}
# 文档标签 → 套图文件里的同义标签
_SYN_F={'长发':'长直发','耳环':'耳饰','耳洞':'耳饰','连帽卫衣':'卫衣','校服':'水手服'}
_SYN_M={'学兰':'学生制服','衬衫领带':'领带'}
# 文档标签 → 该类型旧标签（复用 tags_v2 旧图）
_OLDSYN={('异种','龙娘'):('种族','龙人'),('异种','铠甲'):('穿着','盔甲'),('异种','哥特洛丽塔'):('穿着','哥特裙'),
 ('异种','角'):('特征','角'),('异种','翅膀'):('特征','翅膀'),('异种','尖耳'):('特征','尖耳'),('异种','光环'):('特征','光环'),
 ('Furry','卫衣'):('穿着','连帽卫衣'),('Furry','项圈'):('特征','铃铛项圈'),
 ('赛博格','机械臂'):('机械部位','机械臂'),('赛博格','机械腿'):('机械部位','机械腿'),('赛博格','关节球'):('机械部位','球形关节')}
def _oldimg(t,g,l):
  for k in (imgkey(t,g,l,type_style(t)),imgkey(t,g,l)):
    if os.path.exists(os.path.join(_HERE,'tags_v2',k+'.webp')): return 'tags_v2/'+k+'.webp'
TYPE_IMG={}
for _t in ('少女','御姐','假小子','少年','熟男','男娘','赛博格','异种','Furry'):
  for g,it in TAGS[_t]:
    for l,_ in it:
      f=None
      if _t!='Furry' or g=='瞳色':
        if _t in _MALE: f=f'tags_v3/男/{g}_{_SYN_M.get(l,l)}.webp'
        else: f=f'tags_v3/少女/{g}_{_SYN_F.get(l,l)}.webp'
        if _t=='Furry' and g=='瞳色': f=SHARED_IMG.get((g,l))
        if f and not os.path.exists(os.path.join(_HERE,f)): f=None
      if not f:
        og,ol=_OLDSYN.get((_t,l),(g,l)); f=_oldimg(_t,og,ol)
      if f: TYPE_IMG[(_t,g,l)]=f
# 10-09 木木夕：tag 配图按分类各跑一套（tags_v3/<类型>/），有就优先用本类型自己的图
for _t in TAGS:
  if not os.path.isdir(os.path.join(_HERE,'tags_v3',_t)) or _t in ('少女','男'): continue
  for g,it in TAGS[_t]:
    for l,_ in it:
      f=f'tags_v3/{_t}/{g}_{l}.webp'
      if os.path.exists(os.path.join(_HERE,f)): TYPE_IMG[(_t,g,l)]=f
# 10-09 木木夕：异色瞳要两只眼睛不同色，单眼特写表达不了 → 换成黑瞳
for _t in TAGS:
  TAGS[_t]=[(g,[(('黑瞳','black eyes') if (g=='瞳色' and l=='异色瞳') else (l,w)) for l,w in it]) for g,it in TAGS[_t]]
  if not any(g=='瞳色' and any(l=='黑瞳' for l,_ in it) for g,it in TAGS[_t]): continue
  for f in (f'tags_v3/{_t}/瞳色_黑瞳.webp','tags_v3/男/瞳色_黑瞳.webp' if _t in _MALE else 'tags_v3/少女/瞳色_黑瞳.webp'):
    if os.path.exists(os.path.join(_HERE,f)): TYPE_IMG[(_t,'瞳色','黑瞳')]=f; break

# 10-09 木木夕：每组 6 → 5（特征也单选，预设库 5⁵×4 画风×7 类型 = 8.75 万张）。砍掉和同组撞车 / 小图看不出来的
_CUT={
 '*':{'发色':['蓝发'],'瞳色':['绿瞳'],'毛色':['蓝色毛']},
 '少女':{'发型':['编发'],'穿着':['卫衣'],'特征':['发花']},
 '御姐':{'发型':['编发'],'穿着':['毛衣'],'特征':['项链']},
 '假小子':{'发型':['碎发'],'穿着':['牛仔'],'特征':['耳洞']},
 '少年':{'发型':['小辫子'],'穿着':['学兰'],'特征':['耳环']},
 '熟男':{'发型':['极短发'],'穿着':['衬衫领带'],'特征':['小胡子']},
 '男娘':{'发型':['编发'],'穿着':['毛衣'],'特征':['发卡']},
 'Furry':{'物种':['犬'],'穿着':['衬衫'],'特征':['耳洞']},
}
for _t in ['少女','御姐','假小子','少年','熟男','男娘','Furry']:
  _c={**_CUT['*'],**_CUT[_t]}
  TAGS[_t]=[(g,[(l,w) for l,w in it if l not in _c.get(g,[])]) for g,it in TAGS[_t]]
