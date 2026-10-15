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
URL=re.compile(r'(?:https?://|www\.)[^\s<>\[\]{}"\']+',re.I)
def clean(value):
    if not isinstance(value,str):return value
    value=html.unescape(value)
    value=re.sub(r'!\[[^\]]*\]\([^)]*\)','',value)
    value=re.sub(r'\[([^\]]*)\]\((?:https?://|www\.)[^)]*\)',r'\1',value)
    if re.search(r'</?(?:div|p|br|hr|img|a|h[1-6]|span|script|style|details|summary|iframe)\b',value,re.I):
        parser=Reader();parser.feed(value);value=''.join(parser.parts)
    lines=[]
    for line in value.splitlines():
        line=line.strip()
        if AD.search(line):
            # 同一行混有剧情与推广时按句拆除，不整行丢掉人物设定。
            if len(line)>160:
                parts=re.split(r'(?<=[。！？!?；;])',line)
                line=''.join(x for x in parts if not AD.search(x)).strip()
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
