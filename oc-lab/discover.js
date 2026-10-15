const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const AUD=['女性向','男性向','不限'],REL=['BL','GL','BG','GB','CB','无CP','其他'],THEMES=['日常','恋爱','冒险','奇幻','悬疑','治愈','病娇','强制爱','SM','近亲关系','其他'];
let characters=[],category='全部',audience='全部',relation='全部',theme='全部',prefs={};
const search=document.getElementById('search'),adult=document.getElementById('adultSwitch');
try{prefs=JSON.parse(localStorage.getItem('oc-preferences-v1')||'{}')}catch(e){}
const status=document.getElementById('resultCount');let loadSeq=0;
function store(){try{localStorage.setItem('oc-preferences-v1',JSON.stringify(prefs))}catch(e){}}
function values(c,k){return c.classification?.[k]||[]}
function tags(c){return [...values(c,'audiences'),...values(c,'relations'),...values(c,'themes')]}
function score(c){return (prefs.audiences||[]).filter(v=>values(c,'audiences').includes(v)).length*4+(prefs.relations||[]).filter(v=>values(c,'relations').includes(v)).length*3+(prefs.themes||[]).filter(v=>values(c,'themes').includes(v)).length*2}
function draw(){const q=search.value.trim().toLowerCase();const filtered=characters.filter(c=>(adult.checked?c.adult_only:!c.adult_only)&&(category==='全部'||c.category===category)&&(audience==='全部'||values(c,'audiences').includes(audience))&&(relation==='全部'||values(c,'relations').includes(relation))&&(theme==='全部'||values(c,'themes').includes(theme))&&!(prefs.avoid||[]).some(v=>tags(c).includes(v))&&[c.name,c.role,c.type,c.summary,...tags(c)].join(' ').toLowerCase().includes(q)).sort((a,b)=>score(b)-score(a));
document.getElementById('characterWall').innerHTML=filtered.map(c=>`<article class="discover-card"><a href="c/${encodeURIComponent(c.id)}"><img src="${esc(adult.checked?(c.nsfw_cover||c.img):c.img)}" alt="${esc(c.name)}" loading="lazy"><div class="card-caption"><b>${esc(c.name)}</b><small>${esc(tags(c).slice(0,4).join(' · ')||c.role||c.type||c.category)}</small></div></a><a class="card-chat" href="chat?cid=${encodeURIComponent(c.id)}" aria-label="和${esc(c.name)}聊天" title="和${esc(c.name)}聊天"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12a9 9 0 0 1-9 9H3l2-5a9 9 0 1 1 16-4Z"/></svg></a></article>`).join('')||'<p class="discover-empty">暂时没有符合这些条件的角色。可以减少筛选，或稍后再看，更多角色正在分类。</p>';
status.textContent=filtered.length+' 个角色'+(adult.checked?' · 成人区':' · 普通区')+(prefs.done?' · 按已选偏好排序':'')+' · 未完成分级的导入卡暂不展示';}
async function load(){const seq=++loadSeq;status.textContent='正在加载角色…';try{const r=await fetch('discover/api/characters'+(adult.checked?'?adult=1':''),{cache:'no-store'});if(r.status===401){location.href='login';return}if(!r.ok)throw Error('角色加载失败');const data=await r.json();if(seq!==loadSeq)return;characters=data.characters;draw()}catch(e){status.textContent=e.message}}
function strip(id,options,set){const box=document.getElementById(id);box.innerHTML=['全部',...options].map(x=>`<button type="button" data-value="${esc(x)}" class="${x==='全部'?'active':''}">${esc(x==='近亲关系'?'近亲关系':x)}</button>`).join('');box.onclick=e=>{const b=e.target.closest('button');if(!b)return;box.querySelectorAll('button').forEach(x=>x.classList.toggle('active',x===b));set(b.dataset.value);draw()}}
strip('audiences',AUD,v=>audience=v);strip('relations',REL,v=>relation=v);strip('themes',THEMES,v=>theme=v);
function preferenceDialog(){
 const dlg=document.createElement('dialog');dlg.className='preference-dialog preference-wizard';
 const draft={audiences:[...(prefs.audiences||[])],relations:[...(prefs.relations||[])],themes:[...(prefs.themes||[])],avoid:[...(prefs.avoid||[])]};
 let step=0,moreRelations=false,tab='themes',saved=false;
 const descriptions={BL:'男生与男生',GL:'女生与女生',BG:'男生与女生',GB:'女方主导的男女关系',无CP:'不以恋爱关系为主'};
 const choice=(key,v,small='')=>`<button type="button" class="preference-choice ${draft[key].includes(v)?'chosen':''}" data-key="${key}" data-choice="${esc(v)}" aria-pressed="${draft[key].includes(v)}"><span>${esc(v)}</span>${small?`<small>${esc(small)}</small>`:''}</button>`;
 const finish=()=>{prefs={...prefs,...draft,done:true};store();saved=true;dlg.close();draw()};
 function paint(){
  const heading=step===0?'先选一个喜欢的方向':step===1?'更喜欢哪种关系？':'再挑一点偏好';
  const hint=step===0?'选喜欢的就好，也可以不限。':step===1?'可以多选，也可以直接开始浏览。':'这些都可以以后再改。';
  let content='';
  if(step===0)content=`<div class="preference-direction">${AUD.map(v=>choice('audiences',v)).join('')}</div>`;
  else if(step===1)content=`<div class="preference-relationship">${(moreRelations?REL:REL.slice(0,4)).map(v=>choice('relations',v,descriptions[v]||'')).join('')}</div><button type="button" class="preference-link" data-action="expand">${moreRelations?'收起':'更多关系'}</button>`;
  else content=`<div class="preference-tabs"><button type="button" data-tab="themes" aria-pressed="${tab==='themes'}">喜欢的剧情</button><button type="button" data-tab="avoid" aria-pressed="${tab==='avoid'}">不想看到</button></div><div class="preference-chips">${[...new Set(tab==='themes'?THEMES:REL.concat(THEMES))].map(v=>choice(tab,v)).join('')}</div>`;
  dlg.innerHTML=`<div class="preference-top"><span>${step===2?'更多偏好':`${step+1} / 2`}</span><button type="button" data-action="close" aria-label="关闭偏好选择">×</button></div><h2>${heading}</h2><p>${hint}</p>${content}<div class="preference-actions">${step===0?'<button type="button" data-action="skip">跳过</button><button type="button" data-action="next">下一步</button>':step===1?'<button type="button" data-action="back">上一步</button><button type="button" data-action="done">开始浏览</button>':'<button type="button" data-action="back">返回</button><button type="button" data-action="done">保存偏好</button>'}</div>${step===1?'<button type="button" class="preference-link preference-more" data-action="more">更多偏好 · 剧情与避开标签</button>':''}`;
 }
 dlg.addEventListener('click',e=>{
  const b=e.target.closest('button');if(!b)return;
  if(b.dataset.choice){const key=b.dataset.key,v=b.dataset.choice;draft[key]=draft[key].includes(v)?draft[key].filter(x=>x!==v):[...draft[key],v];if(key==='audiences'){if(v==='不限'&&draft[key].includes(v))draft[key]=['不限'];else if(v!=='不限')draft[key]=draft[key].filter(x=>x!=='不限')}paint();return}
  if(b.dataset.tab){tab=b.dataset.tab;paint();return}
  switch(b.dataset.action){case 'close':dlg.close();return;case 'next':case 'skip':step=1;break;case 'back':step=Math.max(0,step-1);break;case 'more':step=2;break;case 'expand':moreRelations=!moreRelations;break;case 'done':finish();return}paint();
 });
 dlg.addEventListener('close',()=>{if(!saved){prefs.done=true;store()}dlg.remove()});
 document.body.appendChild(dlg);paint();dlg.showModal();
}
async function enableAdult(){const dlg=document.createElement('dialog');dlg.className='preference-dialog';dlg.innerHTML='<form method="dialog"><h2>进入成人角色区</h2><p>此处包含 NSFW 角色卡。确认你已年满18岁，并愿意查看成人内容。</p><div class="preference-actions"><button value="cancel">取消</button><button value="confirm">已满18岁，继续</button></div></form>';document.body.appendChild(dlg);dlg.showModal();const confirmed=await new Promise(resolve=>dlg.addEventListener('close',()=>resolve(dlg.returnValue==='confirm'),{once:true}));dlg.remove();if(!confirmed)return false;const r=await fetch('discover/api/adult-access',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({confirmed:true})});return r.ok}
search.oninput=draw;
adult.onchange=async()=>{adult.disabled=true;try{if(adult.checked&&!(await enableAdult()))adult.checked=false;if(!adult.checked)await fetch('discover/api/adult-access',{method:'POST',headers:{'Content-Type':'application/json'},body:'{"confirmed":false}'});await load()}finally{adult.disabled=false}};
document.querySelectorAll('[data-category]').forEach(b=>b.onclick=()=>{category=b.dataset.category;document.querySelectorAll('[data-category]').forEach(x=>x.classList.toggle('active',x===b));draw()});
document.getElementById('preferences').onclick=preferenceDialog;
(async()=>{if(new URLSearchParams(location.search).get('adult')==='1'){adult.checked=await enableAdult()}await load();if(!prefs.done&&!adult.checked)preferenceDialog()})();
