import json,pathlib,gzip,collections,random
root=pathlib.Path('work/full-catalogue-pass');path=root/'book-candidates.json';d=json.load(open(path));books={}
for p in pathlib.Path('work/library-site/dist/book-records').glob('*.json.gz'):books.update(json.load(gzip.open(p,'rt')))
assert set(d['records'])==set(books) and len(books)==49780
probe='w135ac8cf8c87'
if probe in d['records']:
 d['records'][probe]['searchAssessment'].update(individualExternalSearch=True,externalSearchSources=['Crossref bibliographic search','OpenAlex search'],externalSearchPurpose='One diagnostic title probe used to validate article-corpus coverage')
d['stats']['articleCorpusRecords']=d['stats'].get('crossrefRecords',0)
d['stats']['individualExternalRecordSearches']=1;d['stats']['individualExternalTitleApiRequests']=2
log=json.load(open(root/'cache/crossref-retrieval-log.json'));d['stats']['crossrefBatchRequests']=log['requests'];d['stats']['crossrefItemsRetrieved']=log['itemsRetrieved'];d['stats']['crossrefJournalQueries']=len(log['journals'])
d['methodology']['externalSearchScope']='One family title was individually probed through Crossref and OpenAlex. All 49,780 family records were locally screened; the main external activity was public-corpus retrieval (93 Crossref batch requests plus journal discovery), not 49,780 web searches.'
d['methodology']['reviewedFalsePositiveProtections']='Spot-checking exposed publisher/imprint words matching unrelated book reviews. Three named regression records were rechecked after removing imprint variants: Das Gold and Mathematische Schwingungslehre no longer matched unrelated reviews; Molecular rays now matched a source with that title. Common publication-format tokens are excluded. Low-confidence related-title mismatches still remain and are explicitly labelled.'
d['methodology']['falsePositivePolicy']='Low-confidence candidates can be false matches. Imprints and common publication-format words are removed before title matching; apparent book reviews and host-journal leads are separately labelled. No automatic candidate is marked verified.'
source_counts=collections.Counter();type_counts=collections.Counter();best_levels=collections.Counter();statuses=collections.Counter();section=collections.defaultdict(collections.Counter)
for wid,r in d['records'].items():
 assert r.get('searchAssessment',{}).get('localCorpusScreened') is True
 assert isinstance(r.get('containerCandidates'),list);assert len(r['candidates'])<=2
 statuses[r['status']]+=1
 if r['candidates']:best_levels[r['candidates'][0]['confidence']['level']]+=1
 for c in r['candidates']+r['containerCandidates']:
  assert c['confidence']['level'] in ['low','medium','high'];assert c.get('url','').startswith('https://');assert c.get('editionRelation');assert c.get('referenceType');assert 'verified' not in c or not c['verified'];assert 'survivingCopies' not in c
  source_counts[c['source']]+=1;type_counts[c['referenceType']]+=1
  if c['referenceType']=='possible book review or bibliographic notice':assert not c.get('candidateAuthorNames')
  for i in c.get('images',[]):assert i['sourceUrl'] and i['rights'] and i['confidence']
 if r['candidates']:section[books[wid]['section']]['workCandidates']+=1
 if r['containerCandidates']:section[books[wid]['section']]['hostCandidates']+=1
 if r['candidates'] or r['containerCandidates']:section[books[wid]['section']]['anyLead']+=1
previous=json.load(open('work/broad-research/book-candidates.json'))['records']
newids=[wid for wid,r in d['records'].items() if r['candidates'] and not previous[wid]['candidates']]
lostids=[wid for wid,r in d['records'].items() if not r['candidates'] and previous[wid]['candidates']]
coverage={'totalRecords':len(books),'localCorpusScreened':len(books),'individualExternalTitlesQueried':1,'individualExternalTitleApiRequests':2,'withWorkCandidates':sum(bool(r['candidates']) for r in d['records'].values()),'workReferenceThumbnailCandidateRecords':sum(any(c.get('images') for c in r['candidates']) for r in d['records'].values()),'hostPublicationThumbnailCandidateRecords':sum(any(c.get('images') for c in r['containerCandidates']) for r in d['records'].values()),'withHostPublicationCandidates':sum(bool(r['containerCandidates']) for r in d['records'].values()),'hostOnlyRecords':sum(bool(r['containerCandidates']) and not r['candidates'] for r in d['records'].values()),'withAnyLead':sum(bool(r['candidates'] or r['containerCandidates']) for r in d['records'].values()),'noCandidateInSelectedCorpora':sum(not r['candidates'] and not r['containerCandidates'] for r in d['records'].values()),'newWorkCandidateRecords':len(newids),'oldCandidateRecordsNotRetainedByThisPass':len(lostids),'bestWorkCandidateConfidence':dict(best_levels),'referenceTypes':dict(type_counts),'referenceSources':dict(source_counts),'statuses':dict(statuses),'sectionCoverage':{k:dict(v) for k,v in section.items()},'crossrefRetrieval':log,'validation':'PASS: complete record coverage, distinct relationship types, no automatic verified flags, no scan-to-survivor conversions, and complete image/source provenance fields.'}
d['stats']['coverageSummary']=coverage
path.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')))
(root/'expanded-candidates.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')))
(root/'coverage-report.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2))
(root/'methodology.json').write_text(json.dumps(d['methodology'],ensure_ascii=False,indent=2))
random.seed(20261017);sample=[]
for level in ['high','medium','low']:
 pool=[(wid,r) for wid,r in d['records'].items() if r['candidates'] and r['candidates'][0]['confidence']['level']==level]
 for wid,r in random.sample(pool,min(20,len(pool))):sample.append({'id':wid,'title':r['searchedTitle'],'candidate':r['candidates'][0]})
(root/'validation-sample.json').write_text(json.dumps(sample,ensure_ascii=False,indent=2))
(root/'candidate-changes.json').write_text(json.dumps({'newWorkCandidateIds':newids,'oldCandidateIdsNotRetained':lostids,'note':'Parent should preserve existing manually curated and verified research, and may retain older low-confidence candidates as earlier leads.'}))
print(json.dumps({k:v for k,v in coverage.items() if k not in ['crossrefRetrieval','sectionCoverage']},indent=2))
