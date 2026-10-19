'use strict';
(()=>{
 const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;if(cls)n.className=cls;return n;};
 const navBase=new URL('.',document.currentScript.src);
 const file=location.pathname.split('/').filter(Boolean).pop()||'index.html',isAuthors=/^authors(?:\.html)?$/.test(file),isBooks=/^books(?:\.html)?$/.test(file);
 const nav=el('nav',null,'library-navigation');nav.setAttribute('aria-label','Main navigation');
 const home=el('a','La Biblioteca','library-home');home.href=navBase.href;nav.append(home);
 for(const [text,url,active] of [['The Books','books.html',isBooks],['The Authors','authors.html',isAuthors],['The Catalogue','cards.html?catalogue=1#many',new URL(location.href).searchParams.has('catalogue')]]){const a=el('a',text);a.href=new URL(url,navBase).href;if(active)a.setAttribute('aria-current','page');nav.append(a);}document.body.prepend(nav);document.body.classList.add('has-library-navigation');
 if(!isAuthors&&!isBooks)return;
 document.body.classList.add('library-directory');
 const setup=()=>{
  const grid=document.querySelector(isAuthors?'#authorGrid':'#bookGrid');if(!grid)return false;
  const section=isAuthors?grid.closest('section'):grid.closest('.book-directory');section.classList.add('library-browser');
  if(isAuthors){document.querySelector('#authorApp').classList.add('directory-only');section.querySelector('h2').textContent='The Authors.';const lives=el('a','Compare lifespans ↗','library-lifespans-link');lives.href=new URL('author-lifespans.html',navBase).href;section.querySelector('h2').after(lives);}else section.querySelector('h1').textContent='The Books.';
  if(isBooks){document.body.classList.add('books-grid-only');grid.classList.remove('library-list');const u=new URL(location.href);u.searchParams.delete('view');history.replaceState(history.state,'',u);return true;}
  const tools=section.querySelector(isAuthors?'.directory-toolbar':'.book-tools'),switcher=el('div',null,'library-view-switch');switcher.setAttribute('role','group');switcher.setAttribute('aria-label','Display');
  const buttons=[];let mode=new URL(location.href).searchParams.get('view')||sessionStorage.getItem('biblioteca-directory-view')||'grid';
  const setView=value=>{mode=value;grid.classList.toggle('library-list',mode==='list');buttons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===mode)));sessionStorage.setItem('biblioteca-directory-view',mode);const u=new URL(location.href);u.searchParams.set('view',mode);history.replaceState(history.state,'',u);};
  for(const value of ['grid','list']){const b=el('button',value==='grid'?'Grid':'List');b.type='button';b.dataset.view=value;b.onclick=()=>setView(value);switcher.append(b);buttons.push(b);}tools.append(switcher);setView(mode==='list'?'list':'grid');
  return true;
 };
 if(!setup()){const observer=new MutationObserver(()=>{if(setup())observer.disconnect();});observer.observe(document.querySelector(isAuthors?'#authorApp':'#bookApp')||document.body,{childList:true,subtree:true});}
})();
