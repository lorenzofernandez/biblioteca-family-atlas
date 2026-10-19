const fs=require('fs'),path=require('path'),zlib=require('zlib'),assert=require('assert');
const root=path.join(__dirname,'../dist');
const read=n=>JSON.parse(n.endsWith('.gz')?zlib.gunzipSync(fs.readFileSync(path.join(root,n))):fs.readFileSync(path.join(root,n),'utf8'));
const all=Object.assign({},...fs.readdirSync(path.join(root,'book-records')).filter(n=>n.endsWith('.gz')).map(n=>read('book-records/'+n)));
const data=read('books-data.json.gz'),coverage=read('research-data.json'),rarity=read('rarity-data.json'),pass=data.deepResearchPass;
assert(pass.reviewedRecords>60);assert(pass.newRarityRecords>50);assert.equal(rarity.researched,309+pass.newRarityRecords);
assert.equal(coverage.sourceVerification.verified,229+pass.newVerifiedEditions);
assert.equal(pass.records.length,pass.reviewedRecords);assert.equal(new Set(pass.records).size,pass.records.length);
for(const id of pass.records){
 const r=all[id],v=r.editionReview,sr=r.survivalResearch,b=data.books.find(b=>b.id===id);
 assert(v.sources.some(s=>s.url.startsWith('https://')));assert(v.checkedFields);assert(v.reasoning||v.evidenceReasoning);assert(b.deepResearchPass);
 if(v.decision==='verified_edition')assert(b.editionVerified&&r.research.curated&&r.confidence.metadata.level==='high');
 else assert(!b.editionVerified);
 if(sr?.documentedLowerBound!=null){
  assert(sr.documentedLowerBound>0);assert(sr.evidence.length>0);assert.equal(sr.worldwideSurvivingRange.min,sr.documentedLowerBound);
  const counted=sr.evidence.filter(e=>e.copies>0);
  if(counted.length)assert.equal(counted.reduce((s,e)=>s+e.copies,0),sr.documentedLowerBound,id+' lower bound must reconcile to identified source copies');
  assert.equal(new Set(counted.map(e=>[e.institution,e.callNumber||e.url].join('|'))).size,counted.length,id+' duplicated source copy');
 }
 if(sr){assert.equal(sr.worldwideEstimate,null);assert.equal(sr.worldwideSurvivingRange.max,null);assert(sr.editionMatchConfidence);assert(sr.evidenceConfidence)}
 for(const e of r.survivalEvidence||[])assert(e.range==null||typeof e.range!=='object',id+' range must display as text');
 if(r.bibliographyAssessment)assert(r.bibliographyAssessment.sources.length&&r.bibliographyAssessment.confidence==='low');
}
assert.equal(all.w908e18d4ea8f.survivalResearch.documentedLowerBound,7);
assert.equal(all.w647821587e75.survivalResearch.documentedLowerBound,4);
assert.equal(all.w09b0d7410fc7.survivalResearch.documentedLowerBound,3);
assert.equal(all.w647821587e75.authors[0],'a2b30cab1fdf0');
assert.equal(read('author-records/2b.json.gz').a2b30cab1fdf0.length,2);
assert.equal(all.w2f6fdbab3156.survivalResearch.documentedLowerBound,all.w72aff4f5ac4e.survivalResearch.documentedLowerBound);
for(const id of ['wc716497da7b0','w41db16d36c4b'])assert(!data.books.find(b=>b.id===id).hasSurvivalEvidence,'Edition conflicts without matched-copy evidence are excluded');
console.log(JSON.stringify({checks:'passed',reviewed:pass.reviewedRecords,newVerified:pass.newVerifiedEditions,newEvidence:pass.newRarityRecords,evidenceTotal:rarity.researched,verifiedTotal:coverage.sourceVerification.verified},null,2));
