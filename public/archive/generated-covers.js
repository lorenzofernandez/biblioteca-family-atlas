/* Imagined covers, composed from generated ornament and catalogue metadata.
 * They are a presentation fallback, never a historical image or research source. */
(() => {
 'use strict';
 const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;if(cls)n.className=cls;return n;};
 let geographyPromise;
 const ready=()=>geographyPromise||(geographyPromise=LibraryData.json('cards-assets/geography.json').catch(()=>null));
 const regions={ITA:'italian',FRA:'french',GBR:'anglo',IRL:'anglo',USA:'anglo',CAN:'anglo',AUS:'anglo',DEU:'northern',AUT:'northern',NLD:'northern',BEL:'northern',CHE:'northern'};
 function design(record,geography){
  const hit=geography?.records?.[record.id],code=hit?.[0],country=geography?.countries?.[code]?.name;
  const knownPlace=country&&!['UNKNOWN','MULTI'].includes(code);
  const place=knownPlace?[hit[1],country].filter((v,i,a)=>v&&a.indexOf(v)===i).join(', '):'';
  const raw=Number(record.year),year=Number.isInteger(raw)&&raw>=1400&&raw<=2030?raw:null;
  const period=year?(year<1800?'early':year<1920?'industrial':'modern'):'undated';
  let region=knownPlace?regions[code]:null;
  if(['CHE','BEL'].includes(code)&&/gen[eè]ve|geneva|lausanne|bruxelles|brussels/i.test(hit[1]||''))region='french';
  const style=year&&region?(period==='modern'?'modern':region+'-'+period):'neutral';
  return {style,period,region:region||'neutral',year,place,src:'generated-covers/'+style+'.jpg'};
 }
 function create(record,geography){
  const frame=el('div',null,'generated-cover-frame'),cover=el('div',null,'generated-book-cover'),art=el('img',null,'generated-cover-art'),copy=el('div',null,'generated-cover-copy');
  const title=String(record.title||'Untitled catalogue record').replace(/\s+/g,' ').trim(),names=(record.authorNames||[]).filter(Boolean).join(' · ')||record.author||record.heading||'';
  cover.setAttribute('role','img');cover.setAttribute('aria-label','Generated cover interpretation: '+title+(names?' — '+names:''));
  art.alt='';art.loading='lazy';art.decoding='async';art.setAttribute('aria-hidden','true');
  art.onerror=()=>{art.hidden=true;cover.classList.add('generated-cover-no-art');};
  const author=el('span',names,'generated-cover-author'),heading=el('span',title,'generated-cover-title'),rule=el('span',null,'generated-cover-rule'),imprint=el('span',null,'generated-cover-imprint');
  heading.style.setProperty('--title-size',title.length>220?'5.2cqw':title.length>120?'6cqw':title.length>65?'7.2cqw':'10cqw');
  heading.title=title;author.title=names;copy.append(author,heading,rule,imprint);cover.append(art,copy);frame.append(cover,el('span','Generated cover','generated-cover-label'));
  const update=geo=>{const d=design(record,geo);cover.dataset.style=d.style;cover.dataset.period=d.period;cover.dataset.region=d.region;art.src=d.src;imprint.replaceChildren();if(d.place)imprint.append(el('span',d.place));if(d.year)imprint.append(el('span',String(d.year)));frame.title='Generated interpretation'+(d.year||d.place?' · '+[d.place,d.year].filter(Boolean).join(' · '):' · publication date and place unspecified');};
  update(geography);if(geography===undefined)ready().then(update);
  return frame;
 }
 function caption(record,geography){
  const box=el('div',null,'reading-cover-caption'),details=el('details'),d=design(record,geography);details.append(el('summary','About this cover'));
  details.append(el('p','An imagined design'+(d.year||d.place?' inspired by '+[d.place,d.year].filter(Boolean).join(' · '):' for this catalogue record')+'. It does not depict the original binding.'));
  box.append(details);return box;
 }
 window.LibraryGeneratedCovers={create,caption,design,ready};
})();
