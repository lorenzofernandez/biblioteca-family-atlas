 const regions={ITA:'italian',FRA:'french',GBR:'anglo',IRL:'anglo',USA:'anglo',CAN:'anglo',AUS:'anglo',DEU:'northern',AUT:'northern',NLD:'northern',BEL:'northern',CHE:'northern'};
 export function coverDesign(record,geography){
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

export function coverCandidates(record){
 const all=[...(record.research?.images||[]),...(record.onlineCandidates||[]).flatMap(c=>(c.images||[]).map(i=>({...i,sourceUrl:i.sourceUrl||c.url,credit:i.credit||c.source})))];
 if(record.image)all.push({src:record.image,label:'Reference cover'});
 const seen=new Set();return all.filter(i=>{const src=i.src||i.url;if(typeof src!=='string'||!/^(https?:\/\/|book-images\/|images\/)/.test(src)||seen.has(src))return false;seen.add(src);return true}).sort((a,b)=>Number(/cover|binding/i.test(b.label||''))-Number(/cover|binding/i.test(a.label||'')));
}
