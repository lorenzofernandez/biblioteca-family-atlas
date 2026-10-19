"""Check reviewed identities, shared datasets, and preservation of catalogue links."""
import gzip
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
def read(p):
    raw=p.read_bytes()
    return json.loads(gzip.decompress(raw) if p.suffix=='.gz' else raw)
review=read(root/'research/author-biographies/reviewed-biographies.json')
original=read(root/'research/author-biographies/original-profiles.json.gz')
directory=read(root/'dist/authors-data.json')
index={a['id']:a for a in directory['authors']}
assert len(index)==22551
checked={}
for entry in review['entries']:
    for aid in entry['authorIds']:
        profile=read(root/f'dist/author-profiles/{aid[1:3]}.json.gz')[aid]
        checked[aid]=profile
        assert profile['bio']==entry['biography']
        assert len(profile['bio'].split())>=60 and len(profile['bioShort'].split())<=40
        assert profile['bioSources'] and all(s['url'].startswith('https://') and s['title'] for s in profile['bioSources'])
        for key in ['displayName','bio','bioShort','lifeLabel','portrait','birth','death']:
            assert index[aid].get(key)==profile.get(key),(aid,key)
        for key in ['id','name','aliases','recordCount','referenceCount','firstYear','lastYear']:
            assert profile.get(key)==original[aid].get(key),(aid,key)
        records=read(root/f'dist/author-records/{aid[1:3]}.json.gz')[aid]
        assert len(records)==profile['recordCount']
        assert profile['identityCandidates'][0]['bio']==profile['bio']

rorario=checked['a773a245cb082']
assert rorario['birth'] is None and rorario['death'] is None
assert rorario['confidence']['identity']['level']=='high'
assert '1566' in rorario['bio'] and '1542' in rorario['bio']
assert checked['a79050fa903c8']['possibleIdentity']=='Ferdinand Anne Kröger'
assert checked['a79050fa903c8']['birth']==1915
assert checked['a4bac48d3223d']['possibleIdentity']=='Alfred Lacroix'
assert 'Adolphe' not in (checked['a4bac48d3223d']['portrait'] or '')
for aid in ['ab627d370df4d','ae2fd855e09e7','ad4eeb96524e8','a6ca1ea3916cc','ad5304850f719']:
    assert checked[aid]['portrait'] is None,aid
for aid in ['ab627d370df4d','ad4eeb96524e8','a6ca1ea3916cc','ad5304850f719']:
    assert checked[aid]['birth'] is None and checked[aid]['death'] is None,aid
assert checked['ad4eeb96524e8']['confidence']['identity']['level']=='medium'
scene=read(root/'dist/cards-assets/authors.json')
for row in scene['authors']:
    if row['id'] in checked:
        p=checked[row['id']]
        assert row['name']==p['displayName'] and row['portrait']==p['portrait']
        assert row['count']==p['recordCount']
changed=subprocess.check_output(['git','diff','--name-only'],cwd=root,text=True).splitlines()
assert not any(p.startswith(('dist/book-records/','dist/author-records/')) for p in changed)
print(f'{len(checked)} biographies verified; index/profile/portrait-scene consistency passed; catalogue records unchanged.')
