#!/usr/bin/env python3
"""Check consolidation against the pre-merge commit and all emitted datasets."""
import collections, gzip, itertools, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'dist'
read = lambda p: json.loads(gzip.decompress(p.read_bytes()) if p.suffix == '.gz' else p.read_bytes())
plan = read(ROOT / 'research/author-deduplication/decisions.json')
base = plan['baselineCommit']
def original(path):
    raw = subprocess.check_output(['git', 'show', base + ':' + str(path.relative_to(ROOT))], cwd=ROOT)
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)
def shards(folder):
    return {k:v for p in (D/folder).glob('*.gz') for k,v in read(p).items()}
authors=read(D/'authors-data.json'); profiles=shards('author-profiles'); records=shards('author-records'); books=shards('book-records')
redirect=authors['authorRedirects']; resolve=lambda aid:redirect.get(aid,aid)
assert len(profiles)==len(authors['authors'])==22551
assert len(redirect)==234 and len(plan['groups'])==215
assert set(profiles)=={a['id'] for a in authors['authors']}
assert all(old not in profiles and new in profiles and new not in redirect for old,new in redirect.items())
assert all(len(rs)==len({r['id'] for r in rs})==profiles[aid]['recordCount'] for aid,rs in records.items())
changed_books=0
for path in (D/'book-records').glob('*.gz'):
    old=original(path); new=read(path)
    assert old.keys()==new.keys()
    for bid,before in old.items():
        after=new[bid]
        assert {k:v for k,v in before.items() if k not in ('authors','authorNames','attributionEvidence')} == {k:v for k,v in after.items() if k not in ('authors','authorNames','attributionEvidence','catalogueAuthorIds','catalogueAuthorNames')}, bid
        assert after['authors']==list(dict.fromkeys(resolve(a) for a in before['authors'])),bid
        assert set(after['authors'])<=profiles.keys() and len(after['authors'])==len(after['authorNames']),bid
        changed_books+=before['authors']!=after['authors'] or before['authorNames']!=after['authorNames']
for path in (D/'author-records').glob('*.gz'):
    for aid,old in original(path).items():
        new={r['id']:r for r in records[resolve(aid)]}
        assert {r['id'] for r in old}<=new.keys(),aid
        assert all(r['text']==new[r['id']]['text'] for r in old),aid
for row in read(D/'books-data.json.gz')['books']:
    assert row['authors']==books[row['id']]['authors']
    assert row['authorNames']==books[row['id']]['authorNames']
edges=authors['edges']; pairs=[tuple(sorted((e['a'],e['b']))) for e in edges]
assert len(pairs)==len(set(pairs))
assert all(a!=b and a in profiles and b in profiles for a,b in pairs)
assert len(books)==49780
# Uncertain surname-only Farkas and Hélène Duhem remain distinct.
assert 'afc5b339d79e7' in profiles and 'a65b2550a74a6' in profiles
assert resolve('a7354d8b4af19') != resolve('afc5b339d79e7')
assert resolve('a65b2550a74a6') != resolve('a578dd096cc1f')
result={'pass':True,'catalogueCardsPreserved':len(books),'updatedBookAuthorLists':changed_books,'canonicalAuthors':len(profiles),'redirectsChecked':len(redirect),'coauthorEdges':len(edges)}
print(json.dumps(result,indent=2))
