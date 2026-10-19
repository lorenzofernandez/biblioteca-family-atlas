"""Apply reviewed biographies without changing catalogue headings or links."""
import copy
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'dist'
R = ROOT / 'research' / 'author-biographies'

def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)

def save(path, data):
    raw = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode()
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == '.gz' else raw)

review = read(R / 'reviewed-biographies.json')
directory = read(D / 'authors-data.json')
index = {a['id']: a for a in directory['authors']}
shards = {}
backup_path = R / 'original-profiles.json.gz'
originals = read(backup_path) if backup_path.exists() else {}
audit = []

for entry in review['entries']:
    for aid in entry['authorIds']:
        path = D / 'author-profiles' / (aid[1:3] + '.json.gz')
        if path not in shards:
            shards[path] = read(path)
        author = shards[path][aid]
        originals.setdefault(aid, copy.deepcopy(author))
        before = originals[aid]
        level = 'medium' if aid in entry.get('mediumIds', []) else entry['identityLevel']
        corrected = entry.get('corrected', False) or aid in entry.get('correctedIds', [])
        old_candidates = before.get('identityCandidates', [])
        qid = entry.get('wikidata', None if entry.get('resetIdentity') else before.get('wikidata'))
        approved = next((c for c in old_candidates if qid and c.get('wikidataId') == qid), {})
        if entry.get('resetIdentity'):
            author.update(portrait=approved.get('imageUrl'), portraitSource=approved.get('imageCreditUrl'),
                          imageKind='Candidate reference image' if approved.get('imageUrl') else None,
                          wikidata=qid)
        birth, death = entry['birth'], entry['death']
        life = entry.get('lifeLabel') or f'{birth}–{death}'
        identity = dict(level=level, reason=entry['identityReason'])
        author.update(displayName=entry['name'], possibleIdentity=entry['name'],
                      birth=birth, death=death, lifeLabel=life, origins=entry['origins'],
                      bio=entry['biography'], bioShort=entry['short'], description=entry['short'],
                      bioSources=entry['sources'], bioSource=entry['sources'][0]['url'],
                      bioSourceTitle=entry['sources'][0]['title'], bioSourceKind='research-summary',
                      bioLicense=None, biographyReviewedAt=review['reviewedAt'])
        author['confidence'].update(overall=level, identity=identity,
            biography=dict(level='high' if level=='high' else 'medium',
                reason='Source-checked biographical summary. '+('The catalogue identity remains tentative.' if level!='high' else 'The linked work titles and subjects support this identification.')))
        if not author.get('portrait'):
            author['confidence']['image'] = dict(level='unresolved', reason='No verified portrait has been added for this author.')
        elif entry.get('resetIdentity'):
            author['confidence']['image'] = dict(level='medium', reason='Reference portrait attached to the reviewed authority identity; source attribution is linked.')
        # Replace unsupported homonyms in the live selector, retaining all originals
        # in the review archive. Reviewed candidates carry the same sourced biography.
        candidate_id = qid or ('reviewed-' + aid)
        candidate = dict(authorId=aid, catalogueName=author['name'], candidateId=candidate_id,
                         candidateName=entry['name'], wikidataId=qid,
                         sourceUrl=author['bioSource'], authorityUrl=author['bioSource'],
                         bioSourceKind='research-summary', bio=author['bio'], bioShort=author['bioShort'],
                         bioSources=author['bioSources'], description=entry['short'],
                         birth=birth, death=death, lifeLabel=life, origins=entry['origins'],
                         imageUrl=author.get('portrait'), imageCreditUrl=author.get('portraitSource'),
                         confidence=identity, matchMethod='manual-title-and-biographical-source-review',
                         retrievedAt=review['reviewedAt'])
        author['identityCandidates'] = [candidate]
        author['candidateId'] = candidate_id
        row = index[aid]
        for key in ['displayName','possibleIdentity','birth','death','lifeLabel','origins','bio','bioShort',
                    'portrait','imageKind','biographyReviewedAt']:
            row[key] = author.get(key)
        row.update(confidence={'overall':level}, candidateNames=[entry['name']], candidateCount=1)
        audit.append(dict(authorId=aid, catalogueName=author['name'], reviewedName=entry['name'],
                          correctedIdentity=corrected, identityLevel=level,
                          previousIdentity=before.get('possibleIdentity'),
                          supersededCandidates=[dict(name=c.get('candidateName'),id=c.get('wikidataId'))
                              for c in old_candidates if not qid or c.get('wikidataId') != qid],
                          reason=entry['identityReason']))
        for key in ['id','key','name','aliases','recordCount','referenceCount','firstYear','lastYear']:
            assert author.get(key) == before.get(key), (aid,key)

save(backup_path, originals)
for path,data in shards.items():
    save(path,data)
save(D / 'authors-data.json', directory)
# LibraryData prefers compressed siblings when present.
if (D / 'authors-data.json.gz').exists():
    save(D / 'authors-data.json.gz', directory)
summary = dict(reviewedAt=review['reviewedAt'], authors=len(audit),
               people=len(review['entries']), correctedIdentities=sum(a['correctedIdentity'] for a in audit),
               sourceCount=len({s['url'] for e in review['entries'] for s in e['sources']}),
               scope='Targeted review of missing/thin biographies and suspect identity matches; not a complete audit of all authors.')
research = read(D / 'research-data.json')
research['authorBiographicalReview'] = summary
(D / 'research-data.json').write_text(json.dumps(research, ensure_ascii=False, indent=2)+'\n')
if (D / 'research-data.json.gz').exists():
    save(D / 'research-data.json.gz',research)
save(R / 'review-audit.json', dict(summary=summary, entries=audit))
print(json.dumps(summary, indent=2))
