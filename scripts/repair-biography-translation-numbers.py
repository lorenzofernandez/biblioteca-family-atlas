from pathlib import Path
import json,re,collections,sys
import ctranslate2,sentencepiece
root=Path(__file__).resolve().parents[1];model=Path(sys.argv[1]);cache=root/'research/biography-translations-it/sentence-cache.json'
# Run only after the translation writer has completed.
data=json.loads(cache.read_text());sp=sentencepiece.SentencePieceProcessor(model_file=str(model/'sentencepiece.model'));translator=ctranslate2.Translator(str(model/'model'),device='cpu',compute_type='int8',intra_threads=4)
issues=[s for s,t in data.items() if collections.Counter(re.findall(r'\d+',s))!=collections.Counter(re.findall(r'\d+',t))];fixed=0
for source in issues:
 pieces=re.split(r'(\d+)',source);strings=[piece for i,piece in enumerate(pieces) if i%2==0 and re.search(r'[A-Za-z]',piece)];translated=iter([sp.decode(r.hypotheses[0]) for r in translator.translate_batch([sp.encode(x,out_type=str) for x in strings],beam_size=4,max_decoding_length=512)])
 out=[]
 for i,piece in enumerate(pieces):
  if i%2 or not re.search(r'[A-Za-z]',piece):out.append(piece);continue
  text=next(translated);text=re.sub(r'\d+','',text);out.append((' ' if piece.startswith(' ') else '')+text+(' ' if piece.endswith(' ') else ''))
 result=''.join(out)
 if collections.Counter(re.findall(r'\d+',source))==collections.Counter(re.findall(r'\d+',result)):data[source]=result;fixed+=1
cache.write_text(json.dumps(data,ensure_ascii=False));print('Repaired numeric preservation:',fixed,'of',len(issues),flush=True)
