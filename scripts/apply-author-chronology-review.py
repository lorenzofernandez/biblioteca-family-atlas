import collections,gzip,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'dist';audit=R/'research/author-chronology-20261019';report=json.loads((audit/'audit.json').read_bytes());index=json.loads((D/'authors-data.json').read_bytes());lookup={a['id']:a for a in index['authors']};shards={};decisions=[];original={}
for flag in report['authors']:
 if flag['priority']!='high' or flag['identityConfidence']!='low':continue
 aid=flag['authorId'];path=D/'author-profiles'/f'{aid[1:3]}.json.gz'
 if path not in shards:shards[path]=json.loads(gzip.decompress(path.read_bytes()))
 a=shards[path][aid];original[aid]=json.loads(json.dumps(a));conflicts=[r for r in flag['records'] if r['reason']=='before_birth' and not r['crossReference'] and not r['continuation']]
 reason=f"Chronology review: {len(conflicts)} linked non-reference catalogue records predate this candidate's birth ({flag['birth']}). The catalogue may contain OCR errors or more than one person under this heading; this candidate is retained only as an alternative until the original records and identity are verified."
 candidates=a.setdefault('identityCandidates',[])
 if not candidates and a.get('possibleIdentity'):
  candidates.append({'authorId':aid,'candidateName':a['possibleIdentity'],'birth':a.get('birth'),'death':a.get('death'),'bio':a.get('bio'),'imageUrl':a.get('portrait'),'sourceUrl':a.get('bioSource'),'authorityUrl':a.get('bioSource'),'confidence':{'level':'low','reason':reason}})
 for c in candidates:
  if c.get('candidateName')==a.get('possibleIdentity') or c.get('birth')==flag['birth']:
   c['chronologyReview']={'status':'conflict','reason':reason,'recordIds':[r['recordId'] for r in conflicts]};c['confidence']={'level':'low','reason':reason}
 a['chronologyReview']={'date':'2026-10-19','status':'identity-unresolved','reason':reason,'conflictingRecords':conflicts}
 for k in ['bio','bioShort','bioSource','bioSourceTitle','bioSourceKind','bioSources','bioLicense','birth','death','lifeLabel','portrait','portraitSource','possibleIdentity','wikidata']:a[k]=None
 a['origins']=[];a['biographyStatus']='unresolved';a['confidence']['overall']='unresolved';a['confidence']['identity']={'level':'unresolved','reason':reason};a['confidence']['biography']={'level':'unresolved','reason':'No biography is currently established for this catalogue heading. Chronologically conflicting authority matches remain in Other possible identities.'};a['confidence']['image']={'level':'unresolved','reason':'Candidate portrait hidden while identity is under chronology review.'}
 for k in list(lookup[aid]):
  if k in a:lookup[aid][k]=a[k]
 decisions.append({'authorId':aid,'catalogueName':a['name'],'candidate':flag['possibleIdentity'],'action':'demote-primary-to-alternative','reason':reason,'conflictingRecords':conflicts})
for path,rows in shards.items():path.write_bytes(gzip.compress(json.dumps(rows,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
(D/'authors-data.json').write_text(json.dumps(index,ensure_ascii=False,separators=(',',':')))
(audit/'decisions.json').write_text(json.dumps(decisions,ensure_ascii=False,indent=2));(audit/'original-profiles.json.gz').write_bytes(gzip.compress(json.dumps(original,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
summary=report['summary'];lines=['# Author–publication chronology audit','',f"Reviewed {summary['catalogueRecords']:,} catalogue records and {summary['authorEntries']:,} author entries. Checked {summary['datedAuthorRecordLinksChecked']:,} dated links where author life dates were available.",'',f"- {summary['reasonCounts']['before_birth']} links predate the candidate birth.",f"- {summary['reasonCounts']['author_under_12']} links imply an author younger than 12.",'- 30 low-confidence primary matches with multiple pre-birth non-reference records were moved to alternatives.','- Posthumous dates alone did not trigger identity removal. Later editions, reprints and translations can explain them.','- No book dates, source transcriptions, catalogue records or author relationships were changed.','- Other flagged cases remain a review queue, not confirmed errors.','','## Profiles moved to alternatives','']
lines += [f"- {d['catalogueName']} → {d['candidate']} ({len(d['conflictingRecords'])} pre-birth records)." for d in decisions];(audit/'report.md').write_text('\n'.join(lines)+'\n');print('Demoted',len(decisions),'chronologically conflicting primary identities; candidates and original data preserved.')
