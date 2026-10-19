import json,re,unicodedata,pathlib,math,collections,sys,heapq,time,html,os,gzip
sys.path.insert(0,'work/broad-research/python-libs')
from rapidfuzz.fuzz import ratio,token_set_ratio,partial_ratio
from rapidfuzz import process
ROOT=pathlib.Path('work/full-catalogue-pass');PREVIOUS=pathlib.Path('work/broad-research');CACHE=PREVIOUS/'book-cache'
STOP=set('the and for with from into that this their sur les des une dans pour par aux avec est comme der die das den dem und von zur zum uber ueber ein eine eines einer mit fur fuer auf aus bei del della delle degli dello dei nel nell nella nelle sulla sul sui su per che con una uno gli lo le la il i e di de et a el en es da du un an as in of on at to or is vol volume band parte part serie ser edition ed text texte abbildungen abbildung illustrations fig seiten pages press verlag university publisher estr extr estratto est extrait auszug herausgegeben'.split())
def flat(x):
 if isinstance(x,list):return ' ; '.join(str(y) for y in x)
 return str(x or '')
def norm(x):
 x=html.unescape(re.sub('<[^>]*>',' ',flat(x))).replace('£','f').replace('æ','ae').replace('œ','oe')
 x=re.sub(r'(\w)[-=¬]\s+(\w)',r'\1\2',x)
 x=x.replace('Ueber','Uber').replace('ueber','uber')
 x=unicodedata.normalize('NFKD',x).encode('ascii','ignore').decode().lower()
 x=re.sub(r'[^a-z0-9]+',' ',x);return ' '.join(x.split())
def toks(x):return set(t for t in norm(x).split() if len(t)>2 and not t.isdigit() and t not in STOP)
def namekeys(names):
 result=set()
 for name in names:
  part=re.sub(r'\d.*','',str(name)).strip(' ,.;')
  if not part:continue
  if ',' in part:result.update(toks(part.split(',')[0]))
  else:
   words=norm(part).split()
   if words and len(words[-1])>2:result.add(words[-1])
 return result
def year(x):
 m=re.search(r'(?<!\d)(1[0-9]{3}|20[0-2][0-9])(?!\d)',flat(x));return int(m[0]) if m else None

def clip(x,n=26):
 s=html.unescape(re.sub('<[^>]*>',' ',flat(x)));s=' '.join(s.split());words=s.split();return ' '.join(words[:n])+(' …' if len(words)>n else '')

corpus=[];inv=collections.defaultdict(list);author_inv=collections.defaultdict(list);seen=set()
for p in sorted(CACHE.glob('ia-corpus-*.json'))[:int(os.environ.get('CORPUS_PAGE_LIMIT','999'))]:
 if p.name.endswith('log.json'):continue
 for d in json.load(open(p)).get('items',[]):
  if d.get('identifier') in seen or not d.get('title'):continue
  seen.add(d['identifier']);title=flat(d['title']);nt=norm(title);tt=toks(title)
  if not tt:continue
  idx=len(corpus)
  creators=d.get('creator',[]);creators=creators if isinstance(creators,list) else [creators]
  subjects=d.get('subject',[]);subjects=subjects if isinstance(subjects,list) else [subjects]
  record={'source':'Internet Archive','referenceType':'digitized publication','url':'https://archive.org/details/'+d['identifier'],'id':d['identifier'],'title':title,'creators':creators,'year':year(d.get('date')),'publisher':flat(d.get('publisher')),'description':clip(d.get('description'),24),'subjects':[clip(z,12) for z in subjects[:8]],'rights':flat(d.get('rights')),'license':flat(d.get('licenseurl')),'language':d.get('language'),'collection':d.get('collection',[]),'nt':nt,'tokens':tt,'ct':namekeys(creators)}
  corpus.append(record)
  for namekey in record['ct']:author_inv[namekey].append(idx)
  for t in tt:inv[t].append(idx)
 print('loaded',p.name,len(corpus),flush=True)
