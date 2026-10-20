// A virtual camera renders every matching item without mounting thousands of covers.
export function createBoard(grid){
 const host=document.createElement('div');host.className='library-space';host.setAttribute('aria-label','Zoomable collection board');
 const canvas=document.createElement('canvas'),layer=document.createElement('div');layer.className='library-space-items';host.append(canvas,layer);document.body.append(host);
 const ctx=canvas.getContext('2d');let restoreCamera=true;let data,items=[],cols=1,rows=1,cell=1,scale=1,x=0,y=0,W=0,H=0,left=24,top=80,areaW=0,areaH=0,list=null,drag=null,moved=false,raf=0;
 const rendered=new Map();
 function dimensions(){W=innerWidth;H=innerHeight;const ratio=devicePixelRatio||1;canvas.width=W*ratio;canvas.height=H*ratio;ctx.setTransform(ratio,0,0,ratio,0,0);areaW=Math.max(100,W-(W>=1000?420:48));areaH=Math.max(150,H-175);top=W>=1000?80:Math.min(H*.4,260);if(W<1000)areaH=H-top-90;}
 function fit(){dimensions();cols=Math.max(1,Math.ceil(Math.sqrt(items.length*areaW/(areaH*.72))));rows=Math.ceil(items.length/cols);cell=Math.min(areaW/cols,areaH/Math.max(1,rows)/1.4);scale=1;x=left;y=top;render();}
 function update(){const shouldRestore=restoreCamera;restoreCamera=false;data=window.LibraryBoardRecords;if(!data)return;items=data.items;rendered.clear();layer.replaceChildren();fit();if(shouldRestore){try{const saved=JSON.parse(sessionStorage.getItem('biblioteca-board-camera')||'null');if(saved&&saved.kind===data.kind&&saved.signature===[items.length,items[0]?.id,items[items.length-1]?.id].join(':')&&saved.W===W&&saved.H===H){scale=saved.scale;x=saved.x;y=saved.y;render();}}catch{}}}
 function render(){if(list)return;ctx.clearRect(0,0,W,H);const cw=cell*scale,ch=cw*1.4;const seen=new Set();
  for(let i=0;i<items.length;i++){const px=x+(i%cols)*cw,py=y+Math.floor(i/cols)*ch;if(px+cw<0||py+ch<0||px>W||py>H)continue;const w=cw*.82,h=ch*.86;ctx.fillStyle=data.kind==='books'?'#dfdccb':'#adb4a3';if(cw<65)ctx.fillRect(px,py,Math.max(.8,w),Math.max(.8,h));
   if(cw>=65){seen.add(i);let node=rendered.get(i);if(!node){node=data.render(items[i]);node.classList.add('library-space-item');node.style.pointerEvents='none';rendered.set(i,node);layer.append(node);}node.style.cssText+=';width:'+w+'px;height:'+h+'px;transform:translate3d('+px+'px,'+py+'px,0);';}
  }
  for(const [i,node] of rendered)if(!seen.has(i)){node.remove();rendered.delete(i);}
 }
 function zoom(factor,px=W/2,py=H/2){const next=Math.max(1,Math.min(3000,scale*factor)),ratio=next/scale;x=px-(px-x)*ratio;y=py-(py-y)*ratio;scale=next;render();}
 host.addEventListener('wheel',e=>{if(list)return;e.preventDefault();zoom(Math.exp(-Math.max(-300,Math.min(300,e.deltaY))*.003),e.clientX,e.clientY);},{passive:false});
 host.addEventListener('pointerdown',e=>{if(e.button!==0)return;drag={px:e.clientX,py:e.clientY,x,y};moved=false;host.setPointerCapture(e.pointerId);host.classList.add('dragging');});
 host.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag.px,dy=e.clientY-drag.py;if(Math.abs(dx)+Math.abs(dy)>5)moved=true;x=drag.x+dx;y=drag.y+dy;cancelAnimationFrame(raf);raf=requestAnimationFrame(render);});
 host.addEventListener('pointerup',e=>{if(!drag)return;drag=null;host.classList.remove('dragging');if(moved)return;const c=Math.floor((e.clientX-x)/(cell*scale)),r=Math.floor((e.clientY-y)/(cell*scale*1.4)),i=r*cols+c;if(c>=0&&c<cols&&r>=0&&i<items.length)location.href=data.url(items[i]);});
 function setList(value){if(list===value)return;list=value;document.body.classList.toggle('library-space-mode',!list);host.hidden=list;if(!list)fit();}
 window.addEventListener('pagehide',()=>{try{sessionStorage.setItem('biblioteca-board-camera',JSON.stringify({kind:data.kind,signature:[items.length,items[0]?.id,items[items.length-1]?.id].join(':'),scale,x,y,W,H}));}catch{}});document.addEventListener('library-board-update',update);window.addEventListener('resize',fit);setList(false);update();return{fit,zoom,setList};
}
