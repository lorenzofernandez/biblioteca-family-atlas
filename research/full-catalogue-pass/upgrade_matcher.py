from pathlib import Path
p=Path('work/full-catalogue-pass/match_catalogue.py');s=p.read_text()
s=s.replace('import json,re,unicodedata,pathlib,math,collections,sys,heapq,time,html,os','import json,re,unicodedata,pathlib,math,collections,sys,heapq,time,html,os,gzip')
s=s.replace('from rapidfuzz.fuzz import ratio,token_set_ratio,partial_ratio','from rapidfuzz.fuzz import ratio,token_set_ratio,partial_ratio\nfrom rapidfuzz import process')
s=s.replace("ROOT=pathlib.Path('work/broad-research');CACHE=ROOT/'book-cache'","ROOT=pathlib.Path('work/full-catalogue-pass');PREVIOUS=pathlib.Path('work/broad-research');CACHE=PREVIOUS/'book-cache'")
s=s.replace(" x=html.unescape(re.sub('<[^>]*>',' ',flat(x)))"," x=html.unescape(re.sub('<[^>]*>',' ',flat(x))).replace('£','f').replace('æ','ae').replace('œ','oe')\n x=re.sub(r'(\\w)[-=¬]\\s+(\\w)',r'\\1\\2',x)\n x=x.replace('Ueber','Uber').replace('ueber','uber')")
s=s.replace("corpus=[];inv=collections.defaultdict(list);author_inv=collections.defaultdict(list);seen=set()","corpus=[];inv=collections.defaultdict(list);author_inv=collections.defaultdict(list);seen=set()")
s=s.replace("record={'id':d['identifier']", "record={'source':'Internet Archive','referenceType':'digitized publication','url':'https://archive.org/details/'+d['identifier'],'id':d['identifier']")
# Add journal-article metadata to the same corpus.
marker="N=len(corpus);idf="
pos=s.index(marker)
extra='''for p in sorted((ROOT/'cache'/'crossref').glob('*.json')):
 try:items=json.load(open(p)).get('message',{}).get('items',[])
 except Exception:continue
 for d in items:
  ident=d.get('DOI')
  if not ident or ident in seen or not d.get('title'):continue
  seen.add(ident);title=flat(d['title']);nt=norm(title);tt=toks(title)
  if not tt:continue
  creators=[' '.join([a.get('given',''),a.get('family','')]).strip() for a in d.get('author',[]) if a.get('family') and a.get('family') not in ['&NA;','NA']]
  creators=creators[:20];dateparts=d.get('published',{}).get('date-parts',[[None]])
  pubyear=dateparts[0][0] if dateparts and dateparts[0] else None
  container=flat(d.get('container-title'));idx=len(corpus)
  record={'source':'Crossref','referenceType':d.get('type','article'),'url':d.get('URL') or 'https://doi.org/'+ident,'id':ident,'title':title,'creators':creators,'year':pubyear,'publisher':flat(d.get('publisher')),'description':'Article metadata: '+container+(' · volume '+str(d['volume']) if d.get('volume') else '')+(' · pages '+str(d['page']) if d.get('page') else ''),'subjects':[],'rights':'Metadata supplied through Crossref; access and reuse terms of article content are determined by the publisher.','license':'','language':None,'collection':[],'nt':nt,'tokens':tt,'ct':namekeys(creators),'containerTitle':container,'volume':d.get('volume'),'issue':d.get('issue'),'pages':d.get('page'),'issn':d.get('ISSN',[])}
  corpus.append(record)
  for namekey in record['ct']:author_inv[namekey].append(idx)
  for t in tt:inv[t].append(idx)
 print('loaded article file',p.name,'total corpus',len(corpus),flush=True)
'''
s=s[:pos]+extra+s[pos:]
start=s.index("books=json.load(open('work/library-site/dist/books-data.json'))")
end=s.index('records={};stats=',start)
new='''books=[]
for p in sorted(pathlib.Path('work/library-site/dist/book-records').glob('*.json.gz')):
 books.extend(json.load(gzip.open(p,'rt')).values())
if not books:
 for p in sorted(pathlib.Path('work/library-site/dist/book-records').glob('*.json')):books.extend(json.load(open(p)).values())
books=books[:int(os.environ.get('BOOK_LIMIT','999999'))]
corrections=json.load(open(PREVIOUS/'attribution-candidates.json')) if (PREVIOUS/'attribution-candidates.json').exists() else {}
name_map={a['id']:a.get('name','') for a in json.load(open('work/library-site/dist/authors-data.json'))['authors']}

def phon(t):
 return t.replace('ae','e').replace('oe','e').replace('ue','u').replace('ph','f').replace('y','i').replace('j','i').replace('ck','k')
phon_inv=collections.defaultdict(list);prefix_vocab=collections.defaultdict(list);suffix_vocab=collections.defaultdict(list)
for token,posting in inv.items():
 if len(token)>=4:
  phon_inv[phon(token)].append(token)
  if len(posting)>=2:
   prefix_vocab[token[:2]].append(token);suffix_vocab[token[-3:]].append(token)
spell_cache={}
def expansions(token):
 if token in spell_cache:return spell_cache[token]
 result={token:1.0}
 for t in phon_inv.get(phon(token),[]):
  if t!=token and len(inv[t])<25000:result[t]=.94
 if len(token)>=5 and len(inv.get(token,[]))<5:
  pool=set(prefix_vocab.get(token[:2],[])+suffix_vocab.get(token[-3:],[]))
  pool=[t for t in pool if abs(len(t)-len(token))<=max(2,len(token)//5)]
  for match,score,_ in process.extract(token,pool,scorer=ratio,score_cutoff=83 if len(token)>7 else 88,limit=3):result[match]=max(result.get(match,0),score/100*.9)
 spell_cache[token]=result;return result
city_re=re.compile(r'\\b(?:Paris|Londres|London|Berlin|Leipzig|Leipsic|Leida|Lugduni|Amstelodami|Venetiis|Venetia|Venezia|Padova|Patavii|Bologna|Bononiae|Roma|Romae|Napoli|Neapoli|Torino|Firenze|Geneve|Geneva|Ginevra|Milano|Milan|Basel|Basileae|Cambridge|Oxford|New York|Amsterdam|Halle|Heidelberg|Wien|Vienna|Breslau|Stuttgart|Jena|Gottingen|Göttingen|Brescia|Modena|Pavia|Florence|Edinburgh|Edimburgo)\\b',re.I)
def variants(b):
 originals=[b.get('displayTitle') or b.get('title',''), corrections.get(b['id'],{}).get('title') or b.get('title','')]
 vals=[]
 for x in originals:
  x=x.replace('£','f');x=re.sub(r'(\\w)[-=¬]\\s+(\\w)',r'\\1\\2',x)
  x=re.split(r'\\b(?:Estr\\.?|Estratto|Estralt|Extrait|Extracted|Auszug)\\b',x,flags=re.I)[0]
  x=re.split(r'\\b(?:cm\\.?|pp\\.?)\\s*\\d',x,flags=re.I)[0]
  for m in city_re.finditer(x):
   if m.start()>12:
    vals.append(x[:m.start()].strip(' ,.;'));break
  vals.append(x.strip(' ,.;'))
 unique=[];seenq=set()
 for v in vals:
  n=norm(v)
  # Repair line-broken words when the joined form occurs in the public title vocabulary.
  words=n.split();i=0;out=[]
  while i<len(words):
   if i+1<len(words) and len(words[i])>=2 and len(words[i+1])>=2 and words[i]+words[i+1] in inv and (words[i] not in inv or words[i+1] not in inv):out.append(words[i]+words[i+1]);i+=2
   else:out.append(words[i]);i+=1
  n=' '.join(out)
  if n not in seenq and len(n)>5:seenq.add(n);unique.append((v,n,toks(n)))
 return unique[:3] or [(b.get('title',''),norm(b.get('title','')),toks(b.get('title','')))]
'''
s=s[:start]+new+s[end:]
start=s.index(" original=b['title'];title=");end=s.index(' ranked=[]',start)
new=''' qvars=variants(b);title,nt,qt=qvars[0];names=b.get('authorNames',[])[:]
 for aid in corrections.get(b['id'],{}).get('additionalAuthors',[]):
  if name_map.get(aid) and name_map[aid] not in names:names.append(name_map[aid])
 ct=namekeys(names);knownyear=b.get('year');kind='cross_reference' if b.get('crossReference') else 'continuation' if b.get('continuation') else 'journal_offprint' if re.search(r'\\b(?:Estr\\.?|Estratto|Extrait)\\b',b.get('text',''),re.I) else 'record'
 qfull=set().union(*(z[2] for z in qvars));ex={t:expansions(t) for t in qfull}
 eligible=sorted((t for t in qfull if any(t2 in inv and len(inv[t2])<=30000 for t2 in ex[t])),key=lambda t:min((len(inv.get(t2,[])) for t2 in ex[t] if t2 in inv),default=999999))[:12]
 counter=collections.defaultdict(float)
 for t in eligible:
  for alt,wgt in ex[t].items():
   if len(inv.get(alt,[]))>30000:continue
   for idx in inv.get(alt,[]):counter[idx]+=idf.get(alt,1)*wgt
 for namekey in ct:
  if len(author_inv.get(namekey,[]))<=5000:
   for idx in author_inv.get(namekey,[]):counter[idx]+=5
 shortlisted=heapq.nlargest(180,counter,key=counter.get)
'''
s=s[:start]+new+s[end:]
start=s.index(' qmass=sum(');end=s.index('  author_score=0',start)
new=''' for idx in shortlisted:
  d=corpus[idx];best=None
  for qtitle,qnt,qtt in qvars:
   qmass=sum(idf.get(t,7) for t in qtt)
   weights={t:max((w for alt,w in ex.get(t,{t:1}).items() if alt in d['tokens']),default=0) for t in qtt}
   ninter=sum(w>.7 for w in weights.values())
   if ninter<1:continue
   coverage=sum(idf.get(t,7)*w for t,w in weights.items())/max(qmass,1)
   reverse=sum(max((idf.get(alt,7)*w for alt,w in ex.get(t,{t:1}).items() if alt in d['tokens']),default=0) for t in qtt)/max(sum(idf[t] for t in d['tokens']),1)
   reverse=min(1,reverse);overlap=2*coverage*reverse/max(coverage+reverse,.01)
   fuzz=ratio(qnt,d['nt'])/100;tokenf=token_set_ratio(qnt,d['nt'])/100
   partial=partial_ratio(qnt,d['nt'])/100
   title_score=.30*tokenf+.22*fuzz+.18*partial+.30*overlap
   if best is None or title_score>best[0]:best=(title_score,coverage,ninter,qtitle,len(qtt))
  if best is None:continue
  title_score,coverage,ninter,usedtitle,qlen=best
'''
s=s[:start]+new+s[end:]
s=s.replace("  if ninter==1:score=min(score,.52)","  if ninter==1 and author_score<.5:score=min(score,.52)")
start=s.index('  # Include uncertain title leads');end=s.index(' ranked.sort',start)
new='''  # Generous candidate tier still requires title coherence, and known creator conflicts are explicit.
  if coverage<.25 or title_score<.47 or score<.46:continue
  if ninter<2 and not (qlen<=3 and author_score>=.8 and title_score>=.65):continue
  if ninter<3 and author_score<.5 and title_score<.84:continue
  if coverage<.38 and author_score<.5:continue
  if ct and d['ct'] and author_score==0 and title_score<.84:continue
  ranked.append((score,title_score,author_score,coverage,delta,idx,ninter,usedtitle))
'''
s=s[:start]+new+s[end:]
s=s.replace('for score,ts,aus,coverage,delta,idx,ninter in ranked:', 'for score,ts,aus,coverage,delta,idx,ninter,usedtitle in ranked:')
s=s.replace("sourceurl='https://archive.org/details/'+d['id']", "sourceurl=d['url']")
s=s.replace("{'source':'Internet Archive','externalId'", "{'source':d['source'],'referenceType':d['referenceType'],'externalId'")
s=s.replace("'images':[image],'manifestUrl':'https://iiif.archive.org/iiif/'+d['id']+'/manifest.json'", "'images':[image] if d['source']=='Internet Archive' else [],'manifestUrl':'https://iiif.archive.org/iiif/'+d['id']+'/manifest.json' if d['source']=='Internet Archive' else None,'containerTitle':d.get('containerTitle'),'volume':d.get('volume'),'issue':d.get('issue'),'pages':d.get('pages'),'issn':d.get('issn',[])")
s=s.replace("'matchedUsingTitle':title", "'matchedUsingTitle':usedtitle")
s=s.replace("records[b['id']]={'status':status,'recordKind':kind,'searchedTitle':title,'candidates':cand}", "records[b['id']]={'status':status,'recordKind':kind,'searchedTitle':title,'titleVariants':[x[0] for x in qvars],'candidates':cand,'containerCandidates':[],'searchAssessment':{'localCorpusScreened':True,'individualExternalSearch':False,'method':'OCR-aware title variants plus creator/year matching against cached Internet Archive and bounded Crossref journal metadata','confidence':'low' if not cand else cand[0]['confidence']['level'],'outcome':status,'survivingCopies':'Not inferred from digital references'}}")
s=s.replace("'book-candidates-checkpoint.json'", "'candidates-checkpoint.json'").replace("'book-candidates.json'", "'book-candidates.json'")
s=s.replace("'corpusRecords':N", "'corpusRecords':N,'internetArchiveRecords':sum(x['source']=='Internet Archive' for x in corpus),'crossrefRecords':sum(x['source']=='Crossref' for x in corpus),'localRecordsScreened':len(books),'individualExternalRecordSearches':0")
s=s.replace("All catalogue records searched locally against public Internet Archive metadata. Token-index retrieval followed by fuzzy title, creator and publication-year scoring.","All catalogue records screened locally against public Internet Archive and a bounded Crossref journal-article metadata corpus. OCR f/£ repair, line-break repair, shortened imprint-free title variants, phonetic token normalization and near-spelling retrieval precede fuzzy title, creator and publication-year scoring.")
s=s.replace("Scientific and historical collections plus science-related subject records dated through 1965, selected through the query saved in book-cache/ia-corpus-log.json.","All family catalogue records were screened locally, not individually searched on the web. Internet Archive corpus source selection is recorded in the earlier broad-research/book-cache/ia-corpus-log.json. The added bounded Crossref journal corpus and its requests are recorded in full-catalogue-pass/cache/crossref-retrieval-log.json. Unmatched records may be absent from these corpora, have unreadable OCR, or need other sources; this is not an exhaustive search of world catalogues.")
p.write_text(s)
