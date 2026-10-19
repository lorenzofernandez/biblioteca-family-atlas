import json,gzip,collections,copy,subprocess,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;S=P.parent/'library-site/dist';B=P/'baseline'
def load(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_text())
def save(p,d):
 b=json.dumps(d,ensure_ascii=False,separators=(',',':')).encode();p.write_bytes(gzip.compress(b,mtime=0) if p.suffix=='.gz' else b)
records={}
for p in (B/'book-records').glob('*.gz'): records.update(load(p))
bookData=load(B/'books-data.json.gz');oldBooks={x['id']:copy.deepcopy(x) for x in bookData['books']};coverage=load(B/'research-data.json')
previousRarity=load(B/'rarity-data.json')['researched'];previousVerified=coverage['sourceVerification']['verified']
reviews=[]
for name in ['root-results.json','early-results.json','later-results.json','deep-results.json']:
 if (P/name).exists():
  data=load(P/name)
  if isinstance(data,dict):data=data.get('records',data.get('results',data.get('reviews',[])))
  for p in data:
   v=p['editionReview'];v['decision']={'verified':'verified_edition','probable':'probable_edition'}.get(v['decision'],v['decision'])
   for f in v.get('checkedFields',[]):
    if isinstance(f,dict) and f.get('family'):f['catalogue']=f.pop('family')
   if p.get('correctedMetadata'):
    meta=p['correctedMetadata'];p['researchPatch']={'imprint':meta['referenceEdition'],'summary':'Bibliographic description: '+meta['referenceEdition']+' A separate content synopsis has not been established in this pass.','summarySources':v['sources'],'summaryType':'Bibliographic description'}
    allowed=[]
    for c in p.get('candidateDecisions',[]):
     if c['decision'] in ['retain_as_edition_reference','retain_as_probable_edition_reference']:allowed.append(c['externalId'])
     c['decision']={'reject_as_exact_edition':'rejected','retain_as_edition_reference':v['decision'],'retain_as_probable_edition_reference':'probable_edition','retain_as_related_reference_only':'rejected'}.get(c['decision'],c['decision'])
     if c.get('externalId'):c.setdefault('url','https://archive.org/details/'+c['externalId'])
    p['sourceCorrections']={'allowedExistingImageCandidateIds':allowed,'preferredSourceUrl':next((s['url'] for s in v['sources'] if s['url'].startswith('https://')),None)}
   reviews.append(p)
