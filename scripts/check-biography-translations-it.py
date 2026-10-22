"""Check shipping Italian dictionaries against all rendered biography variants."""
from pathlib import Path
import json,gzip,re,collections
root=Path(__file__).resolve().parents[1];dist=root/'dist';translations={}
for file in (dist/'biographies-it').glob('*.json'):
 if file.name.startswith('.'):continue
 translations.update(json.loads(file.read_text()))
translations.update(json.loads((dist/'translations-it.json').read_text()))
texts=set()
for file in (dist/'author-profiles').glob('*.json.gz'):
 if file.name.startswith('.'):continue
 for author in json.load(gzip.open(file)).values():
  for candidate in [author]+author.get('identityCandidates',[]):
   for field in ('bio','bioShort'):
    texts.update(p.strip() for p in re.split(r'\n\s*\n',candidate.get(field) or '') if p.strip())
for author in json.loads((dist/'authors-data.json').read_text())['authors']:
 text=(author.get('bio') or '').strip()
 if not text:continue
 texts.add(text)
 if len(text)>240:
  matches=list(re.finditer(r'[.!?](?:\s|$)',text[:240]));texts.add(text[:matches[-1].start()+1] if matches else re.sub(r'\s+\S*$','',text[:237])+'…')
missing=[text for text in texts if not translations.get(text,'').strip()]
assert not missing,f'{len(missing)} missing translations: {missing[:2]}'
wrong_numbers=[text for text in texts if collections.Counter(re.findall(r'\d{3,4}',text))!=collections.Counter(re.findall(r'\d{3,4}',translations[text]))]
assert not wrong_numbers,f'{len(wrong_numbers)} year mismatches: {wrong_numbers[:2]}'
print(f'PASS: {len(texts):,} biography, alternative-identity and directory-preview texts have nonempty Italian translations; source years preserved.')
