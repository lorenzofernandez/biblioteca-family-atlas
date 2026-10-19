"""Prepare original card images and a compact dataset for the separate scroll story."""
from pathlib import Path
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import json,gzip,subprocess,shutil
from PIL import Image,ImageOps

root=Path(__file__).resolve().parents[1]
dist=root/'dist';out=dist/'cards-assets';out.mkdir(exist_ok=True)
tmp=root.parent/'card-story'/'renders';tmp.mkdir(parents=True,exist_ok=True)
images_dir=tmp/'cards';images_dir.mkdir(exist_ok=True)
cat=json.loads((dist/'catalogue.json').read_text())
books=json.loads(gzip.decompress((dist/'books-data.json.gz').read_bytes()))['books']
by_id={b['id']:b for b in books}
rarity=json.loads((dist/'rarity-data.json').read_text())
# Reuse the visitor-facing rarity rule; keep tentative scarcity separate from unknown.
script="global.window={};require('./dist/rarity.js');const fs=require('fs'),d=JSON.parse(fs.readFileSync('dist/rarity-data.json'));process.stdout.write(JSON.stringify(d.records.filter(r=>window.LibraryRarity.classify(r,d.defaultThreshold,true,'sources').key==='possible').map(r=>r.id)))"
rare=set(json.loads(subprocess.check_output(['node','-e',script],cwd=root)))
rare_records={r['id']:r for r in rarity['records'] if r['id'] in rare}
records=[];seen=set();groups=defaultdict(list)
for c in cat['cards']:
    id=c['workId'];b=by_id[id];seen.add(id)
    record={'id':id,'title':b['title'],'author':' · '.join(b['authorNames']),'year':b.get('year'),'file':c['file'],'page':c['page'],'samplePage':c['samplePage'],'rare':id in rare}
    records.append(record);groups[c['file']].append(record)
shards={}
extra=[]
represented_eras={r['year']//100*100 for r in records if r.get('year') is not None}
missing_era_ids={min((b for b in books if b.get('year') is not None and b['year']//100*100==era),key=lambda b:b['year'])['id'] for era in {b['year']//100*100 for b in books if b.get('year') is not None}-represented_eras}
for id in sorted((rare|missing_era_ids)-seen):
    prefix=id[1:3]
    if prefix not in shards:shards[prefix]=json.loads(gzip.decompress((dist/'book-records'/f'{prefix}.json.gz').read_bytes()))
    r=shards[prefix][id];b=by_id[id]
    record={'id':id,'title':b['title'],'author':' · '.join(b['authorNames']),'year':b.get('year'),'file':r['file'],'page':r['page'],'rare':id in rare}
    records.append(record);extra.append(record)
for r in records:
    if r['rare']:
        evidence=rare_records[r['id']];q=evidence.get('qualitative') or {}
        r['rarityNote']=q.get('reason') or evidence.get('note') or 'Tentative scarcity evidence; a worldwide total is not established.'
        r['sources']=q.get('sources') or evidence.get('sources') or []

def render_sample(item):
    filename,rows=item
    if all((images_dir/f"{r['id']}.jpg").exists() for r in rows):return
    prefix=tmp/Path(filename).stem
    subprocess.run(['pdftoppm','-jpeg','-jpegopt','quality=82','-scale-to','640',str(dist/'sources'/filename),str(prefix)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    images=sorted(tmp.glob(prefix.name+'-*.jpg'),key=lambda p:int(p.stem.rsplit('-',1)[1]))
    for r in rows:shutil.copy2(images[r['samplePage']-1],images_dir/f"{r['id']}.jpg")
def render_extra(r):
    path=images_dir/r['id']
    if path.with_suffix('.jpg').exists():return
    subprocess.run(['pdftoppm','-f',str(r['page']),'-l',str(r['page']),'-singlefile','-jpeg','-jpegopt','quality=82','-scale-to','640',str(dist/'originals'/r['file']),str(path)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(render_sample,groups.items()))
print('Sample cards rendered',flush=True)
with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(render_extra,extra))
first=records[0]
subprocess.run(['pdftoppm','-f','1','-l','1','-singlefile','-jpeg','-jpegopt','quality=90','-scale-to','1440',str(dist/'sources'/first['file']),str(out/'first-card')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
atlas=Image.new('RGB',(4096,4096),'#f6f3e9')
for i,r in enumerate(records):
    x=(i%36)*112;y=(i//36)*76
    img=Image.open(images_dir/f"{r['id']}.jpg").convert('RGB')
    tile=ImageOps.contain(img,(108,72),Image.Resampling.LANCZOS)
    atlas.paste(tile,(x+2+(108-tile.width)//2,y+2+(72-tile.height)//2))
    r['uv']=[(x+1)/4096,(y+1)/4096,110/4096,74/4096]
atlas.save(out/'atlas.jpg',quality=88,optimize=True)
centuries=Counter((b['year']//100)*100 for b in books if b.get('year') is not None)
data={'total':len(books),'dated':sum(centuries.values()),'undated':len(books)-sum(centuries.values()),'sampleCount':len(cat['cards']),'shown':len(records),'rare':len(rare),'undetermined':len(books)-len(rare),'centuries':dict(sorted(centuries.items())),'checked':rarity['checked'],'cards':records}
(out/'data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
print({'cards':len(records),'rare':len(rare),'dated':data['dated'],'atlas_bytes':(out/'atlas.jpg').stat().st_size},flush=True)
