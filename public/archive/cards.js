/* A separate card-first story. All textures are original catalogue scans. */
'use strict';
(async()=>{
 const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
 const catalogueOnly=new URL(location.href).searchParams.has('catalogue');
 document.body.classList.toggle('catalogue-only',catalogueOnly);
 let scrollGuideDismissed=false;
 const dismissScrollGuide=()=>{scrollGuideDismissed=true;$('#interactionGuide').hidden=true;};
 window.addEventListener('wheel',event=>{if(event.deltaY||event.deltaX)dismissScrollGuide();},{passive:true});
 window.addEventListener('touchmove',dismissScrollGuide,{passive:true});
 window.addEventListener('keydown',event=>{if(!event.target.closest('input,textarea,select,[contenteditable=true]')&&['ArrowDown','ArrowUp','PageDown','PageUp','Home','End',' '].includes(event.key))dismissScrollGuide();});
 window.addEventListener('pointerdown',event=>{if(event.clientX>=document.documentElement.clientWidth)dismissScrollGuide();},{passive:true});
 const canvas=$('#cardSpace'),steps=$$('.story-step'),copies=$$('.chapter-copy'),nav=$$('.chapters a'),introWords=$$('.intro-word'),contextCopy=$('#contextIntro'),projectCopy=$('#unfinishedProject'),familyPhotos=$$('#familyPhotographs figure');
 const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x)),mix=(a,b,t)=>a+(b-a)*t,smooth=t=>{t=clamp(t);return t*t*(3-2*t)};
 const fmt=n=>n.toLocaleString('en-US');
 const originalSequenceStart=1.7,originalCardSpan=.25;
 const cataloguerHold=3,labourHold=5,overviewHold=2.6,holds=[0,cataloguerHold,labourHold,overviewHold,.9,1.9,1.6,0];
 const originalSlides=$$('.original-slide'),cataloguerNarrative=$('#cataloguerTitle'),cataloguerIntro=$('#cataloguerIntro'),narrationEnglish=cataloguerNarrative.getAttribute('aria-label'),typedNarrative=$('#typedNarrative'),untypedNarrative=$('#untypedNarrative');
 const narrationItalian='La sua collezione fu catalogata con cura da mia nonna, Edvige Tonolli. Una alla volta, riportò le informazioni su una scheda.';

 let labourTyping=0,originalPhase=0,wallZoomProgress=0,wallTravel=0,wallOpacity=0;
 function drawOriginals(){
  const distance=Math.max(0,(scrollY-chapterTop(1))/H);
  originalPhase=clamp(distance/cataloguerHold);
  const narration=document.documentElement.lang==='it'?narrationItalian:narrationEnglish;
  const typedCount=reduced?narration.length:Math.floor(narration.length*clamp(distance/1));
  typedNarrative.textContent=narration.slice(0,typedCount);untypedNarrative.textContent=narration.slice(typedCount);
  cataloguerNarrative.classList.toggle('is-complete',typedCount===narration.length);
  const border=reduced?(distance>=1.05?1:0):smooth((distance-1.05)/.25),narrativeOpacity=1-smooth((distance-1.45)/.25);
  cataloguerIntro.style.opacity=narrativeOpacity;cataloguerIntro.setAttribute('aria-hidden',String(narrativeOpacity<.05));
  cataloguerIntro.querySelector('svg').style.opacity=border;cataloguerIntro.querySelector('rect').style.strokeDashoffset=1-border;
  cataloguerIntro.dataset.phase=distance<1?'typing':distance<1.3?'outline':distance<1.7?'complete':'scans';
  originalSlides.forEach((node,i)=>{
   const local=(distance-originalSequenceStart)/originalCardSpan-i;
   const opacity=local<0||local>1?0:reduced?1:smooth(local/.12)*(1-smooth((local-.5)/.4));
   node.style.opacity=opacity;node.style.visibility=opacity>.005?'visible':'hidden';node.style.pointerEvents=opacity>.45?'auto':'none';node.tabIndex=opacity>.45?0:-1;
   node.style.transform='translate3d(-50%,-50%,'+(reduced?0:mix(35,-300,clamp(local)))+'px)';
   node.setAttribute('aria-hidden',String(opacity<.45));
  });
  $('#cataloguer').dataset.card=String(Math.min(5,Math.max(0,Math.floor((distance-originalSequenceStart)/originalCardSpan)+1)));
 }

 let W=innerWidth,H=innerHeight,progress=catalogueOnly?3:0,target=catalogueOnly?3:0,raf=0,active=-1,hovered=-1,pointer=null,hoverTimer,modalPool=[],modalIndex=0,selectedCard=-1,focusAmount=0,focusTarget=0,modalAnimation=null,modalClosing=false;
 let cardSearch=null,cardFilterMask=null,reopenSearch=false;
 let routes,authorPanel,routeReady=false,routeQueue=Promise.resolve(),cardById=new Map(),routeError=false;
 let authorScene=null,authorReveal=0,authorRevealTarget=0;
 const matchingIds=ids=>cardSearch?.active?cardSearch.subset(ids||[]):ids;
 const preference=matchMedia('(prefers-reduced-motion: reduce)');let reduced=preference.matches;
 const motion=$('#motionToggle');function setMotion(value){reduced=value;if(motion){motion.setAttribute('aria-pressed',String(value));motion.setAttribute('aria-label',value?'Enable full motion':'Reduce motion')}document.documentElement.classList.toggle('reduced-motion',value);document.documentElement.style.scrollBehavior=value?'auto':'smooth';wake()}
 if(motion)motion.onclick=()=>setMotion(!reduced);preference.addEventListener('change',e=>setMotion(e.matches));
 const typingPromise=fetch('cards-assets/typing.json').then(r=>{if(!r.ok)throw Error('Typing text unavailable');return r.json()}).catch(()=>null);
 const data=await fetch('cards-assets/data.json?v16',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('Card data could not load');return r.json()}).catch(()=>null);
 if(!data){$('#sceneCaption').hidden=false;$('#sceneCaption').textContent='The cards could not load. Refresh to try again.';return;}
 const cards=data.cards,typingData=await typingPromise;
 const {createSquareLayouts,createFilteredWallLayout,timelineRowGap}=await import('./cards-square-layouts.mjs?v=19');
 const minutes=typingData?.minutesPerCard||2,hours=data.total*minutes/60,workingDays=hours/(typingData?.hoursPerDay||8),workingWeeks=workingDays/(typingData?.daysPerWeek||5),workingMonths=workingWeeks/(typingData?.weeksPerMonth||52/12);
 const durations=[{number:'≈ '+fmt(Math.round(hours)),unit:'hours'},{number:'≈ '+fmt(Math.round(workingDays)),unit:'working days'},{number:'≈ '+Math.round(workingMonths),unit:'working months'}];
 const durationNumber=$('#labourNumber'),durationUnit=$('#labourUnit');
 function drawLabour(){
  const distance=Math.max(0,(scrollY-chapterTop(2))/H);
  const zoomStart=labourHold-.35,zoomEnd=(chapterTop(3)-chapterTop(2))/H+overviewHold;
  labourTyping=clamp(distance/labourHold);
  wallTravel=Math.min(distance,zoomEnd);
  wallZoomProgress=clamp((distance-zoomStart)/(zoomEnd-zoomStart));
  wallOpacity=smooth((progress-1.82)/.18);
  const duration=durations[Math.min(2,Math.floor(labourTyping*3))];
  durationNumber.textContent=duration.number;durationUnit.textContent=duration.unit;
  $('#labour').dataset.unit=duration.unit;
  canvas.dataset.typing=wallOpacity>.01?labourTyping.toFixed(3):'inactive';
 }
 $('#selectionNote').textContent='The five featured cards and the typed wall use original scans and catalogue transcriptions. Close views draw on '+fmt(data.shown)+' available card images. The overview, timeline and map use '+fmt(data.total)+' squares, one per scanned catalogue record. The portrait scene shows the 48 most-mentioned authors with identified profiles, with portrait area proportional to linked catalogue records. These include cross-references, not just distinct books. Reference portraits may depict proposed identities; initials mark missing images. In the following lifespan chart, the same authors are arranged by birth year using their biographical birth and death dates. These overlaps do not establish personal acquaintance.';

 const eraKeys=Object.keys(data.centuries).map(Number),byEra=new Map(eraKeys.map(y=>[y,[]])),undated=[];
 // Travel through one continuous, multi-screen timeline before regrouping by publication country.
 const timelineLead=1.15;
 function sizeTimeline(){
  holds[4]=timelineLead+.44+eraKeys.length*timelineRowGap(H)/H+.6;
  steps[4].style.height=((holds[4]+1.4)*H)+'px';
 }
 sizeTimeline();
 const rare=[],unknown=[];cards.forEach((c,i)=>{c.index=i;const era=c.year==null?null:Math.floor(c.year/100)*100;if(byEra.has(era))byEra.get(era).push(i);else undated.push(i);(c.rare?rare:unknown).push(i);});
 function updateEraControls(){
  const host=$('#eraAxis');host.replaceChildren();
  [...eraKeys,null].forEach((era,group)=>{
   const ids=matchingIds(era===null?undated:byEra.get(era)),count=cardSearch?.active?ids.length:era===null?data.undated:data.centuries[era];
   const button=document.createElement('button');button.type='button';button.dataset.group=String(group);
   button.append(document.createTextNode(era===null?'Undated':era+'s'));
   const countNode=document.createElement('span');countNode.textContent=fmt(count);button.append(countNode);
   button.setAttribute('aria-label',(era===null?'Undated':era+' to '+(era+99))+': '+fmt(count)+' records. Explore an original card.');
   button.disabled=!ids?.length;button.onclick=()=>openCard(ids[0],ids);host.append(button);
  });
 }
 updateEraControls();
 const initialImage=new Image(),atlas=new Image();initialImage.src='cards-assets/first-card.jpg';atlas.src='cards-assets/atlas.jpg';
 await Promise.all([initialImage.decode(),atlas.decode()]).catch(()=>{});
 // Close-ups reuse the catalogue PDFs, so the story does not duplicate the archive.
 const scanCache=new Map(),pdfDocuments=new Map(),imageTokens=new WeakMap(),scanJobs=[];
 let pdfModule,scanActive=0,scanToken=0;
 function trimDocuments(){for(const [key,entry] of pdfDocuments){if(pdfDocuments.size<=3)break;if(!entry.users){pdfDocuments.delete(key);entry.promise.then(doc=>doc.destroy()).catch(()=>{})}}}
 async function renderScan(card,width){
  const key=card.id+':'+width;if(scanCache.has(key))return scanCache.get(key);
  pdfModule??=import('./vendor/pdfjs/pdf.mjs');const pdfjs=await pdfModule;
  pdfjs.GlobalWorkerOptions.workerSrc=new URL('./vendor/pdfjs/pdf.worker.mjs',location.href).href;
  const source=''+(card.samplePage?'sources/':'originals/')+card.file,pageNumber=card.samplePage||card.page;
  let entry=pdfDocuments.get(source);
  if(!entry){entry={users:0,promise:pdfjs.getDocument({url:source,isEvalSupported:false,disableAutoFetch:true,disableStream:true,wasmUrl:new URL('./vendor/pdfjs/wasm/',location.href).href}).promise};pdfDocuments.set(source,entry);entry.promise.catch(()=>{if(pdfDocuments.get(source)===entry)pdfDocuments.delete(source)})}
  entry.users++;
  try{const doc=await entry.promise,page=await doc.getPage(pageNumber),base=page.getViewport({scale:1}),viewport=page.getViewport({scale:Math.min(5,width/base.width)}),surface=document.createElement('canvas');surface.width=Math.ceil(viewport.width);surface.height=Math.ceil(viewport.height);await page.render({canvas:surface,canvasContext:surface.getContext('2d'),viewport,background:'#ffffff'}).promise;const result=surface.toDataURL('image/jpeg',.91);surface.width=surface.height=0;scanCache.set(key,result);while(scanCache.size>24)scanCache.delete(scanCache.keys().next().value);return result;}finally{entry.users--;trimDocuments()}
 }
 function drainScans(){while(scanActive<2&&scanJobs.length){const job=scanJobs.shift();if(imageTokens.get(job.img)!==job.token)continue;scanActive++;renderScan(job.card,job.width).then(src=>{if(imageTokens.get(job.img)===job.token){job.img.src=src;job.img.style.opacity='1';job.img.removeAttribute('aria-busy');job.img.dataset.scanReady='true'}}).catch(error=>{if(imageTokens.get(job.img)===job.token){job.img.removeAttribute('aria-busy');job.img.dataset.scanReady='false';job.img.title='Preview only. Open the original scan for the full card.';}console.warn('Original card preview unavailable',error.message)}).finally(()=>{scanActive--;drainScans()})}}
 function scanImage(card,img,width,background=false){
  const token=++scanToken;imageTokens.set(img,token);img.title='';img.style.opacity='1';img.dataset.scanReady='false';
  if(card.index===0){img.src='cards-assets/first-card.jpg';img.removeAttribute('aria-busy');img.dataset.scanReady='true';return;}
  const cached=scanCache.get(card.id+':'+width);if(cached){img.src=cached;img.removeAttribute('aria-busy');img.dataset.scanReady='true';return;}
  if(card.uv){const uv=card.uv,preview=document.createElement('canvas');preview.width=220;preview.height=148;preview.getContext('2d').drawImage(atlas,uv[0]*4096,uv[1]*4096,uv[2]*4096,uv[3]*4096,0,0,220,148);img.src=preview.toDataURL('image/jpeg');}else{img.style.opacity='0';img.removeAttribute('src');}img.setAttribute('aria-busy','true');
  const job={card,img,width,token};if(!background&&width>640)scanJobs.unshift(job);else scanJobs.push(job);drainScans();
 }

 const wallCanvas=$('#wallSpace'),wallContext=wallCanvas.getContext('2d'),massCanvas=document.createElement('canvas'),massContext=massCanvas.getContext('2d');
 const wallTexts=cards.map(card=>{
  const source=typingData?.texts?.[card.id]||[card.author,card.title,card.year||''].filter(Boolean).join('\n'),lines=[];
  source.split(/\r?\n/).forEach(line=>{let rest=line.trim();if(!rest)return;while(rest.length>36){let cut=rest.lastIndexOf(' ',36);if(cut<12)cut=36;lines.push(rest.slice(0,cut));rest=rest.slice(cut).trimStart();}if(rest)lines.push(rest);});
  return lines.slice(0,10);
 });
 let wallGrid,wallView,catalogueCards=[],wallIds=new Int32Array(data.total),wallCellById=new Int32Array(data.total);
 let squareLayouts=[],squarePositions=new Float32Array(data.total*3),squareBitmaps=[],squaresActive=false;
 let filteredWallLayout=null,filterTransition=null;
 let wallBrowsing=catalogueOnly,wallList=false;
 const inSearchMode=()=>catalogueOnly||cardSearch?.isOpen||cardSearch?.active;
 const wallCamera={scale:1,x:0,y:0};
 let wallDrag=null,suppressWallClick=false;
 const canPanWall=()=>inSearchMode()&&wallBrowsing&&!wallList&&wallCamera.scale>1&&!document.querySelector('dialog:modal')&&!authorPanel?.isOpen;
 function updateWallCursor(){
  const canPan=canPanWall();canvas.style.cursor=wallDrag?.moved?'grabbing':canPan?'grab':hovered>=0?'pointer':'default';
  canvas.style.touchAction=canPan?'none':'';
 }
 function finishWallPan(event){
  if(!wallDrag||event&&event.pointerId!==undefined&&event.pointerId!==wallDrag.id)return;
  const drag=wallDrag;wallDrag=null;suppressWallClick=drag.moved;
  if(canvas.hasPointerCapture(drag.id))canvas.releasePointerCapture(drag.id);
  const guide=$('#interactionGuide'),zoomGuide=inSearchMode()&&(wallBrowsing||wallZoomProgress>=.999);
  guide.hidden=scrollGuideDismissed||!!document.querySelector('dialog:modal')||wallList;
  $('#interactionGuideTitle').textContent=zoomGuide?'Scroll to zoom':'Scroll to explore';
  guide.classList.toggle('is-zoom',zoomGuide);
  updateWallCursor();
 }
 function constrainWallCamera(){
  wallCamera.x=clamp(wallCamera.x,W*(1-wallCamera.scale),0);wallCamera.y=clamp(wallCamera.y,H*(1-wallCamera.scale),0);
 }
 function resetWallCamera(){finishWallPan();wallCamera.scale=1;wallCamera.x=wallCamera.y=0;}
 function setWallView(list){
  finishWallPan();
  if(catalogueOnly){const url=new URL(location.href);url.searchParams.set('view',list?'list':'grid');history.replaceState(history.state,'',url);}
  wallBrowsing=true;wallList=list;document.body.classList.add('wall-browsing');document.body.classList.toggle('wall-list',list);
  cardSearch.setListMode(list);$('#cardGridView').setAttribute('aria-pressed',String(!list));$('#cardListToggle').setAttribute('aria-pressed',String(list));$('#cardZoomControls').hidden=list;
  hideHover();showFilterWall();if(list)$('#cardListView').focus({preventScroll:true});
 }
 function leaveWall(){
  if(catalogueOnly){wallBrowsing=true;showFilterWall();return;}
  wallBrowsing=false;wallList=false;cardSearch.setListMode(false);document.body.classList.remove('wall-browsing','wall-list');resetWallCamera();
  $('#cardGridView').setAttribute('aria-pressed','true');$('#cardListToggle').setAttribute('aria-pressed','false');$('#cardZoomControls').hidden=false;hideHover();wake();
 }
 function zoomWall(x,y,factor){
  finishWallPan();
  if(!wallBrowsing)setWallView(false);
  filterTransition=null;
  const next=clamp(wallCamera.scale*factor,1,Math.max(128,400/(wallGrid.cell*.65))),ratio=next/wallCamera.scale;
  // Keep the catalogue coordinate under the pointer fixed while scaling.
  wallCamera.x=x-(x-wallCamera.x)*ratio;wallCamera.y=y-(y-wallCamera.y)*ratio;wallCamera.scale=next;
  if(next===1)resetWallCamera();else constrainWallCamera();hideHover();wake();
 }
 $('#cardGridView').onclick=()=>setWallView(false);$('#cardListToggle').onclick=()=>setWallView(true);
 $('#cardZoomFit').onclick=()=>{resetWallCamera();setWallView(false);};
 $('#cardZoomIn').onclick=()=>zoomWall(W/2,H/2,1.6);$('#cardZoomOut').onclick=()=>zoomWall(W/2,H/2,1/1.6);
 $('#cardContinue').onclick=()=>{cardSearch.hide();leaveWall();history.replaceState(null,'','#time');window.scrollTo({top:chapterTop(4),behavior:'instant'});};
 canvas.addEventListener('wheel',event=>{
  if(!inSearchMode()||wallList||document.querySelector('dialog:modal')||!(wallBrowsing||wallZoomProgress>=.999&&Math.abs(progress-3)<.01))return;
  event.preventDefault();const delta=event.deltaY*(event.deltaMode===1?16:event.deltaMode===2?H:1);
  zoomWall(event.clientX,event.clientY,Math.exp(-clamp(delta,-350,350)*.003));
 },{passive:false});
 const wallScans=new Map(),legibleCardWidth=280;
 let coverMode=catalogueOnly&&new URL(location.href).searchParams.get('display')==='covers',coverRecords=new Map();
 const coverLayer=document.createElement('div');coverLayer.className='catalogue-cover-layer';document.body.append(coverLayer);const coverNodes=new Map();
 fetch('books-data.json').then(r=>r.json()).then(d=>{coverRecords=new Map(d.books.map(b=>[b.id,b]));coverNodes.clear();coverLayer.replaceChildren();wake();}).catch(()=>{});
 $$('input[name=catalogueDisplay]').forEach(input=>{input.checked=input.value===(coverMode?'covers':'cards');input.onchange=()=>{coverMode=input.value==='covers';const u=new URL(location.href);u.searchParams.set('display',coverMode?'covers':'cards');history.replaceState(history.state,'',u);hideHover();wake();};});
 function drawCovers(){
  const visible=new Set();coverLayer.hidden=!coverMode||!catalogueOnly||wallList||selectedCard>=0;
  if(coverLayer.hidden)return;
  for(let id=0;id<squarePositions.length/3;id++){const at=id*3,x=squarePositions[at],y=squarePositions[at+1],size=squarePositions[at+2];if(cardFilterMask&&!cardFilterMask[id]||size<75||x+size/2<0||x-size/2>W||y+size/2<0||y-size/2>H)continue;visible.add(id);let node=coverNodes.get(id);if(!node){const card=cardAt(id),record=coverRecords.get(card.id)||card;node=document.createElement('div');node.className='catalogue-cover';if(record.image){const image=new Image();image.src=record.image;image.alt=record.title;image.onerror=()=>image.replaceWith(LibraryGeneratedCovers.create(record));node.append(image);}else node.append(LibraryGeneratedCovers.create(record));coverNodes.set(id,node);coverLayer.append(node);}node.style.cssText='left:'+(x-size/2)+'px;top:'+(y-size/2)+'px;width:'+size+'px;height:'+size+'px;';}
  for(const [id,node] of coverNodes)if(!visible.has(id)){node.remove();coverNodes.delete(id);}
 }

 let timelineGeometry=null,timelinePan=0,timelinePanTarget=0,geographyData=null,geographyGeometry=null,worldOutlines=null;
 const cardAt=index=>index<cards.length?cards[index]:catalogueCards[index-cards.length];
 const filterReopen=document.createElement('button');filterReopen.className='filter-reopen';filterReopen.type='button';filterReopen.textContent='Filters';filterReopen.hidden=true;filterReopen.onclick=()=>cardSearch.show();document.body.append(filterReopen);
 cardSearch=LibraryCardSearch.create({
  onVisibility:open=>{filterReopen.hidden=open||!catalogueOnly;hideHover();if(open)showFilterWall();else if(!cardSearch.active)leaveWall();wake();},
  onOpen:(index,ids,wasOpen)=>{reopenSearch=wasOpen;openCard(index,ids);},
  onFilter:({active,mask,count})=>{
   if(!active&&!cardSearch.isOpen&&wallBrowsing)leaveWall();
   cardFilterMask=mask;squareBitmaps=[];resetWallCamera();repackFilteredWall(true);hideHover();
   authorScene?.setFilter(mask?Array.from(mask,(included,index)=>included?cardAt(index).id:null).filter(Boolean):null);
   if(wallGrid)renderMassCanvas();
   updateEraControls();if(geographyGeometry)renderGeography();
   wallCanvas.dataset.visibleCount=String(count);wake();
  }
 });
 Promise.all([LibraryData.json('cards-assets/catalogue-index.json'),LibraryData.json('cards-assets/geography.json'),fetch('cards-assets/world-outlines.json').then(r=>{if(!r.ok)throw Error('Map outlines unavailable');return r.json()})]).then(([index,geo,world])=>{
  geographyData=geo;worldOutlines=world;
  const located=geo.matched-(geo.counts.MULTI||0),countryCount=Object.values(geo.countries).filter(c=>c.anchor).length;
  $('#geographyCoverage').textContent=fmt(located)+' cards · '+countryCount+' countries';
  const dateCorrections=new Map((data.dateCorrections||[]).map(entry=>[entry.id,entry.year]));
  catalogueCards=index.cards.map(row=>({id:row[0],title:row[1],author:row[2],year:dateCorrections.has(row[0])?dateCorrections.get(row[0]):row[3],file:index.files[row[4]],page:row[5],rare:false}));
  if(catalogueCards.length+cards.length!==data.total)throw Error('Incomplete catalogue lookup');
  if(wallGrid){buildWallLookup();layoutSquares();}cardSearch.setRecords([...cards,...catalogueCards],geo);if(catalogueOnly){setWallView(new URL(location.href).searchParams.get('view')!=='grid');cardSearch.show();}wallCanvas.dataset.catalogueReady='true';cardById=new Map([...cards,...catalogueCards].map((card,index)=>[card.id,index]));routeReady=true;syncRoute();wake();
 }).catch(error=>{cardSearch.failed();wallCanvas.dataset.catalogueReady='false';console.warn('Catalogue geography unavailable',error.message);$('#sceneCaption').hidden=false;$('#sceneCaption').textContent='The catalogue map could not load. Refresh to try again.'});
 function buildWallLookup(){
  wallIds.fill(-1);wallCellById.fill(-1);
  const g=wallGrid,remaining=[];
  cards.forEach((card,id)=>{
   const col=g.cx-12+id%25,row=g.cy-30+Math.floor(id/25),cell=row*g.columns+col;
   if(col>=0&&col<g.columns&&row>=0&&row<g.rows&&cell<data.total){wallIds[cell]=id;wallCellById[id]=cell;}else remaining.push(id);
  });
  for(let i=0;i<catalogueCards.length;i++)remaining.push(cards.length+i);
  let next=0;for(let cell=0;cell<wallIds.length&&next<remaining.length;cell++)if(wallIds[cell]<0){const id=remaining[next++];wallIds[cell]=id;wallCellById[id]=cell;}
 }
 function layoutWall(){
  const columns=Math.ceil(Math.sqrt(data.total*W/H)),rows=Math.ceil(data.total/columns),cell=Math.min(W*.97/columns,H*.95/rows);
  wallGrid={columns,rows,cell,cx:Math.floor(columns/2),cy:Math.floor(rows/2),zoom:(W<751?255:350)/cell};
  buildWallLookup();
  const dpr=Math.min(devicePixelRatio||1,2);wallCanvas.width=Math.round(W*dpr);wallCanvas.height=Math.round(H*dpr);massCanvas.width=wallCanvas.width;massCanvas.height=wallCanvas.height;
  renderMassCanvas();wallCanvas.dataset.total=String(data.total);layoutSquares();
 }
 function renderMassCanvas(){
  const {columns,rows,cell}=wallGrid,dpr=wallCanvas.width/W,size=cell*.65;
  massContext.setTransform(dpr,0,0,dpr,0,0);massContext.clearRect(0,0,W,H);massContext.fillStyle='#ecebe3';
  for(let i=0;i<data.total;i++){
   if(cardFilterMask&&!cardFilterMask[wallIds[i]])continue;
   const col=i%columns,row=Math.floor(i/columns);massContext.fillRect((W-columns*cell)/2+col*cell+(cell-size)/2,(H-rows*cell)/2+row*cell+(cell-size)/2,size,size);
  }
 }
 function layoutSquares(){
  if(catalogueCards.length+cards.length!==data.total||!wallGrid)return;
  const result=createSquareLayouts({width:W,height:H,records:[...cards,...catalogueCards],wallIds,grid:wallGrid,eras:eraKeys,geography:geographyData});
  squareLayouts=result.layouts;squareBitmaps=[];repackFilteredWall();timelineGeometry=result.timeline;geographyGeometry=result.geography;renderGeography();
  timelinePanTarget=clamp((scrollY-chapterTop(4))-H*timelineLead,0,timelineGeometry.maxPan);
  timelinePan=timelinePanTarget;
  for(const era of eraKeys)byEra.set(era,result.byEra.get(era));
  undated.splice(0,undated.length,...result.byEra.get(null));
  rare.splice(0,rare.length,...result.rare);unknown.splice(0,unknown.length,...result.unknown);
  updateEraControls();
  wallCanvas.dataset.timelineCounts=JSON.stringify([...result.byEra.values()].map(ids=>ids.length));
  wallCanvas.dataset.geographyCounts=JSON.stringify(Object.fromEntries([...geographyGeometry.groups].map(([code,ids])=>[code,ids.length])));
 }

 function repackFilteredWall(animate=false){
  if(!squareLayouts.length)return;
  const ids=cardFilterMask?Array.from(wallIds).filter(id=>id>=0&&cardFilterMask[id]):[];
  filteredWallLayout=cardFilterMask?createFilteredWallLayout({width:W,height:H,ids,base:squareLayouts[0]}):null;
  filterTransition=animate&&!reduced&&squaresActive&&Math.abs(progress-3)<.01?{from:squarePositions.slice(),started:performance.now()}:null;
 }

 function prepareWallScans(){
  const eligible=new Set();
  if(progress>=2.999&&progress<3.6&&!wallList)for(let at=0;at<squarePositions.length;at+=3){
   const id=at/3,x=squarePositions[at],y=squarePositions[at+1],size=squarePositions[at+2];
   if((!cardFilterMask||cardFilterMask[id])&&size>=legibleCardWidth&&x+size/2>0&&x-size/2<W&&y+size/2>0&&y-size/2<H)eligible.add(id);
  }
  for(const [id,entry] of wallScans)if(!eligible.has(id)){imageTokens.delete(entry.image);entry.image.onload=null;entry.image.removeAttribute('src');wallScans.delete(id);}
  for(const id of eligible){
   const width=Math.min(1400,Math.max(640,Math.ceil(squarePositions[id*3+2]*Math.min(devicePixelRatio||1,2)/160)*160));
   let entry=wallScans.get(id);
   if(entry&&entry.width>=width)continue;
   if(entry){imageTokens.delete(entry.image);entry.image.onload=null;}
   const image=new Image();entry={image,width,ready:false,loadedAt:0};wallScans.set(id,entry);
   image.onload=()=>{if(wallScans.get(id)!==entry||image.dataset.scanReady!=='true')return;entry.ready=true;entry.loadedAt=performance.now();wake();};
   scanImage(cardAt(id),image,width,true);
  }
  wallCanvas.dataset.scanCandidates=String(eligible.size);
 }
 function drawWallScans(ctx){
  let shown=0;
  if(progress>=2.999&&progress<3.6){
   for(const [id,entry] of wallScans){
    if(!entry.ready)continue;
    const at=id*3,x=squarePositions[at],y=squarePositions[at+1],size=squarePositions[at+2];
    const opacity=smooth((size-legibleCardWidth)/40)*(1-smooth((progress-3.1)/.4));
    if(opacity<=0||x+size/2<0||x-size/2>W||y+size/2<0||y-size/2>H)continue;
    const fade=reduced?1:clamp((performance.now()-entry.loadedAt)/260),image=entry.image;
    const scale=Math.min((size-8)/image.naturalWidth,(size-8)/image.naturalHeight),w=image.naturalWidth*scale,h=image.naturalHeight*scale;
    ctx.globalAlpha=opacity*fade;ctx.fillStyle='#fff';ctx.fillRect(x-size/2,y-size/2,size,size);ctx.drawImage(image,x-w/2,y-h/2,w,h);ctx.globalAlpha=1;
    shown++;if(fade<1)wake();
   }
  }
  wallCanvas.dataset.scanCount=String(shown);
 }

 function renderGeography(){
  const svg=$('#geographyMap'),labels=$('#countryLabels'),select=$('#countryBrowser'),g=geographyGeometry;
  svg.replaceChildren();labels.replaceChildren();select.replaceChildren(new Option('Choose a country',''));
  svg.setAttribute('viewBox','0 0 '+W+' '+H);
  const ns='http://www.w3.org/2000/svg';
  const element=(name,attrs)=>{const node=document.createElementNS(ns,name);for(const [k,v] of Object.entries(attrs))node.setAttribute(k,v);return node;};
  worldOutlines.countries.forEach(country=>{
   const path=country.polygons.map(polygon=>polygon.map(ring=>ring.map((point,i)=>{const [x,y]=g.project(point);return(i?'L':'M')+x.toFixed(2)+','+y.toFixed(2)}).join('')+'Z').join('')).join('');
   svg.append(element('path',{d:path,class:'country-outline','data-country':country.code}));
  });
  g.blocks.forEach(block=>{
   const {code}=block,ids=matchingIds(block.ids);
   if(block.anchor){
    const end=[block.x+block.width/2,block.y+block.height];
    svg.append(element('path',{d:'M'+block.anchor.join(',')+'L'+end.join(','),class:'country-leader'}));
    svg.append(element('circle',{cx:block.anchor[0],cy:block.anchor[1],r:1.7,class:'country-anchor'}));
   }
   if(block.labelled){
    const button=document.createElement('button');button.type='button';button.dataset.country=code;
    button.className='country-label'+(block.tray?' country-tray':'');button.style.left=block.labelX+'px';button.style.top=block.labelY+'px';
    const name=document.createElement('span');name.textContent=code==='USA'?'United States':code==='GBR'?'UK':block.name;
    const count=document.createElement('strong');count.textContent=fmt(ids.length);button.append(name,count);
    button.disabled=!ids.length;button.setAttribute('aria-label',block.name+': '+fmt(ids.length)+' cards. Explore original cards.');button.onclick=()=>openCard(ids[0],ids);
    labels.append(button);
   }
  });
  [...g.groups].sort((a,b)=>geographyData.countries[a[0]].name.localeCompare(geographyData.countries[b[0]].name)).forEach(([code,allIds])=>{const ids=matchingIds(allIds);if(ids.length)select.append(new Option(geographyData.countries[code].name+' · '+fmt(ids.length),code));});
  select.onchange=()=>{const ids=matchingIds(g.groups.get(select.value));if(ids?.length)openCard(ids[0],ids);select.value='';};
 }
 function squareOrigin(id){
  if(id<0||id>=data.total||!squaresActive)return null;
  const at=id*3;return{id,x:squarePositions[at],y:squarePositions[at+1],w:squarePositions[at+2],h:squarePositions[at+2],z:1,angle:0};
 }
 function pickSquare(x,y){
  let nearest=-1,distance=Infinity;
  for(let id=0;id<data.total;id++){
   if(cardFilterMask&&!cardFilterMask[id])continue;
   const at=id*3,dx=x-squarePositions[at],dy=y-squarePositions[at+1],radius=Math.max(3.5,squarePositions[at+2]/2);
   if(Math.abs(dx)>radius||Math.abs(dy)>radius)continue;
   const candidate=dx*dx+dy*dy;if(candidate<distance){nearest=id;distance=candidate;}
  }
  return nearest;
 }
 function drawSquareScene(){
  const ctx=wallContext,dpr=wallCanvas.width/W;
  const from=reduced?clamp(Math.round(progress)-3,0,2):clamp(Math.floor(progress)-3,0,2);
  const to=Math.min(2,from+1),amount=reduced?0:smooth((progress-(from+3)-.1)/.8);
  const layoutAt=index=>index===0&&filteredWallLayout?filteredWallLayout:squareLayouts[index];
  const a=layoutAt(from),b=layoutAt(to),settled=amount===0?from:amount===1?to:-1;
  if(settled>=0){
   squarePositions.set(layoutAt(settled));
   if(settled===1)for(let i=1;i<squarePositions.length;i+=3)squarePositions[i]-=timelinePan;
  }else for(let i=0;i<squarePositions.length;i++){
   const pan=i%3===1?timelinePan:0;
   squarePositions[i]=mix(a[i]-(from===1?pan:0),b[i]-(to===1?pan:0),amount);
  }
  let packing=false;
  if(filterTransition){
   const fraction=reduced?1:clamp((performance.now()-filterTransition.started)/420);
   if(fraction<1&&settled===0){
    const ease=1-Math.pow(1-fraction,3);packing=true;
    for(let i=0;i<squarePositions.length;i++)squarePositions[i]=mix(filterTransition.from[i],squarePositions[i],ease);
    wake();
   }else filterTransition=null;
  }
  const cameraActive=settled===0&&wallBrowsing&&wallCamera.scale!==1;
  if(cameraActive)for(let at=0;at<squarePositions.length;at+=3){squarePositions[at]=squarePositions[at]*wallCamera.scale+wallCamera.x;squarePositions[at+1]=squarePositions[at+1]*wallCamera.scale+wallCamera.y;squarePositions[at+2]*=wallCamera.scale;}
  wallCanvas.dataset.cameraScale=String(wallCamera.scale);wallCanvas.dataset.cameraX=String(wallCamera.x);wallCanvas.dataset.cameraY=String(wallCamera.y);
  prepareWallScans();$('#cardZoomOut').disabled=wallCamera.scale===1;
  wallCanvas.dataset.packing=String(packing);wallCanvas.dataset.filteredLayout=String(!!filteredWallLayout);
  ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,W,H);ctx.save();
  if(focusAmount>0){const origin=squareOrigin(selectedCard)||{x:W/2,y:H/2};ctx.translate(origin.x,origin.y);ctx.scale(1+focusAmount*2,1+focusAmount*2);ctx.translate(-origin.x,-origin.y);}
  if(settled>=0&&settled!==1&&!packing&&!cameraActive){
   if(!squareBitmaps[settled]){
    const bitmap=document.createElement('canvas');bitmap.width=wallCanvas.width;bitmap.height=wallCanvas.height;
    const cached=bitmap.getContext('2d');cached.setTransform(dpr,0,0,dpr,0,0);cached.fillStyle='#ecebe3';
    for(let i=0;i<squarePositions.length;i+=3){if(cardFilterMask&&!cardFilterMask[i/3])continue;const size=squarePositions[i+2];cached.fillRect(squarePositions[i]-size/2,squarePositions[i+1]-size/2,size,size);}
    squareBitmaps[settled]=bitmap;
   }
   ctx.drawImage(squareBitmaps[settled],0,0,W,H);
  }else{
   ctx.fillStyle='#ecebe3';
   for(let i=0;i<squarePositions.length;i+=3){if(cardFilterMask&&!cardFilterMask[i/3])continue;const x=squarePositions[i],y=squarePositions[i+1],size=squarePositions[i+2];if(y+size<0||y-size>H||x+size<0||x-size>W)continue;ctx.fillRect(x-size/2,y-size/2,size,size);}
  }
  drawWallScans(ctx);ctx.restore();
  const selected=squareOrigin(hovered);
  if(selected&&focusAmount<.01){const size=Math.max(5,selected.w);ctx.strokeStyle='#e4cea0';ctx.lineWidth=1.5;ctx.strokeRect(selected.x-size/2,selected.y-size/2,size,size);}
  wallCanvas.dataset.phase=['overview','timeline','geography','authors'][Math.round(progress)-3]||'overview';
  wallCanvas.dataset.squareCount=String(data.total);wallCanvas.dataset.transition=amount.toFixed(3);
 }
 function drawWall(){
  const sceneFade=1-smooth((progress-5.25)/.65);
  wallCanvas.style.opacity=wallOpacity*(1-focusAmount*.8)*sceneFade;squaresActive=squareLayouts.length>0&&(wallZoomProgress>=.999||progress>3.001);
  if(sceneFade===0){wallCanvas.dataset.phase='authors';return;}
  if(wallOpacity<.005||!wallGrid)return;
  if(squaresActive){drawSquareScene();return;}
  const ctx=wallContext,g=wallGrid,dpr=wallCanvas.width/W,ease=smooth(wallZoomProgress),zoom=reduced?(progress>=3?1:g.zoom):Math.exp(Math.log(g.zoom)*(1-ease));
  const cell=g.cell*zoom,aspect=mix(.66,1,ease),cardWidth=cell*mix(.9,.65,ease),cardHeight=cardWidth*aspect;
  // Continue travelling through the wall while pulling back from that same viewpoint.
  // Recenter only near the overview, when the cards are already small.
  const reframe=smooth((wallZoomProgress-.65)/.35);
  const pan=reduced?0:wallTravel*H*.34*(zoom/g.zoom)*(1-reframe);
  const originX=W/2-g.columns*cell/2,originY=H/2-g.rows*cell/2-pan;
  wallView={originX,originY,cell,cardWidth,cardHeight};
  ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,W,H);
  const bitmapMix=smooth((12-cell)/6);
  if(bitmapMix>0){ctx.globalAlpha=bitmapMix;ctx.drawImage(massCanvas,W/2-W*zoom/2,H/2-H*zoom/2-pan,W*zoom,H*zoom);}
  if(bitmapMix<1){
   const minCol=Math.max(0,Math.floor(-originX/cell)),maxCol=Math.min(g.columns-1,Math.ceil((W-originX)/cell));
   const minRow=Math.max(0,Math.floor(-originY/cell)),maxRow=Math.min(g.rows-1,Math.ceil((H-originY)/cell));
   for(let row=minRow;row<=maxRow;row++)for(let col=minCol;col<=maxCol;col++){
    const recordIndex=row*g.columns+col;if(recordIndex>=data.total||cardFilterMask&&!cardFilterMask[wallIds[recordIndex]])continue;
    let x=originX+(col+.5)*cell,y=originY+(row+.5)*cell;const dx=x-W/2,dy=y-H/2,length=Math.hypot(dx,dy)||1;x+=dx/length*W*.55*focusAmount;y+=dy/length*H*.55*focusAmount;const left=x-cardWidth/2,top=y-cardHeight/2;
    ctx.globalAlpha=(1-bitmapMix)*.76;ctx.strokeStyle='#eee';ctx.lineWidth=Math.max(.5,Math.min(1,cardWidth/300));ctx.strokeRect(left,top,cardWidth,cardHeight);
    // Featured cells retain their transcription; every cell resolves to its own catalogue record.
    const slot=(row-g.cy+30)*25+(col-g.cx+12),id=slot>=0&&slot<cards.length&&Math.abs(col-g.cx)<=12?slot:-1;
    if(cardWidth>45&&id>=0){
     const delay=(row-g.cy+2)*.11+(col-g.cx+2)*.014;
     const typed=reduced||progress>=3?1:clamp((labourTyping-delay)/.28),lines=wallTexts[id];
     let letters=Math.floor(lines.reduce((n,line)=>n+line.length,0)*typed);
     ctx.font=(cardWidth*.032)+'px "Courier New",monospace';ctx.fillStyle='#fff';ctx.textBaseline='top';ctx.globalAlpha=(1-bitmapMix)*.9;
     lines.forEach((line,n)=>{const visible=line.slice(0,Math.max(0,letters));letters-=line.length;ctx.fillText(visible,left+cardWidth*.065,top+cardHeight*.09+n*cardHeight*.075);});
    }
   }
  }
  const selected=wallOrigin(hovered);if(selected&&focusAmount<.01){ctx.globalAlpha=1;ctx.strokeStyle='#e4cea0';ctx.lineWidth=1.5;ctx.strokeRect(selected.x-Math.max(4,selected.w)/2,selected.y-Math.max(4,selected.h)/2,Math.max(4,selected.w),Math.max(4,selected.h));}
  ctx.globalAlpha=1;wallCanvas.dataset.zoom=zoom.toFixed(3);wallCanvas.dataset.pan=pan.toFixed(1);wallCanvas.dataset.phase=wallZoomProgress<=0?'typing':wallZoomProgress<1?'zooming':'overview';
 }
 function wallOrigin(id){
  if(squaresActive)return squareOrigin(id);
  if(id<0||!wallView||wallOpacity<=.5||wallCellById[id]<0)return null;
  const cell=wallCellById[id],v=wallView;return{id,x:v.originX+(cell%wallGrid.columns+.5)*v.cell,y:v.originY+(Math.floor(cell/wallGrid.columns)+.5)*v.cell,w:v.cardWidth,h:v.cardHeight,z:1,angle:0};
 }
 function pickWall(x,y){
  if(squaresActive)return pickSquare(x,y);
  if(!wallView||wallOpacity<=.5)return -1;
  const v=wallView,col=Math.floor((x-v.originX)/v.cell),row=Math.floor((y-v.originY)/v.cell);
  if(col<0||col>=wallGrid.columns||row<0||row>=wallGrid.rows)return -1;
  const cell=row*wallGrid.columns+col;const id=cell<wallIds.length?wallIds[cell]:-1;return cardFilterMask&&!cardFilterMask[id]?-1:id;
 }

 let projected=[];
 function showFilterWall(){window.scrollTo({top:Math.ceil(chapterTop(3)+H*overviewHold),behavior:'instant'});target=progress=3;wake();}
 function resize(){
  W=innerWidth;H=innerHeight;sizeTimeline();
  const storyCardWidth=Math.min(760,W*.84,H*.62/(866/1440));
  document.documentElement.style.setProperty('--story-card-width',storyCardWidth+'px');
  resetWallCamera();layoutWall();authorScene?.resize(W,H);if(authorScene)steps[7].style.height=(authorScene.timelineTravel+H*1.6)+'px';if(cardSearch?.isOpen||wallBrowsing)showFilterWall();onScroll();
 }
 function chapterTop(index){return steps[index].offsetTop}
 function onScroll(){
  authorRevealTarget=clamp((scrollY-chapterTop(6)+H*.65)/(H*2));
  if(wallBrowsing){target=progress=3;wake();return;}
  if(scrollY<chapterTop(1))target=clamp((scrollY-chapterTop(1)+H*1.4)/(H*1.4),0,1);
  else{target=7;for(let i=1;i<7;i++){const end=chapterTop(i)+H*holds[i];if(scrollY<chapterTop(i+1)){target=i+clamp((scrollY-end)/(1.4*H));break;}}}
  timelinePanTarget=timelineGeometry?clamp((scrollY-chapterTop(4))-H*timelineLead,0,timelineGeometry.maxPan):0;
  hideHover();wake();
 }
 function wake(){if(!raf)raf=requestAnimationFrame(frame)}
 function frame(){
  raf=0;focusAmount=reduced?focusTarget:mix(focusAmount,focusTarget,.105);if(Math.abs(focusAmount-focusTarget)<.001)focusAmount=focusTarget;progress=reduced?target:mix(progress,target,.14);if(Math.abs(progress-target)<.0003)progress=target;
  authorReveal=reduced?authorRevealTarget:mix(authorReveal,authorRevealTarget,.14);if(Math.abs(authorReveal-authorRevealTarget)<.001)authorReveal=authorRevealTarget;
  timelinePan=reduced?timelinePanTarget:mix(timelinePan,timelinePanTarget,.14);
  if(Math.abs(timelinePan-timelinePanTarget)<.05)timelinePan=timelinePanTarget;
  const timelineDistance=(scrollY-chapterTop(4))/H;
  const openingDistance=scrollY/H;
  const contextOpacity=reduced?(openingDistance<.64?1:0):1-smooth((openingDistance-.1)/.58);
  contextCopy.style.opacity=contextOpacity;contextCopy.style.visibility=contextOpacity>.01?'visible':'hidden';
  contextCopy.setAttribute('aria-hidden',String(contextOpacity<.01));contextCopy.inert=contextOpacity<.6;
  const projectOpacity=reduced?(openingDistance>=2.3&&openingDistance<3.65?1:0):smooth((openingDistance-2.05)/.4)*(1-smooth((openingDistance-3.45)/.5));
  projectCopy.style.opacity=projectOpacity;projectCopy.style.visibility=projectOpacity>.01?'visible':'hidden';projectCopy.setAttribute('aria-hidden',String(projectOpacity<.01));
  const photoEnd=(scrollY-chapterTop(1))/H;
  const photoOpacity=(1-smooth((photoEnd-1.5)/.65))*(1-focusAmount)*(cardSearch?.isOpen||wallBrowsing?0:1);
  $('#familyPhotographs').style.opacity=photoOpacity;$('#familyPhotographs').style.visibility=photoOpacity>.01?'visible':'hidden';
  familyPhotos.forEach(photo=>{const y=reduced?Number(photo.dataset.start)*H: Number(photo.dataset.start)*H-scrollY*Number(photo.dataset.speed);photo.style.transform='translate3d(0,'+y+'px,0)';});
  const stage=Math.round(progress);
  if(stage!==active){active=stage;document.body.dataset.chapter=String(stage);nav.forEach((a,i)=>{if(i===stage)a.setAttribute('aria-current','step');else a.removeAttribute('aria-current')});$('.stage-shade').style.background=stage===1||stage===5?'none':stage===2?(W<751?'linear-gradient(#000e 6%,#000d 35%,transparent 72%)':'linear-gradient(90deg,#000e 7%,#000d 30%,#0005 53%,transparent 76%)'):stage===3||stage===4?'radial-gradient(ellipse at center,#000f 0%,#000c 20%,transparent 58%)':stage>=4&&stage<=5?'linear-gradient(#000 8%,#000e 28%,transparent 42%)':'linear-gradient(90deg,#000e,rgba(0,0,0,.12) 65%,transparent)';}
  drawOriginals();drawLabour();if(cardSearch?.isOpen||wallBrowsing){wallZoomProgress=1;wallOpacity=1;}
  let narrationOpacity=0;
  copies.forEach((copy,i)=>{
   let opacity=reduced?(i===stage?1:0):smooth(clamp(1-Math.abs(progress-i)/.49));
   if(i===0)opacity*=(reduced?(openingDistance>=.64&&openingDistance<2.1?1:0):smooth((openingDistance-.64)/.36)*(1-smooth((openingDistance-1.85)/.35)));
   if(i===3)opacity*=cardSearch?.isOpen||cardSearch?.active||wallBrowsing?0:smooth((wallZoomProgress-.6)/.32);
   if(i===4)opacity*=1-smooth((timelineDistance-.5)/.55);
   copy.style.opacity=opacity;copy.style.visibility=opacity>.01?'visible':'hidden';
   if(i!==1&&i!==6&&i!==7&&opacity>.01)narrationOpacity=Math.max(narrationOpacity,opacity);
   copy.style.transform=i===0?'translate3d(-50%,calc(-50% + '+(reduced?0:-progress*24)+'px),0)':i===1?'none':i===3||i===4?'translate3d(-50%,-50%,0)':reduced?'none':'translateY('+((i-progress)*24)+'px)';
   copy.setAttribute('aria-hidden',String(i!==stage||opacity<.01));copy.inert=i!==stage||opacity<.01;
  });
  narrationOpacity=Math.max(narrationOpacity,contextOpacity,projectOpacity);
  $('.stage-shade').style.opacity=.8*narrationOpacity*(1-focusAmount);
  const reading=clamp((scrollY-H*.74)/(H*.86));introWords.forEach((word,i)=>{word.style.opacity=reduced?1:mix(.12,1,smooth((reading*(introWords.length+2)-i+2)/4));});
  const timelineLabels=$('#timelineLabels'),axisOpacity=clamp(1-Math.abs(progress-4)/.3)*smooth((timelineDistance-.75)/.3);
  timelineLabels.hidden=axisOpacity<.01;timelineLabels.style.opacity=axisOpacity;timelineLabels.inert=axisOpacity<.6;
  if(timelineGeometry){
   const axis=$('#eraAxis');
   axis.style.setProperty('--axis-top',Math.max(0,timelineGeometry.rowCenters[0]-timelinePan)+'px');
   axis.style.setProperty('--axis-bottom',Math.min(H,timelineGeometry.rowCenters.at(-1)-timelinePan)+'px');
   [...axis.children].forEach((button,i)=>{
    const y=timelineGeometry.rowCenters[i]-timelinePan,visible=y>-45&&y<H+45;
    button.style.top=y+'px';button.hidden=!visible;button.tabIndex=visible&&axisOpacity>=.6?0:-1;
   });
  }
  wallCanvas.dataset.timelinePan=timelinePan.toFixed(1);
  for(const [node,index] of [[$('#geographyLabels'),5]]){const opacity=clamp(1-Math.abs(progress-index)/.3);node.hidden=opacity<.05;node.style.opacity=opacity;node.inert=opacity<.6;}
  $('#geographyMap').style.opacity=smooth(clamp(1-Math.abs(progress-5)/.8))*(1-focusAmount);
  $('#scrollProgress').style.transform='scaleX('+clamp(scrollY/(chapterTop(7)+steps[7].offsetHeight-H))+')';
  $('#cardViewToolbar').hidden=!(inSearchMode()&&(wallBrowsing||progress>2.8&&progress<3.05));
  const guide=$('#interactionGuide'),zoomGuide=inSearchMode()&&(wallBrowsing||wallZoomProgress>=.999);
  guide.hidden=scrollGuideDismissed||!!document.querySelector('dialog:modal')||wallList;
  $('#interactionGuideTitle').textContent=zoomGuide?'Scroll to zoom':'Scroll to explore';
  guide.classList.toggle('is-zoom',zoomGuide);
  updateWallCursor();
  projected=[];drawWall();drawCovers();authorScene?.render(authorReveal,progress>5.4&&!wallBrowsing&&!cardSearch?.isOpen,reduced,smooth(progress-6),Math.max(0,scrollY-chapterTop(7)-H*.3));
  if(Math.abs(progress-target)>.0003||focusAmount!==focusTarget||timelinePan!==timelinePanTarget||authorReveal!==authorRevealTarget)wake();
 }
 const tooltip=$('#hoverCard');let highlighted=-1;
 function hideHover(){clearTimeout(hoverTimer);tooltip.hidden=true;imageTokens.set(tooltip.querySelector('img'),++scanToken);if(hovered!==-1){hovered=-1;updateWallCursor();wake()}}
 function pick(x,y){if(progress>5.4)return -1;if(wallOpacity>.5)return pickWall(x,y);if(progress<.65||Math.abs(progress-Math.round(progress))>.24)return -1;for(const c of projected){const dx=x-c.x,dy=y-c.y,cos=Math.cos(-c.angle),sin=Math.sin(-c.angle),localX=dx*cos-dy*sin,localY=dx*sin+dy*cos;if(Math.abs(localX)<Math.max(c.w/2,6)&&Math.abs(localY)<Math.max(c.h/2,5))return c.id;}return -1;}
 function moveTooltip(x,y){
  const rect=tooltip.getBoundingClientRect();let left=clamp(x+20,12,W-rect.width-12);const top=clamp(y+20,85,H-rect.height-65);
  if(cardSearch?.isOpen){const panel=$('#cardSearchDialog').getBoundingClientRect();if(left+rect.width>panel.left&&left<panel.right&&top+rect.height>panel.top&&top<panel.bottom)left=clamp(Math.min(x-rect.width-20,panel.left-rect.width-16),12,W-rect.width-12);}
  tooltip.style.left=left+'px';tooltip.style.top=top+'px';
 }
 canvas.addEventListener('pointermove',event=>{
  if(wallDrag){
   if(event.pointerId!==wallDrag.id)return;
   const dx=event.clientX-wallDrag.x,dy=event.clientY-wallDrag.y;
   if(!wallDrag.moved&&Math.hypot(dx,dy)<6)return;
   wallDrag.moved=true;event.preventDefault();filterTransition=null;
   wallCamera.x=wallDrag.cameraX+dx;wallCamera.y=wallDrag.cameraY+dy;constrainWallCamera();updateWallCursor();wake();return;
  }
  if(event.pointerType==='touch'||$('#cardDialog').open||$('#aboutDialog').open||authorPanel?.isOpen)return;
  pointer={x:event.clientX,y:event.clientY};const id=pick(pointer.x,pointer.y);
  if(id!==hovered){hideHover();hovered=id;updateWallCursor();wake();if(id>=0){hoverTimer=setTimeout(()=>{if(hovered!==id)return;const card=cardAt(id),img=tooltip.querySelector('img');scanImage(card,img,640);img.alt='Original catalogue card for '+card.title;tooltip.querySelector('.hover-year').textContent=(card.year||'Undated')+(active===5?' · '+(geographyData.countries[geographyData.records[card.id]?.[0]||'UNKNOWN']?.name||'Place unknown'):card.rare?' · Potentially rare · low confidence':'');tooltip.querySelector('strong').textContent=card.title;tooltip.hidden=false;moveTooltip(pointer.x,pointer.y)},180)}}
  if(!tooltip.hidden)moveTooltip(pointer.x,pointer.y);
 });
 canvas.addEventListener('pointerleave',hideHover);
 let down;canvas.addEventListener('pointerdown',e=>{
  if(!e.isPrimary||e.button!==0)return;
  down={x:e.clientX,y:e.clientY};suppressWallClick=false;
  if(canPanWall()){wallDrag={id:e.pointerId,x:e.clientX,y:e.clientY,cameraX:wallCamera.x,cameraY:wallCamera.y,moved:false};canvas.setPointerCapture(e.pointerId);hideHover();}
 });
 for(const type of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(type,finishWallPan);
 canvas.addEventListener('click',e=>{if(suppressWallClick){suppressWallClick=false;return;}if(down&&Math.hypot(e.clientX-down.x,e.clientY-down.y)>10)return;const id=pick(e.clientX,e.clientY);if(id>=0)openCard(id,matchingIds(squaresActive&&active===5?geographyGeometry.groups.get(geographyData.records[cardAt(id).id]?.[0]||'UNKNOWN'):squaresActive&&active===4?(cardAt(id).year==null?undated:byEra.get(Math.floor(cardAt(id).year/100)*100)||undated):wallOpacity>.5?wallIds.filter(id=>id>=0):cards.map((c,i)=>i)));});
 const dialog=$('#cardDialog'),detailRoot=$('#detailResearch');
 const shardCache=new Map();let detailToken=0,modalOrigin=null,returnScroll=0,navigationAnimation=null;
 const make=(tag,text,className)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(className)node.className=className;return node;};
 const safeUrl=value=>typeof value==='string'&&(/^(https?:\/\/|originals\/|sources\/|images\/|author-images\/|portraits\/)/.test(value))?value:null;
 const link=(text,url)=>{const node=make('a',text);node.href=url;node.target='_blank';node.rel='noopener';return node;};
 function confidence(level,reason){level=level||'unresolved';const node=make('span',level.replaceAll('-',' ')+' confidence','detail-confidence');node.dataset.level=level;node.title=reason||'Confidence in the linked identification or estimate.';node.tabIndex=0;node.setAttribute('aria-label',node.textContent+'. '+node.title);return node;}
 function section(kicker,title){const node=make('section',undefined,'detail-section');node.append(make('div',kicker,'eyebrow'),make('h3',title));return node;}
 function sourceList(sources,host){const list=make('ul',undefined,'detail-sources'),seen=new Set();for(const source of sources||[]){const url=safeUrl(source.url);if(!url||seen.has(url))continue;seen.add(url);const item=make('li');item.append(link((source.title||'Source')+' ↗',url));if(source.role)item.append(make('p',source.role));list.append(item);}if(list.childNodes.length)host.append(list);}
 function jsonShard(kind,id){const path=kind+'/'+id.slice(1,3)+'.json';if(!shardCache.has(path)){const promise=LibraryData.json(path).catch(error=>{shardCache.delete(path);throw error});shardCache.set(path,promise);while(shardCache.size>18)shardCache.delete(shardCache.keys().next().value);}return shardCache.get(path).then(records=>records[id]||null);}
 let modelPromise,authorDirectory;
 const validId=(id,prefix)=>new RegExp('^'+prefix+'[a-f0-9]{12}$').test(id||'');
 const storyHref=(values,standalone=false)=>routes.href(values,standalone);
 // Nested views restore their scene position explicitly when they close.
 history.scrollRestoration='manual';routes=LibraryCardHistory.create(syncRoute);
 authorPanel=LibraryAuthorPanel.create({
  loadProfile:async id=>{
   if(!validId(id,'a'))return null;
   const author=await jsonShard('author-profiles',id);if(author)return author;
   authorDirectory??=fetch('authors-data.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('Author index unavailable');return r.json();});
   const directory=await authorDirectory,canonical=directory.authorRedirects?.[id];return canonical?jsonShard('author-profiles',canonical):null;
  },
  loadWorks:id=>jsonShard('author-records',id).then(works=>works||[]),
  loadNeighbours:async id=>{
   authorDirectory??=fetch('authors-data.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('Author index unavailable');return r.json();});const directory=await authorDirectory,authors=directory.authors,map=new Map(authors.map(a=>[a.id,a]));let ids;try{ids=JSON.parse(sessionStorage.getItem('biblioteca-author-sequence')||'null');}catch{}if(!Array.isArray(ids)||!ids.includes(id))ids=[...authors].sort((a,b)=>a.surname.localeCompare(b.surname)||a.displayName.localeCompare(b.displayName)).map(a=>a.id);ids=[...new Set(ids.map(a=>directory.authorRedirects?.[a]||a).filter(a=>map.has(a)))];const at=ids.indexOf(id);return{previous:at>0?map.get(ids[at-1]):null,next:at>=0&&at<ids.length-1?map.get(ids[at+1]):null,index:at,total:ids.length};
  },
  authorHref:id=>storyHref({author:id,authorView:'full'},true),
  onNavigate:id=>routes.write({author:id,authorView:$('#authorPanel').classList.contains('is-fullscreen')?'full':null},{replace:true,kind:'author'}),
  cardHref:id=>storyHref({card:id},true),
  onClose:()=>routes.close('author'),
  onFullscreen:full=>routes.write({authorView:full?'full':null},{replace:true}),
  onCanonical:id=>routes.write({author:id},{replace:true,notify:false}),
  onCard:id=>{reopenSearch=false;routes.write({card:id,author:null,authorView:null},{kind:'card'});},
 });
 function openAuthor(id){routes.write({author:id,authorView:null},{kind:'author'});}
 import('./cards-authors.mjs?v=lifespans-1').then(({createAuthorScene})=>createAuthorScene({host:$('#authorPortraits'),onOpen:openAuthor,href:id=>storyHref({author:id,card:null},true)+'#authors',onChange:wake})).then(scene=>{
  authorScene=scene;if(cardFilterMask)scene.setFilter(Array.from(cardFilterMask,(included,index)=>included?cardAt(index).id:null).filter(Boolean));scene.resize(W,H);steps[7].style.height=(scene.timelineTravel+H*1.6)+'px';wake();
 }).catch(error=>{console.warn('Author scene unavailable',error.message);$('#authorsTitle').nextElementSibling.textContent='Explore the people behind the catalogue.';const link=document.createElement('a');link.href='authors.html#directory';link.textContent='Explore the authors →';link.style.pointerEvents='auto';$('#authorsTitle').after(link);});
 function syncRoute(){
  if(!routeReady)return;
  routeQueue=routeQueue.then(async()=>{
   const state=routes.current();
   if(!state.author)authorPanel.close();
   if(routeError){$('#sceneCaption').hidden=true;routeError=false;}
   const index=cardById.get(state.card);
   if(state.card&&index!==undefined){
    cardSearch.hide();
    if(!dialog.open)openCard(index,Array.from(cardById.values()),{fromHistory:true});
    else if(selectedCard!==index){if(!modalPool.includes(index))modalPool=Array.from(cardById.values());modalIndex=modalPool.indexOf(index);showCard(index);dialog.scrollTop=0;}
   }else{
    if(dialog.open)await closeCard({fromHistory:true,restoreSearch:!state.author});
    if(state.card){routeError=true;$('#sceneCaption').textContent='This card could not be found. Use search to find another card.';$('#sceneCaption').hidden=false;}
   }
   if(state.author){cardSearch.hide();hideHover();authorPanel.open(state.author,{full:state.full});}
   else document.title=dialog.open?cardAt(selectedCard).title+' · Biblioteca':'A life in cards · Biblioteca';
  }).catch(error=>console.warn('Could not open this view',error.message));
 }
 // Author links in the key facts use the same panel as the author cards.
 $('#detailFacts').addEventListener('click',event=>{
  const anchor=event.target.closest('a');if(!anchor||event.button||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
  const id=new URL(anchor.href).searchParams.get('author');if(id){event.preventDefault();openAuthor(id);}
 });
 function openCard(index,pool,{fromHistory=false}={}){
  if(modalClosing)return;if(cardSearch?.isOpen){reopenSearch=true;cardSearch.hide();}if(!fromHistory)routes.write({card:cardAt(index).id,author:null,authorView:null},{kind:'card',notify:false});hideHover();modalPool=pool?.length?pool:cards.map((c,i)=>i);modalIndex=Math.max(0,modalPool.indexOf(index));
  const origin=wallOrigin(index)||projected.find(p=>p.id===index);modalOrigin=origin?{...origin}:null;selectedCard=index;focusTarget=1;returnScroll=scrollY;
  showCard(index);dialog.classList.remove('is-settled');dialog.showModal();dialog.scrollTop=0;document.body.classList.add('card-open');
  const image=$('#detailImage'),rect=image.getBoundingClientRect(),start=origin||{x:W/2,y:H/2,w:Math.min(180,W*.4),h:120,angle:0};
  const transform='translate('+(start.x-(rect.left+rect.width/2))+'px,'+(start.y-(rect.top+rect.height/2))+'px) rotate('+start.angle+'rad) scale('+start.w/rect.width+','+start.h/rect.height+')';
  modalAnimation?.cancel();modalAnimation=image.animate([{transform,opacity:.85},{transform:'none',opacity:1}],{duration:reduced?0:760,easing:'cubic-bezier(.22,.8,.24,1)',fill:'both'});
  modalAnimation.finished.then(()=>{if(!modalClosing&&dialog.open){dialog.classList.add('is-settled');modalAnimation?.cancel();modalAnimation=null;}}).catch(()=>{});wake();
 }
 async function closeCard({fromHistory=false,restoreSearch=true}={}){
  if(!fromHistory){routes.close('card');return;}
  if(modalClosing||!dialog.open)return;modalClosing=true;detailToken++;navigationAnimation?.cancel();imageTokens.set($('#detailImage'),++scanToken);$$('.card-neighbour img').forEach(image=>imageTokens.set(image,++scanToken));dialog.classList.remove('is-settled');focusTarget=0;wake();
  modalAnimation?.cancel();const image=$('#detailImage'),rect=image.getBoundingClientRect(),onScreen=rect.bottom>40&&rect.top<H,origin=modalOrigin;
  const end=origin&&onScreen?'translate('+(origin.x-(rect.left+rect.width/2))+'px,'+(origin.y-(rect.top+rect.height/2))+'px) rotate('+origin.angle+'rad) scale('+origin.w/rect.width+','+origin.h/rect.height+')':'scale(.92)';
  modalAnimation=image.animate([{transform:'none',opacity:1},{transform:end,opacity:onScreen?1:0}],{duration:reduced?0:520,easing:'cubic-bezier(.4,0,.3,1)',fill:'both'});
  try{await modalAnimation.finished;}catch{}
  dialog.close();modalAnimation?.cancel();modalAnimation=null;document.body.classList.remove('card-open');selectedCard=-1;modalClosing=false;window.scrollTo({top:returnScroll,behavior:'instant'});if(reopenSearch&&restoreSearch){reopenSearch=false;cardSearch.show();}wake();
 }
 function showCard(index){
  detailRoot.querySelectorAll('.summary-carousel,.reading-authors').forEach(node=>node.dispose?.());
  const card=cardAt(index),image=$('#detailImage');selectedCard=index;dialog.dataset.cardId=card.id;document.title=card.title+' · Biblioteca';$('#detailCoverPanel').hidden=true;$('#detailCover').replaceChildren();$('#detailCoverCaption').replaceChildren();$('#detailFacts').replaceChildren(make('p','Loading key facts…','detail-loading'));scanImage(card,image,1400);image.alt='Original family catalogue card for '+card.title+', scan '+card.page;
  $('#cardDialogTitle').textContent=card.title;$('#detailAuthor').textContent=[card.author,card.year||'Date not detected'].filter(Boolean).join(' · ');$('#detailEyebrow').textContent='Original catalogue / Card '+card.page;
  [[-1,'#previousCardPreview','Previous'],[1,'#nextCardPreview','Next']].forEach(([direction,selector,label])=>{
   const button=$(selector);button.hidden=modalPool.length<2;if(button.hidden)return;
   const neighbour=cardAt(modalPool[(modalIndex+direction+modalPool.length)%modalPool.length]);
   button.setAttribute('aria-label',label+' card: '+neighbour.title);button.title=label+' card: '+neighbour.title;
   button.dataset.cardId=neighbour.id;scanImage(neighbour,button.querySelector('img'),640);
  });
  detailRoot.replaceChildren(make('p','Opening this card’s story…','detail-loading'));detailRoot.setAttribute('aria-busy','true');loadDetails(card,++detailToken);wake();
 }
 async function loadDetails(card,token){
  try{
   const [record,estimate]=await Promise.all([jsonShard('book-records',card.id),jsonShard('circulation-estimates',card.id).catch(()=>null)]);
   if(token!==detailToken)return;if(!record)throw Error('Catalogue record unavailable');
   const authorIds=record.authors||[],authors=await Promise.all(authorIds.map(id=>jsonShard('author-profiles',id).catch(()=>null)));
   if(token!==detailToken)return;
   $('#detailFacts').replaceChildren(LibraryBookReading.facts(record,estimate,geographyData));
   $('#detailFacts').querySelectorAll('a').forEach(anchor=>{const id=new URL(anchor.href).searchParams.get('id');if(id)anchor.href=storyHref({author:id},true);});
   LibraryBookReading.mountCover($('#detailCover'),$('#detailCoverCaption'),{...card,...record,title:card.title},geographyData);
   $('#detailCoverPanel').hidden=false;
   detailRoot.replaceChildren(LibraryBookSummaries.create(record,{dark:true}));
   detailRoot.append(LibraryBookReading.authors(record,authors,{dark:true,onOpenAuthor:openAuthor,authorHref:id=>storyHref({author:id},true)}));
   const more=make('details',undefined,'reading-more');more.append(make('summary','Images, catalogue & sources'));detailRoot.append(more);
   const visual=section('02 / Covers & pages','A glimpse of the book.'),gallery=make('div',undefined,'detail-gallery'),images=[],seen=new Set();
   function addImage(image,candidate,host=false){const src=safeUrl(image.src||image.url);if(!src||seen.has(src))return;seen.add(src);images.push({src,label:image.label||'Reference image',url:safeUrl(image.sourceUrl||candidate?.url),credit:image.credit||candidate?.source||'',level:image.confidence||'low',relation:image.editionRelation||candidate?.editionRelation||record.research?.imageEditionRelation||record.research?.editionRelation||'',host});}
   (record.research?.images||[]).forEach(image=>addImage(image));
   (record.onlineCandidates||[]).forEach(candidate=>(candidate.images||[]).forEach(image=>addImage(image,candidate)));
   if(!images.length)(record.containerCandidates||[]).forEach(candidate=>(candidate.images||[]).forEach(image=>addImage(image,candidate,true)));
   images.forEach(image=>{const figure=make('figure',undefined,'detail-reference'),anchor=link('',image.url||image.src),img=make('img');img.src=image.src;img.alt=image.label;img.loading='lazy';img.onerror=()=>img.replaceWith(make('div','Preview unavailable · open source ↗','reference-unavailable'));anchor.append(img);const caption=make('figcaption');caption.append(make('strong',image.host?'Possible journal reference':image.label));if(image.credit)caption.append(make('span',image.credit+' · '));if(image.url)caption.append(link('Source ↗',image.url));caption.append(confidence(image.level,image.relation||'A reference copy; correspondence to the family edition is not confirmed.'));if(image.relation){const details=make('details');details.append(make('summary','Edition connection'),make('p',image.relation));caption.append(details);}figure.append(anchor,caption);gallery.append(figure);});
   if(images.length){visual.append(gallery,make('p','Reference copies, which may show a different edition. The original family card appears above.'));}else visual.append(make('p','No reference cover or interior image is linked yet. The original catalogue card above records this copy.'));
   more.append(visual);
   more.append(link('Original catalogue scan ↗','originals/'+card.file+'#page='+card.page));
   const geoHit=geographyData?.records?.[card.id];
   if(geoHit){const place=section('03 / Publication place',geographyData.countries[geoHit[0]].name);place.append(make('p',geoHit[1]+' · medium confidence'),make('p',geoHit[2]),link('Original catalogue evidence ↗','originals/'+card.file+'#page='+card.page));more.append(place);}
   const scarcity=section('04 / Scarcity','How rare is it?'),summary=make('div',undefined,'scarcity-summary'),status=make('div'),count=make('div');
   if(card.rare){status.append(make('div','Potentially rare','scarcity-status'),confidence('low',card.rarityNote));summary.append(status);}else summary.classList.add('scarcity-summary-single');
   const research=record.research,n=research?.documentedCopies;
   if(estimate){count.append(make('span','Estimated surviving copies worldwide','scarcity-label'),make('strong','≈ '+fmt(estimate.min)+'–'+fmt(estimate.max),'scarcity-count'),confidence(estimate.confidence,'An uncalibrated ballpark estimate based on assumed print run and survival. Actual totals can lie outside the range.'),make('p','A broad ballpark for this printing or volume, including private and institutional copies.'));}
   else if(n!=null){count.append(make('span','Documented surviving copies','scarcity-label'),make('strong','At least '+fmt(n),'scarcity-count'),confidence(record.confidence?.survival?.level,record.confidence?.survival?.reason),make('p','A minimum found in the sources, not the worldwide total.'));}
   else{count.append(make('span','Surviving copies worldwide','scarcity-label'),make('strong','Unknown','scarcity-count'),make('p','A copy estimate is not yet available for this entry.'));}
   if(estimate&&n!=null)count.append(make('p','At least '+fmt(n)+' copies are documented separately.'));
   summary.append(count);scarcity.append(summary);
   const evidence=make('details');evidence.append(make('summary','Confidence, assumptions & sources'));
   if(card.rarityNote||research?.rarityNote)evidence.append(make('p',card.rarityNote||research.rarityNote));
   if(estimate){evidence.append(make('p','The range is a model scenario, not an edition-specific census. '+estimate.scope+'.'));(estimate.notes||[]).forEach(note=>evidence.append(make('p',note)));
    const context=make('p');evidence.append(context);
    modelPromise??=fetch('circulation-model.json').then(r=>{if(!r.ok)throw Error('No model');return r.json()});
    modelPromise.then(model=>{if(token!==detailToken)return;const cohort=model.cohorts.find(c=>c.id===estimate.cohort);if(cohort)context.textContent='Assumed original print run: '+fmt(cohort.printRun[0])+'–'+fmt(cohort.printRun[1])+'. Assumed survival: '+cohort.survivingFraction.map(n=>Math.round(n*100)+'%').join('–')+'. These are scenario inputs, not observed counts for this edition.';}).catch(()=>{});
   }
   sourceList([...(card.sources||[]),...(research?.holdingSources||[]),...(estimate?.sources||[])],evidence);
   evidence.append(link('How the estimates work ↗','circulation.html'));scarcity.append(evidence);more.append(scarcity);detailRoot.setAttribute('aria-busy','false');
  }catch(error){if(token!==detailToken)return;LibraryBookReading.mountCover($('#detailCover'),$('#detailCoverCaption'),card,geographyData);$('#detailCoverPanel').hidden=false;$('#detailFacts').replaceChildren(LibraryBookReading.facts({id:card.id,year:card.year,authorNames:[card.author].filter(Boolean)},null,geographyData));detailRoot.replaceChildren(make('p','The additional information could not load. You can still read the original card or open the full book page.','detail-loading'));detailRoot.setAttribute('aria-busy','false');console.warn('Card details unavailable',error.message);}
 }
 function navigateCard(direction){
  if(modalClosing||modalPool.length<2||!dialog.classList.contains('is-settled'))return;
  modalIndex=(modalIndex+direction+modalPool.length)%modalPool.length;
  navigationAnimation?.cancel();showCard(modalPool[modalIndex]);modalOrigin=null;routes.write({card:cardAt(modalPool[modalIndex]).id},{replace:true,notify:false});
  dialog.scrollTo({top:0,behavior:reduced?'instant':'smooth'});
  navigationAnimation=$('#detailImage').animate([{transform:'translateX('+(direction*45)+'px)',opacity:.45},{transform:'none',opacity:1}],{duration:reduced?0:320,easing:'cubic-bezier(.22,.8,.24,1)'});
 }
 $('#previousCardPreview').onclick=()=>navigateCard(-1);
 $('#nextCardPreview').onclick=()=>navigateCard(1);
 dialog.addEventListener('keydown',event=>{
  if(event.altKey||event.ctrlKey||event.metaKey||event.target.matches('input,textarea,select,[contenteditable]'))return;
  if(event.key==='ArrowLeft'||event.key==='ArrowRight'){event.preventDefault();navigateCard(event.key==='ArrowLeft'?-1:1);}
 });
 dialog.addEventListener('cancel',event=>{event.preventDefault();closeCard()});
 originalSlides.forEach(node=>node.onclick=()=>{const rect=node.getBoundingClientRect(),id=Number(node.dataset.cardIndex);projected.push({id,x:rect.x+rect.width/2,y:rect.y+rect.height/2,w:rect.width,h:rect.height,z:1,angle:0});openCard(id,originalSlides.map(n=>Number(n.dataset.cardIndex)))});
 $('#aboutView').onclick=()=>{$('#aboutDialog').showModal();hideHover()};
 $$('dialog:not(#cardSearchDialog):not(#authorPanel)').forEach(dialog=>{dialog.querySelector('.dialog-close').onclick=()=>dialog.id==='cardDialog'?closeCard():dialog.close();dialog.addEventListener('click',event=>{if(event.target===dialog){if(dialog.id==='cardDialog'){closeCard();return;}const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close()}})});
 window.addEventListener('scroll',onScroll,{passive:true});window.addEventListener('resize',resize);window.addEventListener('blur',()=>{finishWallPan();hideHover();});
 $('.skip-link').addEventListener('click',()=>{cardSearch.hide();leaveWall();});
 nav.forEach((a,i)=>a.addEventListener('click',event=>{event.preventDefault();cardSearch.hide();leaveWall();history.replaceState(null,'',a.getAttribute('href'));window.scrollTo({top:chapterTop(i),behavior:reduced?'instant':'smooth'});}));
 setMotion(reduced);resize();if(location.hash){const hash=location.hash==='#scarcity'?'#geography':location.hash==='#inheritance'?'#authors':location.hash;const index=steps.findIndex(step=>'#'+step.id===hash);if(index>=0){window.scrollTo({top:chapterTop(index),behavior:'instant'});target=progress=index;onScroll();wake()}}
 canvas.dataset.ready='true';
})().catch(error=>{console.error(error);const caption=document.querySelector('#sceneCaption');if(caption){caption.hidden=false;caption.textContent='The scene could not load. Please refresh or visit the original library.'}});
