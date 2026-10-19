import re,json,unicodedata,hashlib,collections
from pathlib import Path

def norm(x):
 return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',x).encode('ascii','ignore').decode().lower())
def clean(x):
 return re.sub(r'\s+',' ',x.strip(' .:;[]|•\"')).strip()
# Explicit name headings, requiring a comma after an uppercase family name.
name_rx=re.compile(r"(?=(?:^|\s+(?:et|and|und|en|e|y|&|u\.|ET|AND|UND)\s+|,\s*)([A-ZÀ-Ý][A-ZÀ-Ý'’\- ()]{1,42}),\s*([^,;]{1,65}))")
join_rx=re.compile(r'\s+(?:et|and|und|en|e|y|&|u\.)\s+(?=[A-ZÀ-Ý])')
nonperson={'MISCELLANEA','RACCOLTA','COLLEGIO','ACADEMIE','ACCADEMIA','SOCIETA','SOCIETE','UNIVERSITA','ISTITUTO','COMMISSION','NOUVEAU','MANUEL','TRATTATO','ENCYCLOPEDIE','DIZIONARIO','OBSERVATIONS','GIORNALE','ANNALES','JOURNAL','REVUE','PERIODICI','INDICI','INSTITUT','SOMMARIO','CONGRESSO','COLLOQUE'}
single_map={'ARISTOTELES':'Aristotle','ARISTOTELE':'Aristotle','EUCLIDES':'Euclid','EUCLIDE':'Euclid','PLATO':'Plato','PLATONE':'Plato','THEOPHRASTUS':'Theophrastus','AVERROE':'Averroes','ORIBASIUS':'Oribasius','PICO DELLA MIRANDOLA':'Giovanni Pico della Mirandola','THOMAS DE AQUINO (S)':'Thomas Aquinas','THOMAS DE AQUINO (S.)':'Thomas Aquinas','GALENUS':'Galen','HIPPOCRATES':'Hippocrates'}

def names_from(lines):
 # First content line, allowing an immediately following continuation of a coauthor line.
 if not lines:return [],0
 start=next((i for i,l in enumerate(lines[:6]) if len(re.findall('[A-Za-zÀ-ÿ]',l))>=4 and not re.search(r'Misc\b|^(?:[Il1VX]+[ .,:/BCA0-9-]|cm\b|pp\.|mss|Im/|seconda scheda|terza scheda|quarta scheda)',l,re.I)),None)
 if start is None:return [],0
 line=lines[start]; names=[]
 if start+1<len(lines) and re.match(r'^(?:et|and|und|e|y|&)\b',lines[start+1]):line+=' '+lines[start+1]
 if any(w in line.upper() for w in nonperson):return [],start
 for m in name_rx.finditer(line):
  sur=clean(m.group(1));given=clean(join_rx.split(m.group(2))[0]);given=re.sub(r'\s+(?:s\.?j\.?|S\.J\.|F\.R\.S\.).*','',given,flags=re.I)
  if len(sur)<2 or re.search(r'\d',sur+given):continue
  # A given name can be initials, but not a sentence or bibliographic title.
  if len(given.split())>6 or re.search(r'\b(?:Vedi|See|Estr|cm|Traité|sur|della|libri|Opera|Edited)\b',given,re.I):continue
  if not given or re.search(r'[a-zà-ÿ]',given) or re.fullmatch(r"[A-ZÀ-Ý.'’\- ]+",given):
   display=clean(given+' '+sur.title())
   names.append({'key':norm(sur)+':'+norm(given),'surname':sur.title(),'given':given,'name':display,'raw':sur+', '+given})
 if not names and re.fullmatch(r"[A-ZÀ-Ý][A-ZÀ-Ý'’\- ]{2,40},\s*",line):
  sur=clean(line.rstrip(','));names=[dict(key=norm(sur)+':',surname=sur.title(),given='',name=sur.title(),raw=line)]
 if not names:
  key=line.upper().strip(' .:;[]')
  if key in single_map:
   display=single_map[key];names=[dict(key=norm(display)+':',surname=display,given='',name=display,raw=line)]
 return names,start

def load_cards():
 cards={}
 for p in Path('work').glob('full-*.jsonl'):
  for line in p.read_text().splitlines():
   try:c=json.loads(line)
   except:continue
   cards[(c['file'],c['page'])]=c
 # Substitute higher-quality OCR where previously extracted.
 for line in Path('work/cards.jsonl').read_text().splitlines():
  c=json.loads(line);cards[(c['file'],c['page'])]=c
 return [cards[k] for k in sorted(cards)]

