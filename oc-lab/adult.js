// 10-10 成人模式（测试版）：顶栏开关 + 18+ 确认 → 暗酒红主题 → 8 类类型卡（悬停/滚动播视频）→ 剧情列表 → 互动剧情播放器
// 后端 adult.py：/adult/stories、/adult/story/<id>、/adult/media/<path>、/adult/cards/<name>。开关记在 localStorage ol_adult=1。
// 搬家时：manifest 格式不变（char/scenario/start/nodes{video,poster,lines[t,ja,zh],prompt,keyframe,choices[label,sub,to,aff],end}），界面按官网组件重写。
(()=>{
const E=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const U=p=>!p?'':/^(https?:|\/|blob:|data:)/.test(p)?p:p.replace(/^\.\//,'');   // manifest 里的路径相对 /oc-lab/
const LS=(k,v)=>{try{if(v===undefined)return localStorage.getItem(k);if(v===null)localStorage.removeItem(k);else localStorage.setItem(k,v)}catch(e){}};
const MOCK=/[?&]mock=1/.test(location.search)||LS('ol_adult_mock')==='1';   // 开发用测试数据
const HOVER=matchMedia('(hover:hover) and (pointer:fine)').matches;
const TYPES=[['御姐','yujie','成熟 · 掌控感'],['甜心','tianxin','甜美 · 黏人'],['辣妹','lamei','张扬 · 小麦肤色'],['熟女','shunv','温柔 · 包容'],
  ['型男','xingnan','冷峻 · 肌肉线条'],['熟男','shunan','沉稳 · 大叔'],['魅魔','meimo','魅惑 · 恶魔'],['兽人','shouren','野性 · 毛茸茸']];
const PLACE=['温泉偶遇','酒店房间','情人节礼物','周末早晨'];
const st=()=>document.getElementById('st');
let STORIES=null,curType=null,io=null;

const AD=window.AD={on:LS('ol_adult')==='1',home,openType,play};
function apply(){document.body.classList.toggle('adult',AD.on);const t=document.getElementById('adT');if(t)t.checked=AD.on;
 const m=document.querySelector('meta[name=theme-color]');if(m)m.content=AD.on?'#12070B':'#F8F7F7'}
apply();
document.addEventListener('DOMContentLoaded',()=>{const oc=new URLSearchParams(location.search).get('adult_oc');   // 10-10 普通角色主页「成人模式」按钮跳过来
 const vw=new URLSearchParams(location.search).get('vid');
 const albumType=new URLSearchParams(location.search).get('adult_type');
 if(albumType&&TYPES.some(t=>t[0]===albumType))setTimeout(()=>openType(albumType),0);
 if(oc)setTimeout(()=>{const go=async()=>{await ocGen(oc);if(vw)try{const w=((await (await fetch('adult/gen/list?cid='+encodeURIComponent(oc),{cache:'no-store'})).json()).works||[]).find(x=>x.id===vw);if(w)vidSheet(w)}catch(e){}};AD.on?go():gate(go)},0);
 const t=document.getElementById('adT');if(!t)return;apply();
 t.onchange=()=>{if(t.checked){t.checked=false;gate()}else{AD.on=false;LS('ol_adult',null);closePlayer();apply();go(0)}}});

/* ---------- 18+ 确认层 ---------- */
function gate(cb){const o=document.createElement('div');o.className='ad-gate';
 o.innerHTML=`<div class="ad-gbox" role="dialog" aria-modal="true"><h3>进入成人模式</h3><p>我已年满 18 岁，并了解这里是成人向虚构内容</p><small>所有角色均为成年人。可以随时在顶栏关闭。</small>
  <div class="ad-gbtn"><button class="ad-b2" data-k="0">取消</button><button class="ad-b1" data-k="1">确认</button></div></div>`;
 document.body.appendChild(o);requestAnimationFrame(()=>o.classList.add('on'));
 o.onclick=e=>{const k=e.target.dataset&&e.target.dataset.k;if(k===undefined&&e.target!==o)return;o.classList.remove('on');setTimeout(()=>o.remove(),200);
  if(k==='1'){AD.on=true;LS('ol_adult','1');apply();cb?cb():go(0)}}}

/* ---------- 数据 ---------- */
async function loadStories(){if(STORIES)return STORIES;
 try{const r=await fetch('adult/stories'+(MOCK?'?mock=1':''),{cache:'no-store'});STORIES=(await r.json()).stories||[]}catch(e){STORIES=[]}
 return STORIES}
const byType=t=>(STORIES||[]).filter(s=>s.type===t).sort((a,b)=>(b.ready-a.ready)||(a.id==='mock')-(b.id==='mock'));

/* ---------- 第 0 步：8 张类型卡 ---------- */
function mount(html,step){const s=st();s.dataset.step=step;s.classList.remove('hascta');s.innerHTML=`<div class="fade ad-page">${html}</div>`;window.scrollTo(0,0);return s}
async function home(){if(io){io.disconnect();io=null}
 const s=mount(`<div class="ad-hd"><span></span></div><h1 class="ad-h1">今晚，想和<span>谁</span>在一起</h1><div class="ad-sub">成人向虚构内容 · 所有角色均为成年人</div>
 <div class="ad-types">${TYPES.map(([t,k,sub])=>`<div class="ad-tc" data-t="${t}"><div class="ad-tp"><img src="adult/cards/${k}.jpg" alt="${t}" loading="lazy"${HOVER?'':` data-anim="adult/cards/${k}_m.webp"`}>${HOVER?`<video muted loop playsinline preload="none" poster="adult/cards/${k}.jpg" data-src="adult/cards/${k}.mp4"></video>`:''}</div>
  <div class="ad-tl"><b>${t}</b><small><span class="d">${sub}</span></small></div></div>`).join('')}</div>`,'ad0');
 const cards=[...s.querySelectorAll('.ad-tc')];
 cards.forEach(c=>{c.onclick=()=>openType(c.dataset.t);
  if(HOVER){c.onmouseenter=()=>vplay(c);c.onmouseleave=()=>vstop(c)}});
 if(!HOVER)animAll(cards);   // 10-10 木木夕：手机端全部默认动；夸克/UC 会把 <video> 接管成播放器（挡住点击），所以手机不用 video，改动态 webp
 await loadStories();   // 没有可玩剧情的类型，小字提示「剧情制作中」
 cards.forEach(c=>{if(!byType(c.dataset.t).length)c.querySelector('small').insertAdjacentHTML('beforeend','<span class="s">剧情制作中</span>')})}
function vplay(c){const v=c.querySelector('video');if(!v)return;if(!v.src)v.src=v.dataset.src;c.classList.add('playing');v.play().catch(()=>{})}
function vstop(c){const v=c.querySelector('video');if(!v)return;c.classList.remove('playing');v.pause();try{v.currentTime=0}catch(e){}}
// 10-10 手机：夸克/UC 会把可见的 <video> 接管成自带播放器（盖住选项、吃掉点击）。手机上把 video 缩成 2px 只负责出声，画面逐帧画到 canvas 上
function mirror(o){o.classList.add('cvm');const fr=o.querySelector('.ad-fr'),cv=document.createElement('canvas');cv.className='ad-cv';fr.querySelector('video.off').after(cv);const x=cv.getContext('2d');
 const loop=()=>{if(!o.isConnected)return;requestAnimationFrame(loop);const dpr=Math.min(devicePixelRatio||1,2),W=Math.round(fr.clientWidth*dpr),H=Math.round(fr.clientHeight*dpr);
  if(cv.width!==W||cv.height!==H){cv.width=W;cv.height=H}
  const v=P&&P.o===o?P.v:null;if(!v||!v.currentSrc||v.readyState<2||!v.videoWidth){if(v&&!v.currentSrc)x.clearRect(0,0,W,H);return}
  const s=Math.max(W/v.videoWidth,H/v.videoHeight),w=v.videoWidth*s,h=v.videoHeight*s;x.drawImage(v,(W-w)/2,(H-h)/2,w,h)};loop()}
function animAll(cards){io=new IntersectionObserver(es=>es.forEach(e=>{if(!e.isIntersecting)return;const im=e.target.querySelector('img[data-anim]');io.unobserve(e.target);if(!im)return;
  const pre=new Image();pre.onload=()=>{im.src=pre.src};pre.src=im.dataset.anim}),{rootMargin:'300px 0px'});cards.forEach(c=>io.observe(c))}
// 手机：滚到视口中间的那张自动播，同时只播一张
function watch(cards){const vis=new Set();let raf=0,cur=null;
 const pick=()=>{raf=0;let best=null,bd=1e9;const mid=innerHeight/2;
  vis.forEach(c=>{const r=c.getBoundingClientRect();const d=Math.abs(r.top+r.height/2-mid)*10+r.left;if(d<bd){bd=d;best=c}});
  if(best===cur)return;if(cur)vstop(cur);cur=best;if(cur)vplay(cur)};
 const sched=()=>{if(!raf)raf=requestAnimationFrame(pick)};
 io=new IntersectionObserver(es=>{es.forEach(e=>e.isIntersecting?vis.add(e.target):vis.delete(e.target));sched()},{rootMargin:'-35% 0px -35% 0px'});
 cards.forEach(c=>io.observe(c));
 const onS=()=>{if(!document.body.contains(cards[0])){removeEventListener('scroll',onS);return}sched()};addEventListener('scroll',onS,{passive:true})}

/* ---------- 选剧情页 ---------- */
let ALBUM=null;
async function loadAlbum(){if(ALBUM)return ALBUM;try{ALBUM=await (await fetch('adult/cards/album.json',{cache:'no-store'})).json()}catch(e){ALBUM={}}return ALBUM}
// 选剧情页顶部：角色资料 + 状态配图（横滑相册，点开灯箱看大图 + 场景标签 + 创作配方）
function profHTML(a,t){if(!a||!(a.imgs||[]).length)return '';
 return `<div class="ad-prof"><div class="ad-pfh"><b>${E(a.name_zh||a.name)}</b><span>${E(a.name||'')} · ${E(t)}</span></div><p>${E(a.intro||'')}</p>
 <div class="ad-alb">${a.imgs.map((x,i)=>`<figure data-i="${i}"><img src="${E(x.thumb||x.src)}" alt="" loading="lazy"><figcaption>${E(x.label||'')}</figcaption></figure>`).join('')}
 <figure class="ad-albcus" id="adGenBtn"><div class="ad-cusimg"><span>＋</span></div><figcaption>自定义 · 选姿势出一张</figcaption></figure></div></div>`}
function albumBox(a,i){const o=document.createElement('div');o.className='ad-lb';document.body.appendChild(o);document.body.style.overflow='hidden';
 const row=(k,v)=>v?`<div class="rr"><b>${k}</b><span>${v}</span></div>`:'';
 const draw=()=>{const x=a.imgs[i],r=x.recipe||{};
  o.innerHTML=`<button class="ad-ic ad-lbx" data-k="x" aria-label="关闭">✕</button><div class="ad-lbw"><div class="ad-lbi"><img src="${E(x.src)}" alt="">
   ${a.imgs.length>1?`<button class="ad-ic ad-lbp" data-k="p" aria-label="上一张">‹</button><button class="ad-ic ad-lbn" data-k="n" aria-label="下一张">›</button>`:''}</div>
   <div class="ad-lbt"><b>${E(x.label||'')}</b><small>${i+1} / ${a.imgs.length} · ${E(a.name_zh||a.name)}</small></div>
   <details class="pl-rc ad-lrc"><summary>创作配方</summary>${row('模型',E(r.model))}${row('画风',E(r.style_name))}${row('尺寸',E(r.size))}${row('来源',E(r.source))}
    ${r.prompt?`<details open><summary>提示词</summary><pre>${E(r.prompt)}</pre></details>`:''}${r.negative_prompt?`<details><summary>负面提示词</summary><pre>${E(r.negative_prompt)}</pre></details>`:''}
    <button class="pl-btn g" data-k="c">复制完整配方</button></details>${x.id&&/adult\/gen\/img/.test(x.src||'')?`<button class="pl-btn ad-mkv" data-k="v">▶ 做成视频</button>`:''}</div>`};
 const close=()=>{o.remove();document.body.style.overflow='';removeEventListener('keydown',key,true)};
 const key=e=>{if(e.key==='Escape')close();else if(e.key==='ArrowLeft'){i=(i+a.imgs.length-1)%a.imgs.length;draw()}else if(e.key==='ArrowRight'){i=(i+1)%a.imgs.length;draw()}};
 addEventListener('keydown',key,true);
 o.onclick=e=>{const k=e.target.dataset&&e.target.dataset.k;
  if(k==='x'||e.target===o||e.target.classList.contains('ad-lbw'))close();
  else if(k==='p'){i=(i+a.imgs.length-1)%a.imgs.length;draw()}else if(k==='n'){i=(i+1)%a.imgs.length;draw()}
  else if(k==='v'){vidSheet(a.imgs[i])}
  else if(k==='c'){const b=e.target;navigator.clipboard.writeText(JSON.stringify(Object.assign({type:a.type,character:a.name,label:a.imgs[i].label,src:a.imgs[i].src},a.imgs[i].recipe),null,1)).then(()=>{b.textContent='已复制 ✓';setTimeout(()=>b.textContent='复制完整配方',1500)})}};
 draw()}
async function openType(t){curType=t;if(io){io.disconnect();io=null}await Promise.all([loadStories(),loadAlbum()]);const alb=ALBUM[t];
 const k=(TYPES.find(x=>x[0]===t)||[])[1];const real=byType(t);
 const ph=((alb&&alb.plots)||PLACE.map(x=>({t:x,d:''}))).filter(x=>!real.some(s=>s.title===x.t)).slice(0,Math.max(3,4-real.length));   // 10-10 木木夕：每个角色的剧情按人设区分（album.json 的 plots）
 mount(`<div class="ad-hd"><button class="back" id="adBack">‹ 返回选角色</button></div>${profHTML(alb,t)}
 <h1 class="ad-h1 ad-h1s">${E(t)} · 选一段<span>剧情</span></h1><div class="ad-sub">看完一段会出现选项，你的选择决定接下来发生什么</div>
 <div class="ad-stories">${real.map(s=>`<div class="ad-sc" data-id="${E(s.id)}"><div class="ad-scimg"><img src="${E(U(s.cover)||`adult/cards/${k}.jpg`)}" alt="" loading="lazy"></div>
   <div class="ad-sct"><b>${E(s.title)}</b><p>${E(s.desc||'')}</p><small>${s.name?E(s.name)+' · ':''}${s.ready?'互动剧情 · 有声':'这段还在制作中'}</small></div></div>`).join('')}
  ${ph.map((n,i)=>`<div class="ad-sc wip"><div class="ad-scimg"><img src="${E(((alb&&alb.imgs||[])[i+1]||{}).thumb||`adult/cards/${k}.jpg`)}" alt="" loading="lazy"></div><div class="ad-sct"><b>${E(n.t)}</b><p>${E(n.d)}</p><small>制作中</small></div></div>`).join('')}
  <div class="ad-sc ad-cus" id="adCus"><div class="ad-scimg ad-cusimg"><span>＋</span></div><div class="ad-sct"><b>自定义剧情</b><p>写下你想要的场景和关系，Mari 为 ${E((alb&&alb.name_zh)||t)} 编一段专属剧情</p><small>会员专属</small></div></div></div>`,'ad1');
 {const c=document.getElementById('adCus');if(c)c.onclick=()=>cusPlot(t,alb)};document.getElementById('adBack').onclick=home;
 st().querySelectorAll('.ad-sc[data-id]').forEach(c=>c.onclick=()=>play(c.dataset.id));
 st().querySelectorAll('.ad-alb figure[data-i]').forEach(f=>f.onclick=()=>albumBox(alb,+f.dataset.i));
 {const g=document.getElementById('adGenBtn');if(g)g.onclick=()=>poseGen(t,alb)}}

/* ---------- 互动剧情播放器 ----------
   两个 <video> 轮换：普通节点只用当前那个；带 tiers 的互动节点切档时在另一个里预载，0.3s 交叉淡入，不黑屏。 */
const TIER_N=['温柔','激烈','高潮'],TIER_VOL=[.8,.9,1],HIT=.06,DECAY=.08,IDLE=15000,AFF_PER=10,AFF_CAP=5;
let P=null;
function closePlayer(){if(!P)return;const o=P.o;stopTier();P.vs.forEach(v=>{v.pause();v.removeAttribute('src');v.load()});P=null;o.classList.remove('on');document.body.style.overflow='';setTimeout(()=>o.remove(),220)}
AD.close=closePlayer;
async function play(id){closePlayer();
 const o=document.createElement('div');o.className='ad-pl';
 o.innerHTML=`<div class="ad-fr"><img class="ad-poster" alt=""><video playsinline webkit-playsinline x5-playsinline x5-video-player-type="h5-page" disablepictureinpicture controlslist="nodownload nofullscreen noremoteplayback" preload="auto"></video><video class="off" playsinline webkit-playsinline x5-playsinline x5-video-player-type="h5-page" disablepictureinpicture controlslist="nodownload nofullscreen noremoteplayback" preload="auto"></video>
  <div class="ad-wip"><b>这段还在制作中</b><small>素材做好后这里会自动出现</small></div>
  <div class="ad-tb"><button class="ad-ic" data-a="back" aria-label="返回">‹</button><span class="ad-aff" title="好感度">♡ <i>0</i></span><span class="sp"></span>
   <button class="ad-ic ad-subb" data-a="sub" aria-label="字幕开关">字幕</button><button class="ad-ic" data-a="mute" aria-label="静音">🔊</button><button class="ad-ic ad-rcb" data-a="rc">配方</button></div>
  <div class="pl-rc ad-rc"></div>
  <div class="ad-mt"><div class="ad-mtr"><span class="ad-mlv"></span><div class="ad-mbar"><i></i></div><span class="ad-mn"></span></div><div class="ad-mtip">${HOVER?'狂按空格':'连点屏幕'}</div></div>
  <div class="ad-box"><div class="ad-nm"></div><div class="ad-zh"></div><div class="ad-ja"></div><button class="ad-jab" data-a="ja" title="显示日文原文">日</button></div>
  <div class="ad-ch"></div><button class="ad-skip" data-a="skip">跳过 ›</button>
  <div class="ad-start"></div><div class="ad-end"></div><div class="ad-ach"></div><div class="ad-glow"></div></div>`;
 document.body.appendChild(o);document.body.style.overflow='hidden';requestAnimationFrame(()=>o.classList.add('on'));
 if(!HOVER)mirror(o);
 const vs=[...o.querySelectorAll('video')];P={o,vs,v:vs[0],id,aff:0,node:null,m:null,li:-1,lines:[],T:null};
 vs.forEach(v=>{v.muted=LS('ol_adult_mute')==='1';
  v.addEventListener('timeupdate',e=>{if(P&&e.target===P.v)onTime()});
  v.addEventListener('ended',e=>{if(P&&e.target===P.v)(P.T?tierEnded():onEnd())});
  v.addEventListener('error',e=>{if(P&&e.target===P.v&&P.v.getAttribute('src')&&!P.T)wip()});
  v.addEventListener('waiting',e=>{if(P&&e.target===P.v)o.classList.add('ld')});v.addEventListener('playing',()=>o.classList.remove('ld'))});
 o.classList.toggle('ja',LS('ol_adult_ja')==='1');o.classList.toggle('nosub',LS('ol_adult_nosub')==='1');syncMute();
 o.addEventListener('click',onClick);
 let m=null;try{const r=await fetch('adult/story/'+encodeURIComponent(id),{cache:'no-store'});if(r.ok)m=await r.json()}catch(e){}
 if(!P||P.o!==o)return;
 if(!m||!m.nodes){o.classList.add('nomf');return}
 P.m=m;const c=m.char||{},sc=m.scenario||{};
 o.querySelector('.ad-start').innerHTML=`${sc.cover?`<img src="${E(U(sc.cover))}" alt="" onerror="this.remove()">`:''}<div class="ad-sti"><small>${E(c.name_zh||c.name||'')}${c.type?' · '+E(c.type):''}</small><h2>${E(sc.title||'')}</h2><p>${E(sc.desc||'')}</p>
  <button class="ad-b1" data-a="start">开始</button><em>有声播放，可随时静音</em></div>`;
 o.classList.add('st')}
// 空格：只在播放器打开时拦截（不滚页面、不触发聚焦按钮）；互动节点里连续按下才计数，按住（repeat）不算
const isSpace=e=>e.code==='Space'||e.key===' ';
addEventListener('keydown',e=>{if(!P||!isSpace(e))return;e.preventDefault();if(!e.repeat)hit()},true);
addEventListener('keyup',e=>{if(P&&isSpace(e))e.preventDefault()},true);
function onClick(e){if(!P)return;const b=e.target.closest('[data-a]');
 if(!b){if(P.T&&!e.target.closest('.ad-rc,.ad-box'))hit();return}   // 手机：点视频区域 = 按一次
 const a=b.dataset.a;
 if(a==='back'){closePlayer();if(curType)openType(curType);else home()}
 else if(a==='mute'){const mu=!P.v.muted;P.vs.forEach(v=>v.muted=mu);LS('ol_adult_mute',mu?'1':null);syncMute()}
 else if(a==='sub'){P.o.classList.toggle('nosub');LS('ol_adult_nosub',P.o.classList.contains('nosub')?'1':null)}
 else if(a==='ja'){P.o.classList.toggle('ja');LS('ol_adult_ja',P.o.classList.contains('ja')?'1':null)}
 else if(a==='rc'){P.o.classList.toggle('rco')}
 else if(a==='achnext'||a==='glownext'){if(P.cxNext)P.cxNext()}
 else if(a==='skip'){if(P.o.classList.contains('chs'))return;if(P.T){tierFinish();return}if(P.pre){P.v.pause();onEnd();return}P.v.pause();if(P.lines.length)showLine(P.lines.length-1);onEnd()}
 else if(a==='start'){P.o.classList.remove('st');P.aff=0;setAff(0);goNode(P.m.start||'intro')}
 else if(a==='choice'){const ch=P.chs[+b.dataset.i];P.aff+=+ch.aff||0;setAff(P.aff,true);if(ch.sub_list)showChoices(P.node,null,ch.sub_list);else goNode(ch.to)}
 else if(a==='again'){P.o.classList.remove('fin');P.aff=0;setAff(0);goNode(P.m.start||'intro')}
 else if(a==='other'){const t=curType||((P.m||{}).char||{}).type||'御姐';closePlayer();openType(t)}
 else if(a==='types'){closePlayer();home()}
 else if(a==='copy'){const n=P.node||{};navigator.clipboard.writeText(JSON.stringify({story:P.id,node:P.nid,tier:P.T?P.T.i+1:undefined,video:n.video,tiers:n.tiers,prompt:n.prompt,keyframe:n.keyframe,pre:n.pre},null,1)).then(()=>{b.textContent='已复制 ✓';setTimeout(()=>b.textContent='复制完整配方',1500)})}}
function syncMute(){const b=P&&P.o.querySelector('[data-a=mute]');if(b){b.textContent=P.v.muted?'🔇':'🔊';b.setAttribute('aria-label',P.v.muted?'取消静音':'静音')}}
function setAff(n,bump){P.o.querySelector('.ad-aff i').textContent=n;if(bump)bumpHeart()}
function bumpHeart(){const a=P.o.querySelector('.ad-aff');a.classList.remove('bump');void a.offsetWidth;a.classList.add('bump')}
// 10-10 pre：节点有 pre（H3 过渡段，有台词可跳过）就先播 pre，播完 / 跳过 / 出错再进主体（video / tiers / 制作中）；pre 期间 P.T=null，不启用狂按空格
function goNode(nid,noPre){stopTier();const n=P.m.nodes[nid];const o=P.o;P.pre=false;
 o.classList.remove('chs','fin','wipn','rco','tier','pre','ach','glow');o.querySelector('.ad-ch').innerHTML='';P.prev=P.nid;P.nid=nid;P.node=n;P.li=-1;P.lines=(n&&n.lines)||[];
 o.querySelector('.ad-box').classList.remove('show');o.querySelector('.ad-nm').textContent=(P.m.char||{}).name_zh||(P.m.char||{}).name||'';
 if(!n){wip();return}
 if(!noPre&&n.pre&&n.pre.video){playPre(n,nid);return}
 drawRecipe(n,nid);
 const pi=o.querySelector('.ad-poster');pi.onerror=()=>pi.removeAttribute('src');if(n.poster)pi.src=U(n.poster);else pi.removeAttribute('src');
 if((n.tiers||[]).some(t=>t.video)){startTier(n);return}   // tiers 都还没出片 → 按普通节点走（显示制作中 + 选项）
 if(!n.video){wip();return}
 const v=P.v;P.vs.forEach(x=>{if(x!==v){x.pause();x.classList.add('off')}});v.classList.remove('off');
 v.loop=false;v.playbackRate=1;v.volume=1;v.poster=n.poster?U(n.poster):'';v.src=U(n.video);v.currentTime=0;pv(v)}
function playPre(n,nid){const pr=n.pre,o=P.o;P.pre=true;o.classList.add('pre');P.lines=pr.lines||[];P.li=-1;
 drawRecipe({video:pr.video,prompt:pr.prompt,keyframe:pr.keyframe},nid+' · 过渡');
 const pi=o.querySelector('.ad-poster');pi.onerror=()=>pi.removeAttribute('src');if(pr.poster)pi.src=U(pr.poster);else pi.removeAttribute('src');
 const v=P.v;P.vs.forEach(x=>{if(x!==v){x.pause();x.classList.add('off')}});v.classList.remove('off');
 v.loop=false;v.playbackRate=1;v.volume=1;v.poster=pr.poster?U(pr.poster):'';v.src=U(pr.video);v.currentTime=0;pv(v)}
function pv(v){v.play().catch(err=>{if(err&&err.name==='NotAllowedError'){P.vs.forEach(x=>x.muted=true);syncMute();v.play().catch(()=>{})}})}
function wip(){if(!P)return;if(P.pre){onEnd();return}P.o.classList.add('wipn');P.v.pause();if(P.lines.length)showLine(0);onEnd()}
function onTime(){const ls=P.lines;const t=P.v.currentTime;let k=-1;for(let i=0;i<ls.length;i++)if(ls[i].t<=t)k=i;if(k!==P.li&&k>=0)showLine(k)}
function showLine(k){P.li=k;const l=P.lines[k];const o=P.o,box=o.querySelector('.ad-box');
 o.querySelector('.ad-zh').textContent=l.zh||'';o.querySelector('.ad-ja').textContent=l.ja||'';box.classList.toggle('noja',!l.ja);
 box.classList.remove('show');void box.offsetWidth;box.classList.add('show')}
function onEnd(){if(!P)return;if(P.pre){goNode(P.nid,true);return}const n=P.node,o=P.o;if(!n){o.classList.add('chs');return}
 if(n.end||!(n.choices||[]).length){showEnd();return}
 showChoices(n)}
function showChoices(n,nid,list){const o=P.o;P.chs=list||n.choices||[];if(nid){P.nid=nid;P.node=n}
 o.querySelector('.ad-ch').innerHTML=P.chs.map((c,i)=>`<button class="ad-cb" data-a="choice" data-i="${i}" style="--d:${i*70}ms"><b>${E(c.label)}</b>${c.sub?`<small>${E(c.sub)}</small>`:''}</button>`).join('');
 o.classList.add('chs');requestAnimationFrame(()=>{const h=o.querySelector('.ad-ch').offsetHeight;o.style.setProperty('--chh',h+'px')})}
function showEnd(){const o=P.o,c=P.m.char||{};o.classList.add('fin','chs');
 o.querySelector('.ad-end').innerHTML=`<div class="ad-endi"><small>${E((P.m.scenario||{}).title||'')}</small><h2>— 完 —</h2><p>和${E(c.name_zh||c.name||'')}的好感 ♡ ${P.aff}</p>
  <button class="ad-b1" data-a="again">再来一次</button><button class="ad-b2" data-a="other">换个剧情</button><button class="ad-b2" data-a="types">返回选角色</button></div>`}

/* ---------- 互动节点：连按提升兴奋度 + 三档加速（1 温柔 / 2 激烈 / 3 高潮） ---------- */
function startTier(n){const o=P.o;P.T={n,i:-1,p:0,hits:0,aff:0,last:performance.now(),raf:0,idle:0,busy:false};o.classList.add('tier');
 tierTo(0,true);P.T.raf=requestAnimationFrame(tierTick);armIdle()}
function stopTier(){if(!P||!P.T)return;cancelAnimationFrame(P.T.raf);clearTimeout(P.T.idle);P.T=null;P.o.classList.remove('tier','tdone')}
function armIdle(){const T=P.T;clearTimeout(T.idle);T.idle=setTimeout(()=>{if(P&&P.T===T)tierIdle()},IDLE)}
function tierTo(i,first){const T=P.T,tr=T.n.tiers[i];T.i=i;T.p=0;T.busy=true;
 const o=P.o;const TL=T.n.tier_labels||TIER_N;o.querySelector('.ad-mlv').textContent=TL[i]||('第'+(i+1)+'档');o.querySelector('.ad-mn').textContent=(i+1)+'/'+T.n.tiers.length;o.dataset.tier=i+1;
 P.lines=tr.lines||T.n.lines||[];P.li=-1;o.querySelector('.ad-box').classList.remove('show');
 drawRecipe(Object.assign({},T.n,{video:tr.video,prompt:tr.prompt||T.n.prompt,keyframe:tr.keyframe!==undefined?tr.keyframe:T.n.keyframe}),P.nid+' · '+(TL[i]||i+1));
 const loop=i<T.n.tiers.length-1,vol=TIER_VOL[Math.min(i,2)];
 if(!tr.video){T.busy=false;return}
 if(first){const v=P.v;P.vs.forEach(x=>{if(x!==v){x.pause();x.classList.add('off')}});v.classList.remove('off');
  Object.assign(v,{loop,volume:vol,playbackRate:1});v.poster=tr.poster?U(tr.poster):'';v.src=U(tr.video);v.currentTime=0;pv(v);T.busy=false;return}
 // 交叉淡入：另一个 video 先加载，能播了再 0.3s 淡入
 const old=P.v,nv=P.vs.find(x=>x!==old);let done=false;
 const swap=()=>{if(done||!P||P.T!==T)return;done=true;nv.removeEventListener('error',bad);P.v=nv;pv(nv);nv.classList.remove('off');old.classList.add('off');setTimeout(()=>old.pause(),320);T.busy=false};
 const bad=()=>{if(done)return;done=true;old.playbackRate=1;old.volume=vol;T.busy=false};   // 这一档视频缺了：留在当前画面继续
 Object.assign(nv,{loop,volume:vol,playbackRate:1,muted:old.muted});nv.poster=tr.poster?U(tr.poster):'';
 nv.addEventListener('canplay',swap,{once:true});nv.addEventListener('error',bad,{once:true});nv.src=U(tr.video);nv.currentTime=0;nv.load();setTimeout(swap,1500)}
function hit(){const T=P&&P.T;if(!T||P.o.classList.contains('chs')||P.o.classList.contains('st'))return;
 T.p=Math.min(1,T.p+HIT);T.hits++;bumpHeart();armIdle();P.o.classList.add('tap');clearTimeout(T.tapT);T.tapT=setTimeout(()=>P&&P.o.classList.remove('tap'),900);
 if(T.hits%AFF_PER===0&&T.aff<AFF_CAP){T.aff++;P.aff++;setAff(P.aff)}
 if(T.p>=1&&!T.busy){if(T.i<T.n.tiers.length-1)tierTo(T.i+1);else tierFinish()}}
function tierTick(now){const T=P&&P.T;if(!T)return;const dt=Math.min(.1,(now-T.last)/1000);T.last=now;
 if(!T.busy)T.p=Math.max(0,T.p-DECAY*dt);
 const r=1+.25*T.p;if(!T.busy&&Math.abs(P.v.playbackRate-r)>.01)P.v.playbackRate=r;   // 档内随兴奋度提速，切档复位
 P.o.querySelector('.ad-mbar i').style.width=(T.p*100).toFixed(1)+'%';T.raf=requestAnimationFrame(tierTick)}
function tierEnded(){const T=P.T;if(T.idleShown)return;if(T.i>=T.n.tiers.length-1)tierFinish()}   // 只有最后一档不循环
// 第 3 档播完 / 进度满 → 优先跳 tier_end（manifest 字段，如 after）；旧结构：选项里有 climax → 进 climax；否则出该节点的选项
function tierNext(n){if(n.tier_end&&P.m.nodes[n.tier_end])return n.tier_end;const cs=n.choices||[];return P.m.nodes.climax&&(cs.some(c=>c.to==='climax')||(!cs.length&&!n.end&&P.nid!=='climax'))?'climax':null}
function tierFinish(){const T=P.T;if(!T||T.idleShown)return;const n=T.n;P.o.classList.add('tdone');cancelAnimationFrame(T.raf);clearTimeout(T.idle);
 const to=tierNext(n);setTimeout(()=>{if(!P||P.T!==T)return;if(to){if(n.climax){climax(n,to);return}goNode(to)}else{stopTier();onEnd()}},450)}
// 10-10 木木夕：高潮后不直接切事后视频 → ①成就解锁「特殊 CG」（记 localStorage 收集进度）②一段两人余韵的文字 ③再进 tier_end（after）
// manifest：体位节点 climax:{title, cg(图), text:[段落…]}；点击推进，也会自动往下走
function cgKey(){return 'ol_adult_cg'}
function cgGot(){try{return JSON.parse(LS(cgKey())||'[]')}catch(e){return []}}
function climax(n,to){const cx=n.climax,o=P.o,tok={};P.cx=tok;stopTier();P.v.pause();o.querySelector('.ad-box').classList.remove('show');
 const id=P.id+':'+P.nid,got=cgGot(),isNew=!got.includes(id);if(isNew){got.push(id);LS(cgKey(),JSON.stringify(got))}
 const all=Object.entries(P.m.nodes).filter(([k,v])=>v.climax).map(([k])=>P.id+':'+k),have=all.filter(k=>got.includes(k)).length;
 const cg=cx.cg||(n.keyframe&&n.keyframe.file)||n.poster;
 o.querySelector('.ad-ach').innerHTML=`<div class="ad-achc"><small>${isNew?'✦ 成就解锁 ✦':'✦ 再次达成 ✦'}</small>
  ${cg?`<div class="ad-cg"><img src="${E(U(cg))}" alt=""><i></i></div>`:''}<h3>特殊 CG「${E(cx.title||'')}」</h3>
  <p>CG 收集 <b>${have}</b> / ${all.length}</p><button class="ad-b1" data-a="achnext">继续</button></div>`;
 o.classList.add('ach');P.cxNext=()=>glow(cx,to,tok);setTimeout(()=>{if(P&&P.cx===tok&&o.classList.contains('ach'))P.cxNext()},5200)}
function glow(cx,to,tok){if(!P||P.cx!==tok)return;const o=P.o;o.classList.remove('ach');const ps=cx.text||[];
 if(!ps.length){P.cx=null;goNode(to);return}
 o.querySelector('.ad-glow').innerHTML=`<div class="ad-glw">${ps.map((p,i)=>`<p style="--d:${(i*1.6).toFixed(1)}s">${E(p)}</p>`).join('')}
  <button class="ad-b2" data-a="glownext" style="--d:${(ps.length*1.6+.4).toFixed(1)}s">继续 ›</button></div>`;
 o.classList.add('glow');P.cxNext=()=>{if(!P||P.cx!==tok)return;P.cx=null;P.cxNext=null;o.classList.remove('glow');goNode(to)};
 setTimeout(()=>{if(P&&P.cx===tok&&o.classList.contains('glow'))P.cxNext()},(ps.length*1.6+6)*1000)}
// 15 秒没按：不强迫，弹普通选项（换个体位 / 一起到达）；画面继续循环
function tierIdle(){const T=P.T,n=T.n;T.idleShown=true;cancelAnimationFrame(T.raf);P.v.playbackRate=1;P.o.classList.add('tdone');
 const to=tierNext(n);if(!to||n.tier_end){if((n.choices||[]).length)showChoices(n);else showEnd();return}
 const others=(n.choices||[]).filter(c=>c.to!=='climax'&&!/_fast$/.test(c.to||''));
 showChoices(n,null,[...(others.length?[{label:'换个体位',sub:'',sub_list:others,aff:0}]:[]),{label:'一起到达',sub:'',to,aff:1}])}
// 创作配方：复用 plays.js 灯箱配方面板（.pl-rc）的写法和样式
function drawRecipe(n,nid){const p=n.prompt||{},k=n.keyframe;const row=(a,b)=>b?`<div class="rr"><b>${a}</b><span>${b}</span></div>`:'';
 const par=p.params&&Object.keys(p.params).length?Object.entries(p.params).map(([a,b])=>`${E(a)}=${E(typeof b==='object'?JSON.stringify(b):b)}`).join(' · '):'';
 const kimg=k&&(k.image||k.src||k.file);
 P.o.querySelector('.ad-rc').innerHTML=`<h4>创作配方</h4>${row('节点',E(nid))}${row('模型',E(p.model||'—'))}${row('参数',par)}${row('视频',n.video?`<a href="${E(U(n.video))}" target="_blank">${E(n.video.split('/').pop())}</a>`:'')}
  ${p.text?`<details open><summary>提示词</summary><pre>${E(p.text)}</pre></details>`:''}
  ${k?`<details><summary>首帧配方</summary>${row('模型',E(k.model||''))}${row('画风',E(k.style||k.style_name||''))}${kimg?`<div class="rr"><b>首帧</b><span class="ri"><figure><a href="${E(U(kimg))}" target="_blank"><img src="${E(U(kimg))}"></a></figure></span></div>`:''}${k.prompt?`<pre>${E(k.prompt)}</pre>`:''}${typeof k==='string'?`<pre>${E(k)}</pre>`:''}</details>`:row('首帧','无（直接文生视频或沿用上一段）')}
  <button class="pl-btn g" data-a="copy">复制完整配方</button>`}

/* 10-10 木木夕：剧情加「自定义（会员专属）」——会员填场景 / 关系 / 氛围，提交后进制作队列 */
const CUS_MOOD=['甜蜜','暧昧','强势','温柔','刺激','治愈'];
function cusPlot(t,alb){const vip=localStorage.getItem('ol_vip')==='1';const nm=(alb&&alb.name_zh)||t;
 const o=document.createElement('div');o.className='ad-cussh';
 o.innerHTML=vip?`<div class="pan"><div class="hd"><b>为 ${E(nm)} 自定义剧情</b><button class="x" aria-label="关闭">✕</button></div>
  <label>在哪里</label><input id="cuP" maxlength="30" placeholder="例如：下雨天的便利店、圣诞夜的公寓">
  <label>你们是什么关系</label><input id="cuR" maxlength="30" placeholder="例如：刚认识的邻居、合租室友、多年的搭档">
  <label>想要的氛围</label><div class="moods">${CUS_MOOD.map(m=>`<button data-m="${m}">${m}</button>`).join('')}</div>
  <label>还想补充什么（可不填）</label><textarea id="cuD" maxlength="200" placeholder="例如：她今天刚失恋，想找人陪她喝一杯"></textarea>
  <p class="tip">所有角色均为成年人。提交后 Mari 会写开场和选项，并生成开场动画，做好会出现在剧情列表里。</p>
  <button class="go" id="cuGo">提交给 Mari</button></div>`
 :`<div class="pan"><div class="hd"><b>自定义剧情</b><button class="x" aria-label="关闭">✕</button></div>
  <p class="lead">会员专属：自己写场景和关系，让 ${E(nm)} 陪你演一段只属于你的剧情。</p>
  <button class="go" id="cuVip">开通会员</button><p class="tip">测试站：点击即模拟开通，不扣费。</p></div>`;
 document.body.appendChild(o);requestAnimationFrame(()=>o.classList.add('on'));
 const close=()=>{o.classList.remove('on');setTimeout(()=>o.remove(),200)};o.onclick=e=>{if(e.target===o)close()};o.querySelector('.x').onclick=close;
 if(!vip){o.querySelector('#cuVip').onclick=()=>{localStorage.setItem('ol_vip','1');close();setTimeout(()=>cusPlot(t,alb),220)};return}
 const sel=new Set();o.querySelectorAll('.moods button').forEach(b=>b.onclick=()=>{sel.has(b.dataset.m)?sel.delete(b.dataset.m):sel.add(b.dataset.m);b.classList.toggle('on')});
 o.querySelector('#cuGo').onclick=async()=>{const P=o.querySelector('#cuP').value.trim(),R=o.querySelector('#cuR').value.trim();if(!P||!R){o.querySelector('.tip').textContent='先写一下在哪里、你们是什么关系';return}
  const b=o.querySelector('#cuGo');b.disabled=true;b.textContent='提交中…';
  try{const r=await fetch('adult/custom',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:t,name:(alb&&alb.name)||'',place:P,relation:R,moods:[...sel],note:o.querySelector('#cuD').value.trim()})});if(!r.ok)throw 0;
   o.querySelector('.pan').innerHTML=`<div class="hd"><b>已收到</b><button class="x" aria-label="关闭">✕</button></div><p class="lead">「${E(P)} · ${E(R)}」已经交给 Mari，做好会出现在 ${E(nm)} 的剧情列表里。</p><button class="go">好的</button>`;
   o.querySelectorAll('.x,.go').forEach(x=>x.onclick=close)}catch(e){b.disabled=false;b.textContent='提交给 Mari';o.querySelector('.tip').textContent='提交失败，稍后再试'}}}


