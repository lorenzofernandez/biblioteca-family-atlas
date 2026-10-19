import glob,gzip,json,re,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parent
records={}
for f in glob.glob(str(ROOT.parent/'library-site/dist/book-records/*.json.gz')):records.update(json.load(gzip.open(f,'rt')))
patterns={
'scarcity':r'\b(?:rar[oaie](?:issim[oaie])?|rarissim[oaie]|rariss\.?|rarit[aà]|rare|rarissime|selten(?:e[rsnm]?)?)\b',
'printing':r'\b(?:tirat[ouiea]|tiratur[ae]|tirage|tir[ée]s?|limitat[aoie]|limited|numbered|numerat[oaie]|esemplari|exemplaires|exemplaren|exemplare|copies|copie|numerot[ée]s?|esempl\.?|exempl\.?)\b',
'manuscript':r'\b(?:manoscritt[oaie]|manuscrits?|manuscripts?|handschrift(?:en|lich)?|autograf[oaie])\b|\b(?:ms|mss)\.(?=\s|$)',
'reproduction':r'\b(?:fac[.\s-]?simil[eié]s?|facsimile|ristamp[ae]|reprint(?:ed)?|anastatic[oaie]|riproduzione|photocopy|fotocopi[ae]|faksimile)\b',
'offprint':r'\b(?:estr|extr|estratt)\.(?=\s|[A-Za-z\"\'])|\b(?:estratt[oi]|extraits?|offprints?|sonderdruck|abdruck|separatum)\b',
'incomplete':r'\b(?:mancant[ei]|manca(?:no)?|mutil[oaie]|scomplet[oaie]|incomplet[oaie]|incomplete|difettos[oaie]|fehl(?:en|t)|lacks?|wanting|defective)\b',
}
rx={k:re.compile(v,re.I) for k,v in patterns.items()}
candidates={};counts=collections.Counter();cross=collections.Counter()
for id,r in records.items():
 text=r.get('text','');signals={}
 for k,x in rx.items():
  ms=list(x.finditer(text))
  if ms:
   signals[k]=[{'match':m.group(),'start':m.start(),'excerpt':text[max(0,m.start()-130):min(len(text),m.end()+180)]} for m in ms]
   counts[k]+=1
 if signals:
  candidates[id]={k:r.get(k) for k in ['id','file','page','section','text','heading','title','year','crossReference','continuation','source']}
  candidates[id]['signals']=signals
  if r.get('crossReference') or r.get('continuation'):cross['excludedRecords']+=1
(ROOT/'signal-candidates.json').write_text(json.dumps(candidates,ensure_ascii=False,indent=2))
(ROOT/'signal-scan-stats.json').write_text(json.dumps({'recordsScreened':len(records),'candidateRecords':len(candidates),'patternCounts':dict(counts),'nonIndependentCandidates':dict(cross),'patterns':patterns},ensure_ascii=False,indent=2))
print(len(records),len(candidates),counts,cross)
for key in ['scarcity','printing','manuscript','reproduction','incomplete']:
 with (ROOT/(key+'-review.txt')).open('w') as o:
  for id,r in candidates.items():
   if key in r['signals']:
    o.write('\n'+id+' '+str(r['file'])+' #page='+str(r['page'])+' CROSS='+str(r.get('crossReference'))+' CONT='+str(r.get('continuation'))+'\n'+r['text']+'\n')
