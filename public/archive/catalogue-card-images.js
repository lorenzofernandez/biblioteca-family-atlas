'use strict';
window.LibraryCatalogueCards=(()=>{
 const shards=new Map(),documents=new Map(),previews=new Map(),watched=new Set(),jobs=[];
 let pdfModule,active=0;
 const make=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n;};
 const trim=(cache,limit)=>{while(cache.size>limit)cache.delete(cache.keys().next().value);};
 async function recordFor(id){
  const key=id.slice(1,3);let pending=shards.get(key);
  if(!pending){pending=LibraryData.json('book-records/'+key+'.json');shards.set(key,pending);pending.catch(()=>shards.delete(key));trim(shards,8);}
  return (await pending)[id];
 }
 function trimDocuments(){
  for(const [key,entry] of documents){if(documents.size<=3)break;if(entry.users===0){documents.delete(key);entry.promise.then(doc=>doc.destroy()).catch(()=>{});}}
 }
 async function render(record,width){
  pdfModule??=import('./vendor/pdfjs/pdf.mjs');const pdfjs=await pdfModule;
  pdfjs.GlobalWorkerOptions.workerSrc=new URL('./vendor/pdfjs/pdf.worker.mjs',location.href).href;
  let entry=documents.get(record.file);
  if(!entry){const task=pdfjs.getDocument({url:record.source,isEvalSupported:false,disableAutoFetch:true,disableStream:true,wasmUrl:new URL('./vendor/pdfjs/wasm/',location.href).href});entry={promise:task.promise,users:0};documents.set(record.file,entry);entry.promise.catch(()=>{if(documents.get(record.file)===entry)documents.delete(record.file);});}
  entry.users++;documents.delete(record.file);documents.set(record.file,entry);
  try{
   const doc=await entry.promise,page=await doc.getPage(record.page),base=page.getViewport({scale:1}),viewport=page.getViewport({scale:Math.min(5,width/base.width)}),canvas=make('canvas');
   canvas.width=Math.ceil(viewport.width);canvas.height=Math.ceil(viewport.height);
   await page.render({canvas,canvasContext:canvas.getContext('2d'),viewport,background:'#fff'}).promise;
   const src=canvas.toDataURL('image/jpeg',width>720?.94:.85);canvas.width=canvas.height=0;return src;
  }finally{entry.users--;trimDocuments();}
 }
 function show(host,book,preview){
  if(!host.isConnected)return;
  const img=make('img');img.src=preview.src;img.alt='Original catalogue card for '+book.title+', scan '+preview.page;img.decoding='async';
  const caption=make('small','Catalogue card');host.replaceChildren(img,caption);host.removeAttribute('aria-busy');host.dataset.scanPage=preview.page;host.dataset.scanFile=preview.file;
 }
 async function load(job){
  const {host,book,width}=job;if(!host.isConnected)return;
  try{
   const cacheKey=book.id+':'+width;let preview=previews.get(cacheKey);
   if(!preview){const record=job.record||await recordFor(book.id);if(!record?.source||!record.page)throw Error('Missing catalogue scan');if(!host.isConnected)return;preview={src:await render(record,width),page:record.page,file:record.file};previews.set(cacheKey,preview);trim(previews,48);}
   show(host,book,preview);
  }catch(error){if(host.isConnected){host.removeAttribute('aria-busy');host.replaceChildren(make('span','Catalogue card unavailable'),make('small','Open the book to view its scan'));}console.error('Catalogue card preview:',book.id,error);}
 }
 function drain(){while(active<2&&jobs.length){const job=jobs.shift();if(!job.host.isConnected)continue;active++;load(job).finally(()=>{active--;drain();});}}
 const observer=new IntersectionObserver(entries=>{entries.forEach(entry=>{if(!entry.isIntersecting)return;const host=entry.target;observer.unobserve(host);watched.delete(host);jobs.push(host._catalogueJob);delete host._catalogueJob;});drain();},{rootMargin:'250px'});
 function create(book,record,options={}){
  const host=make('div');host.className='catalogue-card-image'+(options.fullSize?' catalogue-card-full':'');host.dataset.bookId=book.id;host.setAttribute('aria-busy','true');host.append(make('span','Loading catalogue card…'));
  host._catalogueJob={host,book,record,width:options.fullSize?1600:720};watched.add(host);observer.observe(host);return host;
 }
 function prune(){watched.forEach(host=>{if(!host.isConnected){observer.unobserve(host);watched.delete(host);delete host._catalogueJob;}});}
 return {create,prune};
})();