/* 10-10 木木夕：角色资料「＋自定义」——tag 库（adult/pose_tags.json，取材涩涩词库，只收单人）分类选，用这个角色的配方出一张，结果和配方都存档 */
const MALE_T=['型男','熟男','兽人'];
/* 10-11 木木夕：成人作品「做成视频」——剧情向 H3 / 无声动态 Seedance 1.0 Pro Fast / SEX 动态 LTX；选时长价格实时变；做好进角色主页 */
let VOPTS=null;
async function vidSheet(w){if(!VOPTS)try{VOPTS=await (await fetch('adult/vid/opts',{cache:'no-store'})).json()}catch(e){return}
 const S={k:'live',sec:null,res:null};const o=document.createElement('div');o.className='ad-cussh ad-vsh';
 o.innerHTML=`<div class="pan"><div class="hd"><b>把这张做成视频</b><button class="x" aria-label="关闭">✕</button></div>
  <div class="vs-body"><div class="vs-l"><div class="vs-top"><img src="${E(w.thumb||w.src)}" alt=""><small>${E(w.label||'')}</small></div>
  <div class="vs-kinds">${Object.entries(VOPTS).map(([k,v])=>`<button class="vs-k" data-k="${k}">${v.sample?`<img class="vs-smp" src="${E(v.sample)}" alt="" loading="lazy">`:''}<b>${E(v.name)}</b><small>${E(v.desc)}</small><i>${E(v.eta)}${v.audio?' · 有声':' · 无声'}</i></button>`).join('')}</div></div>
  <div class="vs-r"><label>时长</label><div class="moods" id="vsSec"></div><div id="vsResW"><label>清晰度</label><div class="moods" id="vsRes"></div></div>
  <label>想让她做什么、说什么（可不填）</label><textarea id="vsTxt" maxlength="300" placeholder="例如：她慢慢靠近镜头，小声说「今晚别走了」"></textarea>
  <div class="vs-res" id="vsOut"></div><div class="vs-list" id="vsList"></div>
  <div class="vs-go"><button class="go" id="vsGo">生成</button><p class="tip" id="vsTip">所有角色均为成年人 · 积分从你的账号扣</p></div></div></div></div>`;
 document.body.appendChild(o);requestAnimationFrame(()=>o.classList.add('on'));
 const $=q=>o.querySelector(q),close=()=>{o.classList.remove('on');setTimeout(()=>o.remove(),200)};o.onclick=e=>{if(e.target===o)close()};$('.x').onclick=close;
 const draw=()=>{const v=VOPTS[S.k];if(!v.secs.includes(S.sec))S.sec=v.secs[1];if(!(S.res in v.res))S.res=v.dres;
  o.querySelectorAll('.vs-k').forEach(b=>b.classList.toggle('on',b.dataset.k===S.k));
  $('#vsSec').innerHTML=v.secs.map(x=>`<button data-s="${x}" class="${x===S.sec?'on':''}">${x} 秒</button>`).join('');
  const rs=Object.keys(v.res);$('#vsResW').style.display=rs.length>1?'':'none';$('#vsRes').innerHTML=rs.map(r=>`<button data-r="${r}" class="${r===S.res?'on':''}">${r} · ${v.res[r]}/秒</button>`).join('');
  $('#vsGo').textContent=`生成 · ${v.res[S.res]*S.sec} 积分`};
 o.querySelectorAll('.vs-k').forEach(b=>b.onclick=()=>{S.k=b.dataset.k;draw()});
 $('#vsSec').onclick=e=>{const b=e.target.closest('button');if(b){S.sec=+b.dataset.s;draw()}};$('#vsRes').onclick=e=>{const b=e.target.closest('button');if(b){S.res=b.dataset.r;draw()}};
 const vcard=x=>`<figure><video src="${E(x.src)}" poster="${E(x.poster)}" controls playsinline preload="none" loop></video><figcaption>${E(x.kind_name)} · ${x.sec}秒 · ${x.credits} 积分</figcaption></figure>`;
 const list=async()=>{try{const v=(await (await fetch('adult/vid/list?work='+encodeURIComponent(w.id),{cache:'no-store'})).json()).videos||[];
  $('#vsList').innerHTML=v.length?`<label>这张做过的视频（${v.length}）</label><div class="vs-grid">${v.map(vcard).join('')}</div>`:''}catch(e){}};
 draw();list();
 $('#vsGo').onclick=async()=>{const b=$('#vsGo'),out=$('#vsOut'),v=VOPTS[S.k];b.disabled=true;out.innerHTML=`<div class="pgld">${S.k==='ltx'?'已提交，在后台生成（2~14 分钟）。可以关掉这个窗口，做好会出现在角色主页和这里':'生成中，'+v.eta}</div>`;
  try{const r=await (await fetch('adult/vid',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({work:w.id,kind:S.k,sec:S.sec,res:S.res,text:$('#vsTxt').value.trim()})})).json();if(!r.id)throw r.error||'提交失败';
   let j;for(let n=0;n<700;n++){await new Promise(z=>setTimeout(z,3000));if(!o.isConnected)return;j=await (await fetch('adult/vid/job/'+r.id,{cache:'no-store'})).json();if(j.status!=='run')break}
   if(j.status!=='done')throw j.err||'生成失败';out.innerHTML=vcard(j.video).replace('<video ','<video autoplay ');list()}
  catch(e){out.innerHTML=`<div class="pgld">${E(String(e))}</div>`}b.disabled=false;draw()}}const BRZ=[['flat','贫乳'],['small','小胸'],['medium','中等'],['large','丰满'],['huge','巨乳']],BUZ=[['slim','纤细'],['average','匀称'],['curvy','曲线'],['muscular','肌肉'],['chubby','微胖']];let PTAGS=null;
