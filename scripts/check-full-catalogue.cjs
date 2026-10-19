const fs=require('fs'),path=require('path'),zlib=require('zlib'),vm=require('vm'),assert=require('assert');
const root=path.join(__dirname,'../dist');
const read=n=>JSON.parse(fs.existsSync(path.join(root,n))?fs.readFileSync(path.join(root,n)):zlib.gunzipSync(fs.readFileSync(path.join(root,n+'.gz'))));
const records=Object.assign({},...fs.readdirSync(path.join(root,'book-records')).filter(n=>n.endsWith('.gz')).map(n=>JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(root,'book-records',n))))));
const historyPath=path.join(__dirname,'../research/ocr-review/transcription-history.json.gz');
const history=fs.existsSync(historyPath)?JSON.parse(zlib.gunzipSync(fs.readFileSync(historyPath))):{};
const books=read('books-data.json'),rarity=read('rarity-data.json'),full=books.fullCataloguePass;
assert.equal(Object.keys(records).length,49780);assert.equal(full.screened,49780);
assert.equal(Object.values(full.statuses).reduce((a,b)=>a+b),49780);assert.equal(full.rarityEvidenceRecords,rarity.researched);
assert.equal(books.books.filter(b=>b.hasSurvivalEvidence).length,rarity.researched);
assert.equal(full.externalWorkRecords,read('research-data.json').sourceVerification.linked);
for(const [id,r] of Object.entries(records)){
 const s=r.catalogueScreening;assert(s&&s.checked&&s.status&&s.finding&&s.nextStep,id);assert(s.formatLabel,id);assert(fs.existsSync(path.join(root,r.source)),id);
 for(const signal of s.signals){assert(['low','medium','high'].includes(signal.confidence),id);assert(signal.source?.url.includes('#page='),id);assert(records[signal.source.recordId].text.includes(signal.quote)||(signal.transcriptionVersion&&history[signal.source.recordId]?.before.text.includes(signal.quote)),id+' quote must match the current or explicitly preserved earlier transcription')}
 if(s.status==='catalogue'||s.status==='reference')assert.equal(s.confidence,'unresolved');
 for(const c of r.containerCandidates||[])assert(c.url.startsWith('https://'));
}
const limited=records.wceeacceca787.survivalResearch;assert.equal(limited.conditionalSurvivalBounds.maxApprox,120);assert.equal(limited.documentedLowerBound,null);assert.equal(limited.worldwideEstimate,null);
assert.equal(records.w6aff8edc0f21.survivalResearch.conditionalSurvivalBounds.maxApprox,500);
for(const id of ['wc090b7af60a9','w4c7a884422f6']){assert(!records[id].survivalResearch.conditionalSurvivalBounds);assert.equal(records[id].survivalResearch.worldwideEstimate,null)}
const ctx={window:{}};vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(root,'rarity.js'),'utf8'),ctx);
const classify=ctx.window.LibraryRarity.classify,r=rarity.records.find(r=>r.id==='wceeacceca787');assert.equal(classify(r,100,true,'counts').key,'unknown');assert.equal(classify(r,500,true,'counts').key,'possible');assert.equal(classify(r,500,false,'counts').key,'unknown');
assert(!fs.readFileSync(path.join(root,'rarity.js'),'utf8').includes('unresearched records'));
for(const n of ['books.js','site-navigation.js','books-home.js'])assert(!fs.readFileSync(path.join(root,n),'utf8').includes("fetch('books-data.json')"));
console.log(JSON.stringify({screened:full.screened,externalWorkRecords:full.externalWorkRecords,journalLeads:full.containerRecords,rarityEvidence:rarity.researched,catalogueSignalRecords:full.catalogueSignalRecords,status:'passed'},null,2));