for p in sorted((ROOT/'cache'/'crossref').glob('*.json')):
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
  record={'source':'Crossref','referenceType':'possible book review or bibliographic notice' if re.search(r'\b(?:Verlag|Seiten|Preis|gebunden|Geb\.)\b',title,re.I) and re.search(r'\b(?:19|18)\d{2}\b',title) else d.get('type','article'),'url':d.get('URL') or 'https://doi.org/'+ident,'id':ident,'title':title,'creators':creators,'year':pubyear,'publisher':flat(d.get('publisher')),'description':'Article metadata: '+container+(' · volume '+str(d['volume']) if d.get('volume') else '')+(' · pages '+str(d['page']) if d.get('page') else ''),'subjects':[],'rights':'Metadata supplied through Crossref; access and reuse terms of article content are determined by the publisher.','license':'','language':None,'collection':[],'nt':nt,'tokens':tt,'ct':namekeys(creators),'containerTitle':container,'volume':d.get('volume'),'issue':d.get('issue'),'pages':d.get('page'),'issn':d.get('ISSN',[])}
  corpus.append(record)
  for namekey in record['ct']:author_inv[namekey].append(idx)
  for t in tt:inv[t].append(idx)
 print('loaded article file',p.name,'total corpus',len(corpus),flush=True)
