"""Screen revised titles against the already retrieved IA/Crossref corpus.
Conservative new work leads only: close title, matching creator, matching date.
No new surviving-copy estimates or edition verification flags.
"""
import collections,gzip,json,re,sys,time
from pathlib import Path
from ocr_common import norm
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];WORK=ROOT.parent/'ocr-review';CACHE=ROOT.parent/'broad-research/book-cache';CROSS=ROOT.parent/'full-catalogue-pass/cache/crossref'
sys.path.insert(0,str(ROOT.parent/'broad-research/python-libs'))
from rapidfuzz.fuzz import ratio
STOP=set('the and for with from sur les des dans pour par der die das den und von zur zum uber mit fur aus del della delle dello nel della sul per che con di de et la il le da du un of on in an a e i'.split())
def flat(x):return ' ; '.join(map(str,x)) if isinstance(x,list) else str(x or '')
def words(x):return re.findall(r'[a-z]+',__import__('unicodedata').normalize('NFKD',flat(x)).encode('ascii','ignore').decode().lower())
def tokens(x):return set(w for w in words(x) if len(w)>3 and w not in STOP)
def year(x):
 m=re.search(r'\b(1[4-9]\d\d|20[0-2]\d)\b',flat(x));return int(m[1]) if m else None
def surnames(xs):return {norm(x.split(',')[0] if ',' in x else re.sub(r'\d.*','',x).strip().split(' ')[-1]) for x in xs if x}
def main():
 corpus={};start=time.time()
 for p in CACHE.glob('ia-corpus-*.json'):
  if p.name.endswith('log.json'):continue
  for x in json.loads(p.read_text()).get('items',[]):
   if not x.get('identifier') or not x.get('title'):continue
   authors=x.get('creator',[]);authors=authors if isinstance(authors,list) else [authors]
   id='ia:'+x['identifier'];corpus[id]={'source':'Internet Archive','externalId':x['identifier'],'url':'https://archive.org/details/'+x['identifier'],'title':flat(x['title']),'creators':authors,'year':year(x.get('date')),'referenceType':'digitized publication'}
 for p in CROSS.glob('*.json'):
  for x in json.loads(p.read_text()).get('message',{}).get('items',[]):
   if not x.get('DOI') or not x.get('title'):continue
   authors=[' '.join([a.get('given',''),a.get('family','')]).strip() for a in x.get('author',[]) if a.get('family') not in [None,'NA','&NA;']]
   yrs=x.get('published',{}).get('date-parts',[[]]);y=yrs[0][0] if yrs and yrs[0] else None
   id='doi:'+x['DOI'];corpus[id]={'source':'Crossref','externalId':x['DOI'],'url':'https://doi.org/'+x['DOI'],'title':flat(x['title']),'creators':authors,'year':y,'referenceType':x.get('type','journal-article'),'containerTitle':flat(x.get('container-title')),'pages':x.get('page')}
 inv=collections.defaultdict(set);indexed={}
 for id,c in corpus.items():
  ts=tokens(c['title']);c['_norm']=norm(c['title']);c['_tokens']=ts;c['_authors']=surnames(c['creators'])
  for t in ts:inv[t].add(id)
 books=json.loads(gzip.decompress((WORK/'proposed-books.json.gz').read_bytes()));heads=json.loads(gzip.decompress((WORK/'headings.json.gz').read_bytes()));out={};changes=collections.Counter()
 for i,(wid,b) in enumerate(books.items()):
  title=b.get('displayTitle') or b.get('title','');ts=tokens(title);names=surnames(b.get('authorNames',[]));y=b.get('year')
  h=heads.get(wid,{})
  if h.get('confirmed'):names.update(surnames([n['name'] for n in h.get('names',[])]))
  if not ts or not names or y is None or b.get('crossReference') or b.get('continuation'):continue
  rare=sorted((t for t in ts if 0<len(inv[t])<10000),key=lambda t:len(inv[t]))[:3];candidates=set().union(*(inv[t] for t in rare)) if rare else set()
  ranked=[]
  for id in candidates:
   c=corpus[id]
   if c['source']=='Crossref' and not re.search(r'\b(?:Estr|Extr|Extrait|Sonderdruck)[. :]',b.get('text',''),re.I):continue
   if c['year']!=y or not names&c['_authors']:continue
   if len(ts&c['_tokens'])<min(3,len(ts)) or len(ts&c['_tokens'])/max(len(ts),len(c['_tokens']),1)<.82:continue
   sim=ratio(norm(title),c['_norm'])/100
   if sim<.92:continue
   if re.search(r'\b(?:rezension|book review|review of|berichtigt|erratum)\b',c['title'],re.I):continue
   ranked.append((sim,id))
  if ranked:
   vals=[]
   for sim,id in sorted(ranked,reverse=True)[:2]:
    c={k:v for k,v in corpus[id].items() if not k.startswith('_')};c.update(confidence={'level':'medium','score':round(sim,3),'basis':['Revised OCR title closely matches the cached source title','Creator surname and stated publication year agree','Automated work-level lead; edition and individual copy unverified']},editionRelation='Same stated year; edition and family copy unverified',matchType='Possible work match from revised OCR',matchedUsingTitle=title,images=[],retrievedAt='2026-10-17',recheckedAt='2026-10-18')
    vals.append(c)
   out[wid]=vals
  if i%5000==0:print('screened',i,'elapsed',round(time.time()-start),flush=True)
 result={'records':out,'stats':{'recordsScreened':len(books),'corpusRecords':len(corpus),'withCloseTitleCreatorYearMatch':len(out)},'method':'Local rescreening of the previously retrieved Internet Archive/Crossref corpus. No individual web search for each book. New matches remain work-level candidates.'}
 (WORK/'rematch.json.gz').write_bytes(gzip.compress(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode(),mtime=0));print(json.dumps(result['stats']),flush=True)
if __name__=='__main__':main()
