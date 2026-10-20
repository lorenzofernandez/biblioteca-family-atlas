'use strict';
(()=>{
 const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;if(cls)n.className=cls;return n;};
 const navBase=new URL('.',document.currentScript.src);
 const file=location.pathname.split('/').filter(Boolean).pop()||'index.html',isAuthors=/^authors(?:\.html)?$/.test(file),isBooks=/^books(?:\.html)?$/.test(file);
 const nav=el('nav',null,'library-navigation');nav.setAttribute('aria-label','Main navigation');
 const home=el('a','La Biblioteca','library-home');home.href=navBase.href;nav.append(home);
 for(const [text,url,active] of [['The Authors','authors.html',isAuthors||new URL(location.href).searchParams.get('return')==='authors'],['The Catalogue','cards.html?catalogue=1#many',new URL(location.href).searchParams.has('catalogue')&&new URL(location.href).searchParams.get('return')!=='authors']]){const a=el('a',text);a.href=new URL(url,navBase).href;if(active)a.setAttribute('aria-current','page');nav.append(a);}document.body.prepend(nav);document.body.classList.add('has-library-navigation');
 if(!isAuthors&&!isBooks)return;
 document.body.classList.add('library-directory');
 const setup=()=>{
  const grid=document.querySelector(isAuthors?'#authorGrid':'#bookGrid');if(!grid)return false;
  const section=isAuthors?grid.closest('section'):grid.closest('.book-directory');section.classList.add('library-browser');
  if(isAuthors){document.querySelector('#authorApp').classList.add('directory-only');section.querySelector('h2').textContent='The Authors.';}else section.querySelector('h1').textContent='The Books.';
  document.body.classList.toggle('books-grid-only',isBooks);
  const tools=section.querySelector(isAuthors?'.directory-toolbar':'.book-tools');
  const panel=el('aside',null,'library-filter-panel');panel.hidden=false;panel.setAttribute('aria-label',isAuthors?'Filter authors':'Filter books');
  const heading=el('div',null,'library-filter-heading');heading.append(el('h2',isAuthors?'Filter the authors.':'Filter the books.'));const close=el('button','Hide filters');close.type='button';close.setAttribute('aria-label','Close filters');heading.append(close);panel.append(heading,tools);document.body.append(panel);
  const toggle=el('button',null,'library-filter-toggle');toggle.type='button';toggle.setAttribute('aria-label','Search and filter '+(isAuthors?'authors':'books'));toggle.textContent='Filters';toggle.setAttribute('aria-expanded','true');toggle.hidden=true;document.body.append(toggle);
  const showFilters=open=>{panel.hidden=!open;toggle.setAttribute('aria-expanded',String(open));toggle.hidden=open;document.body.classList.toggle('directory-filters-hidden',!open);if(open)tools.querySelector('input')?.focus();};toggle.onclick=()=>showFilters(panel.hidden);close.onclick=()=>showFilters(false);document.addEventListener('keydown',e=>{if(e.key==='Escape')tools.querySelector('input')?.blur();});
  const switcher=el('div',null,'library-view-switch library-browse-toolbar');switcher.setAttribute('role','group');switcher.setAttribute('aria-label','Catalogue view');document.body.append(switcher);
  const buttons=[];let mode=new URL(location.href).searchParams.get('view')||sessionStorage.getItem('biblioteca-directory-view')||'grid';let zoom=1;
  let board;import('./library-board.mjs?v=return-2').then(({createBoard})=>{board=createBoard(grid);board.setList(mode==='list');});
  const baseColumns=()=>innerWidth<650?2:innerWidth<1000?3:isBooks?5:4;
  const applyZoom=()=>{grid.style.setProperty('--browse-columns',Math.max(1,Math.round(baseColumns()/zoom)));};
  const zoomButtons=[];
  const setView=value=>{mode=value;board?.setList(value==='list');grid.classList.toggle('library-list',mode==='list');buttons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===mode)));zoomButtons.forEach(b=>b.hidden=mode==='list');sessionStorage.setItem('biblioteca-directory-view',mode);const u=new URL(location.href);u.searchParams.set('view',mode);history.replaceState(history.state,'',u);};
  for(const value of ['grid','list']){const b=el('button',value==='grid'?'Grid':'List');b.type='button';b.dataset.view=value;b.onclick=()=>setView(value);switcher.append(b);buttons.push(b);}
  for(const [label,title,action] of [['−','Zoom out',()=>zoom=Math.max(.4,zoom/1.4)],['Fit','Fit all columns',()=>zoom=1],['+','Zoom in',()=>zoom=Math.min(baseColumns(),zoom*1.4)]]){const b=el('button',label);b.type='button';b.setAttribute('aria-label',title);b.onclick=()=>{action();applyZoom();if(label==='Fit')board?.fit();else board?.zoom(label==='+'?1.5:1/1.5);};switcher.append(b);zoomButtons.push(b);}
  grid.addEventListener('wheel',event=>{if(mode==='list'||!event.ctrlKey)return;event.preventDefault();zoom=Math.max(.4,Math.min(baseColumns(),zoom*Math.exp(-event.deltaY*.003)));applyZoom();},{passive:false});
  window.addEventListener('resize',applyZoom);applyZoom();setView(mode==='list'?'list':'grid');
  return true;
 };
 if(!setup()){const observer=new MutationObserver(()=>{if(setup())observer.disconnect();});observer.observe(document.querySelector(isAuthors?'#authorApp':'#bookApp')||document.body,{childList:true,subtree:true});}
})();
