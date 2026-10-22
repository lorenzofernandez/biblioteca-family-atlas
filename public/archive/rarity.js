'use strict';
// Counts of located copies are lower bounds, never estimates of total survivors.
window.LibraryRarity={
 classify(record,threshold,includeTentative,basis='counts'){
  if(!record)return {key:'unknown',confidence:'unresolved',reason:'No edition-specific survival research yet.'};
  const valid=Number.isFinite, range=record.range||{},sameEdition=['high','medium'].includes(record.editionConfidence);
  const minimum=valid(record.minimum)?record.minimum:range.min;
  if(sameEdition&&valid(minimum)&&minimum>=threshold&&['high','medium'].includes(record.evidenceConfidence))return {key:'nonrare',confidence:record.editionConfidence==='high'&&record.evidenceConfidence==='high'?'high':'medium',reason:'At least '+minimum.toLocaleString()+' documented copies: this already reaches the selected threshold.'};
  if(sameEdition&&valid(range.max)&&range.max<threshold&&['high','medium'].includes(range.confidence))return {key:'rare',confidence:record.editionConfidence==='high'&&range.confidence==='high'?'high':'medium',reason:'The supported worldwide range is entirely below the selected threshold.'};
  if(basis==='sources'&&includeTentative&&record.qualitative?.applicable){
   const q=record.qualitative;return {key:'possible',confidence:'low',reason:q.reason+' Edition connection: '+q.matchConfidence+' confidence. '+q.scope};
  }
  if(!sameEdition)return {key:'unknown',confidence:'unresolved',reason:'The connection to this edition still needs checking.'};
  if(includeTentative&&record.census&&valid(minimum)&&minimum<threshold)return {key:'possible',confidence:'low',reason:'A published census records '+minimum+' known copies, below the threshold. Undiscovered copies could change the classification.'};
  if(includeTentative&&valid(record.conditionalBounds?.maxApprox)&&record.conditionalBounds.maxApprox<threshold)return {key:'possible',confidence:'low',reason:'A conditional ceiling of about '+record.conditionalBounds.maxApprox+' copies is below the threshold, assuming the historical print-run estimate is correct.'};
  return {key:'unknown',confidence:'unresolved',reason:valid(minimum)?'At least '+minimum+' copies are documented, but the unknown upper bound prevents a rarity classification.':'No comparable count of complete copies has been established.'};
 },
 async mount(overview){
  const make=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
  const link=(text,url)=>{const n=make('a',text);n.href=url;return n;};
  const number=n=>n.toLocaleString();
  const section=make('section',undefined,'rarity-section');section.id='bookRarity';section.setAttribute('aria-labelledby','rarityTitle');
  const title=make('h3','How rare are the books?');title.id='rarityTitle';
  section.append(make('div','RARITY','eyebrow'),title);overview.append(section);
  try{
   const response=await fetch('rarity-data.json',{cache:'no-cache'});if(!response.ok)throw Error('Rarity data unavailable');const data=await response.json();
   const classified=data.records.map(record=>({record,...LibraryRarity.classify(record,data.defaultThreshold,true,'sources')}));
   const counts={rare:0,possible:0,nonrare:0,unknown:data.total-classified.length};classified.forEach(r=>counts[r.key]++);
   const groups=[{key:'rare',label:'Rare',note:'Supported surviving-copy estimate',color:'#3b5b48'},{key:'possible',label:'Potentially rare',note:'Low confidence',color:'#b29650'},{key:'nonrare',label:'More widely surviving',note:'At least '+number(data.defaultThreshold)+' documented copies',color:'#8a9eac'},{key:'unknown',label:'Rarity undetermined',note:'Could be rare or common',color:'#d5d4c7'}].filter(g=>counts[g.key]);
   const answer=make('p',undefined,'rarity-answer');
   if(counts.rare||counts.possible){
    if(counts.rare)answer.append(make('strong',number(counts.rare)+' entries have evidence of rarity. '));
    if(counts.possible)answer.append(make('strong',number(counts.possible)+' entries may be rare. '));
    answer.append(counts.unknown>data.total/2?'For most of the collection, rarity is still undetermined.':'The breakdown below shows how much is known.');
   }else answer.textContent='The available evidence does not yet establish how much of the collection is rare.';
   section.append(answer);
   const bar=make('div',undefined,'rarity-bar'),stats=make('div',undefined,'rarity-stats');stats.style.setProperty('--rarity-groups',groups.length);bar.setAttribute('role','img');
   groups.forEach(g=>{const count=counts[g.key],percent=(100*count/data.total).toFixed(1)+'%',segment=make('span');segment.style.width=(100*count/data.total)+'%';segment.style.background=g.color;segment.title=g.label+': '+number(count)+' ('+percent+')';bar.append(segment);
    const cell=make('div',undefined,'rarity-stat'),label=make('div',undefined,'rarity-stat-label'),swatch=make('i');swatch.style.background=g.color;label.append(swatch,make('span',g.label));cell.append(label,make('b',number(count)),make('span',percent+' of the catalogue','rarity-percent'),make('small',g.note));stats.append(cell);
   });
   bar.setAttribute('aria-label',groups.map(g=>g.label+': '+number(counts[g.key])+' catalogue entries').join('. '));
   const card=make('div',undefined,'rarity-card');card.append(bar,stats);section.append(card);
   const findings=classified.filter(r=>r.key==='rare'||r.key==='possible').sort((a,b)=>(a.record.year??9999)-(b.record.year??9999));
   if(findings.length){
    const details=make('details',undefined,'rarity-details'),list=make('div',undefined,'rarity-records');details.append(make('summary','Explore the '+number(findings.length)+' potentially rare entries'),list);
    let populated=false;details.addEventListener('toggle',()=>{if(!details.open||populated)return;populated=true;findings.forEach(result=>{const r=result.record,row=make('article'),heading=make('div',undefined,'rarity-record-heading');heading.append(link((r.year?r.year+' · ':'')+r.title,'book.html?id='+r.id));if(window.LibraryConfidence)heading.append(LibraryConfidence.dot({level:result.confidence,reason:result.reason},'Rarity'));row.append(heading);
     const sources=result.key==='possible'&&r.qualitative?.applicable?r.qualitative.sources:r.sources;
     if(sources?.length){const citations=make('div',undefined,'rarity-citations');sources.forEach(s=>{const source=link(s.title+' ↗',s.url);source.target='_blank';source.rel='noopener';citations.append(source)});row.append(citations)}list.append(row);
    })});section.append(details);
   }
   const method=make('details',undefined,'rarity-method');method.append(make('summary','About these figures'),make('p','Potentially rare entries are linked to specialist descriptions of scarcity, published censuses or limited-printing evidence. These are tentative judgments, with low confidence. A book’s age alone does not establish rarity.'),make('p','For numerical evidence, “rare” means fewer than '+number(data.defaultThreshold)+' surviving copies worldwide. '+(counts.rare||counts.nonrare?'':'No entry currently has enough numerical evidence to confirm a rare or non-rare classification at that threshold. ')+ 'Unknown entries may be rare or common.'),make('p','The '+number(data.total)+' entries include books, papers, volumes and cross-references, so they are not a count of distinct physical books. The sources cover selected subjects and cannot establish the rarity of the collection as a whole.'));
   const estimateSlot=make('div');estimateSlot.id='circulationCoverage';method.append(estimateSlot);
   const context=link('Sources and estimate method →','circulation.html'),research=link('Full research notes →','research.html');method.append(context,research,make('p','Sources checked '+data.checked+'.','rarity-checked'));section.append(method);
   // The optional estimate summary never blocks the primary answer.
   fetch('circulation-coverage.json').then(r=>{if(!r.ok)throw Error('Estimate coverage unavailable');return r.json()}).then(c=>{estimateSlot.append(make('p','Approximate surviving-copy ranges are available for '+number(c.estimated)+' entries ('+(100*c.estimated/c.total).toFixed(0)+'%). Confidence is low or very low. These broad ranges often span both rare and common, so they do not settle the rarity classification.'),link('Browse books with copy estimates →','books.html?status=estimated#bookSearch'));}).catch(error=>console.error(error));
   if(location.hash==='#circulationCoverage'){method.open=true;estimateSlot.scrollIntoView({block:'start'})}else if(location.hash==='#bookRarity')section.scrollIntoView({block:'start'});
  }catch(error){section.append(make('p','Rarity information could not load. Please refresh to try again.'));console.error(error)}
 }
};
