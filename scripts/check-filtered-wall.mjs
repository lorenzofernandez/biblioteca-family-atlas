import assert from 'node:assert/strict';
import {createFilteredWallLayout} from '../dist/cards-square-layouts.mjs';

for (const [width, height] of [[1440,1000],[390,844],[1920,720]]) {
  const base = new Float32Array(49780 * 3);
  let previousSize = Infinity;
  for (const count of [0,1,2,7,78,121,3778,49780]) {
    const ids = Array.from({length:count}, (_, i) => 49779-i);
    const layout = createFilteredWallLayout({width,height,ids,base});
    assert.equal(layout.length,base.length);
    assert.ok(base.every(value=>value===0),'Layout must not mutate the full wall');
    const rows = new Map();
    for (const id of ids) {
      const [x,y,size] = layout.subarray(id*3,id*3+3);
      assert.ok(Number.isFinite(size)&&size>0);
      assert.ok(x-size/2>=0&&x+size/2<=width&&y-size/2>=0&&y+size/2<=height,'Every match must fit on screen');
      if(!rows.has(y))rows.set(y,[]);
      rows.get(y).push({x,size});
    }
    let previousBottom=0;
    for(const [y,items] of rows){
      const size=items[0].size;
      assert.ok(y-size/2>=previousBottom,'Rows must not overlap');
      previousBottom=y+size/2;
      for(let i=1;i<items.length;i++)assert.ok(items[i].x-items[i-1].x>=size-.001,'Cards must not overlap');
      assert.ok(Math.abs((items[0].x+items.at(-1).x)/2-width/2)<.001,'Rows must be centred');
    }
    if(count){
      const size=layout[ids[0]*3+2];
      assert.ok(size<=previousSize+.001,'Fewer matches should grow, not shrink');
      previousSize=size;
      assert.ok(ids.length*size*size/(width*height)>.2,'Matches should use the viewport, even for one card');
    }
  }
  console.log(`${width}×${height}: zero through 49,780 matches fit, fill, and remain distinct.`);
}
