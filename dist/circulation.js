'use strict';
window.LibraryCirculation=(()=>{
 let index,model,pending;
 const make=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
 const link=(text,url)=>{const e=make('a',text);e.href=url;return e;};
 const number=n=>n.toLocaleString(),label=e=>number(e.min)+'–'+number(e.max);
 async function ready(){
  pending??=Promise.all([LibraryData.json('circulation-estimates-index.json'),fetch('circulation-model.json').then(r=>{if(!r.ok)throw Error('Estimate method unavailable');return r.json()})]).then(([i,m])=>{index=i;model=m;});
  return pending;
 }
 async function record(id){await ready();if(!index.records[id])return null;const shard=await LibraryData.json('circulation-estimates/'+id.slice(1,3)+'.json');return shard[id]||null;}
 function attach(books){books.forEach(b=>{b.circulationEstimate=index?.records[b.id]||null});}
 function badge(e){return LibraryConfidence.badge({level:e.confidence,reason:model.confidence[e.confidence]},'Ballpark');}
 function teaser(e,host){
  if(!e)return;
  const card=make('div',undefined,'circulation-teaser');
  card.append(make('span','Estimated surviving copies','eyebrow'),make('b','≈ '+label(e)),badge(e),link('Assumptions & sources ↓','#survivalEstimate'));host.append(card);
 }
 function render(e,host){
  if(!e)return;
  const cohort=model.cohorts.find(c=>c.id===e.cohort),card=make('div',undefined,'circulation-estimate');card.id='survivalEstimate';
  card.append(make('div','BALLPARK ESTIMATE · WORLDWIDE','eyebrow'),make('div','≈ '+label(e),'circulation-range'),badge(e),make('p',e.scope+'. This is an uncalibrated scenario range; the actual total may lie outside it. It includes possible private and institutional survivors, not just copies available for sale.'));
  const details=make('details'),summary=make('summary','Why this range?');details.append(summary,make('p',cohort.label+(e.year?' · catalogue year '+e.year:'. Catalogue year unresolved.')));
  details.append(make('p','Assumed original print run: '+number(cohort.printRun[0])+'–'+number(cohort.printRun[1])+'. Assumed surviving fraction: '+(cohort.survivingFraction[0]*100)+'–'+(cohort.survivingFraction[1]*100)+'%. Both are scenario inputs, not observations of this edition.'));
  details.append(make('p',model.method),make('p',model.confidence[e.confidence]));
  e.notes.forEach(note=>details.append(make('p',note)));
  if(e.documentedMinimumApplied)details.append(make('p','The lower end is constrained by the existing documented minimum of '+e.documentedMinimumApplied+' copies. Those sources were not multiplied into a population estimate.'));
  details.append(make('h4','Sources for the inputs'));
  const sources=make('ul');e.sources.forEach(s=>{const li=make('li'),a=link(s.title+' ↗',s.url);a.target='_blank';a.rel='noopener';li.append(a,make('p',s.role));sources.append(li)});details.append(sources);
  details.append(link('Full model, assumptions & historical context →','circulation.html'));card.append(details,make('p','Generated '+model.checked+' · '+model.version+' · confidence is an editorial judgment, not a statistical probability.','caption'));host.append(card);
 }
 async function mountSummary(host){
  try{await ready();const card=make('section',undefined,'circulation-overview');card.id='circulationCoverage';
   card.append(make('div','A BROADER VIEW OF SURVIVAL','eyebrow'),make('h3',number(index.estimated)+' ballpark estimates.'),make('p','Broad ranges now cover '+(100*index.estimated/index.total).toFixed(1)+'% of catalogue records. They use explicit assumptions about print runs and survival; they are additional to the source evidence in the rarity chart below.'));
   const bar=make('div',undefined,'circulation-coverage-bar'),fill=make('span');fill.style.width=(100*index.estimated/index.total)+'%';bar.setAttribute('role','img');bar.setAttribute('aria-label',number(index.estimated)+' model estimates out of '+number(index.total)+' catalogue records');bar.append(fill);card.append(bar);
   const stats=make('div',undefined,'circulation-stats');[[index.confidenceCounts.low||0,'Low confidence · reviewed edition'],[index.confidenceCounts['very-low']||0,'Very low confidence · tentative inputs'],[index.total-index.estimated,'Outside the generic model']].forEach(([n,t])=>{const cell=make('div');cell.append(make('b',number(n)),make('span',t));stats.append(cell)});card.append(stats);
   const actions=make('div',undefined,'circulation-links');actions.append(link('Browse entries with estimates →','books.html?status=estimated#bookSearch'),link('How the estimates work →','circulation.html'));card.append(actions);
   card.append(make('p','Models do not add to the count of researched or verified entries. A broad range crossing the rarity threshold cannot establish whether a book is rare. Cross-references, incomplete sets and other unsuitable records remain outside this model.','caption'));host.append(card);
  }catch(error){console.error(error);}
 }
 async function mountMethod(host){
  try{await ready();host.replaceChildren();host.append(make('div','SURVIVAL / EXPLORATORY ESTIMATES','eyebrow'),make('h1','A ballpark, with its assumptions.'),make('p',model.description,'book-intro'),make('p',model.method),link('Browse '+number(index.estimated)+' entries with estimates →','books.html?status=estimated#bookSearch'));
   const notice=make('div',undefined,'circulation-method-notice');notice.append(make('h2','What is known, and what is assumed.'),make('p','Catalogue cards and bibliographic sources supply dates, format clues and edition connections. The numerical print runs and survival rates below are broad editorial assumptions. They are not source-reported counts for each book, and have not been calibrated against a representative sample.'));
   notice.append(make('p','Low confidence: an individually reviewed edition, but assumed production and survival. Very low confidence: edition, date or format also uncertain. These estimates never become high confidence just because a source match is strong.'));host.append(notice);
   const wrap=make('div',undefined,'circulation-table-wrap'),table=make('table'),head=make('thead'),tr=make('tr');['Scenario','Assumed print run','Assumed surviving fraction','Records'].forEach(t=>tr.append(make('th',t)));head.append(tr);table.append(head);const body=make('tbody');model.cohorts.forEach(c=>{const row=make('tr');[c.label,number(c.printRun[0])+'–'+number(c.printRun[1]),(c.survivingFraction[0]*100)+'–'+(c.survivingFraction[1]*100)+'%',number(index.cohorts[c.id]||0)].forEach(t=>row.append(make('td',t)));body.append(row)});table.append(body);wrap.append(table);host.append(wrap);
   host.append(make('h2','Where the model stops.'));const rules=make('ul');model.rules.forEach(t=>rules.append(make('li',t)));host.append(rules);
   const exclusions=make('details');exclusions.append(make('summary',number(index.total-index.estimated)+' records outside the generic model'));const list=make('ul');Object.entries(index.excluded).forEach(([name,n])=>list.append(make('li',name+': '+number(n))));exclusions.append(list);host.append(exclusions);
   host.append(make('h2','Historical context, not calibration.'));model.sources.forEach(s=>{const p=make('p'),a=link(s.title+' ↗',s.url);a.target='_blank';a.rel='noopener';p.append(a,make('span',' — '+s.role));host.append(p)});
   host.append(make('p','Example: the 1728 Pemberton edition receives a rounded scenario range of about 10–2,000 surviving copies. The date and edition connection are sourced; the 250–3,000 initial copies and 5–50% survival are assumptions, not a newly discovered census.'));
   const actions=make('div',undefined,'circulation-links');actions.append(link('Example: Pemberton, 1728 →','book.html?id=w0ddcff4e34a0#survivalEstimate'),link('Download model inputs ↗','circulation-model.json'),link('Download estimate index (.json.gz) ↗','circulation-estimates-index.json.gz'));host.append(actions,make('p','Model '+model.version+' · generated '+model.checked+'.','caption'));
  }catch(error){host.replaceChildren(make('p','The estimate method could not load. Please refresh.'));console.error(error)}
 }
 return {ready,record,attach,teaser,render,mountSummary,mountMethod,label};
})();
if(document.querySelector('#circulationMethod'))LibraryCirculation.mountMethod(document.querySelector('#circulationMethod'));
