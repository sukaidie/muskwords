'use strict';
const $ = (id) => document.getElementById(id);
const PAGE_SIZE = 60;
const CONTEXT_PAGE_SIZE = 20;
const state = {data:null, onlySaved:false, saved:new Set(), page:1, detailRequest:0};
const cefrLevels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];
const jsonCache = new Map();
try {state.saved = new Set(JSON.parse(localStorage.getItem('muskwords-saved')||'[]'));} catch (_) {}
const escapeHTML = (v) => String(v??'').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const say = (word) => {if('speechSynthesis' in window){speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(word);u.lang='en-US';u.rate=.86;speechSynthesis.speak(u);}};
function matchesLevel(wordLevel, selected) {
  if (selected === 'all') return true;
  if (!selected.endsWith('+')) return wordLevel === selected;
  const minimum = cefrLevels.indexOf(selected.slice(0, -1));
  return minimum >= 0 && cefrLevels.indexOf(wordLevel) >= minimum;
}
function cachedJSON(url) {
  if (state.data?.assetVersion) url += (url.includes('?')?'&':'?')+'v='+encodeURIComponent(state.data.assetVersion);
  if (!jsonCache.has(url)) {
    const request = fetch(url).then(response => {
      if (!response.ok) throw Error('HTTP ' + response.status);
      return response.json();
    }).catch(error => {jsonCache.delete(url); throw error;});
    jsonCache.set(url, request);
  }
  return jsonCache.get(url);
}
function getRows() {
  const term=$('search').value.trim().toLowerCase();
  const level=$('level').value;
  const rows=state.data.words.filter(w=>(w.word.includes(term)||w.zh.toLowerCase().includes(term))&&matchesLevel(w.level,level)&&(!state.onlySaved||state.saved.has(w.word)));
  const sort=$('sort').value;
  if(sort==='alphabet') rows.sort((a,b)=>a.word.localeCompare(b.word));
  else if(sort==='reverse') rows.sort((a,b)=>b.word.localeCompare(a.word));
  else rows.sort((a,b)=>b.count-a.count||a.word.localeCompare(b.word));
  return rows;
}
function toggleSaved(word) {
  state.saved.has(word)?state.saved.delete(word):state.saved.add(word);
  try {localStorage.setItem('muskwords-saved',JSON.stringify([...state.saved]));} catch (_) {}
  render(false);
}
function postHTML(post) {
  const inferred=post.typeBasis==='text_inference'?'（存档推断）':'';
  return `<div class="sample"><time>${escapeHTML(post.date)} · ${post.type==='reply'?'回复':'原创帖'}${inferred}</time><p>${escapeHTML(post.text)}</p><a href="${escapeHTML(post.url)}" target="_blank" rel="noopener noreferrer">在 X 查看 ↗</a><a href="${escapeHTML(post.source)}" target="_blank" rel="noopener noreferrer">查看数据来源 ↗</a></div>`;
}
function openWord(word) {
  const entry=state.data.words.find(item=>item.word===word);
  if (!entry) return;
  const request=++state.detailRequest;
  let ids=null, index=null, shown=0;
  $('detailBody').innerHTML=`<div class="overline">WORD DETAILS</div><h2 class="dialogword">${escapeHTML(entry.word)} <button class="speak" id="speakBtn">▶ 发音</button></h2><p class="notice">${escapeHTML(entry.phonetic)} · ${escapeHTML(entry.level)} · ${entry.count} 次出现 / ${entry.postCount} 条帖子</p><p class="dialogzh">${escapeHTML(entry.zh)}</p><h3>帖子语境 · 数据来源</h3><p class="notice">词频基于当前收录记录，并非马斯克全部历史词频；第三方存档尚未逐条与 X 核对。中文释义与 CEFR 等级为人工学习参考。</p><div id="contextPosts"></div><p id="contextStatus" class="notice" aria-live="polite">正在读取语境…</p><button class="ghost" id="moreContexts">加载语境</button>`;
  $('speakBtn').onclick=()=>say(entry.word);
  if (!$('detail').open) $('detail').showModal();
  async function loadNext() {
    if (request!==state.detailRequest) return;
    $('moreContexts').disabled=true;
    $('contextStatus').textContent='正在读取语境…';
    try {
      if (!ids) {
        const [contexts, postIndex] = await Promise.all([
          cachedJSON(state.data.contextBase+entry.word[0]+'.json'),
          cachedJSON(state.data.postIndex)
        ]);
        if (request!==state.detailRequest) return;
        ids=contexts[entry.word]; index=postIndex;
        if (!ids || ids.length!==entry.postCount) throw Error('语境索引与词库不一致，请刷新页面');
      }
      const next=ids.slice(shown, shown+CONTEXT_PAGE_SIZE);
      const chunks=[...new Set(next.map(id=>index[id]))];
      if (chunks.includes(undefined)) throw Error('帖子索引缺失');
      const bodies=await Promise.all(chunks.map(name=>cachedJSON(state.data.postBase+name)));
      if (request!==state.detailRequest) return;
      const posts=Object.assign({}, ...bodies);
      const records=next.map(id=>posts[id]);
      if (records.some(post=>!post)) throw Error('帖子记录缺失');
      $('contextPosts').insertAdjacentHTML('beforeend',records.map(postHTML).join(''));
      shown+=next.length;
      $('contextStatus').textContent=`已显示 ${shown} / ${ids.length} 条语境（按帖子 ID 从新到旧）`;
      $('moreContexts').hidden=shown>=ids.length;
      $('moreContexts').textContent='再显示 20 条语境';
    } catch (error) {
      if (request!==state.detailRequest) return;
      $('contextStatus').textContent='语境读取失败：'+error.message;
      $('moreContexts').textContent='重试读取语境';
    } finally {
      if (request===state.detailRequest) $('moreContexts').disabled=false;
    }
  }
  $('moreContexts').onclick=loadNext;
  loadNext();
}
function render(resetPage=true) {
  if (!state.data) return;
  if (resetPage) state.page=1;
  const rows=getRows();
  const pageCount=Math.max(1,Math.ceil(rows.length/PAGE_SIZE));
  state.page=Math.min(state.page,pageCount);
  const offset=(state.page-1)*PAGE_SIZE;
  const visible=rows.slice(offset,offset+PAGE_SIZE);
  $('resultCount').textContent=`· ${rows.length.toLocaleString('zh-CN')} 个结果`;
  $('savedBtn').textContent=state.onlySaved?'★ 查看全部':'☆ 我的收藏';
  $('savedBtn').setAttribute('aria-pressed',String(state.onlySaved));
  $('empty').hidden=rows.length!==0;
  $('pagination').hidden=rows.length===0;
  $('pageStatus').textContent=`第 ${state.page} / ${pageCount} 页 · 显示 ${rows.length?offset+1:0}–${offset+visible.length}，共 ${rows.length.toLocaleString('zh-CN')} 词`;
  $('prevPage').disabled=state.page<=1;
  $('nextPage').disabled=state.page>=pageCount;
  $('wordgrid').innerHTML=visible.map(w=>`<article class="word" data-word="${escapeHTML(w.word)}" tabindex="0" role="button" aria-label="查看 ${escapeHTML(w.word)}"><div class="wordhead"><span class="wordname">${escapeHTML(w.word)}</span><span class="level">${escapeHTML(w.level)}</span></div><div class="phonetic">${escapeHTML(w.phonetic)||'&nbsp;'}</div><div class="translation">${escapeHTML(w.zh)}</div><div class="wordfoot"><span>↗ 出现 ${w.count} 次 · ${w.postCount} 帖</span><button class="fav ${state.saved.has(w.word)?'is-saved':''}" data-save="${escapeHTML(w.word)}" aria-label="${state.saved.has(w.word)?'取消收藏':'收藏'} ${escapeHTML(w.word)}">${state.saved.has(w.word)?'★':'☆'}</button></div></article>`).join('');
}
$('wordgrid').addEventListener('click',event=>{
  const save=event.target.closest('[data-save]');
  if(save){toggleSaved(save.dataset.save);return;}
  const card=event.target.closest('[data-word]');
  if(card) openWord(card.dataset.word);
});
$('wordgrid').addEventListener('keydown',event=>{
  if((event.key==='Enter'||event.key===' ')&&event.target.matches('[data-word]')){event.preventDefault();openWord(event.target.dataset.word);}
});
['search','sort','level'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',()=>render()));
$('savedBtn').addEventListener('click',()=>{state.onlySaved=!state.onlySaved;render();});
for (const [id,delta] of [['prevPage',-1],['nextPage',1]]) {
  $(id).onclick=()=>{state.page+=delta;render(false);$('wordgrid').scrollIntoView({block:'start'});};
}
$('closeDialog').onclick=()=>$('detail').close();
$('detail').addEventListener('close',()=>{state.detailRequest++;});
$('exportBtn').onclick=()=>{
  if (!state.data) return;
  const rows=getRows();
  const esc=value=>'"'+String(value??'').replaceAll('"','""')+'"';
  const csv='\ufeff'+[['word','chinese','frequency','posts','level','phonetic'],...rows.map(w=>[w.word,w.zh,w.count,w.postCount,w.level,w.phonetic])].map(row=>row.map(esc).join(',')).join('\r\n');
  const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
  const anchor=document.createElement('a');anchor.href=url;anchor.download='muskwords-sample.csv';anchor.click();
  setTimeout(()=>URL.revokeObjectURL(url),500);
};
cachedJSON('./data/words.json?v=archive-v3').then(data=>{
  state.data=data;
  const metadata=data.metadata;
  $('stats').innerHTML=[[metadata.postCount,'收录帖子'],[metadata.wordCount,'不同词形'],[metadata.tokenCount,'累计词次'],[metadata.missingTranslations,'待补充中文释义']].map(([num,label])=>`<div class="stat"><strong>${Number(num).toLocaleString('zh-CN')}</strong><span>${label}</span></div>`).join('');
  $('coverage').textContent=`覆盖范围：${metadata.coverage} · ${metadata.policy}`;
  $('countingPolicy').textContent=metadata.countingPolicy;
  render();
}).catch(error=>{$('coverage').textContent='数据读取失败，请使用 Web 服务器或 GitHub Pages 打开。'+error.message;});