async function poseGen(t,alb){const im0=(alb.imgs||[])[0]||{};
 return pageGen({nm:(alb&&alb.name_zh)||t,img:im0.thumb||im0.src||'',g:MALE_T.includes(t)?'m':'f',xl:!String((im0.recipe||{}).style_id||'').startsWith('anima_'),
  q:{type:t},list:'type='+encodeURIComponent(t),back:['‹ 返回 '+((alb&&alb.name_zh)||t),()=>openType(t)],en:alb.name,t})}
// 10-10 木木夕：普通角色主页「成人模式」→ 用户自己的角色进这个页面；作品只在成人模式下的角色主页显示
async function ocGen(cid){let c;try{c=await (await fetch('adult/oc/'+encodeURIComponent(cid),{cache:'no-store'})).json()}catch(e){return}
 history.replaceState(null,'',location.pathname);
 if(!c.ok){mount(`<div class="ad-hd"><a class="back" href="c/${encodeURIComponent(cid)}">‹ 返回 ${E(c.name||'角色')}</a></div><h1 class="ad-h1 ad-h1s">进不了<span>成人模式</span></h1><div class="ad-sub">${E(c.why)}</div>`,'ad3');return}
 return pageGen({nm:c.name,img:c.cutout||c.img,g:c.g,xl:/^S\d+$/.test(c.style||''),q:{cid},list:'cid='+encodeURIComponent(cid),body:c.body,back:['‹ 返回 '+c.name+' 的主页',()=>{location.href='c/'+encodeURIComponent(cid)}],en:c.name,t:c.type,oc:true})}
