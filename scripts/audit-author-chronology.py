import collections,gzip,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'dist';out=R/'research/author-chronology-20261019'
authors=json.loads((D/'authors-data.json').read_bytes())['authors'];books=json.loads(gzip.decompress((D/'books-data.json.gz').read_bytes()))['books'];by=collections.defaultdict(list)
for b in books:
 if isinstance(b.get('year'),int):
  for aid in b['authors']:by[aid].append(b)
flags=[];checked=0
for a in authors:
 birth,death=a.get('birth'),a.get('death');rows=by[a['id']]
 if not rows or birth is None and death is None:continue
 checked+=len(rows);cases=[]
 for b in rows:
  y=b['year'];reason=None
  if birth is not None and y<birth:reason='before_birth'
  elif birth is not None and y<birth+12:reason='author_under_12'
  elif death is not None and y>death+100:reason='over_100_years_after_death'
  elif death is not None and y>death:reason='posthumous_publication'
  if reason:cases.append({'recordId':b['id'],'year':y,'title':b['title'],'reason':reason,'crossReference':b.get('crossReference',False),'continuation':b.get('continuation',False),'section':b['section']})
 if cases:
  impossible=[b for b in cases if b['reason']=='before_birth' and not b['crossReference'] and not b['continuation']]
  priority='high' if len(impossible)>=2 else 'review' if any(b['reason'] in ['before_birth','author_under_12'] for b in cases) else 'posthumous_review'
  flags.append({'authorId':a['id'],'name':a['name'],'possibleIdentity':a.get('possibleIdentity'),'birth':birth,'death':death,'identityConfidence':a.get('confidence',{}).get('overall'),'datedRecords':len(rows),'priority':priority,'records':cases})
flags.sort(key=lambda a:({'high':0,'review':1,'posthumous_review':2}[a['priority']],-len([r for r in a['records'] if r['reason']=='before_birth'])))
summary={'catalogueRecords':len(books),'authorEntries':len(authors),'datedAuthorRecordLinksChecked':checked,'authorsWithFlags':len(flags),'reasonCounts':dict(collections.Counter(r['reason'] for a in flags for r in a['records'])),'priorityCounts':dict(collections.Counter(a['priority'] for a in flags)),'note':'Publication years may describe reprints, translations, later editions, cross-references or faulty OCR. Flags are review signals, not proof of incorrect authorship. Posthumous publication alone does not reject an identity.'}
out.mkdir(exist_ok=True);(out/'audit.json').write_text(json.dumps({'summary':summary,'authors':flags},ensure_ascii=False,indent=2));print(json.dumps(summary,indent=2))
for a in flags[:30]:print(a['authorId'],a['name'],'→',a['possibleIdentity'],a['birth'],a['death'],a['datedRecords'],[(r['year'],r['title'][:65]) for r in a['records'][:3]])
