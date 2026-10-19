#!/usr/bin/env python3
"""Check reviewed merges against the immutable pre-review source commit."""
import gzip
import importlib.util
import io
import json
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('review', ROOT / 'scripts/review-author-names.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
read, shards = m.read, m.shards
plan = read(m.R / 'decisions.json')
directory = read(m.D / 'authors-data.json')
profiles, records, books = (shards(folder) for folder in ['author-profiles', 'author-records', 'book-records'])
before = {'author-profiles': {}, 'author-records': {}, 'book-records': {}}
archive = subprocess.check_output(['git', 'archive', plan['baselineCommit'], *['dist/' + name for name in before]], cwd=ROOT)
with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
    for entry in tar:
        if entry.isfile() and entry.name.endswith('.json.gz'):
            folder = entry.name.split('/')[1]
            before[folder].update(json.loads(gzip.decompress(tar.extractfile(entry).read())))
redirect = {member: e['canonicalId'] for e in plan['entries'] for member in e['members'] if member != e['canonicalId']}
resolve = lambda aid: redirect.get(aid, aid)
unique = lambda rows: list(dict.fromkeys(rows))
assert len(books) == len(before['book-records']) == 49780
assert len(profiles) == len(before['author-profiles']) - len(redirect)
assert set(profiles) == {a['id'] for a in directory['authors']}
keys = ['text', 'heading', 'title', 'displayTitle', 'file', 'page', 'source', 'year', 'crossReference', 'continuation']
for bid, old in before['book-records'].items():
    new = books[bid]
    assert all(old.get(k) == new.get(k) for k in keys), (bid, 'source evidence altered')
    assert new['authors'] == unique([resolve(a) for a in old['authors']]), (bid, 'association lost')
    assert len(new['authors']) == len(new['authorNames'])
    assert set(new['authors']) <= profiles.keys()
for aid, rows in before['author-records'].items():
    assert {r['id'] for r in rows} <= {r['id'] for r in records.get(resolve(aid), [])}, aid
for old, new in directory['authorRedirects'].items():
    assert old not in profiles and new in profiles, (old, new)
for edge in directory['edges']:
    assert edge['a'] != edge['b'] and edge['a'] in profiles and edge['b'] in profiles
index = {a['id']: a for a in directory['authors']}
for entry in plan['entries']:
    aid = entry['canonicalId']
    p = profiles[aid]
    assert p['displayName'] == index[aid]['displayName'] == entry['name']
    assert p['recordCount'] == len({r['id'] for r in records.get(aid, [])}) == index[aid]['recordCount']
    assert p['referenceCount'] == sum(bool(r['crossReference']) for r in records.get(aid, []))
    assert p['confidence']['identity']['level'] == 'high' and p['bioSources'] and p['bio']
    assert len(p['identityCandidates']) == 1 and p['identityCandidates'][0]['candidateName'] == entry['name']
    for member in entry['members']:
        old = before['author-profiles'][member]
        assert set(old.get('aliases', []) + [old['name'], old['displayName']]) <= set(p['aliases'])
        if member != aid:
            assert directory['authorRedirects'][member] == aid
    for row in records.get(aid, []):
        assert len(row['authors']) == len(set(row['authors']))
        assert row['authors'] == books[row['id']]['authors']
        assert row['authorNames'] == books[row['id']]['authorNames']
    if entry.get('preserveBiography'):
        assert p['bio'] == before['author-profiles'][aid]['bio']
for held in plan['heldForReview']:
    for aid in held['ids']:
        assert profiles[aid] == before['author-profiles'][aid], ('held entry changed', aid)
book_index = read(m.D / 'books-data.json.gz')
assert len(book_index['books']) == len(books)
for row in book_index['books']:
    assert row['authors'] == books[row['id']]['authors']
    assert row['authorNames'] == books[row['id']]['authorNames']
assert not set(redirect).intersection(a['id'] for a in book_index['authors'])
reviewed = {e['canonicalId'] for e in plan['entries']}
for card in read(m.D / 'cards-assets/catalogue-index.json.gz')['cards']:
    if reviewed.intersection(books[card[0]]['authors']):
        assert card[2] == ' · '.join(books[card[0]]['authorNames'])
orta = books['w55a9cd597be6']
assert orta['authorNames'] == ['Garcia de Orta']
assert 'East Indies' in orta['research']['summary'] and orta['research']['summarySources']
assert all(c['confidence']['level'] == 'low' for c in orta['onlineCandidates'])
print(json.dumps({'status': 'passed', 'cardsPreserved': len(books), 'authors': len(profiles),
    'reviewedPeople': len(reviewed), 'duplicatesMerged': len(redirect), 'redirectsChecked': len(directory['authorRedirects']),
    'checks': ['original OCR and card metadata unchanged', 'all author associations preserved',
               'old IDs resolve to live profiles', 'both variants and search indexes synchronized',
               'reviewed biographies and aliases present', 'ambiguous entries kept separate']}, indent=2))
