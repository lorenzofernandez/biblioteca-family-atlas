"""Apply the reviewed OCR dataset consistently to both visual variants."""
import collections,copy,gzip,itertools,json,re,sys
from pathlib import Path
from ocr_common import norm,similarity
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];D=ROOT/'dist';WORK=ROOT.parent/'ocr-review'
def read(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def save(p,x):
 raw=json.dumps(x,ensure_ascii=False,separators=(',',':')).encode();p.parent.mkdir(parents=True,exist_ok=True)
 if p.suffix=='.gz':raw=gzip.compress(raw,mtime=0)
 if not p.exists() or p.read_bytes()!=raw:p.write_bytes(raw)
def save_shards(folder,data):
 groups={p.name[:2]:{} for p in (D/folder).glob('*.gz')}
 for id,v in data.items():groups.setdefault(id[1:3],{})[id]=v
 for k,v in groups.items():save(D/folder/(k+'.json.gz'),v)
def unique(xs):
 seen=set();out=[]
 for x in xs:
  k=json.dumps(x,sort_keys=True)
  if k not in seen:seen.add(k);out.append(x)
 return out
def main():
 base=read(WORK/'baseline.json.gz');books=read(WORK/'proposed-books.json.gz');heads=read(WORK/'headings.json.gz');stats=read(WORK/'prepare-stats.json')
 assert stats['recognized']==49780,'Full OCR coverage required before publication'
 profiles=read(WORK/'author-profiles-baseline.json.gz');before_profiles=copy.deepcopy(profiles);directory=read(WORK/'authors-data-baseline.json.gz');oldrecords=read(WORK/'author-records-baseline.json.gz')
 proposals=read(WORK/'author-merge-proposals.json');manual=read(HERE/'reviewed-decisions.json');rematch=read(WORK/'rematch.json.gz')
 groups=[];held_merges=list(proposals['held']);manualids={i for g in manual['authorGroups'] for i in g['members']}
 for g in proposals['groups']:
  if manualids.intersection(g['members']):continue
  years=[b['year'] for b in books.values() if b.get('year') and set(g['members']).intersection(b['authors']) and not b.get('crossReference')]
  if years and max(years)-min(years)>100 and not all(profiles[i].get('wikidata') for i in g['members']):
   held_merges.append({'ids':g['members'],'reason':'Publication span exceeds a century without complete authority identifiers'});continue
  groups.append(g)
 groups+=manual['authorGroups'];redirect={i:g['canonicalId'] for g in groups for i in g['members'] if i!=g['canonicalId']}
 def resolve(i):
  while i in redirect:i=redirect[i]
  return i
 assert len(redirect)==sum(len(g['members'])-1 for g in groups),'Overlapping merge groups'
 for g in groups:
  id=g['canonicalId'];p=profiles[id]
  p['aliases']=unique([s for i in g['members'] for s in [*profiles[i].get('aliases',[]),profiles[i]['name'],profiles[i].get('displayName')] if s])
  if not p.get('bioSources'):p['displayName']=g['name']
  p['ocrConsolidation']={'date':'2026-10-18','mergedAuthorIds':[i for i in g['members'] if i!=id],'confidence':g['confidence'],'reason':g['reason']}
  for i in g['members']:
   if i!=id:del profiles[i]
 applied_renames=[]
 for c in proposals['nameCorrections']:
  if c['id'] in profiles and c['id'] not in redirect:
   p=profiles[c['id']];p['aliases']=unique([*p.get('aliases',[]),p['name'],c['after']]);p['displayName']=c['after'];p['ocrNameReview']={'date':'2026-10-18','reason':'Consistent full name in the reread catalogue headings','confidence':'medium'};applied_renames.append(c)
 # Exact full-name lookup; unresolved or multiply matched names are not guessed.
 names=collections.defaultdict(set)
 for aid,p in profiles.items():
  for s in [p['name'],p.get('displayName','')]:names[norm(s)].add(aid)
  for alias in p.get('aliases',[]):
   if ',' in alias:
    sur,given=alias.split(',',1);names[norm(given+' '+sur)].add(aid)
 reassigned=[];recovered=[]
 for wid,b in books.items():
  original=base[wid];oldids=b['authors'];mapped=unique([resolve(i) for i in oldids]);h=heads.get(wid)
  protected=bool(b.get('editionReview') or b.get('research',{}).get('curated') or any(e.get('level')=='high' for e in b.get('attributionEvidence',[])))
  if h and h['confirmed'] and h['names'] and not b.get('crossReference') and not b.get('continuation') and not protected:
   matches=[names.get(norm(n['name']),set()) for n in h['names']]
   if all(len(m)==1 for m in matches):
    proposed=unique([next(iter(m)) for m in matches])
    if proposed!=mapped and (not mapped or set(proposed)&set(mapped) or similarity(h['heading'],original.get('heading',''))>=.7):
     if not mapped:recovered.append(wid)
     reassigned.append({'id':wid,'before':mapped,'after':proposed,'heading':h['heading']});mapped=proposed
     b['attributionEvidence']=[{'author':aid,'level':'medium','reason':'Exact existing full-name match to the reread catalogue heading; ambiguous matches withheld.','evidence':h['heading']} for aid in mapped]
  if wid in manual['records']:
   m=manual['records'][wid]
   for k in ['text','heading','displayTitle']:
    if k in m:b[k]=m[k]
   if 'displayTitle' in m:b['title']=m['displayTitle']
   if 'authors' in m:mapped=m['authors']
   b['catalogueCorrection']={'date':'2026-10-18','reason':m['reason'],'sources':[manual['sources'][i] for i in m['sources']]}
   if 'authors' in m:b['attributionEvidence']=[{'author':aid,'level':'high','reason':m['reason'],'sources':b['catalogueCorrection']['sources']} for aid in mapped]
   if 'text' in m:b['ocrReview']={'date':'2026-10-18','method':'Original scanned card visually reviewed','status':'scan-checked'}
  b['authors']=mapped;b['authorNames']=[profiles[i].get('displayName',profiles[i]['name']) for i in mapped]
  if mapped!=original['authors']:
   b.setdefault('catalogueAuthorIds',original['authors']);b.setdefault('catalogueAuthorNames',original.get('authorNames',[]))
  for e in b.get('attributionEvidence',[]):
   if e.get('author') in redirect:e['author']=resolve(e['author'])
  # Old literal quotations remain evidence of the earlier OCR, with explicit provenance.
  for signal in b.get('catalogueScreening',{}).get('signals',[]):
   sid=signal.get('source',{}).get('recordId',wid)
   if signal.get('quote') and signal['quote'] not in books[sid]['text']:
    signal['transcriptionVersion']='Earlier OCR; retained for research provenance'
  if b.get('containerCandidates'):
   for c in b['containerCandidates']:
    if c.get('citationEvidence') and c['citationEvidence'] not in b['text']:c['citationTranscriptionVersion']='Earlier OCR'
 newleads=0;rechecked=0
 for wid,cs in rematch['records'].items():
  b=books[wid];existing={c.get('url') for c in b.get('onlineCandidates',[])};added=[c for c in cs if c['url'] not in existing]
  rechecked+=1
  if added:
   # Prefer earlier manually curated candidates, preserving their associated images.
   old=b.get('onlineCandidates',[])
   if len(old)<4:b['onlineCandidates']=old+added[:4-len(old)];newleads+=1
   elif not b.get('editionReview') and not b.get('research',{}).get('curated'):
    keep=[c for c in old if c.get('confidence',{}).get('level') in ['high','medium']]
    if len(keep)<4:b['onlineCandidates']=(keep+added+old)[:4];newleads+=1
  if any(c['url'] in {v.get('url') for v in b.get('onlineCandidates',[])} for c in added) and b.get('researchStatus') in ['no_candidate_above_threshold','insufficient_searchable_title']:
   b['researchStatus']='candidate_found'
   screen=b.get('catalogueScreening',{})
   screen.update(checked='2026-10-18',status='linked',confidence='medium',finding='Revised OCR yields a close title, creator and year match in the reference corpus. Edition and individual copy remain unverified.')
 stats.update(authorGroupsMerged=len(groups),duplicateAuthorEntriesMerged=len(redirect),authorNamesReread=len(applied_renames),authorHeadingLinksRevised=len(reassigned),previouslyUnattributedCardsLinked=len(recovered),recordsWithNewReferenceLeads=newleads,referenceRecordsRechecked=rechecked)
 for key in ['text','heading','title','displayTitle','year']:
  stats[key+'Changed']=sum(b.get(key)!=base[wid].get(key) for wid,b in books.items())
 stats['authorLinksRevised']=sum(b['authors']!=base[wid]['authors'] for wid,b in books.items());stats['authorMergeGroupsHeld']=len(held_merges)
 # Rebuild author-card associations from the shared record source.
 minimal={r['id']:r for rows in oldrecords.values() for r in rows};records=collections.defaultdict(list)
 for b in sorted(books.values(),key=lambda x:(x['file'],x['page'])):
  row=copy.deepcopy(minimal.get(b['id'],{}))
  for k in ['id','file','page','section','text','heading','title','year','crossReference','continuation','authors','source','authorNames','attributionEvidence','catalogueCorrection']:
   if k in b:row[k]=b[k]
  row['title']=b.get('displayTitle') or b['title']
  for aid in b['authors']:records[aid].append(row)
 for aid,p in profiles.items():
  rs=records.get(aid,[]);ys=[r['year'] for r in rs if r.get('year')]
  p.update(recordCount=len(rs),referenceCount=sum(bool(r.get('crossReference')) for r in rs),firstYear=min(ys) if ys else None,lastYear=max(ys) if ys else None)
 idx={p['id']:p for p in directory['authors']}
 # Keep the compact directory schema; detailed confidence explanations belong
 # in the lazy-loaded profile shards, not in every directory entry.
 directory['authors']=[{**idx[aid],**{k:p[k] for k in ['displayName','aliases','recordCount','referenceCount','firstYear','lastYear'] if k in p}} for aid,p in profiles.items()]
 directory['authorRedirects']={**{k:resolve(v) for k,v in directory.get('authorRedirects',{}).items()},**redirect}
 directory['coverage']['unassigned']=sum(not b['authors'] for b in books.values());directory['coverage']['ocrReviewDate']='2026-10-18'
 counts=collections.Counter()
 for b in books.values():
  if not b.get('crossReference'):
   for pair in itertools.combinations(sorted(set(b['authors'])),2):counts[pair]+=1
 directory['edges']=[{'a':a,'b':b,'count':n,'type':'coauthor'} for (a,b),n in counts.items()]
 # Track suspicious identities without interpreting posthumous editions as errors.
 issues=[]
 for b in books.values():
  if not b.get('year') or b.get('crossReference'):continue
  for aid in b['authors']:
   birth=profiles[aid].get('birth')
   if isinstance(birth,int) and b['year']<birth-5:issues.append({'id':b['id'],'authorId':aid,'year':b['year'],'authorBirth':birth,'issue':'Date precedes proposed author birth; review attribution/date/role','title':b.get('displayTitle',b['title'])})
 stats.update(authorsAfter=len(profiles),authorChronologyFlags=len(issues),books=len(books))
 audit={'date':'2026-10-18','baselineCommit':'83fa209fb57bf4def3b8d6097f3ba3a1f21c25c6','stats':stats,'matching':rematch['stats'],'method':'Accurate scan recognition on every page, selective higher-resolution second recognition; conservative source-based corrections. OCR confidence is not a calibrated transcription-accuracy percentage.'}
 directory['ocrReview']=audit
 bookindex=read(D/'books-data.json.gz')
 for r in bookindex['books']:
  b=books[r['id']];r.update(title=b.get('displayTitle') or b['title'],authors=b['authors'],authorNames=b['authorNames'],year=b.get('year'),researchStatus=b.get('researchStatus'),researched=bool(b.get('research') or b.get('onlineCandidates') or b.get('containerCandidates')),assessmentStatus=b.get('catalogueScreening',{}).get('status'))
 bookindex['authors']=[{'id':p['id'],'name':p.get('displayName',p['name'])} for p in directory['authors']];bookindex['ocrReview']=audit
 story=read(D/'cards-assets/data.json')
 for c in story['cards']:
  b=books[c['id']];c.update(title=b.get('displayTitle') or b['title'],author=' · '.join(b['authorNames']),year=b.get('year'))
 centuries=collections.Counter((b['year']//100)*100 for b in books.values() if b.get('year') is not None)
 story.update(centuries=dict(sorted(centuries.items())),dated=sum(centuries.values()),undated=len(books)-sum(centuries.values()))
 storypage=D/'cards.html';storyhtml=storypage.read_text()
 storyhtml=re.sub(r'There are <strong>[\d,]+ records with a detected year</strong>',f"There are <strong>{story['dated']:,} records with a detected year</strong>",storyhtml)
 storyhtml=re.sub(r'The remaining [\d,]+ records have no detected year',f"The remaining {story['undated']:,} records have no detected year",storyhtml)
 storypage.write_text(storyhtml)
 cat=read(D/'catalogue.json')
 for c in cat['cards']:
  b=books[c['workId']];c.update(text=b['text'],title=b.get('displayTitle') or b['title'],author=b['heading'],year=b.get('year'))
 typing=read(D/'cards-assets/typing.json')
 typing['texts']={id:books[id]['text'] for id in typing['texts']}
 save(D/'cards-assets/typing.json',typing)
 rarity=read(D/'rarity-data.json')
 for r in rarity['records']:
  if r['id'] in books:
   b=books[r['id']];r.update(title=b.get('displayTitle') or b['title'],author=' · '.join(b['authorNames']))
 research=read(D/'research-data.json');research.update(authorEntries=len(profiles),unattributed=directory['coverage']['unassigned'],coauthorshipLinks=len(directory['edges']),ocrReview=audit)
 research['sourceVerification']['linked']=sum(bool(b.get('onlineCandidates') or b.get('bibliographyMatch') or any(x.get('url','').startswith('https://') for x in b.get('research',{}).get('summarySources',[]))) for b in books.values())
 research['sourceVerification']['tentative']=research['sourceVerification']['linked']-research['sourceVerification']['verified']
 research['sourceVerification']['unmatched']=49780-research['sourceVerification']['linked']
 research['sourceVerification']['checked']='2026-10-18'
 full=bookindex['fullCataloguePass'];full.update(externalWorkRecords=research['sourceVerification']['linked'],statuses=dict(collections.Counter(b['catalogueScreening']['status'] for b in books.values())))
 research['fullCataloguePass']=full;research['bookReferences']=full['externalWorkRecords']
 unattributed_path=D/'unattributed-records.json.gz';unattributed=read(unattributed_path if unattributed_path.exists() else D/'unattributed-records.json');unattributed_templates={b['id']:b for b in unattributed};unattributed_keys=list(unattributed[0])
 unattributed=[{k:b[k] for k in unattributed_templates.get(b['id'],dict.fromkeys(unattributed_keys)) if k in b} for b in books.values() if not b['authors']]
 # Preservation checks before writes.
 assert set(base)==set(books) and len(books)==49780
 for wid,b in books.items():
  assert (b['file'],b['page'],b['source'])==(base[wid]['file'],base[wid]['page'],base[wid]['source'])
  for key in ['research','editionReview','survivalResearch','bibliographyAssessment']:
   assert b.get(key)==base[wid].get(key),(wid,key)
  assert set(b['authors'])<=profiles.keys()
 for aid,p in before_profiles.items():
  if p.get('bioSources') and aid in profiles:
   for field in ['bio','bioShort','bioSources','birth','death','portrait']:assert p.get(field)==profiles[aid].get(field),(aid,field)
 save_shards('book-records',books);save_shards('author-profiles',profiles);save_shards('author-records',dict(records))
 for path,data in [('authors-data.json',directory),('books-data.json.gz',bookindex),('cards-assets/data.json',story),('catalogue.json',cat),('rarity-data.json',rarity),('research-data.json',research),('unattributed-records.json.gz',unattributed)]:save(D/path,data)
 (D/'unattributed-records.json').unlink(missing_ok=True)
 indexpath=D/'index.html';html=indexpath.read_text();html=re.sub(r'(<script[^>]*id="catalogueData"[^>]*>).*?(</script>)',lambda m:m[1]+json.dumps(cat,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+m[2],html,flags=re.S);indexpath.write_text(html)
 save(HERE/'author-profile-history.json.gz',{i:{'before':p,'canonicalId':resolve(i)} for i,p in before_profiles.items() if i in redirect or p!=profiles.get(i)})
 save(HERE/'audit.json',audit);save(HERE/'author-decisions.json',{'groups':groups,'renames':applied_renames,'links':reassigned,'redirects':redirect,'held':held_merges});save(HERE/'chronology-review.json.gz',issues)
 history={wid:{'file':b['file'],'page':b['page'],'before':{k:base[wid].get(k) for k in ['text','heading','title','displayTitle','year','authors','authorNames']},'after':{k:b.get(k) for k in ['text','heading','title','displayTitle','year','authors','authorNames']}} for wid,b in books.items() if any(b.get(k)!=base[wid].get(k) for k in ['text','heading','title','displayTitle','year','authors','authorNames'])}
 save(HERE/'transcription-history.json.gz',history);save(HERE/'review-queue.json.gz',read(WORK/'held.json.gz'));save(HERE/'reference-matches.json.gz',rematch)
 print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
