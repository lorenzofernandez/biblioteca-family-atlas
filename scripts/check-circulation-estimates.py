"""Guard the boundary between an exploratory model and observed evidence."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('estimates',Path(__file__).with_name('build-circulation-estimates.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
base={'id':'wtest','year':1728,'page':1,'source':'originals/test.pdf','text':'A printed work. London, 1728.','catalogueScreening':{'formatLabel':'Publication format unresolved'},'research':{'referenceYear':1954}}

e,reason=module.estimate(base)
assert e['cohort']=='eighteenth' and e['confidence']=='very-low' and (e['min'],e['max'])==(10,2000)
assert base['research']=={'referenceYear':1954},'Model must not mutate research facts'
for marker in ['crossReference','continuation']:
 r={**base,marker:True};assert module.estimate(r)[0] is None
assert module.estimate({**base,'year':None})[0] is None
r={**base,'year':None,'catalogueScreening':{'formatLabel':'Catalogue extract / offprint'}}
e,_=module.estimate(r);assert (e['min'],e['max'])==(1,300) and 'Separate offprint' in e['scope']
r=copy.deepcopy(base);r['survivalResearch']={'editionMatchConfidence':'high','documentedLowerBound':80}
e,_=module.estimate(r);assert e['min']==80 and e['max']==2000
r['survivalResearch']['documentedLowerBound']=3000
assert module.estimate(r)[0] is None,'A known minimum above the model ceiling requires review'
r['survivalResearch']['editionMatchConfidence']='low'
e,_=module.estimate(r);assert e['min']==10 and e['documentedMinimumApplied'] is None,'Uncertain-edition counts cannot constrain another printing'
for evidence in [{'conditionalSurvivalBounds':{'maxApprox':100}}, {'worldwideEstimate':{'min':10,'max':40}}, {'evidence':[{'type':'published edition census'}]}]:
 assert module.estimate({**base,'survivalResearch':evidence})[0] is None
assert module.estimate({**base,'editionReview':{'decision':'different_edition'}})[0] is None
assert module.estimate({**base,'catalogueScreening':{'signals':[{'label':'Incomplete copy or set'}]}})[0] is None

root=module.ROOT;index=json.loads(gzip.decompress((root/'circulation-estimates-index.json.gz').read_bytes()))
assert index['total']==49780 and len(index['records'])==index['estimated']
assert sum(index['confidenceCounts'].values())==index['estimated']
assert sum(index['excluded'].values())+index['estimated']==index['total']
count=0
for path in (root/'circulation-estimates').glob('*.json.gz'):
 estimates=json.loads(gzip.decompress(path.read_bytes()))
 records=json.loads(gzip.decompress((root/'book-records'/path.name).read_bytes()))
 for key,e in estimates.items():
  assert key in records and key in index['records']
  assert 0<e['min']<=e['max'] and e['confidence'] in {'low','very-low'}
  assert e['sources'][0]['url'].startswith('originals/')
  if e['documentedMinimumApplied'] is not None:assert e['min']>=e['documentedMinimumApplied']
  assert not records[key].get('crossReference') and not records[key].get('continuation')
  count+=1
assert count==index['estimated']
print(f'Passed evidence-boundary checks and validation of {count:,} estimate records.')
