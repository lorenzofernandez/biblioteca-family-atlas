"""Build local Italian biography translations; originals and attribution stay untouched.
Requires ctranslate2, sentencepiece and an installed Argos English/Italian model.
Usage: python translate-author-biographies-it.py /path/to/en_it
"""
from pathlib import Path
import sys,json,gzip,re,hashlib,time,collections
import ctranslate2,sentencepiece
root=Path(__file__).resolve().parents[1];dist=root/'dist';model=Path(sys.argv[1]);cache=root/'research/biography-translations-it';cache.mkdir(parents=True,exist_ok=True)
texts=set()
for file in sorted((dist/'author-profiles').glob('*.json.gz')):
 if file.name.startswith('.'):continue
 for author in json.load(gzip.open(file)).values():
  for person in [author]+author.get('identityCandidates',[]):
   for field in ['bio','bioShort']:
    for paragraph in re.split(r'\n\s*\n',person.get(field) or ''):
     if paragraph.strip():texts.add(paragraph.strip())
# Directory previews may be independently shortened.
for author in json.loads((dist/'authors-data.json').read_text())['authors']:
 if author.get('bio'):
  text=author['bio'].strip();texts.add(text)
  if len(text)>240:
   matches=list(re.finditer(r'[.!?](?:\s|$)',text[:240]))
   preview=text[:matches[-1].start()+1] if matches else re.sub(r'\s+\S*$','',text[:237])+'…'
   texts.add(preview)
manual=json.loads((dist/'translations-it.json').read_text());sentences={};parts={}
for text in sorted(texts):
 if text in manual:continue
 pieces=re.split(r'(?<=[.!?])\s+(?=[A-ZÀ-Ý“"\d])',text)
 chunks=[]
 for piece in pieces:
  # Hard limit prevents truncation in exceptionally long source sentences.
  words=piece.split();chunks.extend(' '.join(words[i:i+95]) for i in range(0,len(words),95))
 parts[text]=chunks
 for chunk in chunks:sentences.setdefault(chunk,None)
cachefile=cache/'sentence-cache.json'
if cachefile.exists():
 old=json.loads(cachefile.read_text())
 for source in sentences:
  if source in old:sentences[source]=old[source]
sp=sentencepiece.SentencePieceProcessor(model_file=str(model/'sentencepiece.model'))
translator=ctranslate2.Translator(str(model/'model'),device='cpu',compute_type='int8',inter_threads=2,intra_threads=4)
pending=[s for s,v in sentences.items() if v is None];started=time.time()
for start in range(0,len(pending),96):
 batch=pending[start:start+96];tokens=[sp.encode(s,out_type=str) for s in batch]
 results=translator.translate_batch(tokens,beam_size=2,max_batch_size=96,max_decoding_length=512)
 for source,result in zip(batch,results):sentences[source]=sp.decode(result.hypotheses[0])
 if start%960==0 or start+96>=len(pending):
  cachefile.write_text(json.dumps({k:v for k,v in sentences.items() if v is not None},ensure_ascii=False))
  print(f'{min(start+96,len(pending))}/{len(pending)} sentences translated · {time.time()-started:.0f}s',flush=True)
output=dist/'biographies-it';output.mkdir(exist_ok=True);shards=collections.defaultdict(dict);issues=[]
for source in sorted(texts):
 translated=manual.get(source) or ' '.join(sentences[s] for s in parts[source])
 # Match JS UTF-16 FNV-1a hash used to load only the required dictionary shard.
 h=2166136261
 raw=source.encode('utf-16-le')
 for i in range(0,len(raw),2):h=((h^(raw[i]+256*raw[i+1]))*16777619)&0xffffffff
 shards[f'{h&255:02x}'][source]=translated
 before=collections.Counter(re.findall(r'\d{3,4}',source));after=collections.Counter(re.findall(r'\d{3,4}',translated))
 if before!=after:issues.append({'source':source,'translation':translated,'sourceYears':dict(before),'translatedYears':dict(after)})
for name,data in shards.items():
 (output/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
report={'language':'it','method':'Automatic offline translation with Argos en_it 1.0 / CTranslate2; existing editorial translations take precedence','textCount':len(texts),'translatedCount':sum(map(len,shards.values())),'sourceCharacters':sum(map(len,texts)),'shards':len(shards),'yearMismatchCount':len(issues),'yearMismatches':issues}
(cache/'coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='yearMismatches'}),flush=True)
