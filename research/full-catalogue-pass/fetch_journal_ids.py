import json,urllib.request,urllib.parse,time,pathlib
root=pathlib.Path('work/full-catalogue-pass/cache');queries=['Annalen der Physik','Zeitschrift für physikalische Chemie','Zeitschrift für anorganische und allgemeine Chemie','Zeitschrift für Elektrochemie','Zeitschrift für Physik','Physica','Nuovo Cimento','Journal de Physique et le Radium','Gazzetta Chimica Italiana','Philosophical Magazine','Physical Review','Journal of the American Chemical Society','Journal of Physical Chemistry','Proceedings of the Royal Society A','Comptes Rendus Chimie','Annales de Chimie','Journal für praktische Chemie','Electrochemical Society','Reviews of Modern Physics','Nature']
all={}
for q in queries:
 p=root/('journals-'+str(queries.index(q))+'.json')
 if p.exists():d=json.load(open(p))
 else:
  url='https://api.crossref.org/journals?'+urllib.parse.urlencode({'query':q,'rows':3})
  try:
   d=json.load(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FamilyLibraryCatalogueResearch/1.0'}),timeout=45));p.write_text(json.dumps(d))
  except Exception as e:print(q,e,flush=True);time.sleep(3);continue
  time.sleep(1.4)
 all[q]=d['message']['items'];print(q,[(x['title'],x.get('ISSN'),x.get('counts',{}).get('total-dois')) for x in all[q]],flush=True)
(root/'journal-candidates.json').write_text(json.dumps(all,ensure_ascii=False,indent=2))