N=len(corpus);idf={t:math.log((N+1)/(len(post)+1))+1 for t,post in inv.items()}
books=[]
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
city_re=re.compile(r'\b(?:Paris|Londres|London|Berlin|Leipzig|Leipsic|Leida|Lugduni|Amstelodami|Venetiis|Venetia|Venezia|Padova|Patavii|Bologna|Bononiae|Roma|Romae|Napoli|Neapoli|Torino|Firenze|Geneve|Geneva|Ginevra|Milano|Milan|Basel|Basileae|Cambridge|Oxford|New York|Amsterdam|Halle|Heidelberg|Wien|Vienna|Breslau|Stuttgart|Jena|Gottingen|Göttingen|Brescia|Modena|Pavia|Florence|Edinburgh|Edimburgo)\b',re.I)
def variants(b):
 originals=[b.get('displayTitle') or b.get('title',''), corrections.get(b['id'],{}).get('title') or b.get('title','')]
 vals=[]
 for x in originals:
  x=x.replace('£','f');x=re.sub(r'(\w)[-=¬]\s+(\w)',r'\1\2',x)
  x=re.split(r'\b(?:Estr\.?|Estratto|Estralt|Extr|Extrait|Extracted|Auszug)\b',x,flags=re.I)[0]
  x=re.split(r'\b(?:cm\.?|pp\.?)\s*\d',x,flags=re.I)[0]
  cutoff=None
  for m in city_re.finditer(x):
   if m.start()>5:cutoff=m.start();break
  if cutoff is not None:x=x[:cutoff]
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
records={};stats=collections.Counter();start=time.time()
for bi,b in enumerate(books):
 qvars=variants(b);title,nt,qt=qvars[0];names=b.get('authorNames',[])[:]
 for aid in corrections.get(b['id'],{}).get('additionalAuthors',[]):
  if name_map.get(aid) and name_map[aid] not in names:names.append(name_map[aid])
 ct=namekeys(names);knownyear=b.get('year');kind='cross_reference' if b.get('crossReference') else 'continuation' if b.get('continuation') else 'journal_offprint' if re.search(r'\b(?:Estr\.?|Estratto|Extrait)\b',b.get('text',''),re.I) else 'record'
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
 ranked=[]
 for idx in shortlisted:
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
  author_score=0
  if ct and d['ct']:
   author_score=len(ct&d['ct'])/min(len(ct),len(d['ct']))
   if author_score==0:
    author_score=max((ratio(a,c)/100 for a in ct for c in d['ct'] if len(a)>4 and len(c)>4),default=0)
    author_score=author_score*.8 if author_score>.88 else 0
  delta=abs(knownyear-d['year']) if knownyear and d['year'] else None
  date_score=1 if delta==0 else .9 if delta is not None and delta<=2 else .65 if delta is not None and delta<=10 else .35 if delta is not None and delta<=40 else .1 if delta is not None else .35
  score=.76*title_score+.16*author_score+.08*date_score
  if not ct:score=.88*title_score+.12*date_score
  if ninter==1 and author_score<.5:score=min(score,.52)
  # Generous candidate tier still requires title coherence, and known creator conflicts are explicit.
  if coverage<.25 or title_score<.47 or score<.46:continue
  if ninter<2 and not (qlen<=3 and author_score>=.8 and title_score>=.65):continue
  if ninter<3 and author_score<.5 and title_score<.84:continue
  if coverage<.38 and author_score<.5:continue
  if ct and d['ct'] and author_score==0 and title_score<.84:continue
  ranked.append((score,title_score,author_score,coverage,delta,idx,ninter,usedtitle))
 ranked.sort(reverse=True)
 cand=[];dedup=set()
 for score,ts,aus,coverage,delta,idx,ninter,usedtitle in ranked:
  d=corpus[idx];key=(d['nt'],d['year'],tuple(d['creators']))
  if key in dedup:continue
  dedup.add(key)
  level='high' if score>=.87 and ts>=.87 and aus>=.5 and delta is not None and delta<=1 else 'medium' if score>=.70 and ts>=.70 and (aus>=.35 or not ct) else 'low'
  if kind!='record' and level=='high':level='medium'
  if d['referenceType']=='possible book review or bibliographic notice':level='low'
  relation='Same stated year; edition still unverified' if delta==0 else f'Different publication year: reference {d["year"]}, catalogue {knownyear}' if delta is not None else 'Edition comparison incomplete; one or both publication dates missing'
  matchtype='Possible work match; edition unverified' if level!='low' or (score>=.65 and aus>=.4) else 'Title-overlap lead; work identity uncertain'
  if 'uncertain' in matchtype:relation='Work identity uncertain. '+relation
  if d['referenceType']=='possible book review or bibliographic notice':relation='Possible book review or bibliographic notice, not the book edition itself. '+relation
  if level=='low':relation='Low-confidence candidate. '+relation
  basis=[f'Title similarity {round(ts*100)}%; weighted title-token coverage {round(coverage*100)}%',f'Creator-name overlap {round(aus*100)}%' if ct and d['ct'] else 'Creator identity could not be compared',f'Publication years differ by {delta} year(s)' if delta is not None else 'A publication year is missing','Automated bibliographic candidate; physical edition and ownership not verified']
  if kind!='record':basis.append('Family record is a cross-reference or continuation; connection requires review')
  sourceurl=d['url']
  rights=d['rights'] or d['license'] or 'Rights statement not supplied in retrieved metadata; consult the source record.'
  image={'url':'https://archive.org/services/img/'+d['id'],'label':'Reference scan thumbnail · page type unverified','sourceUrl':sourceurl,'rights':rights,'rightsUrl':d['license'] or None,'verification':'Source-supplied thumbnail URL; cover/title-page identity has not been checked','confidence':'low'}
  cand.append({'source':d['source'],'referenceType':d['referenceType'],'externalId':d['id'],'url':sourceurl,'title':d['title'],'creators':d['creators'],'candidateAuthorNames':[] if d['referenceType']=='possible book review or bibliographic notice' else [z for z in d['creators'] if not re.search(r'(?:Royal College|Wellcome|Library|Libraries|Biblioth[eè]que|Internet Archive|Smithsonian|Museum|University of|Universit[aà]t)',z,re.I)],'creatorRoleStatus':'Names supplied in creator metadata; personal roles have not been independently verified','year':d['year'],'publisher':d['publisher'],'language':d['language'],'editionRelation':relation,'matchType':matchtype,'yearDifference':delta,'confidence':{'level':level,'score':round(score,3),'basis':basis},'sourceDescription':d['description'],'descriptionType':'Catalogue note; may describe physical extent or digitization rather than contents','subjects':d['subjects'],'images':[image] if d['source']=='Internet Archive' else [],'manifestUrl':'https://iiif.archive.org/iiif/'+d['id']+'/manifest.json' if d['source']=='Internet Archive' else None,'containerTitle':d.get('containerTitle'),'volume':d.get('volume'),'issue':d.get('issue'),'pages':d.get('pages'),'issn':d.get('issn',[]),'collection':d['collection'],'matchedUsingTitle':usedtitle,'retrievedAt':'2026-10-17'})
  if len(cand)>=2:break
 if cand:
  stats['withCandidates']+=1;stats[cand[0]['confidence']['level']]+=1
  if cand[0]['yearDifference']==0:stats['sameYear']+=1
  if not names:stats['previouslyNoNames']+=1
  status='candidate_found'
 else:stats['noCandidate']+=1;status='no_candidate_above_threshold' if eligible else 'insufficient_searchable_title'
 records[b['id']]={'status':status,'recordKind':kind,'searchedTitle':title,'titleVariants':[x[0] for x in qvars],'candidates':cand,'containerCandidates':[],'searchAssessment':{'localCorpusScreened':True,'individualExternalSearch':False,'method':'OCR-aware title variants plus creator/year matching against cached Internet Archive and bounded Crossref journal metadata','confidence':'low' if not cand else cand[0]['confidence']['level'],'outcome':status,'survivingCopies':'Not inferred from digital references'}}
 if bi%1000==0:print('matched',bi,'candidates',stats['withCandidates'],'elapsed',round(time.time()-start),flush=True)
 if bi%5000==0 and bi:
  (ROOT/'candidates-checkpoint.json').write_text(json.dumps({'records':records,'stats':dict(stats),'corpusRecords':N,'internetArchiveRecords':sum(x['source']=='Internet Archive' for x in corpus),'crossrefRecords':sum(x['source']=='Crossref' for x in corpus),'localRecordsScreened':len(books),'individualExternalRecordSearches':0},ensure_ascii=False))