assert len({r['id'] for r in reviews})==len(reviews)
newEvidence=[];newMinima=[];newVerified=[];changedAuthors={}
for patch in reviews:
 i=patch['id'];w=records[i];v=patch['editionReview'];old=copy.deepcopy(w)
 for key in ['editionReview','survivalResearch','survivalEvidence','bibliographyAssessment']:
  if patch.get(key):w[key]=copy.deepcopy(patch[key])
 sr=w.get('survivalResearch')
 if sr and not old.get('survivalResearch') and sr.get('documentedLowerBound') is None and not sr.get('worldwideEstimate') and not sr.get('conditionalSurvivalBounds'):
  w['unresolvedSurvivalReview']=w.pop('survivalResearch')
  w['researchExclusions']=[{'source':e['url'],'reason':e.get('note','Not established as a surviving copy of the family edition.')} for e in sr.get('evidence',[]) if e.get('url')]
  w['survivalEvidence']=[]
 for e in w.get('survivalEvidence',[]):
  if isinstance(e.get('range'),dict):
   bounds=e['range'];e['range']=f"At least {bounds['min']} documented copies · upper bound unknown" if bounds.get('min') is not None and bounds.get('max') is None else 'Worldwide total not established'
 q=w.get('bibliographyAssessment')
 if patch.get('bibliographyAssessment') and q:
  q.setdefault('matchConfidence',q.get('editionMatchConfidence','medium'))
  q.setdefault('applicable',q['matchConfidence'] in ['high','medium'])
  q.setdefault('editionRelationship',q.get('scope',v.get('verificationScope')))
  q.setdefault('reason',(q.get('sourceName','Cited source')+' describes this edition as '+q.get('assessment','scarce')+'. '+q.get('note','')))
  if not q.get('sources') and q.get('sourceUrl'):q['sources']=[{'title':q.get('sourceName','Scarcity assessment'),'url':q['sourceUrl']}]
 conf=v.get('confidence','medium');conf=conf.get('level','medium') if isinstance(conf,dict) else conf
 verified=v['decision']=='verified_edition' and conf=='high'
 level='high' if verified else 'medium' if v['decision']=='probable_edition' else 'low'
 reason=v.get('reasoning') or v.get('evidenceReasoning') or 'Individual comparison recorded below.'
 w['confidence']['metadata']={'level':level,'reason':reason}
 w['confidence']['overall']=level
 w['researchStatus']=v['decision'];w['deepResearchPass']='2026-10-17-deep-editions'
 if v.get('cleanTitle') and v['decision'] in ['verified_edition','probable_edition']:w['displayTitle']=v['cleanTitle']
 r=w.setdefault('research',{});r.update(patch.get('researchPatch') or {})
 r.update({'title':w['displayTitle'],'checked':'2026-10-17','curated':verified,'match':reason})
 if v['decision'] in ['verified_edition','probable_edition']:
  imprint=next((f.get('source') for f in v.get('checkedFields',[]) if isinstance(f,dict) and f.get('field','').lower()=='imprint'),None)
  if imprint:r['imprint']=imprint
  for im in r.get('images',[]):im.setdefault('editionRelation',old.get('research',{}).get('editionRelation','External reference copy; edition relationship requires checking.'))
  r['editionRelation']=v.get('verificationScope','Individually reviewed edition connection.')
 r.setdefault('year',w.get('year'));r.setdefault('summarySources',[]);r.setdefault('images',[])
 r['contextSources']=list({x['url']:x for x in r.get('contextSources',[])+v.get('sources',[]) if x.get('url')}.values())
 if not r.get('summary'):
  r['summary']='The bibliographic details of this catalogue entry have now been individually compared with the sources below. A separate content summary has not yet been established.'
 if not r.get('editionRelation'):r['editionRelation']=v.get('verificationScope') or 'See the individual edition review.'
 if patch.get('attributionPatch'):
  a=patch['attributionPatch'];w['authors']=[a['id']];w['authorNames']=[a['name']]
  w['confidence']['attribution']={'level':'high','reason':a['reason']}
  w['attributionEvidence']=[{'author':a['id'],'level':'high','reason':a['reason']}]
  changedAuthors[a['id']]=a
 sr=w.get('survivalResearch')
 if sr:
  n=sr.get('documentedLowerBound');r['documentedCopies']=n;r['countUnit']=sr.get('countUnit','documented copies');r['rarityNote']=sr['note'];r['holdingSources']=sr['evidence']
  w['confidence']['survival']={'level':'low','reason':f"Located evidence: {sr.get('evidenceConfidence','unresolved')} confidence; edition connection: {sr.get('editionMatchConfidence','unresolved')}. Worldwide completeness remains unknown. "+sr['note']}
  if isinstance(n,int) and not isinstance(old.get('survivalResearch',{}).get('documentedLowerBound'),int):newMinima.append(i)
 if (sr or w.get('bibliographyAssessment')) and not(old.get('survivalResearch') or old.get('bibliographyAssessment')):newEvidence.append(i)
 if verified and not oldBooks[i].get('editionVerified'):newVerified.append(i)
 # The comparison is independent of automatic thumbnails: never promote those images silently.
 for c in w.get('onlineCandidates',[]):
  c['reviewDecision']={'decision':v['decision'],'scope':v.get('verificationScope'),'reason':'Read the individual comparison; this original candidate and its images keep their own edition relationship.'}
 if not w.get('onlineCandidates') and v.get('sources'):
  src=next((s for s in v['sources'] if s.get('url','').startswith('https://')),None)
  if src:w['onlineCandidates']=[{'source':src['title'],'title':w['displayTitle'],'creators':w.get('authorNames',[]),'year':w.get('year'),'url':src['url'],'confidence':{'level':level,'reason':reason},'editionRelation':v.get('verificationScope'), 'referenceType':'Individually researched bibliographic source','images':[]}]
 cs=w['catalogueScreening'];cs.update(status='reviewed',confidence=level,finding='Individually compared with the external sources in the edition review. Survival research enumerates the documented copies separately.',nextStep='Inspect the physical family copy for issue and completeness, then expand the deduplicated holdings search. No worldwide upper bound is inferred from the located copies.')
 # Permit an explicit original-candidate correction from the researchers.
 for key in ['candidateDecisions','sourceCorrections','researchNotes','researchExclusions','researchMethod','unresolvedSurvivalReview','reportedCensus']:
  if patch.get(key):w[key]=patch[key]
 decisions=patch.get('candidateDecisions',[])
 if isinstance(decisions,list):
  for c in w.get('onlineCandidates',[]):
   dec=next((d for d in decisions if isinstance(d,dict) and (d.get('url')==c.get('url') or d.get('externalId')==c.get('externalId') and d.get('externalId'))),None)
   if not dec:continue
   c['reviewDecision']=dec
   c['editionRelation']=dec.get('reason',c.get('editionRelation'))
   c['confidence']={'level':'high' if dec.get('decision') in ['verified_edition','accepted','same_edition'] and verified else 'low' if dec.get('decision') in ['different_edition','rejected','wrong_edition'] else 'medium','reason':dec.get('reason',reason)}
   for im in c.get('images',[]):im['editionRelation']=c['editionRelation']
  if w.get('onlineCandidates'):
   first=w['onlineCandidates'][0];dec=next((d for d in decisions if isinstance(d,dict) and d.get('url')==first.get('url')),None)
   if dec and dec.get('decision') in ['different_edition','rejected','wrong_edition']:
    r['imageEditionRelation']=dec.get('reason')
    for im in r.get('images',[]):im['editionRelation']=dec.get('reason')
    if not patch.get('researchPatch',{}).get('summary'):
     r['summary']='The earlier reference describes another edition: '+dec.get('reason','See the edition comparison.')+' A separate content summary for the matched family edition has not yet been established.'
     r['summarySources']=v.get('sources',[])
 if r.get('images') and not r.get('imageEditionRelation'):
  r['imageEditionRelation']=r['images'][0].get('editionRelation',old.get('research',{}).get('editionRelation','External reference copy.'))
 fix=patch.get('sourceCorrections') or {}
 if isinstance(fix,dict) and 'allowedExistingImageCandidateIds' in fix:
  allowed=fix['allowedExistingImageCandidateIds'];pool=[]
  for im in r.get('images',[]):
   if any(ident in im.get('src','') or ident in im.get('sourceUrl','') for ident in allowed):pool.append(im)
  if not pool:
   for c in w.get('onlineCandidates',[]):
    if c.get('externalId') not in allowed:continue
    for im in c.get('images',[]):
     pool.append({**im,'src':im.get('src',im.get('url')),'label':im.get('label','Reference thumbnail · page type unverified'),'credit':im.get('credit',c.get('source','External source')),'rights':im.get('rights','Consult the source record.'),'sourceUrl':im.get('sourceUrl',c['url']),'confidence':im.get('confidence','low'),'editionRelation':v.get('verificationScope')})
  r['images']=list({im['src']:im for im in pool if im.get('src')}.values())
  r['imageEditionRelation']=v.get('verificationScope') if pool else None
  if not pool:w['confidence']['images']={'level':'unresolved','reason':'The earlier gallery belonged to a different or unverified edition. Inspect the labelled reference candidates; no replacement gallery has been selected.'}
  for im in r['images']:im['editionRelation']=v.get('verificationScope')
  preferred=fix.get('preferredSourceUrl')
  if preferred and not any(c.get('url')==preferred for c in w.get('onlineCandidates',[])):
   w.setdefault('onlineCandidates',[]).append({'source':'Individually reviewed source','externalId':fix.get('preferredExternalId'),'url':preferred,'title':w['displayTitle'],'year':w.get('year'),'creators':w.get('authorNames',[]),'confidence':{'level':level,'reason':reason},'editionRelation':v.get('verificationScope'),'images':[]})
  w['onlineCandidates'].sort(key=lambda c:c.get('url')!=preferred)

