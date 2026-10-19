import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {createSquareLayouts} from '../dist/cards-square-layouts.mjs';

const scene=JSON.parse(readFileSync(new URL('../dist/cards-assets/data.json',import.meta.url)));
const index=JSON.parse(gunzipSync(readFileSync(new URL('../dist/cards-assets/catalogue-index.json.gz',import.meta.url))));
const records=[...scene.cards,...index.cards.map(row=>({id:row[0],year:row[3],file:index.files[row[4]],page:row[5],rare:false}))];
const geography=JSON.parse(gunzipSync(readFileSync(new URL('../dist/cards-assets/geography.json.gz',import.meta.url))));
const eras=Object.keys(scene.centuries).map(Number);
assert.equal(records.length,scene.total);
assert.equal(new Set(records.map(record=>record.id)).size,scene.total);
for(const [width,height] of [[1280,720],[390,844],[1920,1080]]){
 const columns=Math.ceil(Math.sqrt(scene.total*width/height)),rows=Math.ceil(scene.total/columns);
 const grid={columns,rows,cell:Math.min(width*.97/columns,height*.95/rows)};
 const wallIds=Int32Array.from({length:scene.total},(_,id)=>scene.total-id-1);
 const result=createSquareLayouts({width,height,records,wallIds,grid,eras,geography});
 assert.deepEqual([...result.byEra.values()].map(ids=>ids.length),[...Object.values(scene.centuries),scene.undated]);
 assert.deepEqual([result.rare.length,result.unknown.length],[scene.rare,scene.undetermined]);
 assert.equal(new Set([...result.byEra.values()].flat()).size,scene.total);
 assert.equal(new Set([...result.geography.groups.values()].flat()).size,scene.total);
 assert.deepEqual(Object.fromEntries([...result.geography.groups].map(([code,ids])=>[code,ids.length])),geography.counts);
 for(const [code,ids] of result.geography.groups)for(const id of ids)assert.equal(geography.records[records[id].id]?.[0]||'UNKNOWN',code);
 const blocks=result.geography.blocks;
 for(let i=0;i<blocks.length;i++)for(let j=i+1;j<blocks.length;j++){
  const a=blocks[i],b=blocks[j];
  assert.ok(a.x+a.width<=b.x||b.x+b.width<=a.x||a.y+a.height<=b.y||b.y+b.height<=a.y,`Overlapping country piles ${a.code}/${b.code}`);
 }
 result.layouts.forEach((layout,stage)=>{
  const points=new Set();
  for(let id=0;id<scene.total;id++){
   const [x,y,size]=layout.subarray(id*3,id*3+3);
   assert.ok(Number.isFinite(x)&&Number.isFinite(y)&&size>0,`Invalid square ${stage}/${id}`);
   const viewHeight=stage===1?result.timeline.worldHeight:height;
   assert.ok(x-size/2>=0&&x+size/2<=width&&y-size/2>=0&&y+size/2<=viewHeight,`Outside layout ${stage}/${id}`);
   if(stage===1){
    assert.ok(y-size/2<=result.timeline.maxPan+height,`Unreachable timeline card ${id}`);
    assert.ok(Math.abs(x-width/2)-size/2>=result.timeline.spineGap,`Card overlaps timeline spine ${id}`);
   }
   points.add(`${x},${y}`);
  }
  assert.equal(points.size,scene.total,`Overlapping squares in stage ${stage}`);
 });
 for(const ids of result.byEra.values()){
  const left=ids.filter(id=>result.layouts[1][id*3]<width/2).length;
  assert.ok(Math.abs(left-(ids.length-left))<=1,'Timeline bars must balance on both sides');
 }
 assert.ok(result.timeline.maxPan>height,'Timeline should still unfold beyond one screen');
 const overview=result.layouts[0],last=scene.total-1;
 assert.equal(overview[last*3],Math.fround((width-columns*grid.cell)/2+grid.cell/2));
 assert.deepEqual(result.layouts[0],result.layouts[3]);
 console.log(`${width}×${height}: all ${scene.total.toLocaleString()} unique cards preserved in four layouts; timeline and geography counts match.`);
}