result={'records':records,'stats':dict(stats)|{'catalogueRecords':len(books),'corpusRecords':N,'internetArchiveRecords':sum(x['source']=='Internet Archive' for x in corpus),'crossrefRecords':sum(x['source']=='Crossref' for x in corpus),'localRecordsScreened':len(books),'individualExternalRecordSearches':0},'retrievedAt':'2026-10-17','methodology':{'approach':'All catalogue records screened locally against public Internet Archive and a bounded Crossref journal-article metadata corpus. OCR f/£ repair, line-break repair, shortened imprint-free title variants, phonetic token normalization and near-spelling retrieval precede fuzzy title, creator and publication-year scoring. Two distinct best metadata candidates retained. This is candidate generation, not a verified catalogue crosswalk.','confidence':'Heuristic tiers, not calibrated probabilities. High requires close title, creator overlap and same/adjacent year; medium supports a plausible work connection; low can be an OCR, translation, edition or false-match lead.','imagePolicy':'Source thumbnails are reference-copy images. Page type and edition match unverified unless separately researched. No image inferred to depict the family copy.','copyCountPolicy':'External record, digitization and search-result counts are never converted into surviving physical copies.','scope':'All family catalogue records were screened locally, not individually searched on the web. Internet Archive corpus source selection is recorded in the earlier broad-research/book-cache/ia-corpus-log.json. The added bounded Crossref journal corpus and its requests are recorded in full-catalogue-pass/cache/crossref-retrieval-log.json. Unmatched records may be absent from these corpora, have unreadable OCR, or need other sources; this is not an exhaustive search of world catalogues.'}}
(ROOT/os.environ.get('BOOK_OUTPUT','book-candidates.json')).write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')))
(ROOT/'book-research-stats.json').write_text(json.dumps(result['stats'],indent=2))
print('FINAL',result['stats'],flush=True)
