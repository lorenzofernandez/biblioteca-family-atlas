"""Resumable public-authority retrieval. Raw evidence stays outside the site archive.

Run from the source checkout; deliberately does not edit site data. Identity matching
uses exact labels/aliases only, with candidates kept for human/chronology review.
"""
import argparse, gzip, hashlib, json, re, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT.parent / 'biography-expansion' / 'cache'
CACHE.mkdir(parents=True, exist_ok=True)
PREFIX = '''PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
'''
def load(path):
    raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)
def save(path,value):
    raw=json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_bytes(gzip.compress(raw,mtime=0) if path.suffix=='.gz' else raw)
    tmp.replace(path)
def profiles():
    return {k:v for f in (ROOT/'dist/author-profiles').glob('*.gz') for k,v in load(f).items()}
def request(url,params):
    key=hashlib.sha256((url+json.dumps(params,sort_keys=True)).encode()).hexdigest()
    path=CACHE/(key+'.json.gz')
    if path.exists(): return load(path)
    data=urllib.parse.urlencode(params).encode()
    req=urllib.request.Request(url,data=data if 'qlever' in url else None,
        headers={'User-Agent':'BibliotecaResearch/1.0 (https://biblioteca-family-atlas.lfernandez85.chatgpt.site; historical catalogue research)',
                 'Accept':'application/json'})
    if 'qlever' not in url: req.full_url=url+'?'+data.decode()
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req,timeout=150) as r: obj=json.load(r)
            if obj.get('error') or obj.get('exception'): raise ValueError(str(obj)[:500])
            save(path,obj);time.sleep(1.1);return obj
        except Exception as e:
            if attempt==4: raise
            wait=int(getattr(e,'headers',{}).get('Retry-After',0) or 0)
            body=e.read().decode(errors='replace')[:500] if hasattr(e,'read') else ''
            print('retry',attempt,str(e)[:160], 'wait',wait,body,flush=True);time.sleep(max(wait,5*(2**attempt)))
def query(q):
    result=request('https://qlever.dev/api/wikidata',{'query':PREFIX+q})
    if 'results' not in result: raise ValueError(str(result)[:300])
    return [{k:v['value'] for k,v in r.items()} for r in result['results']['bindings']]
def qids_from_profiles(p):
    return sorted({q for a in p.values() for q in [a.get('wikidata')] if q and re.fullmatch(r'Q\d+',q)})
def facts(ids):
    out=load(CACHE/'facts.json.gz') if (CACHE/'facts.json.gz').exists() else {}
    todo=[q for q in ids if q not in out]
    props=' '.join('wdt:'+p for p in ['P31','P569','P570','P19','P20','P106','P27','P69','P108','P800','P166','P101'])
    for start in range(0,len(todo),300):
        batch=todo[start:start+300];vs=' '.join('wd:'+x for x in batch)
        rows=query('SELECT ?s ?p ?v WHERE { VALUES ?s { '+vs+' } VALUES ?p { '+props+' rdfs:label schema:description } ?s ?p ?v FILTER(!isLiteral(?v) || LANG(?v)="" || LANG(?v)="en") }')
        urls=query('SELECT ?s ?v WHERE { VALUES ?s { '+vs+' } ?v schema:about ?s; schema:isPartOf <https://en.wikipedia.org/> }')
        for qid in batch:out[qid]={'id':qid,'facts':{}}
        for r in rows:
            qid=r['s'].rsplit('/',1)[-1];prop=r['p'].rsplit('/',1)[-1].rsplit('#',1)[-1]
            out[qid]['facts'].setdefault(prop,[]).append({'value':r['v'],'label':None})
        for r in urls:out[r['s'].rsplit('/',1)[-1]]['facts'].setdefault('url',[]).append({'value':r['v'],'label':None})
        save(CACHE/'facts.json.gz',out)
        print('facts',min(start+len(batch),len(todo)),'/',len(todo),'total',len(out),flush=True)
    labels=load(CACHE/'labels.json.gz') if (CACHE/'labels.json.gz').exists() else {}
    needed=sorted({v['value'].rsplit('/',1)[-1] for d in out.values() for prop,vs in d['facts'].items() if prop.startswith('P') and prop!='P31' for v in vs if 'entity/' in v['value']} - set(labels))
    for start in range(0,len(needed),500):
        batch=needed[start:start+500]
        rows=query('SELECT ?s ?v WHERE { VALUES ?s {'+' '.join('wd:'+x for x in batch)+'} ?s rdfs:label ?v FILTER(LANG(?v)="en") }')
        for qid in batch:labels[qid]=None
        for r in rows:labels[r['s'].rsplit('/',1)[-1]]=r['v']
        save(CACHE/'labels.json.gz',labels)
        print('labels',min(start+len(batch),len(needed)),'/',len(needed),flush=True)
    for d in out.values():
        for vs in d['facts'].values():
            for v in vs:
                if 'entity/' in v['value']:v['label']=labels.get(v['value'].rsplit('/',1)[-1])
    save(CACHE/'facts.json.gz',out)
    return out
