// Flat map projection and collision-free piles; every record keeps its own square.
export function createGeographyLayout({width, height, records, geography}) {
 const groups=new Map(Object.keys(geography.countries).map(code=>[code,[]]));
 records.forEach((record,id)=>groups.get(geography.records[record.id]?.[0]||'UNKNOWN').push(id));
 const positions=new Float32Array(records.length*3),mobile=width<751;
 const map={x:width*.035,y:height*(mobile?.34:.25),width:width*.93,height:Math.min(height*.49,width*.93*.43)};
 const project=([lon,lat])=>[map.x+(lon+180)/360*map.width,map.y+(85-lat)/145*map.height];
 const step=Math.min(width/1280,height/720)*1.75;
 const put=(id,x,y)=>positions.set([x,y,step*.68],id*3);
 const blocks=[],occupied=[];
 const gap=mobile?5:10,labelHeight=mobile?15:22;
 const bounds={left:width*.04,right:width*.94,top:height*(mobile?.26:.18),bottom:height*.77};
 const countryGroups=[...groups].filter(([code])=>geography.countries[code].anchor).sort((a,b)=>b[1].length-a[1].length);
 for(const [code,ids] of countryGroups){
  const country=geography.countries[code],anchor=project(country.anchor);
  const columns=Math.max(1,Math.ceil(Math.sqrt(ids.length*.9))),rows=Math.ceil(ids.length/columns);
  const w=columns*step,h=rows*step,labelled=ids.length>=100;
  const boxW=Math.max(w,labelled?(mobile?47:76):4),boxH=h+(labelled?labelHeight:0);
  let best=null;
  // Nearest non-overlapping position. Leader lines retain the geographic anchor.
  const increment=mobile?5:9;
  for(let y=bounds.top+boxH/2;y<=bounds.bottom-boxH/2;y+=increment){
   for(let x=bounds.left+boxW/2;x<=bounds.right-boxW/2;x+=increment){
    const rect={left:x-boxW/2-gap/2,right:x+boxW/2+gap/2,top:y-boxH/2-gap/2,bottom:y+boxH/2+gap/2};
    if(occupied.some(b=>rect.left<b.right&&rect.right>b.left&&rect.top<b.bottom&&rect.bottom>b.top))continue;
    const score=(x-anchor[0])**2+(y-(anchor[1]-h/2))**2;
    if(!best||score<best.score)best={x,y,rect,score};
   }
  }
  if(!best)throw Error('No room for country stack '+code);
  occupied.push(best.rect);
  const x=best.x-w/2,y=best.y-boxH/2;
  ids.forEach((id,rank)=>put(id,x+(rank%columns+.5)*step,y+(rows-1-Math.floor(rank/columns)+.5)*step));
  blocks.push({code,name:country.name,ids,x,y,width:w,height:h,anchor,labelled,labelX:best.x,labelY:y+h+4});
 }
 // Unlocated and joint imprints stay off the map, never assigned to an arbitrary country.
 for(const [code,x,availableWidth] of [['UNKNOWN',width*.05,width*.73],['MULTI',width*.83,width*.1]]){
  const ids=groups.get(code)||[],columns=Math.max(1,Math.floor(availableWidth/step)),rows=Math.ceil(ids.length/columns);
  const y=height*(mobile?.70:.94)-rows*step;
  ids.forEach((id,rank)=>put(id,x+(rank%columns+.5)*step,y+(Math.floor(rank/columns)+.5)*step));
  blocks.push({code,name:geography.countries[code]?.name||code,ids,x,y,width:columns*step,height:rows*step,labelled:true,labelX:x,labelY:y-23,tray:true});
 }
 return {positions,groups,blocks,map,project,step};
}