async function pageGen(X){if(!PTAGS)try{PTAGS=await (await fetch('adult/pose_tags',{cache:'no-store'})).json()}catch(e){return}
 const t=X.t,alb={name:X.en};
 // 10-10 木木夕：弹窗改成独立页面——左边分类标签页选 tag，右边（手机在上面）是预览 + 已选 + 出图 + 出过的
 const g=X.g,nm=X.nm,xl=X.xl;
 const cats=PTAGS.cats.map(c=>Object.assign({},c,{tags:c.tags.filter(x=>(x.g||g)===g)})).filter(c=>c.tags.length);
 const sel={};let cur=cats[0].id,W=[];
 mount(`<div class="ad-hd"><button class="back" id="pgBack">${E(X.back[0])}</button></div>
 <h1 class="ad-h1 ad-h1s">给 ${E(nm)} <span>出一张</span></h1><div class="ad-sub">按分类挑姿势、穿着和场景，Mari 用 ${E(nm)} 自己的画风画出来${X.oc?'，出的图会放进 '+E(nm)+' 的主页（只在成人模式下显示）':''}</div>
 <div class="pg-wrap"><aside class="pg-side"><div class="pg-pv" id="pgPv"><img src="${E(X.img)}" alt=""${X.oc?' class="oc"':''}><div class="pg-pvt">选好后点「出图」</div></div>
   ${X.body?`<div class="pg-body" id="pgBody"><div class="pg-bh">体型<small>已按立绘读出，可以改</small></div>${g==='f'?`<div class="pg-brow" data-k="breasts"><span>胸型</span>${BRZ.map(([k,z])=>`<button data-v="${k}">${z}</button>`).join('')}</div>`:''}<div class="pg-brow" data-k="build"><span>身材</span>${BUZ.map(([k,z])=>`<button data-v="${k}">${z}</button>`).join('')}</div></div>`:''}
   <div class="pg-sel" id="pgSel"></div>
   <div class="pg-act"><button class="pg-rnd" id="pgRnd">随机搭配</button><button class="pg-go" id="pgGo">出图</button></div>
   <p class="pg-tip">每张约 ${xl?10:15} 积分 · 10~40 秒 · 所有角色均为成年人</p></aside>
  <main class="pg-main"><nav class="pg-tabs" id="pgTabs"></nav><div class="pg-chips" id="pgChips"></div>
   <div class="pg-hist" id="pgHist"></div></main></div>`,'ad3');
 const $=q=>st().querySelector(q);$('#pgBack').onclick=X.back[1];
 const picks=()=>cats.flatMap(c=>(sel[c.id]||[]).map(zh=>({cat:c.id,zh})));
 const draw=()=>{$('#pgTabs').innerHTML=cats.map(c=>`<button data-c="${c.id}" class="${c.id===cur?'on':''}">${E(c.name)}${(sel[c.id]||[]).length?`<i>${sel[c.id].length}</i>`:''}</button>`).join('');
  const c=cats.find(x=>x.id===cur);
  $('#pgChips').innerHTML=`<div class="pg-ch-h">${E(c.name)}<small>${c.max>1?`最多选 ${c.max} 个`:'单选'}</small></div>`+c.tags.map(x=>`<button data-z="${E(x.zh)}" class="${(sel[cur]||[]).includes(x.zh)?'on':''}">${E(x.zh)}</button>`).join('');
  const p=picks();$('#pgSel').innerHTML=p.length?p.map(x=>`<button data-c="${x.cat}" data-z="${E(x.zh)}" title="去掉">${E(x.zh)} ×</button>`).join(''):'<small>还没选，至少选一个</small>';
  $('#pgGo').disabled=!p.length};
 const tog=(cid,z)=>{const c=cats.find(x=>x.id===cid),a=sel[cid]||(sel[cid]=[]),i=a.indexOf(z);if(i>=0)a.splice(i,1);else{if(a.length>=(c.max||1))a.shift();a.push(z)}draw()};
 $('#pgTabs').onclick=e=>{const b=e.target.closest('button');if(b){cur=b.dataset.c;draw()}};
 $('#pgChips').onclick=e=>{const b=e.target.closest('button');if(b)tog(cur,b.dataset.z)};
 $('#pgSel').onclick=e=>{const b=e.target.closest('button');if(b)tog(b.dataset.c,b.dataset.z)};
 $('#pgRnd').onclick=()=>{for(const k in sel)delete sel[k];for(const c of cats)if(['pose','wear','expose','scene','view','face'].includes(c.id))sel[c.id]=[c.tags[Math.floor(Math.random()*c.tags.length)].zh];draw()};
 const box=(imgs,i)=>albumBox({name_zh:nm,name:alb.name,type:t,imgs},i);
 const hist=async()=>{try{W=(await (await fetch('adult/gen/list?'+X.list,{cache:'no-store'})).json()).works||[]}catch(e){}
  $('#pgHist').innerHTML=W.length?`<div class="pg-ch-h">出过的<small>${W.length} 张 · 点开看配方</small></div><div class="pg-grid">${W.map((x,i)=>`<figure data-i="${i}"><img src="${E(x.thumb)}" alt="" loading="lazy"><figcaption>${E(x.label)}</figcaption></figure>`).join('')}</div>`:'';
  st().querySelectorAll('.pg-grid figure').forEach(f=>f.onclick=()=>box(W,+f.dataset.i))};
 const BD=Object.assign({},X.body||{});const bdraw=()=>st().querySelectorAll('.pg-brow').forEach(r=>r.querySelectorAll('button').forEach(b=>b.classList.toggle('on',BD[r.dataset.k]===b.dataset.v)));
 if(X.body){bdraw();st().querySelectorAll('.pg-brow').forEach(r=>r.onclick=e=>{const b=e.target.closest('button');if(b){BD[r.dataset.k]=b.dataset.v;bdraw()}})}
 draw();hist();
 $('#pgGo').onclick=async()=>{const p=picks(),b=$('#pgGo'),pv=$('#pgPv');if(!p.length)return;
  b.disabled=true;b.textContent='Mari 正在画…';pv.classList.add('ld');pv.querySelector('.pg-pvt').textContent='出图中，约 10~40 秒';
  if(!matchMedia('(min-width:960px)').matches)pv.scrollIntoView({behavior:'smooth',block:'start'});
  try{const r=await (await fetch('adult/gen',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.assign({picks:p},X.q,X.body?{body:BD}:{}))})).json();if(!r.id)throw r.error||'创建失败';
   let j;for(let k=0;k<200;k++){await new Promise(z=>setTimeout(z,2000));j=await (await fetch('adult/gen/job/'+r.id,{cache:'no-store'})).json();if(j.status!=='run')break}
   if(j.status!=='done')throw j.err||'出图失败';
   pv.querySelector('img').src=j.work.src;pv.querySelector('.pg-pvt').textContent=`${j.work.label} · ${j.sec}s · 点图看配方`;pv.onclick=()=>box([j.work],0);hist()}
  catch(e){pv.querySelector('.pg-pvt').textContent=String(e)}
  pv.classList.remove('ld');b.textContent='再出一张';b.disabled=!picks().length}}
})();