for p in (B/'book-records').glob('*.gz'):
 old=load(p);new={i:records[i] for i in old}
 if new!=old:save(S/'book-records'/p.name,new)

def linked(w):
 r=w.get('research') or {}
 return bool(any(s.get('url','').startswith('https://') for k in ['summarySources','holdingSources','contextSources'] for s in r.get(k,[])) or any(c.get('url','').startswith('https://') for c in w.get('onlineCandidates',[])))
for b in bookData['books']:
 w=records[b['id']]
 if w.get('deepResearchPass'):
  b.update(title=w['displayTitle'],authors=w['authors'],authorNames=w.get('authorNames',[]),confidence=w['confidence']['overall'],researchStatus=w['researchStatus'],researched=linked(w) or bool(w.get('containerCandidates')),editionVerified=bool(w.get('research',{}).get('curated') and w['confidence']['metadata']['level']=='high'),hasSurvivalEvidence=bool(w.get('survivalResearch') or w.get('bibliographyAssessment')),assessmentStatus=w['catalogueScreening']['status'],deepResearchPass=w['deepResearchPass'])
  if isinstance(w.get('sourceCorrections'),dict) and 'allowedExistingImageCandidateIds' in w['sourceCorrections']:
   b['image']=(w['research'].get('images') or [{}])[0].get('src')

