// 每张快照只有一个视频任务；刷新后继续查询，绝不自动重提收费任务。
// 视频完成后，鼠标悬停缩略图会静音循环预览；移开后暂停并回到静帧。点击「播放视频」仍打开完整播放。
(()=>{
const cache=new Map(),pending=new Set();
const terminal=new Set(['completed','failed','blocked','unknown']);
const hoverMedia=matchMedia('(hover:hover) and (pointer:fine)');
const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)');
const hoverOK=()=>hoverMedia.matches&&!reducedMotion.matches;
function stopPreview(video){
  if(!video)return;
  video.dataset.playToken='';
  video.classList.remove('is-playing');
  video.pause();
  try{if(video.currentTime)video.currentTime=0}catch(e){}
}
function startPreview(video){
  if(!video||!video.isConnected||!hoverOK()||!video.dataset.src)return;
  const token=String(Date.now())+Math.random();
  video.dataset.playToken=token;
  video.muted=true;
  video.defaultMuted=true;
  if(video.dataset.loaded!==video.dataset.src){
    video.dataset.loaded=video.dataset.src;
    video.src=video.dataset.src;
  }
  const played=video.play();
  if(played&&played.then)played.then(()=>{
    if(!video.isConnected||video.dataset.playToken!==token){video.pause();return}
    video.muted=true;
    video.classList.add('is-playing');
  }).catch(()=>{if(video.dataset.playToken===token)video.classList.remove('is-playing')});
}
function artLink(card){return [...card.querySelectorAll(':scope > a')].find(a=>a.querySelector(':scope > img.snapshot-art'))}
function previewRoot(card,link){return card.classList.contains('story-snapshot')?card:link}
function bindPreview(card,src){
  if(!hoverOK())return;
  const link=artLink(card);
  if(!link||!src)return;
  let video=link.querySelector(':scope > video.snapshot-motion-preview');
  if(!video){
    video=document.createElement('video');
    video.className='snapshot-motion-preview';
    video.muted=true;
    video.defaultMuted=true;
    video.loop=true;
    video.playsInline=true;
    video.autoplay=false;
    video.controls=false;
    video.preload='none';
    video.tabIndex=-1;
    video.disableRemotePlayback=true;
    video.setAttribute('muted','');
    video.setAttribute('loop','');
    video.setAttribute('playsinline','');
    video.setAttribute('webkit-playsinline','');
    video.setAttribute('aria-hidden','true');
    const img=link.querySelector('img.snapshot-art');
    if(img){
      video.poster=img.currentSrc||img.src;
      const look=getComputedStyle(img);
      video.style.objectFit=look.objectFit;
      video.style.backgroundColor=look.backgroundColor;
    }
    video.addEventListener('loadeddata',()=>{if(!video.dataset.playToken)video.pause()});
    link.append(video);
    const root=previewRoot(card,link);
    if(!root.dataset.motionHover){
      root.dataset.motionHover='1';
      const current=()=>link.querySelector(':scope > video.snapshot-motion-preview');
      root.addEventListener('pointerenter',()=>startPreview(current()));
      root.addEventListener('pointerleave',()=>stopPreview(current()));
    }
    link.addEventListener('click',()=>stopPreview(video));
  }
  if(video.dataset.src!==src){
    stopPreview(video);
    video.dataset.src=src;
    video.dataset.loaded='';
    video.removeAttribute('src');
    try{video.load()}catch(e){}
  }
  if(previewRoot(card,link).matches(':hover'))startPreview(video);
}
function clearPreview(card){if(!card)return;card.querySelectorAll('video.snapshot-motion-preview').forEach(video=>{stopPreview(video);video.remove()})}
function popup(src){document.querySelectorAll('video.snapshot-motion-preview').forEach(stopPreview);const d=document.createElement('dialog');d.className='snapshot-lightbox';const v=document.createElement('video');v.src=src;v.controls=true;v.playsInline=true;v.style.cssText='max-width:94vw;max-height:88vh;width:auto;object-fit:contain';const b=document.createElement('button');b.className='snapshot-lightbox-close';b.textContent='×';b.setAttribute('aria-label','关闭视频');b.onclick=()=>d.close();const a=document.createElement("a");a.href=src;a.download="剧情快照.mp4";a.textContent="下载视频 ↓";a.style.cssText="position:fixed;bottom:20px;left:24px;color:white";d.append(v,b,a);d.onclick=e=>{if(e.target===d)d.close()};d.onclose=()=>{v.pause();d.remove()};document.body.append(d);d.showModal();b.focus()}
function paint(id,j){cache.set(id,j);document.querySelectorAll('[data-motion-id="'+id+'"]').forEach(b=>{b.disabled=!!j&& !terminal.has(j.status)&&j.status!=='none';b.textContent=j?.status==='completed'?'播放视频 ▷':j?.status==='blocked'?'此片段暂不支持动画':j&&j.status!=='none'&&!terminal.has(j.status)?(j.phase||'生成有声视频中…'):j&&terminal.has(j.status)?'查看生成状态':'动起来 ▷';const card=b.closest('.snapshot-card');if(!card)return;if(j?.status==='completed'&&j.src)bindPreview(card,j.src);else clearPreview(card);});}
async function poll(id,create=false){if(pending.has(id))return;pending.add(id);try{let r=await fetch('api/snapshots/'+id+'/motion',create?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({confirmed:true})}:{});let j=await r.json();if(!r.ok)throw Error(j.error||'暂时无法生成');paint(id,j);if(create&&j.error)alert(j.error);if(!terminal.has(j.status)&&j.status!=='none'){setTimeout(()=>poll(id),5000)}}catch(e){if(create)alert(e.message)}finally{pending.delete(id)}}
function scan(){document.querySelectorAll('.snapshot-card a[href*="/share"]').forEach(a=>{const id=a.getAttribute('href').match(/snapshots\/([a-f0-9]{32})\/share/)?.[1];if(!id||a.parentElement.querySelector('[data-motion-id]'))return;const b=document.createElement('button');b.type='button';b.dataset.motionId=id;b.textContent='动起来 ▷';a.after(b);b.onclick=()=>{const j=cache.get(id);if(j?.status==='completed'){popup(j.src);return}if(j&&terminal.has(j.status)){alert(j.error||'此任务未完成，请联系管理员核对。');return}if(confirm('将这张快照生成 5 秒、768P 有声视频。\n实际费用由测试站供应商账户承担，暂不扣用户积分。\n预计需要数分钟，提交后可继续聊天。是否生成？'))poll(id,true)};if(cache.has(id))paint(id,cache.get(id));else poll(id);});}
reducedMotion.addEventListener('change',()=>{document.querySelectorAll('video.snapshot-motion-preview').forEach(video=>{stopPreview(video);video.remove()});if(hoverOK())cache.forEach((job,id)=>paint(id,job))});
document.addEventListener('visibilitychange',()=>{document.querySelectorAll('video.snapshot-motion-preview').forEach(video=>{const link=video.parentElement,card=video.closest('.snapshot-card'),root=card&&link?previewRoot(card,link):null;if(document.hidden||!root||!root.matches(':hover'))stopPreview(video);else startPreview(video)})});
new MutationObserver(scan).observe(document.body,{childList:true,subtree:true});scan();
})();
