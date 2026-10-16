# 导入文本只保留可读文字，不执行外部 HTML、脚本或加载广告图片。
import re,html
from html.parser import HTMLParser
class Reader(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.parts=[];self.hidden=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','iframe','object'):self.hidden+=1
        if tag in ('div','p','br','hr','h1','h2','h3','li','section','details','summary','tr'):self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style','iframe','object'):self.hidden=max(0,self.hidden-1)
        if tag in ('div','p','h1','h2','h3','li','section','details','summary','tr'):self.parts.append('\n')
    def handle_data(self,data):
        if not self.hidden:self.parts.append(data)
AD=re.compile(r'discord|(?:qm\.|qun\.)?qq\.com|t\.me/|telegram|QQ群|QQ号|群号|加群|进群|交流群|交流群|关注作者|关注公众号|扫码|二维码|付费解锁|购买完整版|赞助作者|爱发电|afdian|patreon|本角色卡分享于|角色卡发布于|先行破限组|水秋海洋馆|点击跳转|查看更新|下载地址|发布地址|作者主页',re.I)
# 作者说明和导入教程属于来源资料，不进入人物正文和聊天开场。
EDITORIAL=re.compile(r'作者\s*(?:id|ID|：|:|@)|这里作者|请勿倒卖|侵删|本模板由|本内容依据|CC\s*BY(?:-SA)?\s*4\.0|^友情提供[：:]|点击.{0,16}开始正文|点击查阅.{0,8}许可|(?:作者|创作者).{0,8}(?:声明|致谢)|角色卡.{0,8}(?:仅发布|仅在|首发)|盗传倒卖|非以上渠道|偷狗|玩到盗版|禁止.{0,8}(?:二传|倒卖)|无授权.{0,8}二传|仅在.{0,30}发布|卡面.{0,30}(?:老师|帮跑|无偿)|(?:开场白|开场).{0,15}(?:写了[一二三四五六七八九十0-9]|分别是)|需要.{0,12}(?:打开|开启|勾选).{0,8}(?:世界书|条目)|(?:手机聊天|看日记).{0,30}(?:世界书|聊天)|(?:玩bl|玩bg|玩BL|玩BG).{0,20}(?:二改|修改)|(?:使用教程|使用说明|导入教程|作者碎碎念|作者的话|创作者说明)',re.I)
URL=re.compile(r'(?:https?://|www\.)[^\s<>\[\]{}"\']+',re.I)
def clean(value):
    if not isinstance(value,str):return value
    value=html.unescape(value)
    value=re.sub(r'(?<![A-Za-z])main_(?![A-Za-z])','',value)

    # 部分开场只有仿社交平台状态栏和作者声明，没有实际剧情。
    def drop_social_block(match):
        block=match.group(0)
        if re.search(r'(?m)^\s*(?:[▶►♫≪≫]|0:00)\s*$',block) and len(re.findall(r'(?m)^\s*(?:[▶►♫≪≫]|0:00)\s*$',block))>=3:return ''
        if '角色状态栏' in block and re.search(r'正在播放|原声|分享',block) and EDITORIAL.search(block):return ''
        return block
    value=re.sub(r'```[\s\S]*?```',drop_social_block,value)
    # 剥除围栏标记，保留其中可读的剧情，不把语言名显示给用户。
    value=re.sub(r'(?m)^\s*```[^\n]*$', '',value)
    value=re.sub(r'<(?:audio|video|button)\b[^>]*>[\s\S]*?</(?:audio|video|button)\s*>','',value,flags=re.I)

    value=re.sub(r'!\[[^\]]*\]\([^)]*\)','',value)
    value=re.sub(r'\[([^\]]*)\]\((?:https?://|www\.)[^)]*\)',r'\1',value)
    if re.search(r'</?(?:div|p|br|hr|img|a|h[1-6]|span|script|style|details|summary|iframe)\b',value,re.I):
        parser=Reader();parser.feed(value);value=''.join(parser.parts)
    lines=[]
    for line in value.splitlines():
        line=line.strip()
        if AD.search(line) or EDITORIAL.search(line):
            # 同一行混有剧情与推广时按句拆除，不整行丢掉人物设定。
            if len(line)>160:
                parts=re.split(r'(?<=[。！？!?；;])',line)
                line=''.join(x for x in parts if not AD.search(x) and not EDITORIAL.search(x)).strip()
                if not line:continue
            else:continue
        line=URL.sub('',line).strip()
        if line in ('{{char}}','{{user}}','点击查看','点击链接','点击这里','链接','作者声明'):continue
        if line and not re.fullmatch(r'[-_=*\s]{3,}',line):lines.append(line)
        elif not line and lines and lines[-1]!='':lines.append('')
    return re.sub(r'\n{3,}','\n\n','\n'.join(lines)).strip()

def clean_tree(value):
    if isinstance(value,str):return clean(value)
    if isinstance(value,list):return [clean_tree(x) for x in value]
    if isinstance(value,dict):return {k:clean_tree(v) for k,v in value.items()}
    return value

def clean_data(data):
    data=dict(data)
    for key in ('description','personality','scenario','first_mes','mes_example','alternate_greetings','creator_notes'):
        if key in data:data[key]=clean_tree(data[key])
    return data

def spoken_line(value):
    """展示台词只取一个完整短句；长叙事没有明确引语时不冒充台词。"""
    text=clean(value or '')
    if not text:return ''
    # 优先内层引号，避免把包住整段剧情的外层书名式引号当台词。
    candidates=re.findall(r'[“"]([^“”"\n]{1,240})[”"]',text)
    candidates+=re.findall(r'「([^「」\n]{1,240})」',text)
    if not candidates:
        if len(text)>140 or '\n' in text or re.search(r'他说|她说|说道|问道|低声|站在|月光|眼睛|抬起|\*',text):return ''
        candidates=[text]
    for candidate in candidates:
        candidate=candidate.strip()
        sentence=re.split(r'(?<=[。！？!?])',candidate,maxsplit=1)[0].strip()
        if sentence and len(sentence)<=100:return sentence
    return ''
