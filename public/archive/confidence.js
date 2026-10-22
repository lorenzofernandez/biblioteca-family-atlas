'use strict';
window.LibraryConfidence={
 labels:{high:'High',medium:'Medium',low:'Low','very-low':'Very low',unresolved:'Unresolved'},
 biography(author={}) {
  const status=author.biographyStatus,placeholder=/biography remains unresearched|biograph(?:y|ical details).*not yet|biography is not yet available/i;
  const hasBiography=Boolean(author.bio?.trim()&&!placeholder.test(author.bio)&&!['catalogue-only','unresolved','non-person'].includes(status));
  const supplied=author.confidence?.biography;
  const confidence=hasBiography?(supplied?.level?supplied:{level:'low',reason:'A biographical description is available, but its source and attribution have not yet received an individual review.'}):{level:'unresolved',reason:status==='non-person'?'This catalogue entry does not identify an individual person. The text describes catalogue evidence rather than a personal biography.':'A sourced biography has not been established for this catalogue identity. Catalogue evidence describes the linked cards, not verified life events.'};
  return {hasBiography,confidence,label:hasBiography?'Biography':'Catalogue evidence',text:hasBiography?author.bio:(author.catalogueContext||'A sourced biography has not yet been matched to this catalogue name.'),summary:hasBiography?(author.bioShort||author.bio):(author.catalogueContext||'A sourced biography has not yet been matched to this catalogue name.')};
 },
 indicator(value,label='Biography') {
  const c=typeof value==='string'?{level:value}:value||{level:'unresolved'},item=document.createElement('span'),text=document.createElement('span');
  item.className='confidence-indicator';item.dataset.confidenceLevel=c.level||'unresolved';item.dataset.confidenceKind=label.toLowerCase();text.textContent=label+' · '+(this.labels[c.level]||'Unresolved');item.append(this.dot(c,label),text);return item;
 },
 explanation(value,label='Identity') {
  const c=typeof value==='string'?{level:value}:value||{},level=c.level||'unresolved';
  if(/incompatible|chronology mismatch|predates.*birth|rejected.*date/i.test(c.reason||''))return 'The source dates conflict with this match.';
  const messages=label==='Biography'?{
   high:'Supported by reviewed sources. Identity is assessed separately.',
   medium:'Based on public sources; not individually reviewed.',
   low:'Source-based biography of a possible identity; not verified.',
   'very-low':'Limited biographical evidence; further checks needed.',
   unresolved:'No verified biography is available.'
  }:{high:'Strong evidence supports this match.',medium:'Plausible match; some details need checking.',low:'Possible match; not individually verified.','very-low':'Limited evidence for this match.',unresolved:'The identity has not been established.'};
  return messages[level]||messages.unresolved;
 },
 dot(value,label='Identity') {
  const c=typeof value==='string'?{level:value}:value||{level:'unresolved'},level=this.labels[c.level]||'Unresolved';
  const defaults={high:'Strong evidence supports this identity. Individual catalogue attributions and images can still have their own uncertainty.',medium:'A plausible identity match, with some details still to check. Connected catalogue records may include tentative attributions.',low:'A tentative identity match. Initials, spelling variants or people with the same name can lead to a different person. Open the profile to compare the candidates and sources.','very-low':'An exploratory lead with limited supporting evidence. Further research is needed.',unresolved:'The available evidence does not establish this identity yet.'};
  const item=document.createElement('span'),button=document.createElement('button'),tip=document.createElement('span'),heading=document.createElement('strong'),reason=document.createElement('span');
  item.className='confidence-dot-wrap';button.type='button';button.className='confidence-dot confidence-'+(this.labels[c.level]?c.level:'unresolved');button.setAttribute('aria-label',label+' confidence: '+level+'. More context');
  const biographyDefaults={high:'The biography is supported by reviewed sources. Identity and catalogue attribution are assessed separately.',medium:'The biography is supported by public sources, with details that still need individual review.',low:'A preliminary biographical description with limited verification. Check the linked sources.','very-low':'A preliminary biographical lead with very limited supporting evidence.',unresolved:'A sourced biography has not yet been established for this catalogue identity.'};
  tip.id='confidence-dot-tip-'+(this._dotSequence=(this._dotSequence||0)+1);tip.className='confidence-tooltip confidence-dot-tooltip';tip.setAttribute('role','tooltip');tip.setAttribute('popover','manual');tip.style.margin='0';tip.hidden=true;heading.textContent=level+' confidence · '+label;reason.textContent=this.explanation(c,label);tip.append(heading,reason);button.setAttribute('aria-describedby',tip.id);item.append(button,tip);
  if(!this._dotState){const state=this._dotState={active:null};const dismiss=()=>state.active?.hide();document.addEventListener('pointerdown',e=>{if(state.active&&!state.active.item.contains(e.target))dismiss()});document.addEventListener('keydown',e=>{if(e.key==='Escape')dismiss()});window.addEventListener('resize',dismiss);window.addEventListener('scroll',e=>{if(!state.active?.item.contains(e.target))dismiss()},{capture:true,passive:true});}
  const state=this._dotState;let pinned=false,timer;
  const hide=()=>{clearTimeout(timer);if(tip.matches(':popover-open'))tip.hidePopover();tip.hidden=true;pinned=false;if(state.active?.item===item)state.active=null;};
  const show=()=>{clearTimeout(timer);if(state.active?.item!==item)state.active?.hide();state.active={item,hide};tip.hidden=false;if(!tip.matches(':popover-open'))tip.showPopover();const rect=button.getBoundingClientRect(),bounds=tip.getBoundingClientRect();tip.style.left=Math.max(16,Math.min(rect.left,innerWidth-bounds.width-16))+'px';tip.style.top=Math.max(16,Math.min(rect.bottom+8+bounds.height<=innerHeight-16?rect.bottom+8:rect.top-bounds.height-8,innerHeight-bounds.height-16))+'px';};
  item.addEventListener('pointerenter',e=>{if(e.pointerType!=='touch')show()});item.addEventListener('pointerleave',()=>{if(!pinned&&document.activeElement!==button)timer=setTimeout(hide,150)});button.addEventListener('focus',show);button.addEventListener('blur',hide);button.addEventListener('click',()=>{if(pinned)hide();else{show();pinned=true}});
  return item;
 },
 badge(value,label='Confidence') { const c=typeof value==='string'?{level:value}:value||{level:'unresolved'};const n=document.createElement('span');n.className='confidence-badge confidence-'+c.level;n.textContent=(this.labels[c.level]||'Unresolved')+' confidence'+(label==='Confidence'?'':' · '+label);if(c.reason)n.title=c.reason;return n;},
 tags(fields) {
  const bar=document.createElement('div');bar.className='confidence-tags';bar.setAttribute('role','group');bar.setAttribute('aria-label','Entry confidence');
  const closeAll=[];let sequence=0;
  Object.entries(fields||{}).forEach(([key,c])=>{
   if(key==='overall'||!c?.level)return;
   const item=document.createElement('span'),button=document.createElement('button'),tip=document.createElement('span');
   const label=key.charAt(0).toUpperCase()+key.slice(1),level=this.labels[c.level]||'Unresolved';
   item.className='confidence-tag';button.type='button';button.className='confidence-badge confidence-'+c.level;button.textContent=label+' · '+level;button.setAttribute('aria-label',label+' confidence: '+level+'. More context');
   tip.id='book-confidence-'+key+'-'+sequence++;tip.className='confidence-tooltip';tip.setAttribute('role','tooltip');tip.hidden=true;tip.textContent=this.explanation(c,label);button.setAttribute('aria-describedby',tip.id);
   let pinned=false,timer;
   const hide=()=>{clearTimeout(timer);tip.hidden=true;pinned=false;};
   const show=()=>{
    clearTimeout(timer);closeAll.forEach(close=>{if(close!==hide)close()});tip.hidden=false;
    const rect=button.getBoundingClientRect(),width=tip.getBoundingClientRect().width;
    tip.style.left=Math.max(16,Math.min(rect.left,window.innerWidth-width-16))+'px';
    tip.style.top=(rect.bottom+8)+'px';
   };
   closeAll.push(hide);
   item.addEventListener('pointerenter',event=>{if(event.pointerType!=='touch')show()});
   item.addEventListener('pointerleave',()=>{if(!pinned&&document.activeElement!==button)timer=setTimeout(hide,120)});
   button.addEventListener('focus',show);button.addEventListener('blur',hide);
   button.addEventListener('click',()=>{if(pinned)hide();else{show();pinned=true}});
   button.addEventListener('keydown',event=>{if(event.key==='Escape'){hide();event.stopPropagation()}});
   item.append(button,tip);bar.append(item);
  });
  const dismiss=()=>closeAll.forEach(close=>close());
  document.addEventListener('pointerdown',event=>{if(!bar.contains(event.target))dismiss()});
  window.addEventListener('resize',dismiss);window.addEventListener('scroll',dismiss,{passive:true});
  return bar;
 },
 panel(fields,title='How confident is this entry?') {const box=document.createElement('section');box.className='confidence-panel';const h=document.createElement('h3');h.textContent=title;box.append(h);const list=document.createElement('dl');Object.entries(fields||{}).forEach(([key,c])=>{if(key==='overall'||!c?.level)return;const row=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.append(this.badge(c,key.charAt(0).toUpperCase()+key.slice(1)));dd.textContent=c.reason||'Further research needed.';row.append(dt,dd);list.append(row)});box.append(list);const l=document.createElement('a');l.href='research.html#confidence';l.textContent='How confidence is assigned →';box.append(l);return box;}
};
