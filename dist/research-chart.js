'use strict';
window.renderSourceCoverage=function(data){
 const root=document.querySelector('#sourceCoverageChart'),intro=document.querySelector('#sourceCoverageIntro');
 if(!data){intro.textContent='Source-verification coverage is not available yet.';return;}
 const make=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
 const fmt=n=>n.toLocaleString(),pct=(n,d)=>d?(100*n/d).toFixed(2)+'%':'0.00%';
 const groups=[{key:'verified',label:'Verified book / source match',color:'#3b5b48',note:'Source-checked edition match with high metadata confidence.'},{key:'tentative',label:'Linked · needs verification',color:'#b29650',note:'A possible book, another edition, or a match that still needs checking.'},{key:'unmatched',label:'No external book match yet',color:'#d5d4c7',note:'Original catalogue scan available; no external book/source connection found.'}];
 intro.textContent=fmt(data.linked)+' entries have an external book or source reference. '+fmt(data.verified)+' meet the current verification standard.';
 const card=make('div',undefined,'source-chart-card'),toolbar=make('div',undefined,'source-chart-toolbar'),caption=make('p','Share of catalogue entries'),toggle=make('div',undefined,'source-chart-toggle');toggle.setAttribute('role','group');toggle.setAttribute('aria-label','Chart scope');
 const all=make('button','All entries'),linked=make('button','Linked entries only');all.type=linked.type='button';toggle.append(all,linked);toolbar.append(caption,toggle);card.append(toolbar);
 const layout=make('div',undefined,'source-chart-layout'),visual=make('div',undefined,'source-donut'),legend=make('div',undefined,'source-chart-legend');layout.append(visual,legend);card.append(layout);
 const note=make('p',undefined,'source-chart-note');note.setAttribute('aria-live','polite');card.append(note);
 function draw(linkedOnly){
  const total=linkedOnly?data.linked:data.total,shown=groups.filter(g=>!linkedOnly||g.key!=='unmatched');
  all.setAttribute('aria-pressed',String(!linkedOnly));linked.setAttribute('aria-pressed',String(linkedOnly));
  visual.replaceChildren();legend.replaceChildren();
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 240 240');svg.setAttribute('role','img');svg.setAttribute('aria-label',shown.map(g=>g.label+': '+fmt(data[g.key])+' entries, '+pct(data[g.key],total)).join('. '));
  const R=94,circ=2*Math.PI*R;let offset=0;
  // Arc lengths retain the true proportions; very small verified shares are not enlarged.
  for(const g of [...shown].reverse()){
   const n=data[g.key],len=total?circ*n/total:0,c=document.createElementNS(svg.namespaceURI,'circle');
   for(const [k,v] of Object.entries({cx:120,cy:120,r:R,fill:'none',stroke:g.color,'stroke-width':27,'stroke-dasharray':len+' '+(circ-len),'stroke-dashoffset':-offset,transform:'rotate(-90 120 120)'}))c.setAttribute(k,String(v));
   const title=document.createElementNS(svg.namespaceURI,'title');title.textContent=g.label+': '+fmt(n)+' ('+pct(n,total)+')';c.append(title);svg.append(c);offset+=len;
  }
  visual.append(svg);const center=make('div',undefined,'source-donut-center');center.append(make('b',fmt(data.verified)),make('span','verified entries'),make('small',pct(data.verified,total)+' of '+fmt(total)));visual.append(center);
  shown.forEach(g=>{const row=make('div',undefined,'source-legend-row'),swatch=make('i');swatch.style.background=g.color;swatch.setAttribute('aria-hidden','true');const text=make('div');text.append(make('h3',g.label),make('p',g.note));const count=make('div',undefined,'source-legend-count');count.append(make('b',fmt(data[g.key])),make('small',pct(data[g.key],total)));row.append(swatch,text,count);legend.append(row);});
  note.textContent=linkedOnly?'Zoomed view: percentages use the '+fmt(data.linked)+' linked entries. The '+fmt(data.unmatched)+' unmatched entries are excluded from this view.':pct(data.linked,data.total)+' of the full catalogue has an external reference. The verified slice is very small because only '+fmt(data.verified)+' entries have completed the stricter edition check. This is not the total number of entries with useful information.';
 }
 all.onclick=()=>draw(false);linked.onclick=()=>draw(true);draw(false);
 const method=make('p',data.definition,'source-chart-method');
 const details=make('details',undefined,'verified-records'),summary=make('summary','Inspect the '+fmt(data.verified)+' verified entries');details.append(summary);
 const list=make('ol');(data.verifiedEntries||[]).forEach(entry=>{const li=make('li'),row=make('div'),book=make('a',(entry.year?entry.year+' · ':'')+entry.title);book.href='book.html?id='+entry.id;row.append(book,make('p',entry.basis));const source=make('a','View cited source ↗','verified-source-link');source.href=entry.source.url;source.target='_blank';source.rel='noopener';li.append(row,source);list.append(li);});details.append(list);
 root.replaceChildren(card,method,details);
};
