const clamp=n=>Math.max(0,Math.min(1,n));
const ease=n=>{n=clamp(n);return n*n*(3-2*n);};
const mix=(a,b,t)=>a+(b-a)*t;

// Square area is proportional to mentions. Adjacent edges align; no rotations,
// random offsets, or minimum-size distortion of the counts.
export function createPortraitLayout(authors,width,height){
 const sorted=authors.filter(a=>a.count>0).slice().sort((a,b)=>b.count-a.count||a.id.localeCompare(b.id));
 if(!sorted.length)return [];
 const placed=[],gap=.035,aspect=width/height;
 for(const author of sorted){
  const size=Math.sqrt(author.count/sorted[0].count);
  if(!placed.length){placed.push({...author,x:-size/2,y:-size/2,size});continue;}
  let best=null,bestScore=Infinity;
  for(const other of placed){
   const candidates=[];
   for(const x of [other.x-size-gap,other.x+other.size+gap])for(const y of [other.y,other.y+other.size-size])candidates.push([x,y]);
   for(const y of [other.y-size-gap,other.y+other.size+gap])for(const x of [other.x,other.x+other.size-size])candidates.push([x,y]);
   for(const [x,y] of candidates){
    if(placed.some(p=>x<p.x+p.size+gap-.00001&&x+size+gap>p.x+.00001&&y<p.y+p.size+gap-.00001&&y+size+gap>p.y+.00001))continue;
    const distance=((x+size/2)/aspect)**2+(y+size/2)**2;
    const score=distance+.00001*(Math.abs(x)+Math.abs(y));
    if(score<bestScore){bestScore=score;best={...author,x,y,size};}
   }
  }
  placed.push(best);
 }
 const minX=Math.min(...placed.map(p=>p.x)),maxX=Math.max(...placed.map(p=>p.x+p.size));
 const minY=Math.min(...placed.map(p=>p.y)),maxY=Math.max(...placed.map(p=>p.y+p.size));
 const scale=Math.min(width/(maxX-minX),height/(maxY-minY));
 const offsetX=(width-(maxX-minX)*scale)/2,offsetY=(height-(maxY-minY)*scale)/2;
 const maxDistance=Math.max(...placed.map(p=>Math.hypot((p.x+p.size/2)/aspect,p.y+p.size/2)))||1;
 return placed.map(p=>({...p,distance:Math.hypot((p.x+p.size/2)/aspect,p.y+p.size/2)/maxDistance,
  x:(p.x-minX)*scale+offsetX,y:(p.y-minY)*scale+offsetY,size:p.size*scale}));
}

