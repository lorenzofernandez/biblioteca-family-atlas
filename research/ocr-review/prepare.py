"""Compare fresh scan OCR to the baseline; stage changes without changing the site.
Raw pass files and baseline live in ../ocr-review beside the site checkout.
"""
import collections,copy,gzip,json,re,sys
from pathlib import Path
from ocr_common import clean_text,norm,similarity,parse,needs_second
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];WORK=ROOT.parent/'ocr-review'
def read(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def load_pass(pattern):
 out={}
 for p in WORK.glob(pattern):
  for line in p.read_text().splitlines():
   try:r=json.loads(line)
   except:continue
   out[(r['file'],r['page'])]=r
 return out
def save(p,x):p.write_bytes(gzip.compress(json.dumps(x,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
def main():
 old=read(WORK/'baseline.json.gz');primary=load_pass('accurate-*.jsonl');second=load_pass('second-*.jsonl')
 books=copy.deepcopy(old);changes={};held=[];stats=collections.Counter();heads={}
 protected_dates={x['id']:x for x in read(ROOT/'dist/cards-assets/data.json').get('dateCorrections',[])}
 for wid,b in books.items():
  k=(b['file'],b['page']);r=primary.get(k)
  if not r:continue
  stats['recognized']+=1;s=second.get(k);stats['secondPass']+=bool(s)
  text=clean_text(r['text']);ratio=similarity(b.get('text',''),text)
  reasons=[]
  if len(norm(text))<.78*len(norm(b.get('text',''))):reasons.append('possible-text-loss')
  if ratio<.60:reasons.append('large-transcription-disagreement')
  if r['confidence']<.82:reasons.append('weak-recognition')
  # Compare complete text, but do not silently modernize unusual historical words.
  if reasons:
   held.append({'id':wid,'issues':reasons,'oldText':b['text'],'proposedText':text,'similarity':round(ratio,3)});stats['transcriptionsHeld']+=1
   continue
  before={key:copy.deepcopy(b.get(key)) for key in ['text','heading','title','displayTitle','year','authors','authorNames']}
  p=parse(text,b);p2=parse(s['text'],b) if s else None
  heading_stable=bool(p2 and norm(p['heading'])==norm(p2['heading'])) or norm(p['heading'])==norm(b.get('heading',''))
  heads[wid]={'heading':p['heading'],'names':p['names'],'confirmed':heading_stable,'oldHeading':b.get('heading'),'isName':p['isName']}
  b['text']=text
  protected=bool(b.get('editionReview') or b.get('research',{}).get('curated'))
  if heading_stable and p['heading']:b['heading']=p['heading']
  if p['title'] and len(p['title'])>=8 and len(p['title'])<=1200 and not b.get('crossReference') and not protected:
   # A readable replacement must retain most of the substantive existing title.
   oldtitle=re.split(r'\b(?:Estr|cm|Leg)\b',b.get('displayTitle') or b.get('title',''),flags=re.I)[0]
   if similarity(oldtitle,p['title'])>=.65 or norm(oldtitle) in norm(p['title']):
    b['title']=p['title'];b['displayTitle']=p['title']
  if p['year']!=b.get('year') and p['year'] is not None and p2 and p2['year']==p['year'] and not protected and wid not in protected_dates:
   # Century-digit errors can recur across OCR settings. Retain the old date
   # unless the scan text explains it as another date (e.g. a title's period).
   if b.get('year') and abs(b['year']-p['year'])>60 and str(b['year']) not in text:
    held.append({'id':wid,'issues':['large-date-change-needs-visual-review'],'before':b['year'],'proposed':p['year'],'evidence':p['yearEvidence']});stats['largeDateChangesHeld']+=1
   else:
    b['year']=p['year'];b['dateEvidence']={'value':p['year'],'quote':p['yearEvidence'],'method':'Agreed by two accurate OCR settings, extracted from publication/citation area','confidence':'medium'}
  if wid in protected_dates:b['year']=protected_dates[wid]['year']
  if p2 and p['yearCandidates']!=p2['yearCandidates']:
   held.append({'id':wid,'issues':['date-disagreement-between-OCR-passes'],'first':p['yearCandidates'],'second':p2['yearCandidates']});stats['dateDisagreements']+=1
  if not heading_stable:
   held.append({'id':wid,'issues':['heading-needs-review'],'oldHeading':b.get('heading'),'first':p['heading'],'second':p2['heading'] if p2 else None});stats['headingsHeld']+=1
  delta={key:{'before':before[key],'after':b.get(key)} for key in before if before[key]!=b.get(key)}
  if delta:
   changes[wid]={'file':b['file'],'page':b['page'],'changes':delta,'secondPass':bool(s)}
   for key in delta:stats[key+'Changed']+=1
  if before['text']!=text:b['ocrReview']={'date':'2026-10-18','method':'Apple Vision accurate, 1800-pixel rendering','secondPass':bool(s),'status':'machine-retranscribed'}
 save(WORK/'proposed-books.json.gz',books);save(WORK/'changes.json.gz',changes);save(WORK/'headings.json.gz',heads);save(WORK/'held.json.gz',held)
 (WORK/'prepare-stats.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats,indent=2))
if __name__=='__main__':main()
