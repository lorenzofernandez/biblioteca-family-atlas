"""Integrate full-catalogue screening without promoting candidates into verified editions."""
import json,gzip,collections,csv,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;S=P.parent/'library-site/dist';B=P/'baseline';DATE='2026-10-17'
records={};shards={}
for p in sorted((B/'book-records').glob('*.gz')):
 d=json.load(gzip.open(p,'rt'));records.update(d);shards[p.name]=list(d)
books=json.load(open(B/'books-data.json'));research=json.load(open(B/'research-data.json'));stats=collections.Counter()
def confidence(x,default='low'):
 return x.get('level',default) if isinstance(x,dict) else x or default

def add_candidates(identifier,candidates,containers):
 r=records[identifier];old=r.setdefault('onlineCandidates',[]);seen={c['url'] for c in old};new=[]
 for c in candidates:
  if not c.get('url','').startswith('https://') or c['url'] in seen:continue
  seen.add(c['url']);c['confidence']={'level':confidence(c.get('confidence')),'reason':c.get('confidence',{}).get('reason') or '; '.join(c.get('confidence',{}).get('basis',[])) or 'Automated candidate; edition not individually verified.' if isinstance(c.get('confidence'),dict) else c.get('reason','Automated candidate; edition not individually verified.')}
  if c['confidence']['level']=='high':c['confidence']['level']='medium'
  new.append(c)
 if new:
  r['onlineCandidates']=(old+new[:2] if r.get('editionReview') or r.get('research',{}).get('curated') else new[:2]+old)[:4];stats['recordsWithAddedWorkLeads']+=1
  if not old and not r.get('editionReview') and not r.get('research',{}).get('curated'):
   level=confidence(new[0].get('confidence'));r['researchStatus']='automated_source_lead';r['confidence']['metadata']={'level':level,'reason':'New automated title/creator connection; original edition or offprint identity remains unverified.'};r['confidence']['overall']=level
 if containers:r['containerCandidates']=containers[:2]

FINDINGS={
 'reviewed':'Bibliographic fields were individually compared with cited external sources. The edition review below states the decision and its scope; rarity is a separate claim.',
 'linked':'A possible external work or edition reference was located. Its title, creator and date need comparison with the original card before the exact edition can be confirmed.',
 'container':'A possible source for the host journal or volume was located. The individual article and any separately printed offprint remain unverified.',
 'catalogue':'The original catalogue text was screened for bibliographic, printing and format clues and compared with the reference corpora. No sufficiently coherent external work or edition lead was retained in this pass.',
 'reference':'This card is marked as a cross-reference or continuation. Its information needs to be traced to the main catalogue record before treating it as an independent publication.'
}
NEXT={
 'reviewed':'Use the reviewed edition and volume scope to compare holdings, deduplicate institutional copies and look for an edition census.',
 'linked':'Compare the candidate title page or journal citation with the card’s imprint, date, pagination and volume before researching surviving copies.',
 'container':'Locate the article within the journal, confirm its author, title and pages, then investigate survival of the separate offprint if that is the family item.',
 'catalogue':'Check the scan for a clean title and imprint, then search specialist or national bibliographies for an edition-level lead.',
 'reference':'Follow the main entry and combine its continuation notes before searching for a matching edition.'
}
# Public-metadata candidates never supersede an individual edition decision.
expanded_path=P/'expanded-candidates.json'
expanded=json.load(open(expanded_path)) if expanded_path.exists() else {'records':{},'stats':{},'methodology':{}}
for ident,item in expanded.get('records',{}).items():
 if ident in records:add_candidates(ident,item.get('candidates',[]),item.get('containerCandidates',[]))

# Two focused source checks retain their edition discrepancies.
for ident,item in json.load(open(P/'focused-source-additions.json')).items():
 add_candidates(ident,item['candidates'],[])
 if item.get('editionReview'):
  r=records[ident];r['editionReview']=item['editionReview'];r['confidence']['metadata']={'level':'medium','reason':item['editionReview']['reasoning']};r['confidence']['overall']='medium';r['researchStatus']='probable_edition'

# Four printed limitation notes were visually checked in the original catalogue.
printing=json.load(open(P/'catalogue-print-run-evidence.json'))
for ident,item in printing.items():
 r=records[ident];signals=[x for x in item['signals'] if 'print_run' in x['type']];assert signals
 n=signals[0];source=n['source'];upper=n.get('conditionalSurvivorUpperBound')
 sources=[{**source,'type':'original catalogue printing note'}]
 if n.get('dateConflict'):sources.append({'title':'Bologna Library · Galvani bicentenary, 1937','url':n['dateConflict']['sourceUrl'],'type':'historical chronology'})
 note=n['meaning']+' '+' '.join(n.get('assumptions',[]))
 evidence={'editionMatchConfidence':'medium' if upper else 'low','evidenceConfidence':'medium' if upper else 'low','documentedLowerBound':None,'countUnit':'physical copies of the specified issue','worldwideSurvivingRange':{'min':None,'max':None,'confidence':'low','isEstimate':False},'worldwideEstimate':None,'note':note,'evidence':sources,'editionRelationship':n['scope'],'checked':DATE}
 if upper:evidence['conditionalSurvivalBounds']={'min':None,'maxApprox':upper,'confidence':'low','kind':'conditional ceiling only; not a likely surviving range','assumptions':' '.join(n.get('assumptions',[]))};evidence['originalPrintRun']=n.get('originalPrintRun')
 # Existing numerical studies remain authoritative if present.
 if not r.get('survivalResearch'):r['survivalResearch']=evidence
 r.setdefault('survivalEvidence',[]).append({'title':'Catalogue limitation statement','range':'Conditional ceiling: '+str(upper)+' copies' if upper else 'No usable numerical ceiling','summary':note,'confidence':'low','editionRelation':n['scope'],'sources':sources})
 r['confidence']['survival']={'level':'low','reason':'A source-backed printing note, with its scope and assumptions. Present-day surviving-copy total is not established.'}
 stats['printingNotesAdded']+=1