def build():
 cards=load_cards(); authors={}; works=[];unassigned=[];last={};edges=collections.Counter()
 for c in cards:
  lines=[clean(l) for l in c['text'].splitlines() if clean(l)]
  names,start=names_from(lines)
  continuation=False
  if not names and c['file'] in last and lines and re.search(r'^(?:\.\.\.|- ?\.\.\.|\.{2}|segue|continu|seconda scheda|terza scheda)',lines[start],re.I):
   names=last[c['file']];continuation=True
  if names:last[c['file']]=names
  text=' '.join(lines[start+1:])
  years=[]
  for l in lines[start+1:]:
   if re.search(r'\bMisc\.|^(?:cm\b|pp?\.|tav\.|leg\.)',l,re.I):continue
   years += [int(y) for y in re.findall(r'(?<![\d/])(1[4-9]\d{2}|19\d{2}|200\d|201[0-4])(?![\d/])',re.split(r'\bpp?\.',l,flags=re.I)[0])]
  cross=bool(re.match(r'^\s*(?:Vedi|See|Voir|Siehe|Cfr)\b',text,re.I))
  wid='w'+hashlib.sha1((c['file']+':'+str(c['page'])).encode()).hexdigest()[:12]
  w=dict(id=wid,file=c['file'],page=c['page'],section=c['file'].split('_')[1],text=c['text'],heading=lines[start] if lines else '',title=' '.join(lines[start+1:start+5])[:350],year=years[0] if years else None,crossReference=cross,continuation=continuation,authors=[n['key'] for n in names])
  works.append(w)
  if not names:unassigned.append(wid)
  for n in names:
   a=authors.setdefault(n['key'],dict(**n,works=[],aliases=[],years=[]))
   a['works'].append(wid)
   if n['raw'] not in a['aliases']:a['aliases'].append(n['raw'])
   if w['year']:a['years'].append(w['year'])
  if len(names)>1 and not cross:
   for i,n in enumerate(names):
    for n2 in names[i+1:]:edges[tuple(sorted([n['key'],n2['key']]))]+=1
 # Merge initials only when a unique longer given name shares every initial.
 bysurname=collections.defaultdict(list)
 for key,a in authors.items():bysurname[norm(a['surname'])].append(key)
 merges={}
 def initials(g):return ''.join(t[0].lower() for t in re.findall(r'[A-Za-zÀ-ÿ]+',g))
 for keys in bysurname.values():
  for key in keys:
   a=authors[key]; g=a['given'];tokens=re.findall(r'[A-Za-zÀ-ÿ]+',g)
   if tokens and not all(len(t)==1 for t in tokens):continue
   candidates=[k for k in keys if k!=key and len(authors[k]['given'])>len(g) and (not g or initials(authors[k]['given'])==initials(g)) and any(len(t)>1 for t in re.findall(r'[A-Za-zÀ-ÿ]+',authors[k]['given']))]
   if len(candidates)==1:merges[key]=candidates[0]
 for key,target in merges.items():
  a,b=authors[key],authors[target];b['works']+=a['works'];b['aliases']+=a['aliases'];b['years']+=a['years'];del authors[key]
 for w in works:w['authors']=list(dict.fromkeys(merges.get(k,k) for k in w['authors']))
 edges2=collections.Counter()
 for (a,b),n in edges.items():
  a,b=merges.get(a,a),merges.get(b,b)
  if a!=b:edges2[tuple(sorted([a,b]))]+=n
 # Recover surname-only headings when precisely one compatible author entry exists.
 surname_to_keys=collections.defaultdict(list)
 for key,a in authors.items():surname_to_keys[norm(a['surname'])].append(key)
 recovered=0
 for w in works:
  if w['authors']:continue
  heading=clean(w['heading'])
  if not re.fullmatch(r"[A-ZÀ-Ý][A-ZÀ-Ý'’\- ()]{2,45}",heading):continue
  matches=surname_to_keys.get(norm(heading),[])
  if len(matches)==1:
   key=matches[0];w['authors']=[key];authors[key]['works'].append(w['id']);recovered+=1
 unassigned=[w['id'] for w in works if not w['authors']]
 print('Recovered surname-only cards:',recovered)
 for key,a in authors.items():
  a['id']='a'+hashlib.sha1(key.encode()).hexdigest()[:12];a['works']=list(dict.fromkeys(a['works']));a['firstYear']=min(a['years']) if a['years'] else None;a['lastYear']=max(a['years']) if a['years'] else None
  del a['years']
 idmap={k:a['id'] for k,a in authors.items()}
 for w in works:w['authors']=[idmap[k] for k in w['authors']]
 edges=[dict(a=idmap[a],b=idmap[b],count=n,type='coauthor') for (a,b),n in edges2.items()]
 out=dict(authors=list(authors.values()),works=works,edges=edges,unassigned=unassigned,coverage=dict(scannedPages=49780,processedPages=len(cards),files=len(set(c['file'] for c in cards))))
 Path('work/author-index.json').write_text(json.dumps(out,ensure_ascii=False))
 print('processed',len(cards),'authors',len(authors),'attributed pages',len(cards)-len(unassigned),'coauthor links',len(edges))
 print('top authors',[(a['name'],len(a['works'])) for a in sorted(authors.values(),key=lambda a:-len(a['works']))[:25]])
if __name__=='__main__':build()
