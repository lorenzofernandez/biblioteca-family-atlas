/* Grid and list share one catalogue, filter mask, and card navigation pool. */
(() => {
 'use strict';
 const normalize=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 const fmt=n=>n.toLocaleString('en-US');
 window.LibraryCardSearch={create({onFilter,onOpen,onVisibility}){
  const $=selector=>document.querySelector(selector),dialog=$('#cardSearchDialog'),trigger=$('#cardSearchToggle'),form=$('#cardSearchForm');
  const query=$('#cardSearchQuery'),country=$('#cardSearchCountry'),from=$('#cardSearchFrom'),to=$('#cardSearchTo'),undated=$('#cardSearchUndated'),range=$('#cardSearchRange'),dateLabel=$('#cardSearchDateLabel');
  const results=$('#cardSearchResults'),status=$('#cardSearchStatus'),more=$('#cardSearchMore'),list=$('#cardListView');
  const summary=$('#cardFilterSummary'),summaryButton=$('#cardFilterCount'),reset=$('#cardSearchReset');
  let records=[],geo=null,searchable=[],matching=[],mask=null,limit=100,listMode=false,timer,rangeFrame=0,ready=false,active=false,minimum=1400,maximum=2000;
  const countryCode=card=>geo?.records?.[card.id]?.[0]||'UNKNOWN';
  const countryName=card=>geo?.countries?.[countryCode(card)]?.name||'Place unknown';
  function renderResults(append=false){
   if(!append)results.replaceChildren();if(!ready||!listMode)return;
   const start=append?results.children.length:0;
   if(!matching.length){const empty=document.createElement('p');empty.className='card-search-empty';empty.textContent='No cards match. Widen the dates or clear a filter.';results.append(empty);}
   for(const index of matching.slice(start,limit)){
    const card=records[index],button=document.createElement('button'),title=document.createElement('strong'),byline=document.createElement('span'),meta=document.createElement('small');
    button.type='button';button.className='card-search-result';button.dataset.cardId=card.id;
    title.textContent=card.title||'Untitled catalogue card';byline.textContent=card.author||'Author not recorded';meta.textContent=[card.year??'Undated',countryName(card)].join(' · ');
    button.append(title,byline,meta);button.onclick=()=>{const wasOpen=dialog.open;hide();onOpen(index,matching.slice(),wasOpen);};results.append(button);
   }
   more.hidden=matching.length<=limit;
  }
  function updateRange(){
   const low=Number(from.value),high=Number(to.value),span=maximum-minimum||1;
   range.style.setProperty('--from',((low-minimum)/span*100)+'%');range.style.setProperty('--to',((high-minimum)/span*100)+'%');
   from.style.zIndex=low===maximum?'4':'2';
   from.setAttribute('aria-valuetext',String(low));to.setAttribute('aria-valuetext',String(high));
   from.setAttribute('aria-valuemax',String(high));to.setAttribute('aria-valuemin',String(low));
   from.disabled=to.disabled=!ready||undated.checked;range.classList.toggle('is-disabled',from.disabled);
   dateLabel.textContent=undated.checked?'Undated':low===minimum&&high===maximum?'All dates':low===high?String(low):low+' — '+high;
   $('#cardSearchFromValue').textContent=String(low);$('#cardSearchToValue').textContent=String(high);
  }
  function apply(){
   clearTimeout(timer);cancelAnimationFrame(rangeFrame);rangeFrame=0;if(!ready)return;
   const words=normalize(query.value.trim()).split(/\s+/).filter(Boolean),code=country.value,low=Number(from.value),high=Number(to.value),bounded=low!==minimum||high!==maximum;
   active=!!(words.length||code||bounded||undated.checked);matching=[];mask=active?new Uint8Array(records.length):null;
   records.forEach((card,index)=>{
    if(code&&countryCode(card)!==code)return;
    if(undated.checked?card.year!=null:bounded&&(card.year==null||card.year<low||card.year>high))return;
    if(words.some(word=>!searchable[index].includes(word)))return;
    matching.push(index);if(mask)mask[index]=1;
   });
   limit=100;list.scrollTop=0;reset.disabled=!active;summary.hidden=!active;summaryButton.textContent=fmt(matching.length)+' matching cards';trigger.classList.toggle('has-filters',active);document.body.classList.toggle('filters-active',active);
   status.textContent=fmt(matching.length)+' of '+fmt(records.length)+' cards';$('#cardListCount').textContent=fmt(matching.length)+' cards';$('#cardSearchEmpty').hidden=matching.length>0;
   updateRange();renderResults();onFilter({active,mask,count:matching.length});
  }
  function show(){
   if(dialog.open)return;dialog.show();trigger.setAttribute('aria-expanded','true');document.body.classList.add('search-open');onVisibility(true);query.focus({preventScroll:true});
  }
  function closed(){if(dialog.open)return;trigger.setAttribute('aria-expanded','false');document.body.classList.remove('search-open');onVisibility(false);}
  function hide(){if(dialog.open){dialog.close();closed();}}
  function clear(){query.value='';country.value='';from.value=minimum;to.value=maximum;undated.checked=false;apply();}
  trigger.disabled=false;trigger.onclick=()=>dialog.open?hide():show();summaryButton.onclick=show;
  $('#clearCardFilters').onclick=clear;reset.onclick=clear;dialog.querySelector('.dialog-close').onclick=()=>{hide();trigger.focus({preventScroll:true});};
  query.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(apply,140);});
  function slide(event){if(event.target===from)from.value=Math.min(Number(from.value),Number(to.value));else to.value=Math.max(Number(to.value),Number(from.value));updateRange();cancelAnimationFrame(rangeFrame);rangeFrame=requestAnimationFrame(apply);}
  from.addEventListener('input',slide);to.addEventListener('input',slide);
  range.addEventListener('pointerdown',event=>{if(event.target!==range||from.disabled)return;const r=range.getBoundingClientRect(),value=Math.round(minimum+Math.max(0,Math.min(1,(event.clientX-r.left)/r.width))*(maximum-minimum));const input=Math.abs(value-Number(from.value))<Math.abs(value-Number(to.value))?from:to;input.value=value;input.focus({preventScroll:true});slide({target:input});});
  country.onchange=apply;undated.onchange=apply;form.onsubmit=e=>{e.preventDefault();apply();};
  more.onclick=()=>{limit+=100;renderResults(true);};
  dialog.addEventListener('cancel',e=>{e.preventDefault();hide();});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&dialog.open&&!document.querySelector('dialog:modal')){e.preventDefault();hide();trigger.focus({preventScroll:true});}});
  dialog.addEventListener('close',closed);
  return {
   show,hide,clear,setListMode(enabled){listMode=enabled;list.hidden=!enabled;if(enabled&&!results.children.length)renderResults();},get isOpen(){return dialog.open;},get active(){return active;},get mask(){return mask;},get matching(){return matching;},
   subset:ids=>active?Array.from(ids).filter(i=>mask[i]):ids,
   setRecords(cards,geography){
    records=cards;geo=geography;searchable=cards.map(card=>normalize(card.title+' '+card.author));
    country.replaceChildren(new Option('All countries',''));
    Object.entries(geo.countries).filter(([code])=>geo.counts[code]>0).sort((a,b)=>a[1].name.localeCompare(b[1].name)).forEach(([code,c])=>country.append(new Option(c.name,code)));
    const years=cards.map(c=>c.year).filter(Number.isFinite);minimum=Math.min(...years);maximum=Math.max(...years);
    for(const input of [from,to]){input.min=minimum;input.max=maximum;input.step=1;}from.value=minimum;to.value=maximum;
    ready=true;query.disabled=country.disabled=undated.disabled=false;apply();
   },
   failed(){status.textContent='Search could not load. Refresh the page to try again.';}
  };
 }};
})();
