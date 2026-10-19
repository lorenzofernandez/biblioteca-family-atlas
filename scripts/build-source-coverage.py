import json,gzip,collections
from pathlib import Path
S=Path(__file__).resolve().parents[1]/'dist';rows=[]
for p in (S/'book-records').glob('*.json.gz'):rows.extend(json.load(gzip.open(p,'rt')).values())
verified=[];linked=[]
for w in rows:
 r=w.get('research') or {}
 sources=[s for key in ['summarySources','holdingSources','contextSources'] for s in r.get(key,[]) if str(s.get('url','')).startswith('https://')]
 has_source=bool(sources or any(c.get('url','').startswith('https://') for c in w.get('onlineCandidates',[])))
 if has_source:linked.append(w['id'])
 if has_source and r.get('curated') is True and w.get('confidence',{}).get('metadata',{}).get('level')=='high':
  edition_sources=[s for s in w.get('editionReview',{}).get('sources',[]) if str(s.get('url','')).startswith('https://')]
  verified.append(dict(id=w['id'],title=w['displayTitle'],year=w.get('year'),source=(edition_sources or sources)[0],basis=w['confidence']['metadata']['reason']))
verified.sort(key=lambda x:(x['year'] or 9999,x['title']))
assert len({w['id'] for w in rows})==len(rows)
assert {x['id'] for x in verified}<=set(linked)
data=json.load(open(S/'research-data.json'))
data['sourceVerification']={'total':len(rows),'linked':len(linked),'verified':len(verified),'tentative':len(linked)-len(verified),'unmatched':len(rows)-len(linked),'checked':data['checked'],'definition':'A verified match has a manually researched edition comparison, high metadata confidence, and a cited external source. Automated candidates, medium-confidence edition matches, images alone, and author biographies do not qualify. This verifies the bibliographic connection, not the physical family copy.','verifiedEntries':verified}
assert sum(data['sourceVerification'][k] for k in ['verified','tentative','unmatched'])==len(rows)
(S/'research-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
print({k:v for k,v in data['sourceVerification'].items() if k not in ['definition','verifiedEntries']})
