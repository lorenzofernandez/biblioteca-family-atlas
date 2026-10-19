"""Check OCR provenance, stable identifiers, author links and shared UI datasets."""
import collections,gzip,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'dist';A=ROOT/'research/ocr-review'
def read(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def shards(n):return {k:v for p in (D/n).glob('*.gz') for k,v in read(p).items()}
books=shards('book-records');profiles=shards('author-profiles');records=shards('author-records');directory=read(D/'authors-data.json');idx=read(D/'books-data.json.gz');hist=read(A/'transcription-history.json.gz');audit=read(A/'audit.json');decisions=read(A/'author-decisions.json')
assert audit['stats']['recognized']==len(books)==49780
assert len(idx['books'])==49780 and len({b['id'] for b in idx['books']})==49780
assert {p['id'] for p in directory['authors']}==profiles.keys()
unattributed=read(D/'unattributed-records.json.gz')
assert {b['id'] for b in unattributed}=={id for id,b in books.items() if not b['authors']}
for b in unattributed:assert b['text']==books[b['id']]['text'] and b['year']==books[b['id']]['year']
redirect=directory['authorRedirects']
for old,new in redirect.items():assert old not in profiles and new in profiles and new not in redirect
linked=collections.defaultdict(set)
for id,b in books.items():
 assert (D/b['source']).exists()
 assert len(b['authors'])==len(set(b['authors']))==len(b['authorNames'])
 assert set(b['authors'])<=profiles.keys()
 for aid in b['authors']:linked[aid].add(id)
 if b.get('dateEvidence'):assert str(b['dateEvidence']['value']) in b['dateEvidence']['quote']
 if id in hist:assert b['text']==hist[id]['after']['text'] and b['year']==hist[id]['after']['year']
 for sig in b.get('catalogueScreening',{}).get('signals',[]):
  sid=sig['source']['recordId'];quote=sig.get('quote','')
  if quote not in books[sid]['text']:
   assert sig.get('transcriptionVersion') and quote in hist[sid]['before']['text'],(id,sid,quote)
for aid,p in profiles.items():
 rs=records.get(aid,[])
 assert {r['id'] for r in rs}==linked[aid],aid
 assert len(rs)==len(linked[aid])==p['recordCount'],aid
 for r in rs:
  b=books[r['id']];assert r['text']==b['text'] and r['year']==b['year'] and r['authors']==b['authors']
for r in idx['books']:
 b=books[r['id']]
 assert r['authors']==b['authors'] and r['authorNames']==b['authorNames'] and r['year']==b['year']
 assert r['title']==(b.get('displayTitle') or b['title'])
for c in read(D/'catalogue.json')['cards']:
 assert c['text']==books[c['workId']]['text'] and c['year']==books[c['workId']]['year']
for c in read(D/'cards-assets/data.json')['cards']:
 assert c['year']==books[c['id']]['year']
scene=read(D/'cards-assets/data.json');assert scene['dated']==sum(b.get('year') is not None for b in books.values())
for c in read(D/'cards-assets/authors.json')['authors']:assert c['count']==profiles[c['id']]['recordCount']
# Source-checked regressions and separate Cassini generations.
assert books['we9f0f991165c']['year']==1949
assert books['w53891c74321d']['year']==1888
assert books['wcb430f98e9b7']['year']==1875
assert books['w98e2aa1e56fc']['authors']==['ad9de4c698273']
assert books['w265691be959e']['authors']==['afeade3824714']
assert 'CASSINI, Jacques' in books['w265691be959e']['text']
assert books['we3bc8b5a94e4']['authors']==['a9ca92da03839'] and books['we3bc8b5a94e4']['year'] is None
assert 'Hippocratis' in books['wf7c1032aeb70']['displayTitle']
assert 'Aeginetae' in books['wf7c1032aeb70']['displayTitle']
assert books['w8b7bb4da8f6b']['year'] is None and books['wb55ff75ba248']['year'] is None
assert books['w72027d3f6782']['year']==1966
assert len(books['w2dc75c8a0d7c']['displayTitle'])<60
# Preserve distinct people previously held apart.
resolve=lambda i:redirect.get(i,i)
assert resolve('a7354d8b4af19')!=resolve('afc5b339d79e7')
assert resolve('a65b2550a74a6')!=resolve('a578dd096cc1f')
assert resolve('a2273c70f0ac3') not in [resolve('ad9de4c698273'),resolve('afeade3824714')]
# Reviewed biographies and rare-book evidence remain unchanged.
review=read(ROOT/'research/author-biographies/reviewed-biographies.json')
for e in review['entries']:
 for aid in e['authorIds']:assert profiles[resolve(aid)]['bio']==e['biography']
assert books['wceeacceca787']['survivalResearch']['conditionalSurvivalBounds']['maxApprox']==120
assert books['w6aff8edc0f21']['survivalResearch']['conditionalSurvivalBounds']['maxApprox']==500
sv=read(D/'research-data.json')['sourceVerification'];assert sv['verified']+sv['tentative']+sv['unmatched']==49780 and sv['linked']==sv['verified']+sv['tentative']
size=sum(p.stat().st_size for p in D.rglob('*') if p.is_file());assert size<=256*1024**2,size
print(json.dumps({'passed':True,'cards':len(books),'authors':len(profiles),'redirects':len(redirect),'historyRecords':len(hist),'staticMiB':round(size/1024**2,2)},indent=2))
