// 10-10 木木夕：角色主页延展玩法（测试版）—— 服装抽卡机 / 运势表情包抽卡机 / 角色出场 PV
// 交互参考 wow 的 feat/gacha-machine（拉一次 → 逐个落定 → 翻牌揭晓 → 再来一次），只取节奏，不搬代码。
// 搬家时：/api/play/* 的输入输出不变，界面按官网组件重写即可。
(()=>{
const E=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const U=p=>/^https?:/.test(p||'')?p:'../'+p;
const post=(p,b)=>fetch('../api/'+p,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}).then(r=>r.json()).then(j=>{if(j.error)throw new Error(j.error);return j});
const get=p=>fetch('../api/'+p).then(r=>r.json());
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const preload=srcs=>Promise.race([Promise.all(srcs.map(u=>new Promise(r=>{const i=new Image();i.onload=i.onerror=r;i.src=u}))),sleep(3000)]);   // 翻牌前先把卡面图加载好，不然翻过来是白的
const RM=matchMedia('(prefers-reduced-motion: reduce)').matches;
let C=null,CID=null;

window.mountPlays=c=>{C=c;CID=c.id;const box=document.getElementById('plays');if(!box)return;const n=E(c.name);
 const ssr='https://kusart.com/Oc-generator/oc-prompt-%20picture/Halloween_costume/Pumpkin%20Witch.webp';
 box.innerHTML=`<h2 class="pl-h">和 ${n} 一起玩</h2><p class="pl-sub">抽卡都免费，喜欢再生成</p>
 <a class="pl-btn pl-create-link" href="../templates?cid=${encodeURIComponent(CID)}">用 ${n} 做新作品 →</a><div class="pl-cards">
  <button class="pl-card" data-pl="outfit"><span class="pl-free">抽卡免费</span><div class="pl-ico"><i class="pl-mini" style="background-image:url(${U('tags_v3/少女/big/穿着_水手服.webp')})"></i><i class="pl-mini ssr" style="background-image:url('${ssr}')"></i><i class="pl-mini" style="background-image:url(${U('tags_v3/御姐/big/穿着_大衣.webp')})"></i></div><b>服装抽卡机</b><p>抽一套衣服给 ${n} 换上，万圣节、圣诞限定是 SSR</p></button>
  <button class="pl-card" data-pl="fortune"><span class="pl-free">抽签免费</span><div class="pl-ico"><div class="pl-kw"><span>小确幸</span><span>好运</span><span>摸鱼</span></div></div><b>运势表情包</b><p>抽今天的三个运势关键词，${n} 用表情包告诉你今天怎么样</p></button>
  <button class="pl-card" data-pl="pv"><div class="pl-ico"><div class="pl-play" style="background-image:url(${U((c.cutout||{}).src||c.img)});background-size:contain;background-repeat:no-repeat;background-position:center;background-color:#15161b"></div></div><b>出场 PV</b><p>选择登场、剧情或 LP 动画，让角色动起来</p></button>
 </div><div class="pl-works" id="plWorks"></div>`;
 box.querySelectorAll('[data-pl]').forEach(b=>b.onclick=()=>({outfit:openOutfit,fortune:openFortune,pv:openPV})[b.dataset.pl]());
 drawWorks();
 // 10-10 唤醒页「接下来一起玩」带 #play=outfit|fortune|pv 进来 → 直接打开对应玩法
 const m=location.hash.match(/play=(\w+)/);if(m&&!window.__plOpened){window.__plOpened=1;const f={outfit:openOutfit,fortune:openFortune,pv:openPV}[m[1]];if(f){box.scrollIntoView();setTimeout(f,300)}}};

function drawWorks(){const w=document.getElementById('plWorks');if(!w)return;const ws=C.works||[];
 if(!ws.length){w.innerHTML='';return}
 const T={outfit:'换装',meme:'表情包',fsign:'运势签',pv:'PV'};
 w.innerHTML=`<h3>${E(C.name)} 的作品 · ${ws.length}</h3><div class="pl-wgrid">${ws.map((x,i)=>`<div class="pl-w ${x.kind}" data-w="${i}">${x.kind==='pv'?`<video src="${U(x.src)}" muted playsinline loop preload="metadata"></video>`:`<img src="${U(x.src)}" loading="lazy">`}<i>${E(T[x.kind]||x.title||'')}${x.rarity==='SSR'?' · SSR':''}</i></div>`).join('')}</div>`;
 w.querySelectorAll('[data-w]').forEach(d=>{const x=ws[+d.dataset.w];const v=d.querySelector('video');if(v){d.onmouseenter=()=>v.play();d.onmouseleave=()=>v.pause()}
  d.onclick=()=>lightbox(x)})}
function lightbox(x){const o=document.createElement('div');o.className='pl-lb';const r=x.recipe;   // 10-10 木木夕：每个作品带「创作配方」（角色 / 模型 / 风格 / 提示词 / 素材），之后别人可以照着复用
 const media=x.kind==='pv'?`<video src="${U(x.src)}" controls autoplay playsinline></video>`:`<img src="${U(x.src)}">`;
 const row=(k,v)=>v?`<div class="rr"><b>${k}</b><span>${v}</span></div>`:'';
 const im=s=>s?`<a href="${E(U(s))}" target="_blank"><img src="${E(U(s))}"></a>`:'';
 const P=r&&r.params||{},card=P.card||{};
 const reuse=r&&['template','outfit','fortune','pv'].includes(r.play)?`<button class="pl-btn" id="workAgain">${x.kind==='pv'?'再做一个':'再来一张'}</button><a class="pl-btn g" style="display:block;text-decoration:none;text-align:center" href="../templates?cid=${encodeURIComponent(CID)}&source_cid=${encodeURIComponent(CID)}&source_src=${encodeURIComponent(x.src)}&action=swap">换角色做同款</a><p id="reuseStatus" role="status"></p>`:'';
 const rec=r?`<div class="pl-rc">${reuse}<details><summary>查看制作信息</summary><h4>创作配方${r.backfill?' <em>补录</em>':''}</h4>
  ${row('玩法',E(r.play_name))}${row('角色',E((r.character||{}).name)+((r.character||{}).type?` · ${E(r.character.type)}`:''))}${row('画风',E((r.character||{}).style_name||'—'))}
  ${row('模型',E((r.model||{}).name)+((r.model||{}).size?` · ${E(r.model.size)}`:'')+((r.model||{}).resolution?` · ${E(r.model.resolution)} ${E(r.model.duration)}s`:''))}
  ${row('模版',E(r.template||(P.template&&P.template.id)||''))}${row('卡片',card.name?E(`${card.rarity||''} ${card.name}`):'')}
  ${row('运势',P.level?E(P.level+(P.keywords&&P.keywords.length?' · '+P.keywords.join(' / '):'')):'')}${row('签文',E(P.sign||''))}
  ${(r.inputs||[]).length?`<div class="rr"><b>素材</b><span class="ri">${r.inputs.map(i=>`<figure>${im(i.src)}<figcaption>${E(i.role)}</figcaption></figure>`).join('')}</span></div>`:''}
  ${r.prompt?`<details><summary>提示词</summary><pre>${E(r.prompt)}</pre></details>`:''}
  <button class="pl-btn g" id="rcp">复制完整配方</button></details></div>`:'';
 o.innerHTML=`<div class="pl-lbw">${media}${rec}</div>`;o.onclick=e=>{if(e.target===o||e.target.classList.contains('pl-lbw'))o.remove()};
 const b=o.querySelector('#rcp');if(b)b.onclick=()=>{navigator.clipboard.writeText(JSON.stringify(Object.assign({src:x.src},r),null,1)).then(()=>{b.textContent='已复制 ✓';setTimeout(()=>b.textContent='复制完整配方',1500)})};
 const again=o.querySelector('#workAgain');if(again)again.onclick=async()=>{again.disabled=true;try{const j=await post('templates/generate',{cid:CID,source_cid:CID,source_src:x.src});localStorage.setItem('oc-lab-template-job',j.job);location.href='../templates?cid='+encodeURIComponent(CID)+'&job='+encodeURIComponent(j.job)}catch(e){o.querySelector('#reuseStatus').textContent=e.message;again.disabled=false}};
 document.body.appendChild(o)}
function addWork(w){C.works=[w,...(C.works||[])];drawWorks()}

function overlay(title){const o=document.createElement('div');o.className='pl-ov';o.innerHTML=`<div class="pl-top"><b>${title}</b><button class="pl-x" aria-label="关闭">✕</button></div><div class="pl-body"></div>`;
 document.body.appendChild(o);document.body.style.overflow='hidden';requestAnimationFrame(()=>o.classList.add('on'));
 o.querySelector('.pl-x').onclick=()=>{o.classList.remove('on');document.body.style.overflow='';setTimeout(()=>o.remove(),250)};return o.querySelector('.pl-body')}
async function runJob(jid,el,hint,est,fixed){let t0=Date.now();el.innerHTML=`<div class="pl-prog"><div class="ph">${hint}</div><div class="bar"><i></i></div></div>`;
 const bar=el.querySelector('.bar i'),ph=el.querySelector('.ph');
 for(;;){await sleep(2000);const j=await get('play/job/'+jid);const s=(Date.now()-t0)/1000;bar.style.width=Math.min(94,s/est*100)+'%';if(fixed)ph.innerHTML=hint+' · '+Math.round(s)+' 秒';else if(j.phase)ph.textContent=j.phase+' · '+Math.round(s)+' 秒';
  if(j.status==='done'){bar.style.width='100%';return j}if(j.status==='error')throw new Error(j.err||'失败了')}}
const cardHTML=(x,cls='')=>`<div class="pl-gc ${(x?x.rarity.toLowerCase():'')} ${cls}"><div class="b"></div><div class="f">${x?`<img src="${U(x.thumb)}" alt=""><div class="nm"><span class="rk">${x.rarity}</span>${E(x.name)}${x.cat?`<em class="ct">${E(x.cat)}</em>`:''}</div>`:''}</div></div>`;

/* ===== 1. 服装抽卡机 ===== */
function openOutfit(){const B=overlay('服装抽卡机');let picked=null;
 const idle=()=>{picked=null;B.innerHTML=`<div class="pl-rate">R 单品配饰 60% · SR 整套服装 30% · <em>SSR 节日限定 10%</em></div>
  <div class="pl-stage" id="st">${cardHTML(null,'idle')}</div>
  <div class="pl-btns"><button class="pl-btn" id="d1">抽一次<small>免费</small></button><button class="pl-btn g" id="d10">十连<small>免费 · 保底 SR</small></button></div>
  <p class="pl-note">抽到喜欢的再让 ${E(C.name)} 换上</p>`;B.querySelector('#d1').onclick=()=>draw(1);B.querySelector('#d10').onclick=()=>draw(10)};
 async function draw(n){B.querySelectorAll('.pl-btn').forEach(b=>b.disabled=true);const st=B.querySelector('#st');
  const req=post('play/outfit/draw',{cid:CID,n});
  if(n===1){const g=st.querySelector('.pl-gc');g.classList.remove('idle');g.classList.add('shake');const r=await req;const x=r.cards[0];await Promise.all([preload([U(x.thumb)]),sleep(RM?0:900)]);
   st.innerHTML=cardHTML(x);const g2=st.querySelector('.pl-gc');await sleep(60);g2.classList.add('open');if(x.rarity==='SSR')st.insertAdjacentHTML('afterbegin','<div class="pl-burst"></div>');picked=x;done()}
  else{st.innerHTML=`<div class="pl-ten">${Array(10).fill(0).map(()=>cardHTML(null,'shake')).join('')}</div>`;const r=await req;await Promise.all([preload(r.cards.map(x=>U(x.thumb))),sleep(RM?0:900)]);
   st.innerHTML=`<div class="pl-ten">${r.cards.map(x=>cardHTML(x)).join('')}</div>`;const gs=[...st.querySelectorAll('.pl-gc')];
   for(let i=0;i<gs.length;i++){await sleep(RM?0:130);gs[i].classList.add('open')}
   const best=r.cards.reduce((a,x,i)=>({SSR:3,SR:2,R:1}[x.rarity]>{SSR:3,SR:2,R:1}[r.cards[a].rarity]?i:a),0);
   const sel=i=>{picked=r.cards[i];gs.forEach((g,k)=>g.classList.toggle('pick',k===i));const b=B.querySelector('#wear');if(b)b.innerHTML=`${picked.kind==='item'?'戴上':'换上'}「${E(picked.name)}」<small>约 40 秒</small>`};
   gs.forEach((g,i)=>g.onclick=()=>sel(i));picked=r.cards[best];done();sel(best);B.querySelector('.pl-note').textContent='点卡片选一套，再让角色换上'}}
 function done(){B.querySelector('.pl-btns').innerHTML=`<button class="pl-btn g" id="again">再抽</button><button class="pl-btn p" id="wear">${picked.kind==='item'?'戴上':'换上'}「${E(picked.name)}」<small>约 40 秒</small></button>`;
  B.querySelector('#again').onclick=idle;B.querySelector('#wear').onclick=wear}
 async function wear(){const card=picked;const res=document.createElement('div');res.className='pl-res';B.innerHTML='';B.appendChild(res);
  // 10-10 木木夕：换装过程做成「原图上闪光 → 新衣服叠化上去」的模拟动画，加载文字「XX 换装中」
  const orig=U((C.cutout||{}).src||C.img);
  res.innerHTML=`<div class="pl-wear ld ${card.rarity.toLowerCase()}"><img class="old" src="${orig}"><i class="sp s1"></i><i class="sp s2"></i><i class="sp s3"></i><i class="sp s4"></i><i class="sp s5"></i></div><div id="wp"></div>`;
  const wv=res.querySelector('.pl-wear');
  try{const {job}=await post('play/outfit/make',{cid:CID,card});const j=await runJob(job,res.querySelector('#wp'),`${E(C.name)} 换装中…`,40,true);
   await preload([U(j.src)]);
   wv.insertAdjacentHTML('beforeend',`<img class="new" src="${U(j.src)}">`);res.querySelector('#wp .ph').textContent=`换好啦！${card.rarity==='SSR'?'✦ ':''}「${card.name}」`;
   wv.classList.remove('ld');void wv.offsetWidth;wv.classList.add('go');await sleep(2300);
   res.innerHTML=`<div class="pl-cmp2"><figure><img src="${U((C.cutout||{}).src||C.img)}"><figcaption>原来</figcaption></figure><figure class="${card.rarity.toLowerCase()}"><img src="${U(j.src)}"><figcaption>${card.rarity==='SSR'?'✦ ':''}${E(card.name)}</figcaption></figure></div>`;   // 10-10 木木夕：两张等大卡片对齐，用原图（不用紧裁的抠图，人物比例才一致）
   addWork({kind:'outfit',src:j.src,title:card.name,rarity:card.rarity});
   B.insertAdjacentHTML('beforeend',`<div class="pl-btns"><button class="pl-btn g" id="again">再抽一套</button><a class="pl-btn" style="display:flex;align-items:center;justify-content:center;text-decoration:none" href="${U(j.src)}" download>保存图片</a></div><p class="pl-note">已放进下面的作品墙</p>`);
   B.querySelector('#again').onclick=idle}
  catch(e){res.innerHTML=`<p class="pl-note" style="color:#ff9b9b">${E(e.message)}</p>`;B.insertAdjacentHTML('beforeend','<div class="pl-btns"><button class="pl-btn g" id="again">回去重抽</button></div>');B.querySelector('#again').onclick=idle}}
 idle()}

/* ===== 2. 运势表情包抽卡机 ===== */
function openFortune(){const B=overlay('今日运势');
 const reel=(w,i)=>`<div class="pl-reel" id="r${i}"><div class="st">${w.map(x=>`<span>${E(x)}</span>`).join('')}</div></div>`;
 const idle=()=>{B.classList.add('pl-fortb');B.innerHTML=`<div class="pl-fpanel">   <!-- 10-10 木木夕：内容别堆在上面 → 签筒面板居中，转轮/印章放大 -->
  <div class="pl-fhead"><img src="${U((C.cutout||{}).src||C.img)}" alt=""><span>${E(C.name)} 给你抽今天的三个关键词</span></div>
  <div class="pl-reels">${[0,1,2].map(i=>reel(['？'],i)).join('')}</div>
  <div class="pl-stamp" id="stp"><div class="pl-lv" id="lv">?</div></div>
  <div class="pl-sign" id="sg"><span class="ph">点下面的按钮，看看今天运气怎么样</span></div></div>
  <div class="pl-tpl" id="tp"></div>
  <div class="pl-btns"><button class="pl-btn" id="go">抽今日运势<small>免费</small></button></div>`;B.querySelector('#go').onclick=draw};
 async function draw(){const go=B.querySelector('#go');go.disabled=true;
  [0,1,2].forEach(i=>{const r=B.querySelector('#r'+i);r.classList.remove('land');r.innerHTML=`<div class="st">${Array(8).fill('？').concat(['？']).map(x=>`<span>${x}</span>`).join('')}</div>`;r.classList.add('spin')});
  const res=await post('play/fortune/draw',{cid:CID}).catch(e=>{alert(e.message);idle()});if(!res)return;
  [0,1,2].forEach(i=>{const r=B.querySelector('#r'+i);r.querySelector('.st').innerHTML=res.reels[i].map(x=>`<span>${E(x)}</span>`).join('')});
  for(let i=0;i<3;i++){await sleep(RM?0:(i?450:900));const r=B.querySelector('#r'+i);r.classList.remove('spin');r.querySelector('.st').innerHTML=`<span>${E(res.keywords[i])}</span>`;r.classList.add('land')}
  await sleep(RM?0:400);const lv=B.querySelector('#lv');lv.className='pl-lv '+res.level;lv.textContent=res.level;B.querySelector('#stp').className='pl-stamp on '+res.level;requestAnimationFrame(()=>lv.classList.add('on'));
  await sleep(RM?0:450);const sg=B.querySelector('#sg');const s=res.sign||'';for(let k=1;k<=s.length;k++){sg.textContent='「'+s.slice(0,k)+(k<s.length?'':'」');await sleep(RM?0:/[，。！？、…]/.test(s[k-1])?160:45)}
  const tp=B.querySelector('#tp');tp.innerHTML=`<img src="${E(res.template.url)}"><p>今天的表情包：${E(res.template.desc)}<br><span style="opacity:.6">换成 ${E(C.name)} 来演</span></p>`;tp.classList.add('on');
  B.querySelector('.pl-btns').innerHTML=`<button class="pl-btn g" id="again">再抽一次</button><button class="pl-btn p" id="mk">生成运势表情包<small>约 30 秒</small></button>`;
  B.querySelector('#again').onclick=idle;B.querySelector('#mk').onclick=()=>make(res)}
 async function make(res){const box=document.createElement('div');box.className='pl-res';B.innerHTML='';B.appendChild(box);   // 运势签上已经有档位和关键词，结果页不再重复
  try{const {job}=await post('play/fortune/make',{cid:CID,template:res.template,level:res.level,keywords:res.keywords,sign:res.sign});const j=await runJob(job,box,`${E(C.name)} 正在演今天的表情包`,35);
   box.innerHTML=`<img class="pl-fcard" src="${U(j.card||j.src)}"><p class="pl-note">长按或点下面按钮保存，分享给朋友</p>`;addWork({kind:'meme',src:j.src,title:'今日运势 · '+res.level});if(j.card)addWork({kind:'fsign',src:j.card,title:'运势签 · '+res.level});
   B.insertAdjacentHTML('beforeend',`<div class="pl-btns"><a class="pl-btn p" style="display:flex;align-items:center;justify-content:center;text-decoration:none" href="${U(j.card||j.src)}" download="今日运势签.jpg">保存运势签</a><a class="pl-btn g" style="display:flex;align-items:center;justify-content:center;text-decoration:none" href="${U(j.src)}" download="运势表情包.webp">只要表情包</a></div><button class="pl-btn g" id="again" style="flex:none;width:100%;margin-top:10px;height:44px">再抽一次</button>`);B.querySelector('#again').onclick=idle}
  catch(e){box.innerHTML=`<p class="pl-note" style="color:#ff9b9b">${E(e.message)}</p>`;B.insertAdjacentHTML('beforeend','<div class="pl-btns"><button class="pl-btn g" id="again">重新抽</button></div>');B.querySelector('#again').onclick=idle}}
 idle()}

/* ===== 3. 角色出场 PV ===== */
async function openPV(){const B=overlay('出场 PV');const old=(C.works||[]).find(w=>w.kind==='pv');let templates=[];try{templates=(await fetch(U('api/play/pv/templates')).then(r=>r.json())).templates||[]}catch(e){B.textContent='模板加载失败，请重新打开';return}let selected=templates[0]?.id||'t04';
 B.innerHTML=`<div class="pl-res">${old?`<video src="${U(old.src)}" controls playsinline></video><p class="pl-note">上一次生成的 PV</p>`:`<img src="${U((C.cutout||{}).src||C.img)}" style="max-height:40vh;background:none">`}</div>
 <p class="pl-note">先看案例，再选喜欢的出场方式。案例角色仅演示镜头效果，生成时使用当前角色。</p><div class="pv-template-grid">${templates.map((t,i)=>`<div class="pv-template ${i?'':'selected'}" data-pv="${E(t.id)}">${t.sample?`<video src="${U(t.sample)}" controls playsinline preload="none"></video>`:'<div class="pv-template-placeholder">${E(t.name)}</div>'}<button type="button"><b>${E(t.name)}</b><small>${E(t.family)} · ${t.duration}秒 · ${E(t.ratio)}</small></button></div>`).join('')}</div>
 <div class="pl-btns"><button class="pl-btn p" id="mk">${old?'再生成一条':'生成出场 PV'}</button></div><p class="pl-note">视频生成成本较高，测试站请勿连续点</p>`;
 B.querySelectorAll('[data-pv] button').forEach(btn=>btn.onclick=()=>{selected=btn.parentElement.dataset.pv;B.querySelectorAll('[data-pv]').forEach(el=>el.classList.toggle('selected',el.dataset.pv===selected))});
 B.querySelector('#mk').onclick=async()=>{if(!confirm('确定生成一条出场 PV 吗？视频成本较高，LP 动画含首尾帧设计，约 3～6 分钟；其他模板约 1～2 分钟。'))return;const box=document.createElement('div');box.className='pl-res';B.innerHTML='';B.appendChild(box);
  try{const {job}=await post('play/pv/make',{cid:CID,template_id:selected});const j=await runJob(job,box,selected==='lp'?'Mari 正在设计角色卡与 LP 动画':'Mari 正在写分镜',selected==='lp'?300:90);
   box.innerHTML=`<video src="${U(j.src)}" controls autoplay playsinline></video><div class="pl-rate" style="margin-top:10px">${E([j.params.CHARACTER_NAME,j.params.STATUS_TEXT_1,j.params.STATUS_TEXT_2].filter(Boolean).join(' · '))}</div>`;
   addWork({kind:'pv',src:j.src,title:'出场 PV'});B.insertAdjacentHTML('beforeend',`<div class="pl-btns"><a class="pl-btn" style="display:flex;align-items:center;justify-content:center;text-decoration:none" href="${U(j.src)}" download>保存视频</a></div>`)}
  catch(e){box.innerHTML=`<p class="pl-note" style="color:#ff9b9b">${E(e.message)}</p>`}}}
})();