def names(p):
    # Initial-only strings and one-word headings cannot establish a person's identity.
    names={}
    for a in p.values():
        if a.get('wikidata') or a.get('bioSourceKind')=='research-summary': continue
        name=a.get('displayName') or a['name']
        words=re.findall(r'[^\W\d_]+',name,re.UNICODE)
        if len(words)<2 or len(words[0])<3: continue
        variants={name, name.replace('.', '').replace('  ',' ').strip()}
        for n in variants: names.setdefault(n,[]).append(a['id'])
    result=load(CACHE/'name-matches.json.gz') if (CACHE/'name-matches.json.gz').exists() else {}
    todo=[n for n in sorted(names) if n not in result]
    for start in range(0,len(todo),50):
        batch=todo[start:start+50]
        values=' '.join(json.dumps(n,ensure_ascii=False)+'@'+lang for n in batch for lang in ['en','it','fr','de','es','pt','la'])
        rows=query('SELECT DISTINCT ?term ?s WHERE { { VALUES ?term { '+values+' } ?s rdfs:label ?term } UNION { VALUES ?term { '+values+' } ?s skos:altLabel ?term } }')
        for n in batch: result[n]=[]
        for r in rows:
            result[r['term']].append({**r,'id':r['s'].rsplit('/',1)[-1]})
        save(CACHE/'name-matches.json.gz',result)
        print('names',min(start+len(batch),len(todo)),'/',len(todo),'matched',sum(bool(x) for x in result.values()),flush=True)
    save(CACHE/'name-author-map.json.gz',names)
    return result
def wiki(f):
    out=load(CACHE/'wikipedia.json.gz') if (CACHE/'wikipedia.json.gz').exists() else {}
    mapping={}
    for qid,d in f.items():
        urls=d['facts'].get('url',[])
        if urls:
            title=urllib.parse.unquote(urls[0]['value'].split('/wiki/',1)[-1]).replace('_',' ')
            if qid not in out: mapping[title]=qid
    titles=sorted(mapping)
    for start in range(0,len(titles),20):
        batch=titles[start:start+20]
        r=request('https://en.wikipedia.org/w/api.php',{'action':'query','format':'json','formatversion':2,
           'prop':'extracts|pageprops|info','inprop':'url','exintro':1,'explaintext':1,'exlimit':20,
           'titles':'|'.join(batch),'redirects':1,'maxlag':5})
        pages=r.get('query',{}).get('pages',[])
        for page in pages:
            qid=page.get('pageprops',{}).get('wikibase_item')
            if qid in set(mapping[t] for t in batch) and 'disambiguation' not in page.get('pageprops',{}):
                out[qid]={k:page.get(k) for k in ['title','extract','fullurl','pageid','lastrevid']}
                out[qid]['qid']=qid
        # A failed/ambiguous page remains empty and will not be used as a biography.
        for t in batch: out.setdefault(mapping[t],{'qid':mapping[t],'extract':None})
        save(CACHE/'wikipedia.json.gz',out)
        print('wikipedia',min(start+len(batch),len(titles)),'/',len(titles),'with text',sum(bool(x.get('extract')) for x in out.values()),flush=True)
    return out
if __name__=='__main__':
    arg=argparse.ArgumentParser();arg.add_argument('mode',choices=['facts','names','wiki','all']);args=arg.parse_args()
    p=profiles()
    if args.mode=='all':
        matches=names(p)
        ids=sorted(set(qids_from_profiles(p))|{x['id'] for rows in matches.values() for x in rows})
        f=facts(ids);wiki(f)
    elif args.mode=='names': names(p)
    elif args.mode=='facts': facts(qids_from_profiles(p))
    elif args.mode=='wiki': wiki(load(CACHE/'facts.json.gz'))
