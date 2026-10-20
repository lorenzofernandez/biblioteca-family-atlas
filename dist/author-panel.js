/* Author information stays beside the book, and can expand into a reading view. */
(() => {
 'use strict';
 const el=(tag,text,cls)=>{const node=document.createElement(tag);if(text!=null)node.textContent=text;if(cls)node.className=cls;return node;};
 const safe=url=>typeof url==='string'&&/^(https?:\/\/|portraits\/|author-images\/|images\/)/.test(url);
 const external=(text,url)=>{const a=el('a',text);a.href=url;a.target='_blank';a.rel='noopener';return a;};
 window.LibraryAuthorPanel={create({loadProfile,loadWorks,cardHref,onClose,onFullscreen,onCard,onCanonical,loadNeighbours,authorHref,onNavigate}){
  const dialog=document.querySelector('#authorPanel'),content=document.querySelector('#authorPanelContent'),expand=document.querySelector('#authorPanelExpand');
  let token=0,currentId=null,currentFull=false,neighbours=null;
  const closeButton=dialog.querySelector('.author-panel-close');closeButton.onclick=onClose;
  dialog.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();onClose();}else if(!e.target.closest('input,textarea,select,[contenteditable=true],.author-alternatives-track')&&!e.altKey&&!e.metaKey&&!e.ctrlKey&&(e.key==='ArrowLeft'||e.key==='ArrowRight')){const next=e.key==='ArrowLeft'?neighbours?.previous:neighbours?.next;if(next){e.preventDefault();onNavigate(next.id);}}});
  dialog.addEventListener('cancel',e=>{e.preventDefault();onClose();});
  dialog.addEventListener('click',e=>{if(e.target!==dialog)return;const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)onClose();});
  expand.onclick=()=>onFullscreen(!currentFull);
  function fullscreen(value){currentFull=value;dialog.classList.toggle('is-fullscreen',value);expand.textContent=value?'Side panel':'Full screen';expand.setAttribute('aria-label',value?'Return author to side panel':'Open author full screen');expand.setAttribute('aria-pressed',String(value));}
  function close(){++token;currentId=null;if(dialog.open)dialog.close();document.body.classList.remove('author-panel-open');}
  async function open(id,{full=false}={}){
   fullscreen(true);document.body.classList.add('author-panel-open');if(!dialog.open){dialog.showModal();closeButton.focus({preventScroll:true});}
   if(currentId===id)return;
   currentId=id;neighbours=null;dialog.dataset.authorId=id;dialog.scrollTop=0;const request=++token;
   const loadingTitle=el('h2','Opening the author…');loadingTitle.id='authorPanelTitle';content.replaceChildren(loadingTitle);content.setAttribute('aria-busy','true');
   try{
    const author=await loadProfile(id);if(request!==token)return;if(!author)throw Error('Author not found');
    if(author.id!==id){currentId=author.id;dialog.dataset.authorId=author.id;onCanonical(author.id);}
    const name=author.displayName||author.name;
    document.title=name+' · Biblioteca';
    const hero=el('div',null,'author-panel-hero'),portrait=el('figure',null,'author-panel-portrait'),intro=el('div',null,'author-panel-intro');
    const monogram=()=>el('div',name.split(/\s+/).slice(0,2).map(s=>s[0]).join(''),'author-panel-monogram');
    if(safe(author.portrait)){const img=el('img');img.src=author.portrait;img.alt='Reference portrait of '+(author.possibleIdentity||name);img.onerror=()=>{portrait.remove();titleCard.classList.remove('has-portrait');};portrait.append(img);if(safe(author.portraitSource)){const caption=el('figcaption');caption.append(external('Image source ↗',author.portraitSource));portrait.append(caption);}}else portrait.append(monogram());
    const heading=el('h2',name);heading.id='authorPanelTitle';intro.append(heading);
    const dates=[author.lifeLabel,...(author.origins||[])].filter(Boolean).join(' · ');if(dates)intro.append(el('p',dates,'author-panel-dates'));
    const confidence=author.confidence?.identity||{level:author.confidence?.overall||'unresolved',reason:''};
    const presentation=LibraryConfidence.biography(author),confidenceRow=el('div',null,'author-confidence-row');confidenceRow.append(LibraryConfidence.indicator(confidence,'Identity'),LibraryConfidence.indicator(presentation.confidence,'Biography'));intro.append(confidenceRow);
    if(author.possibleIdentity&&author.possibleIdentity!==name)intro.append(el('p','Possible identification: '+author.possibleIdentity,'author-panel-candidate'));
    const biography=el('div',null,'author-panel-biography');
    if(!presentation.hasBiography)biography.append(el('p',presentation.label,'biography-context-label'));
    presentation.text.split(/\n\s*\n/).forEach(paragraph=>biography.append(el('p',paragraph)));
    if(presentation.hasBiography&&author.bioSources?.length){
     const sources=el('div',null,'author-panel-sources');sources.setAttribute('aria-label','Biography sources');
     const seen=new Set();author.bioSources.forEach(item=>{if(!safe(item.url)||seen.has(item.url))return;seen.add(item.url);const source=el('p',null,'author-panel-source');source.append(external(item.title+' ↗',item.url));sources.append(source);});
     if(author.bioLicense)sources.append(el('p',author.bioLicense,'author-panel-source biography-license'));
     biography.append(sources);
    }else if(presentation.hasBiography&&safe(author.bioSource)){
     const source=el('p',null,'author-panel-source');source.append(external(author.bioSourceTitle||'Biography source',author.bioSource));
     if(author.bioLicense)source.append(' · '+author.bioLicense);else if(/wikipedia\.org\//.test(author.bioSource)){source.append(' · ');source.append(external('CC BY-SA 4.0','https://creativecommons.org/licenses/by-sa/4.0/'));}
     biography.append(source);
    }
    const titleCard=el('header',null,'author-title-card');titleCard.append(heading);titleCard.append(el('p',dates||'Life dates not verified','author-panel-dates'));
    if(safe(author.portrait)){titleCard.classList.add('has-portrait');titleCard.prepend(portrait);}
    const carousel=el('div',null,'author-title-carousel');carousel.append(titleCard);
    const sidebar=el('aside',null,'author-reading-sidebar'),main=el('div',null,'author-reading-main');intro.append(biography);main.append(intro);hero.append(sidebar,main);content.replaceChildren(carousel,hero);
    const alternatives=(author.identityCandidates||[]).filter(c=>!author.possibleIdentity||c.candidateName!==author.possibleIdentity);
    if(alternatives.length){const section=el('section',null,'author-panel-alternatives'),heading=el('div',null,'author-alternatives-heading'),track=el('div',null,'author-alternatives-track');heading.append(el('h3','Other possible identities'));const controls=el('div'),prev=el('button','←'),next=el('button','→');prev.type=next.type='button';prev.setAttribute('aria-label','Previous possible identity');next.setAttribute('aria-label','Next possible identity');controls.append(prev,next);heading.append(controls);section.append(heading,track);track.tabIndex=0;track.setAttribute('aria-label','Other possible identities');section.setAttribute('aria-roledescription','carousel');alternatives.forEach(candidate=>{const card=el('article');card.append(el('h4',candidate.candidateName),el('p',[candidate.birth,candidate.death].filter(Boolean).join('–')),LibraryConfidence.indicator(candidate.confidence||{level:'low'},'Identity'),el('p',candidate.bioShort||candidate.bio||candidate.description||'Biographical details unavailable.'));const source=candidate.authorityUrl||candidate.sourceUrl;if(safe(source))card.append(external('Source ↗',source));track.append(card);});prev.onclick=()=>track.scrollBy({left:-track.clientWidth,behavior:'smooth'});next.onclick=()=>track.scrollBy({left:track.clientWidth,behavior:'smooth'});main.append(section);}
    if(loadNeighbours)loadNeighbours(author.id).then(result=>{if(request!==token)return;neighbours=result;const nav=el('nav',null,'author-profile-navigation');nav.setAttribute('aria-label','Previous and next authors');for(const [key,label] of [['previous','Previous author'],['next','Next author']]){const other=result[key];if(!other){const placeholder=el('span');nav.append(placeholder);continue;}const link=el('a',null,'author-neighbour author-neighbour-'+key);link.href=authorHref(other.id);link.setAttribute('aria-label',label+': '+other.displayName);if(safe(other.portrait)){const image=el('img');image.src=other.portrait;image.alt='';link.append(image);}else link.append(el('span',other.displayName.split(/\s+/).slice(0,2).map(s=>s[0]).join(''),'author-neighbour-monogram'));const copy=el('span');copy.append(el('small',key==='previous'?'← Previous author':'Next author →'),el('strong',other.displayName),el('span',other.lifeLabel||''));link.append(copy);link.onclick=e=>{if(e.button||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;e.preventDefault();onNavigate(other.id);};nav.append(link);}const position=el('span',(result.index+1).toLocaleString()+' / '+result.total.toLocaleString(),'author-profile-position');nav.append(position);carousel.append(nav);}).catch(()=>{});
    const facts=el('dl',null,'author-panel-facts');
    for(const [label,value] of [['Catalogue records',author.recordCount],['Cross-references',author.referenceCount]]){if(value==null)continue;const item=el('div');item.append(el('dt',label),el('dd',Number(value).toLocaleString('en-US')));facts.append(item);}const factsTitle=el('h3','Key facts');sidebar.append(factsTitle,facts);
    for(const [label,value] of [['Years',author.lifeLabel],['Origin',(author.origins||[]).join(' · ')]]){if(value){const item=el('div');item.append(el('dt',label),el('dd',value));facts.append(item);}}
    if(author.aliases?.length){const names=el('details',null,'author-panel-aliases');names.append(el('summary','Names in the catalogue'),el('p',author.aliases.join(' · ')));main.append(names);}
    const section=el('section',null,'author-panel-works');section.append(el('h3','In the collection'));const host=el('div');host.append(el('p','Loading connected cards…'));section.append(host);main.append(section);const footer=el('p','Biographies and identity matches retain their own confidence and sources.','transcription-note');main.append(footer);content.setAttribute('aria-busy','false');
    try{
     const works=await loadWorks(currentId);if(request!==token)return;
     let limit=20;const search=el('input');search.type='search';search.placeholder='Search this author’s cards…';search.setAttribute('aria-label','Search connected cards');
     const count=el('p',null,'author-panel-count'),list=el('div',null,'author-panel-work-list'),more=el('button','Show more cards','author-panel-more');more.type='button';host.replaceChildren(search,count,list,more);
     function render(){const query=search.value.toLocaleLowerCase(),matching=works.filter(w=>(w.title+' '+(w.year||'')).toLocaleLowerCase().includes(query));count.textContent=matching.length.toLocaleString('en-US')+' connected cards';list.replaceChildren();
      for(const work of matching.slice(0,limit)){const a=el('a',null,'author-panel-work');a.href=cardHref(work.id);a.dataset.cardId=work.id;a.append(el('span',work.year||'Undated'),el('strong',work.title||work.heading||'Catalogue card'),el('span','↗','author-work-arrow'));a.onclick=e=>{if(e.button||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;e.preventDefault();onCard(work.id);};list.append(a);}
      if(!matching.length)list.append(el('p',works.length?'No cards match this search.':'No connected cards are available.'));more.hidden=matching.length<=limit;
     }
     search.oninput=()=>{limit=20;render();};more.onclick=()=>{limit+=20;render();};render();
    }catch{if(request===token)host.replaceChildren(el('p','Connected cards could not load. Please try again.'));}
   }catch{if(request!==token)return;const errorTitle=el('h2','Author unavailable');errorTitle.id='authorPanelTitle';content.replaceChildren(errorTitle,el('p','This author could not be found or loaded. Close the panel and try again.'));content.setAttribute('aria-busy','false');}
  }
  return {open,close,get id(){return currentId;},get isOpen(){return dialog.open;}};
 }};
})();