# All records receive an explicit, source-linked assessment, including negative results.
scan=json.load(open(P/'catalogue-screening-ui.json'));signals=json.load(open(P/'catalogue-signals-stats.json'))
assert set(scan)==set(records)
for ident,r in records.items():
 v=scan[ident];is_reference=v['status']=='non_independent_record'
 linked=bool(r.get('onlineCandidates') or r.get('bibliographyMatch') or any(s.get('url','').startswith('https://') for s in r.get('research',{}).get('summarySources',[])))
 status='reviewed' if r.get('editionReview') or r.get('research',{}).get('curated') else 'linked' if linked else 'container' if r.get('containerCandidates') else 'reference' if is_reference else 'catalogue'
 v['status']=status;v['confidence']=r.get('confidence',{}).get('metadata',{}).get('level','unresolved') if status in ['reviewed','linked'] else 'low' if status=='container' else 'unresolved'
 v['formatLabel']=v.get('formatLabel') or ('Cross-reference / continuation' if is_reference else 'Publication format unresolved')
 v['catalogueFinding']=v['finding'];v['finding']=FINDINGS[status];v['nextStep']=NEXT[status]
 r['catalogueScreening']=v
 stats['status_'+status]+=1
for b in books['books']:
 r=records[b['id']];v=r['catalogueScreening'];b['assessmentStatus']=v['status'];b['hasContainerReference']=bool(r.get('containerCandidates'));b['hasCatalogueSignal']=bool(v['signals']);b['researched']=bool(r.get('research') or r.get('onlineCandidates') or r.get('containerCandidates'));b['hasSurvivalEvidence']=bool(r.get('survivalResearch') or r.get('bibliographyAssessment'));b['confidence']=r['confidence']['overall'];b['researchStatus']=r.get('researchStatus')
full={
 'checked':DATE,'screened':len(records),'externalWorkRecords':sum(bool(r.get('onlineCandidates') or r.get('bibliographyMatch') or any(s.get('url','').startswith('https://') for s in r.get('research',{}).get('summarySources',[]))) for r in records.values()),
 'containerRecords':sum(bool(r.get('containerCandidates')) for r in records.values()),'individualReviews':sum(bool(r.get('editionReview')) for r in records.values()),'rarityEvidenceRecords':sum(bool(r.get('survivalResearch') or r.get('bibliographyAssessment')) for r in records.values()),
 'offprintRecords':signals['signalCounts']['extract_or_offprint_notation'],'catalogueSignalRecords':signals['independentPositiveRecords'],'statuses':{k:stats['status_'+k] for k in FINDINGS},'signalCounts':signals['signalCounts'],
 'articleCorpusRecords':expanded.get('stats',{}).get('articleCorpusRecords',0),'newWorkLeadRecords':stats['recordsWithAddedWorkLeads'],'matchingStats':expanded.get('stats',{}),'matchingMethod':expanded.get('methodology',{}),'publicationConfidencePolicy':'Automatic candidate confidence is capped at medium on the site. High similarity scores do not establish an individually verified edition.',
 'catalogueMethod':json.load(open(P/'catalogue-signals-method.json')),
 'scope':'All catalogue records were screened locally; external API retrievals collected public reference corpora. This is not 49,780 individual web searches or holdings censuses. An unmatched record is not evidence of scarcity. Category bar is exclusive; headline evidence totals can overlap.'
}
assert sum(full['statuses'].values())==49780
books['fullCataloguePass']=full
research['bookResearch']['corpusRecords']=expanded.get('stats',{}).get('corpusRecords',research['bookResearch']['corpusRecords']);research['fullCataloguePass']=full;research['survivalRecords']=sum(bool(r.get('survivalResearch')) for r in records.values());research['bookReferences']=full['externalWorkRecords'];research['bookConfidence']=dict(collections.Counter(r['confidence']['metadata']['level'] for r in records.values()))
for name,ids in shards.items():(S/'book-records'/name).write_bytes(gzip.compress(json.dumps({i:records[i] for i in ids},ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
(S/'books-data.json').write_text(json.dumps(books,ensure_ascii=False,separators=(',',':')))
(S/'research-data.json').write_text(json.dumps(research,ensure_ascii=False,indent=2)+'\n')
(P/'integration-stats.json').write_text(json.dumps(full,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in full.items() if k not in ['catalogueMethod','matchingMethod','matchingStats']},indent=2))
