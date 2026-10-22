'use strict';
(async()=>{
 const $=s=>document.querySelector(s),el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;if(cls)n.className=cls;return n;};
 const level=a=>a.confidence?.identity?.level||a.confidence?.overall||'unresolved';
 const name=a=>a.displayName||a.name,normalize=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 const href=a=>'cards.html?author='+encodeURIComponent(a.id)+'&authorView=full#authors';
 let selected=null,limit=80;
 try{
 const data=await fetch('author-lifespans-data.json').then(r=>{if(!r.ok)throw Error('Life dates unavailable');return r.json();});
 const valid=data.authors.filter(a=>Number.isInteger(a.birth)&&Number.isInteger(a.death)&&a.birth>0&&a.death>=a.birth&&a.death-a.birth<=125);
 const overlap=(a,b)=>{const start=Math.max(a.birth+($('#adult').checked?20:0),b.birth+($('#adult').checked?20:0)),end=Math.min(a.death,b.death);return {start,end,years:Math.max(0,end-start)};};
 function choose(a){selected=a;$('#query').value='';limit=80;render();}
 function render(){
  const query=normalize($('#query').value),period=$('#period').value,certainty=$('#certainty').value;
  let pool=valid.filter(a=>(certainty==='all'||certainty==='high'&&level(a)==='high'||certainty==='strong'&&['high','medium'].includes(level(a)))&&(period==='all'||period==='early'&&a.birth<1750||period==='middle'&&a.birth>=1750&&a.birth<1850||period==='modern'&&a.birth>=1850)&&normalize([name(a),...(a.origins||[]),...(a.aliases||[])].join(' ')).includes(query));
  if(selected)pool=pool.filter(a=>a.id===selected.id||overlap(a,selected).years>0);
  pool.sort((a,b)=>selected?(b.id===selected.id)-(a.id===selected.id)||overlap(b,selected).years-overlap(a,selected).years||b.recordCount-a.recordCount:b.recordCount-a.recordCount);
  const shown=pool.slice(0,limit);if(!selected)shown.sort((a,b)=>a.birth-b.birth||a.death-b.death);
  const host=$('#chart');host.replaceChildren();host.scrollTop=0;$('#reset').hidden=!selected;$('#selection').hidden=!selected;
  if(selected){const section=$('#selection');section.replaceChildren(el('h2',name(selected)+' · '+selected.birth+'–'+selected.death),el('p',pool.filter(a=>a.id!==selected.id).length.toLocaleString()+' matching contemporaries'+($('#adult').checked?' with overlapping years aged 20+.':'.')));const profile=el('a','Open author & sources ↗');profile.href=href(selected);section.append(profile);const hints=el('p','Select another bar to compare their shared years. A common country label is only a research lead.','note');section.append(hints);}
  $('#status').textContent=shown.length+' of '+pool.length.toLocaleString()+' matching profiles · '+(selected?'ranked by years shared':'most-mentioned authors, ordered by birth');$('#more').hidden=shown.length>=pool.length;
  if(!shown.length){host.append(el('p','No complete lifespans match these filters. Clear the selection or broaden the filters.'));return;}
  const min=Math.floor(Math.min(...shown.map(a=>a.birth),...(selected?[selected.birth]:[]))/25)*25,max=Math.ceil(Math.max(...shown.map(a=>a.death),...(selected?[selected.death]:[]))/25)*25,span=Math.max(25,max-min),x=y=>(y-min)/span*100;
  const axis=el('div',null,'axis');axis.append(el('strong','AUTHOR · SELECT TO COMPARE'));const scale=el('div',null,'axis-scale');for(let i=0;i<=5;i++){const tick=el('span',Math.round(min+span*i/5));tick.style.left=(i*20)+'%';scale.append(tick);}axis.append(scale);host.append(axis);
  for(const a of shown){const row=el('div',null,'life-row'),button=el('button',null,'life-name');button.type='button';button.setAttribute('aria-label','Compare '+name(a));const initials=()=>el('span',name(a).split(/\s+/).slice(0,2).map(n=>n[0]).join(''),'initials');if(a.portrait){const img=el('img');img.src=a.portrait;img.alt='';img.loading='lazy';img.onerror=()=>img.replaceWith(initials());button.append(img);}else button.append(initials());const label=el('span',null,'name-text'),dot=el('i',null,'dot '+level(a));dot.title=level(a)+' identity confidence';label.append(dot,document.createTextNode(name(a)));button.append(label);button.onclick=()=>choose(a);
   const track=el('div',null,'life-track'),bar=el('button',null,'life-bar '+level(a)+(selected?.id===a.id?' selected':''));bar.type='button';bar.style.left=x(a.birth)+'%';bar.style.width=Math.max(.15,(a.death-a.birth)/span*100)+'%';let text=name(a)+' · '+a.birth+'–'+a.death+' · '+level(a)+' identity confidence';
   if(selected&&a.id!==selected.id){const shared=overlap(a,selected);text+=' · '+shared.years+' years shared ('+shared.start+'–'+shared.end+')';const common=(a.origins||[]).filter(c=>(selected.origins||[]).includes(c));if(common.length)text+=' · Shared biographical country: '+common.join(', ');const band=el('i',null,'shared');band.style.left=x(shared.start)+'%';band.style.width=(shared.end-shared.start)/span*100+'%';track.append(band);}
   bar.title=text;bar.setAttribute('aria-label',text);bar.onclick=()=>{if(selected&&selected.id!==a.id){const s=overlap(a,selected);$('#selection').append(el('p',name(selected)+' & '+name(a)+': '+s.years+' shared years, '+s.start+'–'+s.end+( $('#adult').checked?' (both aged 20+).':'.')));const p=el('a','Open '+name(a)+' ↗');p.href=href(a);$('#selection').append(p);}else choose(a);};
   const dates=el('span',a.birth+'–'+a.death,'dates');dates.style.left=x(a.birth)+'%';track.append(bar,dates);row.append(button,track);host.append(row);
  }
 }
 $('#controls').onsubmit=e=>e.preventDefault();for(const id of ['query','period','certainty','adult'])$('#'+id).addEventListener(id==='query'?'input':'change',()=>{limit=80;render();});$('#reset').onclick=()=>{selected=null;limit=80;render();};$('#more').onclick=()=>{limit+=80;render();};
 $('#coverage').textContent=valid.length.toLocaleString()+' of '+data.totalProfiles.toLocaleString()+' catalogue author profiles have complete, usable life dates. Green = high identity confidence; gold = medium; orange = low; gray = unresolved. Names may still include duplicate or uncertain identifications.';
 render();
 }catch(error){$('#status').textContent='Life dates could not load. Please refresh to try again.';console.error(error);}
})();
