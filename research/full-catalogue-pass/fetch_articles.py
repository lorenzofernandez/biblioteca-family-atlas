import json,urllib.request,urllib.parse,time,pathlib,hashlib
root=pathlib.Path('work/full-catalogue-pass/cache/crossref');root.mkdir(exist_ok=True)
journals=[('0003-3804','Annalen der Physik'),('0942-9352','Zeitschrift für Physikalische Chemie'),('0044-2313','Zeitschrift für anorganische und allgemeine Chemie'),('0372-8323','Zeitschrift für Elektrochemie und angewandte physikalische Chemie'),('2367-1491','Zeitschrift für Elektrochemie'),('0372-8382','Zeitschrift für Elektrochemie Berichte der Bunsengesellschaft'),('0031-8914','Physica'),('0029-6341','Il Nuovo Cimento'),('0368-3842','Journal de Physique et le Radium'),('0031-899X','Physical Review'),('0002-7863','Journal of the American Chemical Society'),('0022-3654','Journal of Physical Chemistry'),('0941-1216','Journal für praktische Chemie'),('0013-4651','Journal of The Electrochemical Society'),('0034-6861','Reviews of Modern Physics'),('0028-0836','Nature')]
log={'source':'Crossref REST API','retrievedAt':'2026-10-17','requests':0,'itemsRetrieved':0,'journals':[],'scope':'Bounded historical article corpus. Up to 8000 metadata records per selected journal dated1600–1965, in API default order. Not individual searches for every family record.'}
for issn,name in journals:
 cursor='*';got=0;info={'issn':issn,'title':name,'pages':0,'records':0,'totalMatching':None,'complete':False}
 for page in range(8):
  p=root/f'{issn}-{page:02}.json'
  if p.exists():d=json.load(open(p))
  else:
   args={'filter':'until-pub-date:1965-12-31,from-pub-date:1600-01-01','rows':1000,'cursor':cursor,'select':'DOI,title,author,published,container-title,type,URL,volume,issue,page,publisher,ISSN'}
   url=f'https://api.crossref.org/journals/{issn}/works?'+urllib.parse.urlencode(args)
   for attempt in range(3):
    try:
     log['requests']+=1;response=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FamilyLibraryCatalogueResearch/1.0'}),timeout=60);d=json.load(response);p.write_text(json.dumps(d,ensure_ascii=False));break
    except Exception as e:print('error',issn,page,str(e),flush=True);time.sleep(2+attempt*3)
   else:info['error']='Request failed after bounded retries';break
   time.sleep(1.35)
  items=d.get('message',{}).get('items',[]);got+=len(items);info.update(pages=page+1,records=got,totalMatching=d.get('message',{}).get('total-results'));cursor=d.get('message',{}).get('next-cursor')
  log['itemsRetrieved']+=len(items)
  print('article page',issn,page,'items',len(items),'journal total',got,'all retrieved',log['itemsRetrieved'],flush=True)
  if len(items)<1000 or not cursor:info['complete']=True;break
  if log['itemsRetrieved']>=120000:break
 log['journals'].append(info);(root.parent/'crossref-retrieval-log.json').write_text(json.dumps(log,ensure_ascii=False,indent=2))
 if log['itemsRetrieved']>=120000:break
print('FINAL',log['itemsRetrieved'],'items',log['requests'],'requests',flush=True)
