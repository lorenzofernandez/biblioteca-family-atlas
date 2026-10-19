#!/usr/bin/env python3
"""Apply source-reviewed aliases and merges; preserve scans, OCR and old URLs."""
import collections
import copy
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'dist'
R = ROOT / 'research/author-name-review'
spec = importlib.util.spec_from_file_location('merge_helpers', ROOT / 'scripts/merge-author-duplicates.py')
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
read, save, shards, save_shards, unique = (getattr(helpers, name) for name in
    ['read', 'save', 'shards', 'save_shards', 'unique'])


def main():
    plan = read(R / 'decisions.json')
    directory = read(D / 'authors-data.json')
    if directory.get('nameReview', {}).get('baselineCommit') == plan['baselineCommit']:
        print('This reviewed name pass is already applied.')
        return
    profiles, records, books = (shards(folder) for folder in ['author-profiles', 'author-records', 'book-records'])
    before = copy.deepcopy(profiles)
    old_links = {aid: {r['id'] for r in rows} for aid, rows in records.items()}
    old_book_links = {bid: r['authors'].copy() for bid, r in books.items()}
    evidence_keys = ['text', 'heading', 'title', 'displayTitle', 'source', 'file', 'page', 'year', 'crossReference', 'continuation']
    evidence = {bid: {k: r.get(k) for k in evidence_keys} for bid, r in books.items()}
    redirect = {aid: e['canonicalId'] for e in plan['entries'] for aid in e['members'] if aid != e['canonicalId']}
    reviewed = {e['canonicalId']: e for e in plan['entries']}
    resolve = lambda aid: redirect.get(aid, aid)
    affected_books = {bid for bid, r in books.items() if any(resolve(a) in reviewed for a in r['authors'])}

    for entry in plan['entries']:
        aid = entry['canonicalId']
        assert aid in entry['members'] and set(entry['members']) <= profiles.keys(), entry
        p = profiles[aid]
        # Conflicting authority identities require an explicit, reviewed correction.
        for member in entry['members']:
            other = before[member]
            if other.get('wikidata') and p.get('wikidata') and other['wikidata'] != p['wikidata']:
                assert member in entry.get('replaceWrongIdentityIds', []), member
        p['aliases'] = unique([name for member in entry['members'] for name in
            [*before[member].get('aliases', []), before[member]['name'], before[member]['displayName']]
            if name] + entry.get('aliases', []) + [entry['name']])
        p.update(displayName=entry['name'], possibleIdentity=entry['name'], surname=entry['surname'], given=entry['given'],
                 birth=entry['birth'], death=entry['death'], origins=entry['origins'],
                 lifeLabel=entry.get('lifeLabel') or f"{entry['birth']}–{entry['death']}")
        if not entry.get('preserveBiography'):
            p.update(bio=entry['biography'], bioShort=entry['short'], description=entry['short'], bioSources=entry['sources'])
        else:
            p['bioSources'] = unique(p.get('bioSources', []) + entry['sources'])
        p.update(bioSource=p['bioSources'][0]['url'], bioSourceTitle=p['bioSources'][0]['title'],
                 bioSourceKind='research-summary', bioLicense=None, biographyReviewedAt=plan['date'])
        identity = {'level': 'high', 'reason': entry['reason']}
        p['confidence'].update(overall='high', identity=identity, biography={'level': 'high',
            'reason': 'Source-reviewed biography; identity checked against historical aliases and linked work titles.'})
        if not p.get('portrait'):
            p['confidence']['image'] = {'level': 'unresolved', 'reason': 'No verified portrait has been added for this author.'}
        candidate_id = p.get('wikidata') or 'reviewed-' + aid
        p['candidateId'] = candidate_id
        p['identityCandidates'] = [dict(authorId=aid, catalogueName=p['name'], candidateId=candidate_id,
            candidateName=p['displayName'], wikidataId=p.get('wikidata'), sourceUrl=entry['sources'][0]['url'],
            authorityUrl=entry['sources'][0]['url'], bioSourceKind='research-summary', bio=p['bio'], bioShort=p['bioShort'],
            bioSources=p['bioSources'], description=p['description'], birth=p['birth'], death=p['death'],
            lifeLabel=p['lifeLabel'], origins=p['origins'], imageUrl=p.get('portrait'), imageCreditUrl=p.get('portraitSource'),
            confidence=identity, matchMethod='manual-historical-alias-and-work-title-review', retrievedAt=plan['date'])]
        p['nameReview'] = dict(date=plan['date'], originalAuthorIds=entry['members'], confidence='high',
            reason=entry['reason'], sources=entry['sources'])
        if len(entry['members']) > 1:
            prior = p.get('deduplication', {})
            p['deduplication'] = dict(date=plan['date'], confidence='high',
                mergedAuthorIds=unique(prior.get('mergedAuthorIds', []) + [m for m in entry['members'] if m != aid]),
                reasons=unique(prior.get('reasons', []) + [entry['reason']]))
        for member in entry['members']:
            if member != aid:
                del profiles[member]

    def remap(record):
        old_ids = record['authors'].copy()
        ids = unique([resolve(a) for a in old_ids])
        if ids != old_ids:
            record.setdefault('catalogueAuthorIds', old_ids)
            record['authors'] = ids
        if 'authorNames' in record:
            old_names = record['authorNames']
            names = []
            for aid in ids:
                i = next(i for i, a in enumerate(old_ids) if resolve(a) == aid)
                names.append(profiles[aid]['displayName'] if aid in reviewed else
                             old_names[i] if i < len(old_names) else profiles[aid]['displayName'])
            if names != old_names:
                record.setdefault('catalogueAuthorNames', old_names.copy())
                record['authorNames'] = names
        for ev in record.get('attributionEvidence', []):
            aid = resolve(ev.get('author'))
            if ev.get('author') in redirect:
                ev.setdefault('catalogueAuthorId', ev['author'])
                ev['author'] = aid
            if aid in reviewed:
                ev.setdefault('beforeNameReview', {k: copy.deepcopy(v) for k, v in ev.items() if k != 'beforeNameReview'})
                ev.update(level='high', reason=reviewed[aid]['reason'], sources=reviewed[aid]['sources'], reviewedAt=plan['date'])
        if record['id'] in affected_books and isinstance(record.get('confidence'), dict):
            levels = [ev.get('level') for ev in record.get('attributionEvidence', [])]
            if levels and all(level == 'high' for level in levels):
                record['confidence']['attribution'] = dict(level='high', reason='Author names checked against historical aliases and work titles; source evidence is attached to each link.')

    for record in books.values():
        remap(record)
    grouped = collections.defaultdict(dict)
    for aid, rows in records.items():
        grouped[resolve(aid)]  # retain existing empty buckets
        for record in rows:
            remap(record)
            destination = grouped[resolve(aid)]
            if record['id'] in destination:
                existing = destination[record['id']]
                assert existing['text'] == record['text']
                existing['attributionEvidence'] = unique(existing.get('attributionEvidence', []) + record.get('attributionEvidence', []))
            else:
                destination[record['id']] = record
    records = {aid: sorted(rows.values(), key=lambda r: (r['file'], r['page'], r['id'])) if aid in reviewed else list(rows.values())
               for aid, rows in grouped.items()}
    for aid in reviewed:
        rows = records.get(aid, [])
        years = [r['year'] for r in rows if r.get('year') is not None]
        profiles[aid].update(recordCount=len(rows), referenceCount=sum(bool(r['crossReference']) for r in rows),
                            firstYear=min(years) if years else None, lastYear=max(years) if years else None)

    # Give the user's example a source-specific description alongside its corrected identity.
    orta = books['w55a9cd597be6']
    orta['research'] = {**orta.get('research', {}), 'curated': True,
        'summary': 'Medicinal plants, spices and drugs brought from the East Indies, drawing on Garcia de Orta’s observations in India. This Italian version was translated by Annibale Briganti and includes annotations by Carolus Clusius.',
        'summarySources': reviewed['a6d1cb89469a2']['sources'][:2], 'summaryReviewedAt': plan['date']}
    for candidate in orta.get('onlineCandidates', []):
        if candidate.get('externalId') in ['duelibridellhist00orta', 'dellquothistori00orta']:
            candidate['nameReview'] = {'date': plan['date'], 'identity': 'Garzia dall’Horto is Garcia de Orta.',
                'sources': reviewed['a6d1cb89469a2']['sources'][:2]}
            candidate['editionRelation'] = f"Related work under Garcia de Orta's Italian name. Different publication year: reference {candidate['year']}, catalogue 1589; exact edition and image type remain unverified."
            candidate['matchType'] = 'Historical author alias and related title; different edition'
            candidate['confidence']['reason'] = 'The author alias and related title are source-supported. The publication year differs from the catalogue; this is not a verified image or record of the 1589 edition.'

    index = {a['id']: a for a in directory['authors'] if a['id'] not in redirect}
    for aid in reviewed:
        row, profile = index[aid], profiles[aid]
        for key in list(row):
            if key in profile:
                row[key] = copy.deepcopy(profile[key])
        row.update(candidateNames=[profile['displayName']], candidateCount=1,
                   possibleIdentity=profile['displayName'], biographyReviewedAt=plan['date'])
    directory['authors'] = list(index.values())
    directory['authorRedirects'] = {**{old: resolve(new) for old, new in directory.get('authorRedirects', {}).items()}, **redirect}
    shared = collections.defaultdict(set)
    for book in books.values():
        for pair in itertools.combinations(sorted(book['authors']), 2):
            shared[pair].add(book['id'])
    edges, changed = {}, set()
    for edge in directory['edges']:
        a, b = sorted([resolve(edge['a']), resolve(edge['b'])])
        if a == b:
            continue
        pair = (a, b)
        if edge['a'] in redirect or edge['b'] in redirect or pair in edges:
            changed.add(pair)
        edges[pair] = {**edge, 'a': a, 'b': b}
    for pair in changed:
        assert shared[pair], pair
        edges[pair]['count'] = len(shared[pair])
    directory['edges'] = list(edges.values())
    counts = dict(date=plan['date'], baselineCommit=plan['baselineCommit'], scope=plan['scope'],
        peopleReviewed=len(reviewed), entriesReviewed=sum(len(e['members']) for e in plan['entries']),
        duplicateEntriesMerged=len(redirect), incorrectHomonymMatchesCorrected=sum(len(e.get('replaceWrongIdentityIds', [])) for e in plan['entries']),
        entriesBefore=len(before), entriesAfter=len(profiles), affectedBooks=len(affected_books))
    directory['nameReview'] = counts

    assert len(books) == 49780 and set(profiles) == set(index)
    assert all({k: r.get(k) for k in evidence_keys} == evidence[bid] for bid, r in books.items())
    assert all(r['authors'] == unique([resolve(a) for a in old_book_links[bid]]) for bid, r in books.items())
    assert all(old_links[aid] <= {r['id'] for r in records.get(resolve(aid), [])} for aid in old_links)
    assert all(set(r['authors']) <= profiles.keys() for r in books.values())
    assert all(old not in profiles and new in profiles for old, new in directory['authorRedirects'].items())
    assert all(profiles[aid] == before[aid] for held in plan['heldForReview'] for aid in held['ids'])

    save(R / 'original-profiles.json.gz', {aid: before[aid] for entry in plan['entries'] for aid in entry['members']})
    save(R / 'result.json', counts)
    save_shards('author-profiles', profiles)
    save_shards('author-records', records)
    save_shards('book-records', books)
    save(D / 'authors-data.json', directory)
    book_index = read(D / 'books-data.json.gz')
    for row in book_index['books']:
        remap(row)
    book_index['authors'] = [{**row, 'name': profiles[row['id']]['displayName']} if row['id'] in reviewed else row
                             for row in book_index['authors'] if row['id'] not in redirect]
    book_index['nameReview'] = counts
    save(D / 'books-data.json.gz', book_index)
    story = read(D / 'cards-assets/data.json')
    for card in story['cards']:
        if card['id'] in affected_books:
            card['author'] = ' · '.join(books[card['id']]['authorNames'])
    save(D / 'cards-assets/data.json', story)
    compact = read(D / 'cards-assets/catalogue-index.json.gz')
    for card in compact['cards']:
        if card[0] in affected_books:
            card[2] = ' · '.join(books[card[0]]['authorNames'])
    save(D / 'cards-assets/catalogue-index.json.gz', compact)
    rarity = read(D / 'rarity-data.json')
    for row in rarity['records']:
        if row['id'] in affected_books:
            row['author'] = ' · '.join(books[row['id']]['authorNames'])
    save(D / 'rarity-data.json', rarity)
    research = read(D / 'research-data.json')
    research.update(authorEntries=len(profiles), authorBiographies=sum(bool(p.get('bio')) for p in profiles.values()),
        authorImages=sum(bool(p.get('portrait')) for p in profiles.values()),
        authorConfidence=dict(collections.Counter(p['confidence']['overall'] for p in profiles.values())),
        coauthorshipLinks=len(directory['edges']), authorNameReview=counts)
    save(D / 'research-data.json', research)
    print(json.dumps(counts, indent=2))


if __name__ == '__main__':
    main()
