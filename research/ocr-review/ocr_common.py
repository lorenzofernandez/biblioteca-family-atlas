import re,unicodedata,difflib,sys
from legacy_parser import names_from
CYR=str.maketrans({'а':'a','е':'e','о':'o','р':'p','с':'c','х':'x','у':'y','А':'A','В':'B','Е':'E','К':'K','М':'M','Н':'H','О':'O','Р':'P','С':'C','Т':'T','Х':'X','І':'I','і':'i'})
def clean_text(text):
 lines=[]
 for raw in text.splitlines():
  # OCR script confusables in otherwise Latin-script catalogue text.
  raw=re.sub(r'^[сc][тm]([. ,\d])',r'cm\1',raw)
  if len(re.findall('[A-Za-zÀ-ÿ]',raw))>len(re.findall('[\u0400-\u04ff]',raw))*3:raw=raw.translate(CYR)
  if raw.strip() in ['-','•','·','_']:continue
  lines.append(raw.strip())
 return '\n'.join(lines)
def norm(x):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',x).encode('ascii','ignore').decode().lower())
def similarity(a,b):return difflib.SequenceMatcher(None,norm(a),norm(b),autojunk=False).ratio()
SHELF=re.compile(r'^(?:[Il1VX]{1,4}[. ,:]+[ABC0-9]|[Il1VX]{1,4}\s*$|Misc\b|[ABC][.]?\s*Misc|[ABC][.]\d|\(?[Il1VX]+\.[ABC])',re.I)
BIB=re.compile(r'^(?:(?:Estr|Estx|Eatr|Extr)[., ]|Estratto\b|Extrait\b|Auszug\b|[cs]m[., ]|pp?[., ]|Leg[., ]|Tavv?[., ]|s\.[lnIt][., ]|s\.d\.|In\s+vol\b|Sul front|Vedi\b|See\b|Voir\b)',re.I)
CITY=re.compile(r'^(?:Paris|Parigi|London|Londres|Londra|Berlin|Leipzig|Leipsic|Leida|Lugduni(?: Batavorum)?|Amstelodami|Venetiis|Venetia|Venezia|Padova|Patavii|Bologna|Bononiae|Romae?|Napoli|Neapoli|Torino|Firenze|Geneve|Genève|Geneva|Ginevra|Milano|Milan|Basel|Basileae|Cambridge|Oxford|New York|Amsterdam|Halle|Heidelberg|Wien|Vienna|Breslau|Stuttgart|Jena|Gottingen|Göttingen|Brescia|Modena|Pavia|Florence|Edinburgh|Edimburgo|Marburg|München|Zurich|Zürich|Braunschweig|Stockholm|Upsala|Uppsala|Naples|Bruxelles|Pisa|Verona|Genova|Livorno|Vercelli|Bergamo|København|Kobenhavn|Kopenhagen|Copenhagen)\s*[,;:]',re.I)
YRX=re.compile(r'(?<![\d/])(1[4-9]\d{2}|20[0-2]\d)(?![\d/])')
def parse(text,old):
 lines=clean_text(text).splitlines()
 # Rejoin an author surname split across typed lines, before parsing the heading.
 for i in range(min(8,len(lines)-1)-1,-1,-1):
  if re.search(r'[A-ZÀ-Ý]{2,}[=]$',lines[i]) and re.match(r'^[A-ZÀ-Ý]{2,},',lines[i+1]):
   lines[i]=lines[i][:-1]+lines[i+1];del lines[i+1]
 start=next((i for i,l in enumerate(lines[:10]) if len(re.findall('[A-Za-zÀ-ÿ]',l))>=3 and not SHELF.search(l.lstrip('. :;'))),0)
 names,ns=names_from(lines)
 # Explicit author heading, or a close rereading of the already linked heading.
 isname=bool(names) or bool(old.get('authors') and similarity(lines[start] if lines else '',old.get('heading',''))>.72)
 if lines and re.fullmatch(r"[A-ZÀ-Ý][A-ZÀ-Ý'’ -]+\s+(?:et|and|und|e|&)\s+[A-ZÀ-Ý][A-ZÀ-Ý'’ -]+[.]?",lines[start]):isname=True
 if names:start=ns
 if start>=len(lines):return {'heading':'','names':[],'title':'','year':None,'yearEvidence':None}
 heading=lines[start].strip(' .;')
 titlelines=[];bibstart=None
 for i in range(start+1 if isname else start,len(lines)):
  l=lines[i]
  if BIB.match(l) or CITY.match(l) or (l.startswith(('\"',"'",'“','«')) and re.search(r'Journal|Revie|Philo|Acad|Ann|Phys|Chim|Chem|Sci|Zeitsch|Rend|Soc',l,re.I)):
   bibstart=i;break
  titlelines.append(l)
 # If no bibliographic delimiter was found, avoid an unbounded replacement title.
 title=' '.join(titlelines).strip(' .;')
 title=re.sub(r'(?<=\w)[=¬]\s+(?=\w)','',title)
 title=re.sub(r'(?<=\w)-\s+(?=[a-zà-ÿ])','',title)
 title=re.sub(r'\s+',' ',title)
 years=[];evidence=[]
 if bibstart is not None:
  # Publication/citation area only; ignore page counts, shelfmarks, dimensions and binding.
  for l in lines[bibstart:]:
   if re.match(r'^(?:cm[., ]|pp?[., ]|Leg[., ]|Tavv?[., ])',l,re.I):break
   if SHELF.search(l.lstrip('. :;')) or re.search(r'\baltra copia\b',l,re.I):continue
   if re.match(r'^(?:Vedi|See|Voir)\b',l,re.I):break
   ys=YRX.findall(re.split(r'\bpp?\.',l,flags=re.I)[0])
   if ys:years.extend(map(int,ys));evidence.append(l)
 single=sorted(set(years))
 return {'heading':heading,'names':names if isname else [],'title':title if bibstart is not None else '', 'year':single[0] if len(single)==1 else None,'yearCandidates':single,'yearEvidence':' / '.join(evidence),'bibliographicStart':bibstart,'isName':isname}
def needs_second(r,old):
 p=parse(r['text'],old)
 reasons=[]
 if norm(p['heading'])!=norm(old.get('heading','')):reasons.append('heading-change')
 if p['year'] is not None and p['year']!=old.get('year'):reasons.append('publication-year-change')
 if r['confidence']<.96:reasons.append('recognition-uncertainty')
 if len(norm(r['text']))<.78*len(norm(old.get('text',''))):reasons.append('possible-text-loss')
 if similarity(r['text'],old.get('text',''))<.65:reasons.append('large-text-change')
 return reasons
