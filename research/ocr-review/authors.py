"""Propose conservative author consolidation from independent OCR agreement."""
import collections,gzip,json,re
from pathlib import Path
from ocr_common import norm,similarity
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];WORK=ROOT.parent/'ocr-review'
def read(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2))
def main():
 profiles=read(WORK/'author-profiles-baseline.json.gz');books=read(WORK/'proposed-books.json.gz');heads=read(WORK/'headings.json.gz')
 links=collections.defaultdict(list)
 for b in books.values():
  for aid in b['authors']:links[aid].append(b['id'])
 votes={};evidence={};held=[]
 for aid,rs in links.items():
  names=[];samples=[];invalid=False
  for wid in rs:
   b=books[wid];h=heads.get(wid)
   if b.get('crossReference') or b.get('continuation'):continue
   if not h or not h['confirmed']:invalid=True;break
   candidates=[n for n in h['names'] if similarity(n['name'],profiles[aid]['name'])>=.75]
   if len(candidates)!=1:invalid=True;break
   n=candidates[0]
   if re.search(r'\b(?:et|and|und|e|y)\b',n['given']) or '&' in n['given']:invalid=True;break
   # Never merge on a surname or initials alone.
   if not any(len(t)>2 and t.lower() not in {'edm','joh','fr','aug','alf','henr','chas','wilh','alex','geo','ant','emm','eug','fred','edw','phil','chas','char','adol'} for t in re.findall(r'[A-Za-zÀ-ÿ]+',n['given'])):invalid=True;break
   names.append(norm(n['name']));samples.append({'record':wid,'heading':h['heading'],'name':n['name']})
  if not invalid and names and len(set(names))==1:votes[aid]=names[0];evidence[aid]=samples
 groups=collections.defaultdict(list)
 for aid,name in votes.items():groups[name].append(aid)
 merges=[]
 exact=collections.defaultdict(list)
 for aid,p in profiles.items():exact[norm(p['name'])].append(aid)
 for name,ids in groups.items():
  ids=list(dict.fromkeys(ids+exact.get(name,[])))
  if len(ids)<2:continue
  conflicts=[f for f in ['birth','death','wikidata'] if len({str(profiles[i][f]) for i in ids if profiles[i].get(f) is not None})>1]
  if conflicts:held.append({'ids':ids,'reason':'Conflicting authority metadata: '+', '.join(conflicts)});continue
  canonical=max(ids,key=lambda i:(bool(profiles[i].get('biographyReview')),bool(profiles[i].get('bioSources')),bool(profiles[i].get('bio')),profiles[i]['recordCount']))
  merges.append({'canonicalId':canonical,'members':ids,'name':next(evidence[i][0]['name'] for i in ids if i in evidence),'confidence':'medium','reason':'Full given name and surname agree in all substantive source-card headings; changed headings agree across two OCR settings; authority metadata has no conflict.','evidence':[s for i in ids for s in evidence.get(i,[])]})
 corrections=[]
 for aid,name in votes.items():
  p=profiles[aid];new=evidence[aid][0]['name']
  if not p.get('bio') and not p.get('bioSources') and norm(p.get('displayName',p['name']))!=name:
   corrections.append({'id':aid,'before':p.get('displayName',p['name']),'after':new,'evidence':evidence[aid]})
 save(WORK/'author-merge-proposals.json',{'groups':merges,'nameCorrections':corrections,'held':held,'profilesWithConsistentFullHeadings':len(votes)})
 print(json.dumps({'groups':len(merges),'redundantEntries':sum(len(g['members'])-1 for g in merges),'conflictsHeld':len(held)}))
 for g in merges[:35]:print(g['name'],[(i,profiles[i]['name'],profiles[i]['recordCount']) for i in g['members']])
if __name__=='__main__':main()
