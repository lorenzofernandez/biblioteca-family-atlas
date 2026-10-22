/* The same reading layout and catalogue facts in the book page and card viewer. */
(() => {
 'use strict';
 const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;if(cls)n.className=cls;return n;};
 const safe=url=>typeof url==='string'&&/^(https?:\/\/|originals\/|sources\/|images\/|book-images\/|author-images\/|portraits\/)/.test(url);
 const link=(text,url)=>{const n=el('a',text);n.href=url;if(/^https?:/.test(url)){n.target='_blank';n.rel='noopener';}return n;};
 const fmt=n=>Number(n).toLocaleString('en-US');
 function coverCandidates(record){
  const candidates=[...(record.research?.images||[]),...(record.onlineCandidates||[]).flatMap(c=>(c.images||[]).map(i=>({...i,sourceUrl:i.sourceUrl||c.url,credit:i.credit||c.source})))];
  const seen=new Set();return candidates.filter(i=>{const src=i.src||i.url;if(!safe(src)||seen.has(src))return false;seen.add(src);return true;}).sort((a,b)=>Number(isCover(b))-Number(isCover(a)));
 }
 const isCover=image=>/\b(cover|binding)\b/i.test(image.label||'')&&!/unverified|not |no /i.test(image.label||'');
 function cover(record){return coverCandidates(record)[0]||null;}
 function mountCover(target,caption,record,geography){
  const candidates=coverCandidates(record);let index=0;
  const next=()=>{
   const candidate=candidates[index++];
   if(!candidate){target.replaceChildren(LibraryGeneratedCovers.create(record,geography));caption.replaceChildren(LibraryGeneratedCovers.caption(record,geography));return;}
   const image=el('img');image.alt=(isCover(candidate)?'Reference cover: ':'Reference image: ')+(record.title||'Catalogue record');image.loading='lazy';
   image.onerror=()=>{if(target.contains(image))next();};
   target.replaceChildren(image);caption.replaceChildren(coverCaption(candidate));image.src=candidate.src||candidate.url;
  };next();
 }
 function coverCaption(image){
  const caption=el('div',null,'reading-cover-caption');
  if(!image){caption.textContent='Original catalogue card';return caption;}
  caption.append(el('span',isCover(image)?'Reference cover':'Reference image'));
  const details=el('details');details.append(el('summary','Image source'));
  if(image.credit)details.append(el('p',image.credit));
  details.append(el('p',image.editionRelation||'A reference copy; the family’s binding and edition may differ.'));
  if(safe(image.sourceUrl))details.append(link('View source ↗',image.sourceUrl));
  caption.append(details);return caption;
 }
 function facts(record,estimate,geography){
  const box=el('section',null,'reading-facts');box.setAttribute('aria-label','Key facts');box.append(el('h2','Key facts'));
  const list=el('dl'),row=(label,value,note)=>{const pair=el('div');pair.append(el('dt',label));const dd=el('dd');typeof value==='string'?dd.textContent=value:dd.append(value);if(note)dd.append(el('small',note));pair.append(dd);list.append(pair);};
  row('Date',record.year?String(record.year):'Not recorded');
  const hit=geography?.records?.[record.id],country=hit&&geography.countries?.[hit[0]]?.name;
  const imprint=record.research?.imprint||'',referencePlace=/^Reference imprint:/i.test(imprint),researchedPlace=imprint.replace(/^Reference imprint:\s*/i,'').split(/[·,:]/)[0].trim();
  row('Place',hit?[hit[1],country].filter((v,i,a)=>v&&a.indexOf(v)===i).join(', '):researchedPlace||'Not recorded',!hit&&researchedPlace?(referencePlace?'Reference copy · tentative match':'From edition research'):null);
  const names=record.authorNames||[],ids=record.authors||[],by=el('span');
  names.forEach((name,i)=>{if(i)by.append(' · ');by.append(ids[i]?link(name,'author.html?id='+ids[i]):document.createTextNode(name));});
  row('Author',names.length?by:record.heading||'Not identified');
  const count=record.research?.documentedCopies;
  if(estimate)row('Scarcity','≈ '+fmt(estimate.min)+'–'+fmt(estimate.max)+' surviving copies','Ballpark · '+(estimate.confidence||'low').replaceAll('-',' ')+' confidence');
  else if(count!=null)row('Scarcity','At least '+fmt(count)+' documented '+(count===1?'copy':'copies'),'Worldwide total not established');
  else row('Scarcity','Not established');
  box.append(list);return box;
 }
 function authors(record,profiles,{dark=false,onOpenAuthor=null,authorHref=id=>'author.html?id='+id}={}){
  const box=el('section',null,'reading-authors'+(dark?' reading-dark':'')),heading=el('div',null,'reading-authors-heading'),title=el('h2','About the author'+((record.authors?.length||0)>1?'s':''));
  box.setAttribute('aria-label',title.textContent);heading.append(title);box.append(heading);
  if(!profiles.length){box.append(el('p','The author has not yet been identified.'));return box;}
  const track=el('div',null,'reading-author-track');track.tabIndex=0;track.setAttribute('aria-label','Author profiles');box.append(track);
  profiles.forEach((author,i)=>{
   const name=author?.displayName||record.authorNames?.[i]||'Author unidentified',candidate=author?.possibleIdentity,card=el('article',null,'reading-author-card'),figure=el('figure'),body=el('div',null,'reading-author-body');
   card.setAttribute('role','group');card.setAttribute('aria-label',`${i+1} of ${profiles.length}: ${name}`);
   const fallback=()=>el('div',name.split(/\s+/).filter(Boolean).slice(0,2).map(v=>v[0]).join(''),'reading-monogram');
   if(safe(author?.portrait)){const img=el('img');img.src=author.portrait;img.alt='Reference portrait of '+(candidate||name);img.loading='lazy';img.onerror=()=>{img.replaceWith(fallback());};figure.append(img);if(safe(author.portraitSource)){const caption=el('figcaption');caption.append(link('Image source ↗',author.portraitSource));figure.append(caption);}}
   else figure.append(fallback());
   const authorId=record.authors?.[i],openLink=(text,cls)=>{const a=link(text,authorHref(authorId));if(cls)a.className=cls;if(onOpenAuthor)a.onclick=e=>{if(e.button||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;e.preventDefault();onOpenAuthor(authorId);};return a;};
   const heading=el('h3');if(onOpenAuthor&&authorId){card.dataset.authorId=authorId;heading.append(openLink(name,'reading-author-open'));}else heading.textContent=name;body.append(heading);
   if(author?.lifeLabel||author?.origins?.length)body.append(el('p',[author.lifeLabel,author.origins?.join(', ')].filter(Boolean).join(' · '),'reading-author-dates'));
   const confidence=author?.confidence?.identity||{level:'unresolved'},biography=LibraryConfidence.biography(author||{}),confidenceRow=el('div',null,'author-confidence-row');
   confidenceRow.append(LibraryConfidence.indicator(confidence,'Identity'),LibraryConfidence.indicator(biography.confidence,'Biography'));body.append(confidenceRow);
   if(candidate&&candidate!==name&&confidence.level!=='high')body.append(el('p','Possible identity: '+candidate,'reading-identity'));
   if(biography.hasBiography)body.append(el('p',biography.summary,'reading-author-bio'));
   else body.append(el('p','A biography is not yet available for this author.','reading-author-bio reading-author-bio-empty'));
   const actions=el('div',null,'reading-author-links');if(record.authors?.[i])actions.append(openLink('Explore the author →'));
   if(biography.hasBiography){
    if(author.bioSources?.length){const seen=new Set();author.bioSources.forEach(source=>{if(!safe(source.url)||seen.has(source.url))return;seen.add(source.url);actions.append(link((source.title||'Biography source')+' ↗',source.url));});}
    else if(safe(author?.bioSource))actions.append(link((author.bioSourceTitle||'Biography source')+' ↗',author.bioSource));
    if(author.bioLicense)actions.append(el('small',author.bioLicense,'reading-biography-license'));
   }
   card.append(figure,body,actions);track.append(card);
  });
  if(profiles.length===1)return box;
  box.setAttribute('aria-roledescription','carousel');
  const controls=el('div',null,'reading-author-controls'),position=el('span','1 / '+profiles.length),prev=el('button','←'),next=el('button','→');position.setAttribute('aria-live','polite');position.setAttribute('aria-atomic','true');
  [[prev,'Previous author'],[next,'Next author']].forEach(([b,label])=>{b.type='button';b.setAttribute('aria-label',label);});controls.append(position,prev,next);heading.append(controls);
  const cards=[...track.children];let index=0,frame;
  const update=()=>{index=cards.reduce((best,card,i)=>Math.abs(card.offsetLeft-cards[0].offsetLeft-track.scrollLeft)<Math.abs(cards[best].offsetLeft-cards[0].offsetLeft-track.scrollLeft)?i:best,0);position.textContent=(index+1)+' / '+cards.length;prev.disabled=track.scrollLeft<=2;next.disabled=track.scrollLeft>=track.scrollWidth-track.clientWidth-2;};
  const go=i=>{i=Math.max(0,Math.min(cards.length-1,i));track.scrollTo({left:cards[i].offsetLeft-cards[0].offsetLeft,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});};
  prev.onclick=()=>go(index-1);next.onclick=()=>go(index+1);
  box.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();e.stopPropagation();go(e.key==='Home'?0:e.key==='End'?cards.length-1:index+(e.key==='ArrowLeft'?-1:1));});
  track.addEventListener('scroll',()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(update);},{passive:true});const observer=new ResizeObserver(update);observer.observe(track);box.dispose=()=>{observer.disconnect();cancelAnimationFrame(frame);};requestAnimationFrame(update);return box;
 }
 window.LibraryBookReading={cover,coverCandidates,coverCaption,mountCover,facts,authors};
})();
