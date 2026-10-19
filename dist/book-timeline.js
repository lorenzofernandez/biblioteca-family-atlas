'use strict';
window.LibraryBookTimeline={
 mount(host,books){
  const make=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
  const dated=books.filter(b=>Number.isFinite(b.year));if(!dated.length)return;
  const groups=new Map();dated.forEach(b=>{const y=Math.floor(b.year/10)*10;if(!groups.has(y))groups.set(y,[]);groups.get(y).push(b)});
  const rank=b=>Number(!!b.editionVerified)*4+Number(!b.crossReference&&!b.continuation)*2+Number(!!b.image);
  groups.forEach(group=>group.sort((a,b)=>rank(b)-rank(a)||(a.year-b.year)||a.title.localeCompare(b.title)));
  const start=Math.floor(Math.min(...groups.keys())/100)*100,end=Math.floor(Math.max(...groups.keys())/100)*100+99;
  const max=Math.max(...[...groups.values()].map(g=>g.length));
  const box=make('div',undefined,'book-time');box.id='bookTimeline';
  box.append(make('h3','Across time'),make('p','Move sideways through decades, then up or down to scrub through their books. Click to open a book; tap a column for controls.','book-time-intro'));
  const scroll=make('div',undefined,'book-time-scroll'),plot=make('div',undefined,'book-time-plot'),axis=make('div',undefined,'book-time-axis');
  plot.setAttribute('role','group');plot.setAttribute('aria-label','Catalogue timeline by decade');
  const buttons=[],years=[];let selected=null,position=0,token=0,renderTask,mediaTimer,moveFrame,lastPointer,floating=false,pointerInside=false,dragOrigin,dragged=false;
  const preview=make('div',undefined,'book-time-preview');preview.hidden=true;preview.setAttribute('aria-label','Selected timeline record');
  const visual=make('a',undefined,'book-time-visual'),content=make('div',undefined,'book-time-content');
  const date=make('div','','eyebrow'),title=make('h4',''),byline=make('p','','book-time-byline'),credit=make('p','','book-time-credit');
  const actions=make('div',undefined,'book-time-actions'),open=make('a','View book page →','book-time-open'),previous=make('button','←'),next=make('button','→'),counter=make('span','','book-time-counter'),scrubCount=make('div','','book-time-scrub-count');
  previous.type=next.type='button';previous.setAttribute('aria-label','Previous book in this decade');next.setAttribute('aria-label','Next book in this decade');
  previous.disabled=next.disabled=true;actions.append(open,previous,counter,next);
  const close=make('button','×','book-time-close');close.type='button';close.setAttribute('aria-label','Close timeline preview');close.onclick=()=>{buttons.find(b=>Number(b.dataset.decade)===selected)?.focus({preventScroll:true});hidePreview();};
  content.append(date,title,byline,scrubCount,credit,actions);preview.append(close,visual,content);
  const shardCache=new Map(),documents=new Map(),imageCache=new Map();let pdfModule;
  const recordFor=async id=>{const key=id.slice(1,3);if(!shardCache.has(key))shardCache.set(key,LibraryData.json('book-records/'+key+'.json').catch(error=>{shardCache.delete(key);throw error}));const data=await shardCache.get(key);if(shardCache.size>8)shardCache.delete(shardCache.keys().next().value);return data[id];};
  function locate(){
   if(preview.hidden)return;
   const anchor=buttons.find(b=>Number(b.dataset.decade)===selected)?.getBoundingClientRect();
   const point=floating?lastPointer:anchor?{x:anchor.right,y:anchor.top+anchor.height/2}:null;if(!point)return;
   if(!floating&&(anchor.bottom<0||anchor.top>innerHeight)){hidePreview();return;}
   const rect=preview.getBoundingClientRect(),gap=18,pad=12;
   const left=point.x+gap+rect.width<=innerWidth-pad?point.x+gap:point.x-gap-rect.width;
   const top=point.y+gap+rect.height<=innerHeight-pad?point.y+gap:point.y-gap-rect.height;
   preview.style.left=Math.max(pad,Math.min(left,innerWidth-rect.width-pad))+'px';preview.style.top=Math.max(pad,Math.min(top,innerHeight-rect.height-pad))+'px';
  }
  function present(node,text,request,bookId){
   if(request!==token)return;
   visual.replaceChildren(node);visual.removeAttribute('aria-busy');credit.textContent=text;
   imageCache.delete(bookId);imageCache.set(bookId,{node,text});while(imageCache.size>20)imageCache.delete(imageCache.keys().next().value);locate();
  }
  async function card(record,request,bookId){
   if(request!==token)return;
   pdfModule??=import('./vendor/pdfjs/pdf.mjs');const pdfjs=await pdfModule;if(request!==token)return;
   pdfjs.GlobalWorkerOptions.workerSrc=new URL('./vendor/pdfjs/pdf.worker.mjs',location.href).href;
   if(!documents.has(record.file)){
    const task=pdfjs.getDocument({url:record.source,isEvalSupported:false,disableAutoFetch:true,disableStream:true,wasmUrl:new URL('./vendor/pdfjs/wasm/',location.href).href});
    documents.set(record.file,task.promise.catch(error=>{documents.delete(record.file);throw error}));
    while(documents.size>3){const old=documents.keys().next().value,promise=documents.get(old);documents.delete(old);promise.then(d=>d.destroy()).catch(()=>{});}
   }
   const doc=await documents.get(record.file);if(request!==token)return;
   const page=await doc.getPage(record.page);if(request!==token)return;
   const base=page.getViewport({scale:1}),viewport=page.getViewport({scale:Math.min(2,600/base.width)}),canvas=make('canvas');
   canvas.width=Math.ceil(viewport.width);canvas.height=Math.ceil(viewport.height);canvas.setAttribute('role','img');canvas.setAttribute('aria-label','Original catalogue card for '+record.displayTitle+', scan '+record.page);
   renderTask=page.render({canvas,canvasContext:canvas.getContext('2d'),viewport,background:'#ffffff'});await renderTask.promise;
   present(canvas,'Original catalogue card · scan '+record.page,request,bookId);
  }
  async function loadImage(book,request){
   try{
    const record=await recordFor(book.id);if(request!==token)return;
    const image=record.research?.curated&&(record.research.images||[]).find(i=>/cover/i.test(i.label)&&['high','medium'].includes(typeof i.confidence==='object'?i.confidence.level:i.confidence)&&!/different|uncertain|unverified|incomplete/i.test(i.editionRelation||''));
    if(image){
     const img=make('img');img.alt='Reference-copy cover: '+book.title;img.onload=()=>present(img,'Reference-copy cover · another copy of the matched edition',request,book.id);img.onerror=()=>card(record,request,book.id).catch(error=>{if(error.name!=='RenderingCancelledException')unavailable(request)});img.src=image.src;
    }else await card(record,request,book.id);
   }catch(error){if(error.name!=='RenderingCancelledException')unavailable(request)}
  }
  function showBook(){
   const request=++token;clearTimeout(mediaTimer);renderTask?.cancel();renderTask=null;
   const entries=groups.get(selected),book=entries[position];preview.dataset.bookId=book.id;preview.dataset.recordPosition=position+1;preview.dataset.decade=selected;
   date.textContent=book.year+' · '+selected+'–'+(selected+9);title.textContent=book.title;byline.textContent=book.authorNames.join(' · ')||'Author unresolved';
   const href='book.html?id='+book.id;visual.href=open.href=href;visual.setAttribute('aria-label','Open book page: '+book.title);
   counter.textContent=(position+1).toLocaleString()+' / '+entries.length.toLocaleString();scrubCount.textContent='Book '+(position+1).toLocaleString()+' of '+entries.length.toLocaleString()+' · Click column to open';previous.disabled=position===0;next.disabled=position===entries.length-1;
   const cached=imageCache.get(book.id);if(cached){present(cached.node,cached.text,request,book.id);return;}
   visual.setAttribute('aria-busy','true');visual.replaceChildren(make('span','Loading preview…','book-time-empty'));credit.textContent='';
   // Update the title immediately, and wait briefly before fetching scans while scrubbing.
   mediaTimer=setTimeout(()=>loadImage(book,request),floating?90:0);locate();
  }
  function unavailable(request){if(request!==token)return;visual.removeAttribute('aria-busy');visual.replaceChildren(make('span','Preview unavailable','book-time-empty'));credit.textContent='Open the book page for the original scan.';locate();}
  function select(year,index=0){
   const nextPosition=Math.max(0,Math.min(groups.get(year).length-1,index)),changed=selected!==year||position!==nextPosition;
   selected=year;position=nextPosition;buttons.forEach((b,i)=>{b.setAttribute('aria-pressed',String(years[i]===year));b.tabIndex=years[i]===year?0:-1});if(changed)showBook();
  }
  function mode(isFloating){floating=isFloating;preview.classList.toggle('is-floating',floating);preview.classList.toggle('is-anchored',!floating);preview.hidden=false;visual.tabIndex=floating?-1:0;locate();}
  function hidePreview(){pointerInside=false;cancelAnimationFrame(moveFrame);preview.hidden=true;clearTimeout(mediaTimer);++token;renderTask?.cancel();renderTask=null;selected=null;buttons.forEach(b=>b.setAttribute('aria-pressed','false'));}
  function hideFloating(){pointerInside=false;if(floating)hidePreview();}
  function scrub(button,event){
   if(event.pointerType==='touch')return;
   pointerInside=true;lastPointer={x:event.clientX,y:event.clientY};
   if(dragOrigin&&Math.hypot(event.clientX-dragOrigin.x,event.clientY-dragOrigin.y)>6)dragged=true;
   cancelAnimationFrame(moveFrame);moveFrame=requestAnimationFrame(()=>{
    const year=Number(button.dataset.decade),rect=button.getBoundingClientRect(),fraction=Math.max(0,Math.min(1,(lastPointer.y-rect.top)/rect.height));
    mode(true);select(year,Math.min(groups.get(year).length-1,Math.floor(fraction*groups.get(year).length)));locate();
   });
  }
  for(let year=start;year<=end;year+=10){
   const entries=groups.get(year)||[],button=make('button',undefined,'book-time-mark'),bar=make('span');button.type='button';button.dataset.decade=year;button.disabled=!entries.length;button.tabIndex=-1;
   button.setAttribute('aria-label',year+'–'+(year+9)+': '+entries.length.toLocaleString()+' records. Move vertically to scrub books; click to open.');button.setAttribute('aria-pressed','false');bar.style.height=(entries.length?Math.max(3,entries.length/max*126):1)+'px';button.append(bar);plot.append(button);
   if(entries.length){
    years.push(year);buttons.push(button);
    button.addEventListener('pointerenter',event=>scrub(button,event));button.addEventListener('pointermove',event=>scrub(button,event));
    button.addEventListener('pointerdown',event=>{dragOrigin={x:event.clientX,y:event.clientY};dragged=false;});
    button.addEventListener('focus',()=>{if(!pointerInside){mode(false);select(year);}});
    button.addEventListener('click',event=>{dragOrigin=null;if(dragged){dragged=false;return;}if(event.pointerType!=='touch'&&event.detail>0&&floating&&selected===year){location.href='book.html?id='+groups.get(year)[position].id;}else{mode(false);select(year,selected===year?position:0);}});
    button.addEventListener('keydown',event=>{
     if(event.key==='Escape'){hideFloating();preview.hidden=true;return;}
     if(['ArrowUp','ArrowDown'].includes(event.key)){event.preventDefault();pointerInside=false;mode(false);select(year,selected===year?position+(event.key==='ArrowDown'?1:-1):0);return;}
     let at=years.indexOf(year);if(event.key==='ArrowRight')at=Math.min(buttons.length-1,at+1);else if(event.key==='ArrowLeft')at=Math.max(0,at-1);else if(event.key==='Home')at=0;else if(event.key==='End')at=buttons.length-1;else return;
     event.preventDefault();pointerInside=false;mode(false);buttons[at].focus();
    });
   }else button.addEventListener('pointerenter',hideFloating);
  }
  plot.addEventListener('pointerleave',hideFloating);window.addEventListener('scroll',()=>{if(floating)hideFloating();else locate();},{passive:true,capture:true});window.addEventListener('resize',hidePreview);window.addEventListener('blur',hidePreview);
  document.addEventListener('pointerdown',event=>{if(!plot.contains(event.target)&&!preview.contains(event.target))hidePreview();});document.addEventListener('keydown',event=>{if(event.key==='Escape')hidePreview();});
  buttons[0].tabIndex=0;
  for(let year=start;year<=end;year+=100){const tick=make('div');const total=dated.filter(b=>b.year>=year&&b.year<year+100).length;tick.append(make('b',String(year)),make('span',total.toLocaleString()+(total===1?' record':' records')));axis.append(tick);}
  plot.style.gridTemplateColumns='repeat('+((end-start+1)/10)+',minmax(0,1fr))';axis.style.gridTemplateColumns='repeat('+((end-start+1)/100)+',minmax(0,1fr))';
  previous.onclick=()=>{if(position>0){position--;showBook()}};next.onclick=()=>{if(position<groups.get(selected).length-1){position++;showBook()}};
  scroll.append(plot,axis);box.append(scroll,preview,make('p','Dates run left to right; bar height shows records per decade. Move from the top to the bottom of a column to browse its records. Keyboard: left/right changes decade; up/down changes book. Covers show reference copies; otherwise the original catalogue card appears. Detected dates may refer to an edition, a cited work or a serial range.','caption'));host.append(box);
 }
};