export async function createAuthorScene({host,onOpen,href,onChange}){
 const response=await fetch('cards-assets/authors.json?v=lifespans-1');if(!response.ok)throw Error('Author portraits could not load');
 const data=await response.json(),board=host.querySelector('.author-portrait-board'),status=host.querySelector('.author-scene-status');
 let width=innerWidth,height=innerHeight,layout=[],phase=0,visible=false,filtered=null;
 let timelineAmount=0,timelineScroll=0,timelineTravel=0,rowHeight=40,timelineAuthors=[],timelineLeft=230,timelineWidth=0;
 const timeline=document.createElement('div');timeline.className='author-life-chart';timeline.setAttribute('aria-label','Lifespans of the authors from the portrait scene');timeline.hidden=true;host.append(timeline);
 const axis=document.createElement('div');axis.className='author-life-axis';const rowViewport=document.createElement('div');rowViewport.className='author-life-viewport';const rows=document.createElement('div');rows.className='author-life-rows';rowViewport.append(rows);timeline.append(axis,rowViewport);
 const chartRows=new Map();
 const tiles=new Map(),fmt=n=>n.toLocaleString('en-US');
 function build(){
  const authors=data.authors.map(a=>({...a,count:filtered?a.records.reduce((n,id)=>n+filtered.has(id),0):a.count})).filter(a=>a.count>0);
  const padding=width<700?18:Math.max(34,width*.045),top=width<700?180:205,bottom=width<700?75:60;
  layout=createPortraitLayout(authors,width-2*padding,height-top-bottom);
  board.style.inset=`${top}px ${padding}px ${bottom}px`;
  board.replaceChildren();tiles.clear();
  timelineAuthors=authors.filter(a=>Number.isFinite(a.birth)&&Number.isFinite(a.death)&&a.death>=a.birth).sort((a,b)=>a.birth-b.birth||a.death-b.death);
  rowHeight=width<700?50:42;timelineLeft=width<700?130:235;timelineWidth=width-padding*2-timelineLeft-18;
  const min=Math.floor((timelineAuthors.length?Math.min(...timelineAuthors.map(a=>a.birth)):1400)/25)*25,max=Math.ceil((timelineAuthors.length?Math.max(...timelineAuthors.map(a=>a.death)):2000)/25)*25,span=Math.max(25,max-min);
  timeline.style.inset=`${top}px ${padding}px ${bottom}px`;axis.style.left=timelineLeft+'px';rows.replaceChildren();axis.replaceChildren();chartRows.clear();
  for(let i=0;i<=5;i++){const tick=document.createElement('span');tick.textContent=String(Math.round(min+span*i/5));tick.style.left=i/5*100+'%';axis.append(tick);}
  for(const [index,a] of timelineAuthors.entries()){
   const row=document.createElement('div');row.className='author-life-row';row.style.height=rowHeight+'px';
   const name=document.createElement('a');name.className='author-life-name';name.href=href(a.id);name.textContent=a.name;name.title=a.name+' · '+a.birth+'–'+a.death+' · '+a.confidence+' identity confidence';name.onclick=e=>{if(e.button||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;e.preventDefault();onOpen(a.id);};
   const dot=document.createElement('i');dot.className='author-life-dot '+a.confidence;name.prepend(dot);name.style.width=(timelineLeft-46)+'px';
   const bar=document.createElement('a');bar.className='author-life-bar';bar.href=href(a.id);bar.title=name.title;bar.setAttribute('aria-label',name.title+'. Open author.');bar.style.left=(timelineLeft+(a.birth-min)/span*timelineWidth)+'px';bar.style.width=Math.max(2,(a.death-a.birth)/span*timelineWidth)+'px';bar.onclick=name.onclick;
   const dates=document.createElement('span');dates.className='author-life-dates';dates.textContent=a.birth+'–'+a.death;bar.append(dates);row.append(name,bar);rows.append(row);chartRows.set(a.id,{index,row});
  }
  timelineTravel=Math.max(0,timelineAuthors.length*rowHeight-(height-top-bottom-40));

  for(const author of layout){
   const tile=document.createElement('a');tile.className='author-portrait-tile';tile.href=href(author.id);tile.dataset.authorId=author.id;tile.dataset.count=String(author.count);
   tile.setAttribute('aria-label',`${author.name}, ${fmt(author.count)} catalogue mentions. Open author.`);
   tile.title=`${author.name} · ${fmt(author.count)} catalogue mentions · ${author.confidence} identity confidence`;
   const initials=document.createElement('span');initials.className='author-portrait-initials';initials.textContent=author.name.split(/\s+/).filter(Boolean).map(p=>p[0]).slice(0,2).join('');initials.setAttribute('aria-hidden','true');tile.append(initials);
   if(author.portrait){const img=new Image();img.alt=`Reference image for ${author.name}`;img.decoding='async';img.referrerPolicy='no-referrer';img.src=author.portrait;img.onload=()=>tile.classList.add('has-image');img.onerror=()=>{img.remove();tile.classList.add('image-unavailable');};tile.append(img);}
   const caption=document.createElement('span');caption.className='author-portrait-label';const name=document.createElement('strong');name.textContent=author.name;const count=document.createElement('small');count.textContent=fmt(author.count)+' mentions';caption.append(name,count);tile.append(caption);
   tile.style.width=tile.style.height=author.size+'px';tile.classList.toggle('show-label',author.size>=130);
   tile.addEventListener('click',event=>{if(event.button||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;event.preventDefault();onOpen(author.id);});
   tile.addEventListener('focus',()=>{status.textContent=`${author.name} · ${fmt(author.count)} catalogue mentions`;});
   tile.addEventListener('pointerenter',()=>{status.textContent=`${author.name} · ${fmt(author.count)} catalogue mentions`;});
   tile.addEventListener('pointerleave',resetStatus);tile.addEventListener('blur',resetStatus);
   board.append(tile);tiles.set(author.id,tile);
  }
  host.dataset.authorCount=String(layout.length);resetStatus();render(phase,visible);
 }
 function resetStatus(){status.textContent=layout.length?`${layout.length} most-mentioned profiles${filtered?' · matching your filters':''}`:'No featured authors match these filters.';}
 function render(value,enabled=true,reduced=false,life=timelineAmount,travel=timelineScroll){
  timelineAmount=life;timelineScroll=travel;
  phase=value;visible=enabled;host.hidden=!enabled;host.inert=!enabled||(!reduced&&value<.4);
  if(!enabled)return;
  const boardWidth=board.clientWidth,boardHeight=board.clientHeight;
  const blend=reduced?(life>.5?1:0):life,pan=Math.min(timelineTravel,travel);
  timeline.hidden=blend<.01;timeline.style.opacity=String(ease((blend-.3)/.7));timeline.inert=blend<.9;rows.style.transform=`translate3d(0,${-pan}px,0)`;
  status.parentElement.style.opacity=String(1-blend);host.classList.toggle('showing-lifespans',blend>.5);

  for(const author of layout){
   const tile=tiles.get(author.id),delay=author.distance*.38,t=reduced?1:ease((value-delay)/(1-delay));
   const chart=chartRows.get(author.id),rowY=chart?40+chart.index*rowHeight-pan:boardHeight+author.size;
   const visibleRow=rowY+rowHeight>38&&rowY<boardHeight;
   tile.style.opacity=String(ease((t-.08)/.48)*(chart?(blend>.99&&!visibleRow?0:1):1-blend));
   const size=mix(author.size,28,blend),x=mix(mix((boardWidth-author.size)/2,author.x,t),0,blend),y=mix(mix((boardHeight-author.size)/2,author.y,t),rowY+Math.max(0,(rowHeight-28)/2),blend);
   tile.style.width=tile.style.height=size+'px';tile.style.transform=`translate3d(${x}px,${y}px,0) scale(${mix(.12,1,t)})`;
   tile.querySelector('.author-portrait-label').style.opacity=blend>.01?'0':'';

   tile.style.zIndex=String(layout.length-layout.indexOf(author));tile.tabIndex=t>.9&&(blend<.99||visibleRow)?0:-1;tile.style.pointerEvents=t>.9&&(blend<.99||visibleRow)?'auto':'none';
  }
  host.dataset.reveal=value.toFixed(3);
 }
 function resize(w,h){width=w;height=h;build();}
 function setFilter(ids){filtered=ids?new Set(ids):null;build();}
 build();onChange();return {render,resize,setFilter,get timelineTravel(){return timelineTravel;}};
}
