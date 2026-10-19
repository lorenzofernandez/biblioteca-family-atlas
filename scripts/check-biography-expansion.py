"""Integrity and source-confidence checks for the whole-catalogue biography pass."""
import collections,gzip,importlib.util,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'dist';R=ROOT/'research/biography-expansion'
spec=importlib.util.spec_from_file_location('coverage',ROOT/'scripts/expand-biography-coverage.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
p=c.shards('author-profiles');records=c.shards('author-records');books=c.shards('book-records')
index={a['id']:a for a in c.read(D/'authors-data.json')['authors']}
before=c.read(c.CACHE/'baseline-profiles.json.gz');report=c.read(R/'coverage-report.json')
assert len(books)==49780
assert set(p)==set(before)==set(index)
assert set(records)<=set(p)
assert len(p)==21588
manual_ids={i for f in R.glob('manual-*.json') for e in c.read(f)['entries'] for i in e['authorIds']}
for aid,a in p.items():
    assert len(records.get(aid,[]))==a['recordCount'],aid
    assert a['biographyStatus'] in ['reviewed','source-summary','authority-facts','catalogue-only','unresolved','non-person']
    assert a['confidence']['biography']['level'] in ['high','medium','low','very-low','unresolved']
    assert bool(c.meaningful(a))==bool(c.meaningful(index[aid])),aid
    assert a['catalogueContext']
    if c.meaningful(a):
        assert a.get('bioSource') and a['bioSource'].startswith('https://'),aid
        assert not c.PLACEHOLDER.search(a['bio']),aid
    if a.get('bioSourceKind')=='encyclopedia-excerpt':
        assert a['biographyStatus']=='source-summary'
        assert 'CC BY-SA 4.0' in a['bioLicense']
        assert any('creativecommons.org/licenses/by-sa/4.0' in x['url'] for x in a['bioSources'])
        assert any('action=history' in x['url'] for x in a['bioSources'])
        assert a['confidence']['biography']['level']!='high'
    if a['biographyStatus'] in ['catalogue-only','unresolved','non-person']:
        assert not a.get('bio') and a['confidence']['biography']['level']=='unresolved'
    for key in ['id','key','name','recordCount','referenceCount','firstYear','lastYear']:
        assert a.get(key)==before[aid].get(key),(aid,key)
    if before[aid].get('bioSourceKind')=='research-summary' and aid not in manual_ids:
        assert a['bio']==before[aid]['bio'],aid
for path in R.glob('manual-*.json'):
    for entry in c.read(path)['entries']:
        for aid in entry['authorIds']:
            assert p[aid]['bio']==entry['biography']
            assert p[aid]['displayName']==entry['name']
            assert p[aid]['identityCandidates'][0]['biographyConfidence']['level']==entry['identityLevel']
assert p['a137a3c920ed7']['displayName']=='René-Antoine Ferchault de Réaumur'
assert p['ae4a302c99119']['wikidata']=='Q64981'
assert p['ac50582b0895a']['wikidata']=='Q2158984'
assert p['a9ff09b368c17']['birth']==1811
assert p['ad4795137848d']['biographyStatus']=='non-person'
assert report['entriesWithBiographyAfter']==sum(c.meaningful(a) for a in p.values())
assert report['coverageAfter']>report['coverageBefore']
assert report['detailedBiographiesAfter']>report['detailedBiographiesBefore']
assert report['biographyConfidence']==dict(collections.Counter(a['confidence']['biography']['level'] for a in p.values()))
# Check the original scan/transcription and author-link evidence against the saved
# source commit. Only reviewed display names may change on catalogue records.
protected=['id','authors','text','heading','title','displayTitle','source','file','page','year','crossReference','continuation','attributionEvidence']
changed=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines()
checked=0
for path in changed:
    if not path.startswith(('dist/book-records/','dist/author-records/')):continue
    old=json.loads(gzip.decompress(subprocess.check_output(['git','show',report['baselineCommit']+':'+path],cwd=ROOT)))
    new=c.read(ROOT/path)
    assert set(old)==set(new)
    for key,value in old.items():
        arows=value if isinstance(value,list) else [value]
        brows=new[key] if isinstance(new[key],list) else [new[key]]
        assert len(arows)==len(brows)
        for a,b in zip(arows,brows):
            assert all(a.get(k)==b.get(k) for k in protected),(path,key)
            checked+=1
size=sum(f.stat().st_size for f in D.rglob('*') if f.is_file())
assert size<256*1024*1024,('artifact too large',size)
print(json.dumps({'authors':len(p),'cards':len(books),'biographies':report['entriesWithBiographyAfter'],
    'coverage':report['coverageAfter'],'detailedBiographies':report['detailedBiographiesAfter'],
    'catalogueRecordsCompared':checked,'distMiB':round(size/1024**2,2),'result':'passed'},indent=2))