f=bookData['fullCataloguePass'];f.update(statuses=dict(collections.Counter(w['catalogueScreening']['status'] for w in records.values())),externalWorkRecords=sum(linked(w) for w in records.values()),individualReviews=sum(bool(w.get('editionReview')) for w in records.values()),rarityEvidenceRecords=sum(bool(w.get('survivalResearch') or w.get('bibliographyAssessment')) for w in records.values()))
deep={'checked':'2026-10-17','batch':'2026-10-17-deep-editions','previousRarityRecords':previousRarity,'previousVerifiedEditions':previousVerified,'reviewedRecords':len(reviews),'newVerifiedEditions':len(newVerified),'newRarityRecords':len(newEvidence),'newDocumentedMinimums':len(newMinima),'records':[p['id'] for p in reviews],'newEvidenceIds':newEvidence,'newVerifiedIds':newVerified,'editionDecisions':dict(collections.Counter(p['editionReview']['decision'] for p in reviews)),'method':'Individual comparisons of the original catalogue text with primary library catalogues, digitized source copies and specialist bibliographies. Institutional source copies deduplicated by institution, shelfmark and provenance. Catalogue-only physical ownership, duplicate scan mirrors, repeated auction sales, microfilms and modern facsimiles are not added to original-copy counts. No numeric global range is generated from age or the number of search results.','finiteWorldwideEstimatesAdded':sum(bool(p.get('survivalResearch',{}).get('worldwideEstimate')) for p in reviews)}
bookData['deepResearchPass']=deep;coverage['deepResearchPass']=deep
coverage['fullCataloguePass']=f;coverage['bookReferences']=f['externalWorkRecords'];coverage['survivalRecords']=sum(bool(w.get('survivalResearch')) for w in records.values());coverage['recordsWithSurvivalLowerBounds']=sum(isinstance(w.get('survivalResearch',{}).get('documentedLowerBound'),int) for w in records.values());coverage['bookConfidence']=dict(collections.Counter(w['confidence']['overall'] for w in records.values()))
coverage['expansion']['qualitativeRarityRecords']=sum(bool(w.get('bibliographyAssessment')) for w in records.values());coverage['expansion']['applicableQualitativeSignals']=sum(bool(w.get('bibliographyAssessment',{}).get('applicable')) for w in records.values())
coverage['unattributed']=sum(not w.get('authors') for w in records.values())
coverage['bookImages']=sum(bool(b.get('image')) for b in bookData['books'])
coverage['bookGalleries']=sum(len(w.get('research',{}).get('images',[]))>1 for w in records.values())
coverage['survivalHighlights']=[{'id':i,'title':records[i]['displayTitle'],'summary':records[i]['survivalResearch']['note']} for i in ['w647821587e75','w09b0d7410fc7','wba46e50037bf']]+coverage.get('survivalHighlights',[])
save(S/'books-data.json.gz',bookData);save(S/'research-data.json',coverage)

