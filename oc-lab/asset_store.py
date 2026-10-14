# 角色文件的原子更新，异步任务归档时保留其他任务刚写入的作品。
import json, os, tempfile, threading
from pathlib import Path
LOCK=threading.RLock()
ROOT=Path(__file__).resolve().parent

def write_json(path, value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.',suffix='.tmp')
    try:
        with os.fdopen(fd,'w') as f: json.dump(value,f,ensure_ascii=False,indent=2)
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def update_character(cid, change):
    path=ROOT/'chars'/(os.path.basename(cid)+'.json')
    with LOCK:
        c=json.loads(path.read_text()); change(c); write_json(path,c)
    return c
