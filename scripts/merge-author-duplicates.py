#!/usr/bin/env python3
"""Apply the reviewed author-entry consolidation, retaining catalogue evidence.

Run from any directory. The checked-in decisions are deliberately conservative;
the review queue is not an instruction to merge. Safe to run again after applying.
"""
import collections
import copy
import csv
import gzip
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'dist'
AUDIT = ROOT / 'research' / 'author-deduplication'

def read(path):
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes())

def save(path, value):
    if path.exists() and read(path) == value:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == '.gz' else raw)

def shards(folder):
    result = {}
    for file in sorted((D / folder).glob('*.json.gz')):
        result.update(read(file))
    return result

def save_shards(folder, records):
    grouped = {file.name[:2]: {} for file in (D / folder).glob('*.json.gz')}
    for key, value in records.items():
        grouped.setdefault(key[1:3], {})[key] = value
    for prefix, values in grouped.items():
        save(D / folder / (prefix + '.json.gz'), values)

def unique(items):
    seen, result = set(), []
    for item in items:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result

def main():
    plan = read(AUDIT / 'decisions.json')
    authors = read(D / 'authors-data.json')
    if authors.get('deduplication', {}).get('baselineCommit') == plan['baselineCommit']:
        print('Reviewed author consolidation is already applied.')
        return
    profiles, records, books = shards('author-profiles'), shards('author-records'), shards('book-records')
    before = copy.deepcopy(profiles)
    old_links = {aid: {r['id'] for r in rs} for aid, rs in records.items()}
    old_book_evidence = {bid: (r['text'], r['source'], r['file'], r['page']) for bid, r in books.items()}
    old_book_links = {bid: list(r['authors']) for bid, r in books.items()}
    redirect = {aid: g['canonicalId'] for g in plan['groups'] for aid in g['members'] if aid != g['canonicalId']}
    resolve = lambda aid: redirect.get(aid, aid)
    for g in plan['groups']:
        assert set(g['members']) <= profiles.keys(), g
        for field in ('birth', 'death', 'wikidata'):
            assert len({profiles[i][field] for i in g['members'] if profiles[i].get(field) is not None}) <= 1, (g, field)
        aid = g['canonicalId']
        profile = profiles[aid]
        profile['aliases'] = unique([name for i in g['members'] for name in
            [*profiles[i]['aliases'], profiles[i]['name'], profiles[i]['displayName']] if name])
        candidates = {}
        for i in [aid, *[i for i in g['members'] if i != aid]]:
            for original in profiles[i].get('identityCandidates', []):
                key = original.get('candidateId') or original.get('wikidataId') or original.get('authorityUrl') or original.get('sourceUrl') or original['candidateName']
                if key not in candidates:
                    candidates[key] = copy.deepcopy(original)
                    candidates[key]['authorId'] = aid
                    candidates[key]['catalogueAuthorIds'] = []
                candidates[key]['catalogueAuthorIds'] = unique([*candidates[key]['catalogueAuthorIds'], i])
        if candidates:
            profile['identityCandidates'] = list(candidates.values())
        profile['deduplication'] = {'date': plan['date'], 'mergedAuthorIds': [i for i in g['members'] if i != aid],
            'confidence': g['confidence'], 'reasons': unique([p['reason'] for p in g['decisions']])}
        for i in g['members']:
            if i != aid:
                del profiles[i]

    def remap_record(record):
        old_ids = record['authors']
        ids = unique([resolve(i) for i in old_ids])
        if ids != old_ids:
            record.setdefault('catalogueAuthorIds', old_ids.copy())
            record['authors'] = ids
        if 'authorNames' in record:
            names = record['authorNames']
            mapped_names = []
            for aid in ids:
                original_index = next(i for i, old in enumerate(old_ids) if resolve(old) == aid)
                mapped_names.append(profiles[aid]['displayName'] if 'deduplication' in profiles[aid]
                                    else (names[original_index] if original_index < len(names) else profiles[aid]['displayName']))
            if mapped_names != names:
                record.setdefault('catalogueAuthorNames', names.copy())
                record['authorNames'] = mapped_names
        for ev in record.get('attributionEvidence', []):
            if ev.get('author') in redirect:
                ev.setdefault('catalogueAuthorId', ev['author'])
                ev['author'] = resolve(ev['author'])

    for record in books.values():
        remap_record(record)
    merged_records = collections.defaultdict(dict)
    for aid, rows in records.items():
        for r in rows:
            remap_record(r)
            dest = merged_records[resolve(aid)]
            if r['id'] in dest:
                existing = dest[r['id']]
                assert existing['text'] == r['text'], r['id']
                existing['attributionEvidence'] = unique([*existing.get('attributionEvidence', []), *r.get('attributionEvidence', [])])
            else:
                dest[r['id']] = r
    merged_ids = {g['canonicalId'] for g in plan['groups']}
    records = {aid: (sorted(rows.values(), key=lambda r: (r['file'], r['page'], r['id'])) if aid in merged_ids else list(rows.values()))
               for aid, rows in merged_records.items()}
    for g in plan['groups']:
        aid = g['canonicalId']
        rows = records.get(aid, [])
        years = [r['year'] for r in rows if r.get('year') is not None]
        profiles[aid].update(recordCount=len(rows), referenceCount=sum(bool(r['crossReference']) for r in rows),
                             firstYear=min(years) if years else None, lastYear=max(years) if years else None)

    index = {a['id']: a for a in authors['authors'] if a['id'] not in redirect}
    for g in plan['groups']:
        aid = g['canonicalId']
        profile = profiles[aid]
        for key in list(index[aid]):
            if key in profile:
                index[aid][key] = profile[key]
        index[aid]['candidateNames'] = unique([c['candidateName'] for c in profile.get('identityCandidates', [])])
        index[aid]['candidateCount'] = len(profile.get('identityCandidates', []))
    authors['authors'] = list(index.values())
    authors['authorRedirects'] = {**{old: resolve(new) for old, new in authors.get('authorRedirects', {}).items()}, **redirect}

    # Retain the existing graph's scope. Recount only edges affected by a merge,
    # using unique catalogue records so duplicate author labels cannot inflate it.
    shared = collections.defaultdict(set)
    for r in books.values():
        for pair in itertools.combinations(sorted(r['authors']), 2):
            shared[pair].add(r['id'])
    edges, affected = {}, set()
    for e in authors['edges']:
        a, b = sorted([resolve(e['a']), resolve(e['b'])])
        if a == b:
            continue
        key = (a, b)
        if e['a'] in redirect or e['b'] in redirect or key in edges:
            affected.add(key)
        edges[key] = {**e, 'a': a, 'b': b}
    for key in affected:
        if shared[key]:
            edges[key]['count'] = len(shared[key])
        else:
            raise AssertionError(('Merged coauthor edge has no shared records', key))
    authors['edges'] = list(edges.values())
    counts = {'date': plan['date'], 'baselineCommit': plan['baselineCommit'],
              'entriesBefore': len(before), 'entriesAfter': len(profiles), 'mergedGroups': len(plan['groups']),
              'duplicateEntriesMerged': len(redirect), 'candidatePairsHeldForReview': len(plan['heldForReview'])}
    authors['deduplication'] = counts

    # Preserve every original relationship and card. Assert before any data write.
    assert len(books) == 49780
    assert set(profiles) == set(index)
    assert all((r['text'], r['source'], r['file'], r['page']) == old_book_evidence[bid] for bid, r in books.items())
    assert all(r['authors'] == unique([resolve(a) for a in old_book_links[bid]]) for bid, r in books.items())
    assert all(old_links[aid] <= {r['id'] for r in records.get(resolve(aid), [])} for aid in old_links)
    assert all(len(r['authors']) == len(set(r['authors'])) and set(r['authors']) <= profiles.keys() for r in books.values())
    assert all(set(r['authors']) <= profiles.keys() for rs in records.values() for r in rs)
    assert all(e['a'] != e['b'] and e['a'] in profiles and e['b'] in profiles for e in authors['edges'])

    save(AUDIT / 'original-profiles.json.gz', {i: before[i] for g in plan['groups'] for i in g['members']})
    save(AUDIT / 'result.json', counts)
    save_shards('author-profiles', profiles)
    save_shards('author-records', records)
    save_shards('book-records', books)
    save(D / 'authors-data.json', authors)
    book_index = read(D / 'books-data.json.gz')
    for r in book_index['books']:
        remap_record(r)
    save(D / 'books-data.json.gz', book_index)
    story = read(D / 'cards-assets/data.json')
    for card in story['cards']:
        if any('deduplication' in profiles[a] for a in books[card['id']]['authors']):
            card['author'] = ' · '.join(books[card['id']]['authorNames'])
    save(D / 'cards-assets/data.json', story)
    compact = read(D / 'cards-assets/catalogue-index.json.gz')
    for card in compact['cards']:
        if any('deduplication' in profiles[a] for a in books[card[0]]['authors']):
            card[2] = ' · '.join(books[card[0]]['authorNames'])
    save(D / 'cards-assets/catalogue-index.json.gz', compact)
    rarity = read(D / 'rarity-data.json')
    for r in rarity['records']:
        if r['id'] in books and any('deduplication' in profiles[a] for a in books[r['id']]['authors']):
            r['author'] = ' · '.join(books[r['id']]['authorNames'])
    save(D / 'rarity-data.json', rarity)
    research = read(D / 'research-data.json')
    research.update(authorEntries=len(profiles), authorBiographies=sum(bool(p.get('bio')) for p in profiles.values()),
                    authorImages=sum(bool(p.get('portrait')) for p in profiles.values()),
                    authorConfidence=dict(collections.Counter(p['confidence']['overall'] for p in profiles.values())), authorDeduplication=counts)
    save(D / 'research-data.json', research)
    with (AUDIT / 'merged-authors.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Canonical author', 'Canonical ID', 'Original catalogue name', 'Previous ID', 'Merge confidence', 'Evidence'])
        for g in plan['groups']:
            for i in g['members']:
                if i != g['canonicalId']:
                    writer.writerow([g['canonicalName'], g['canonicalId'], before[i]['name'], i, g['confidence'], ' | '.join(d['reason'] for d in g['decisions'])])
    print(json.dumps(counts, indent=2))

if __name__ == '__main__':
    main()
