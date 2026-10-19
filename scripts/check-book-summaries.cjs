const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),zlib=require('node:zlib');
require('../dist/book-summaries.js');
const build=globalThis.LibraryBookSummaries.build;
const root=path.join(__dirname,'../dist/book-records');
const records=Object.assign({},...fs.readdirSync(root).filter(f=>f.endsWith('.gz')).map(f=>JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(root,f))))));
const sample=title=>({title,source:'originals/test.pdf',page:1});
const first=title=>build(sample(title))[0]?.text||'';
const water=build(records.we3bc8b5a94e4);
assert.equal(water.length,3);
for(const topic of ['Uppsala','Danimarchense acidic spring','seawater','artificially prepared medicinal waters'])assert(water[0].text.includes(topic),topic);
assert(water[1].text.includes('cold medicinal waters'));
assert(!water.some(x=>/Denmark|Danish/i.test(x.text)),'Do not turn a spring name into a country');
assert(water.every(x=>x.score<=60&&x.sources[0].url.endsWith('#page=116')));
assert.match(first('Electrodeposited coatings of nickel and chromium on zinc and zinc-based alloys'),/coatings on zinc/);
assert.match(first('Hydrochloric acid: preparation'),/hydrochloric acid/);
assert.doesNotMatch(first('Silver chloride: solubility'),/silver and chlorine/);
assert.match(first('Copper and its alloys at elevated temperatures'),/elevated temperatures/);
assert.match(first('Protein biosynthesis and membrane biochemistry'),/proteins.*membranes/);
assert.doesNotMatch(first('Untersuchungen an Elektrolyten mit Zink'),/Electrolysis/i);
assert.doesNotMatch(first('Examen et surveillance des barrages et des cheminées'),/chemical substances/i);
assert.doesNotMatch(first('Résolution des équations'),/dissolved|solution/i);
assert.deepEqual(build(sample('An unknown title')),[]);
const journal=build({...sample('Sur les ondes'),text:'III.B.10\nSur les ondes\nEstr. da "Journal de Chimie et Physique"\ncm. 20; pp. 20–30.'});
assert(!journal.some(x=>/Chemical substances|Chemical compounds/.test(x.title)),'Journal name must not supply the subject');
assert(build({...records.we3bc8b5a94e4,crossReference:true}).every(x=>x.score<=40));
const curated=build({...sample('Chemical analysis of water'),confidence:{metadata:{level:'high'}},research:{curated:true,summary:'An account of the composition of mineral waters. Another sentence.',summarySources:[{title:'Source',url:'https://example.org/book'}]}});
assert.equal(curated[0].score,85);assert.equal(curated[0].title,'In brief');
assert.deepEqual(build({...sample('An unknown title'),onlineCandidates:[{title:'Chemistry',confidence:{level:'high'},reviewDecision:{status:'rejected'}}]}),[]);
let described=0,specific=0;
for(const record of Object.values(records)){
 const items=build(record);if(items.length)described++;
 if(items.some(x=>x.basis.includes('its continuation')))specific++;
 assert(items.length<=4,record.id);
 assert.equal(new Set(items.map(x=>x.text)).size,items.length,record.id);
 for(const item of items){assert(item.text.split(/\s+/).length<=48,record.id+': '+item.text);assert(Number.isFinite(item.score)&&item.score>=0&&item.score<=100,record.id);assert(item.sources.length,record.id);}
}
console.log(JSON.stringify({records:Object.keys(records).length,described,specific,semanticChecks:'passed'}));