# Keep newly resolved author links reciprocal in the author catalogue.
authors=load(B/'authors-data.json')
for aid,patch in changedAuthors.items():
 paths=[S/'author-records'/(aid[1:3]+'.json.gz'),S/'author-profiles'/(aid[1:3]+'.json.gz')]
 ar=load(B/'author-records'/paths[0].name);ap=load(B/'author-profiles'/paths[1].name)
 works=[w for w in records.values() if aid in w.get('authors',[])]
 ar[aid]=[{k:w[k] for k in ['id','file','page','section','text','heading','title','year','crossReference','continuation','authors','source','attributionEvidence','confidence'] if k in w} for w in works]
 p=ap[aid];p.update(name=patch['name'],displayName=patch['name'],given='Pierre Rémond de',firstYear=1708,lastYear=1713,recordCount=len(works),bio='French mathematician (1678–1719), author of the 1708 and 1713 editions of Essay d’analyse sur les jeux de hazard.',bioSource='https://ccfr.bnf.fr/portailccfr/ark:/16871/00111278843',bioSourceTitle='CCFr · attributed 1708 edition',bioLicense='Original summary of cited institutional records')
 p['confidence'].update(overall='high',identity={'level':'high','reason':'Both 1708 and1713 works are individually identified with institutional sources; the anonymous first-edition card is linked to the same author.'},biography={'level':'high','reason':'Name, lifetime and authorship supported by CCFr and the Edward Worth Library.'})
 p['possibleIdentity']=None;p['bioSourceKind']='research-summary';p['identityReview']={'checked':'2026-10-17','decision':'identified','sources':records['w647821587e75']['editionReview']['sources']}
 p['rejectedIdentityCandidates']=[c for c in p.get('identityCandidates',[]) if c.get('wikidataId')!='Q474930']
 p['identityCandidates']=[c for c in p.get('identityCandidates',[]) if c.get('wikidataId')=='Q474930']
 for c in p.get('identityCandidates',[]):c['reviewDecision']='accepted' if c.get('wikidataId')=='Q474930' else 'rejected for these works'
 for a in authors['authors']:
  if a['id']==aid:
   for k in ['name','displayName','given','firstYear','lastYear','recordCount','bio','possibleIdentity','bioSourceKind']:a[k]=p[k]
   a['confidence']={'overall':'high'}
 save(paths[0],ar);save(paths[1],ap)
save(S/'authors-data.json',authors)
subprocess.run(['python3',str(S.parent/'scripts/build-source-coverage.py')],check=True)
subprocess.run(['python3',str(S.parent/'scripts/build-rarity-data.py')],check=True)
rarity=load(S/'rarity-data.json');rarity['deepResearchPass']=deep;save(S/'rarity-data.json',rarity)
coverage=load(S/'research-data.json');deep['verifiedEditionsAfter']=coverage['sourceVerification']['verified'];deep['rarityEvidenceAfter']=rarity['researched'];save(P/'integration-stats.json',deep)
save(P/'combined-research.json',{'coverage':deep,'records':[{k:w[k] for k in ['id','displayTitle','editionReview','survivalResearch','unresolvedSurvivalReview','survivalEvidence','bibliographyAssessment','reportedCensus','candidateDecisions','researchExclusions'] if k in w} for w in [records[p['id']] for p in reviews]]})
audit=S.parent/'research/deep-rarity-pass';audit.mkdir(exist_ok=True,parents=True)
for p in P.glob('*results.json'):shutil.copy2(p,audit/p.name)
for name in ['integration-stats.json','root-research.py','integrate.py']:shutil.copy2(P/name,audit/name)
print(json.dumps({k:v for k,v in deep.items() if not isinstance(v,(list,dict))},indent=2))
