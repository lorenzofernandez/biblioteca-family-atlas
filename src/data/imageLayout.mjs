/** Preserve the full image inside a frame without stretching or cropping. */
export function containImage(sourceWidth,sourceHeight,x,y,width,height){
 const scale=Math.min(width/sourceWidth,height/sourceHeight);
 const w=sourceWidth*scale,h=sourceHeight*scale;
 return{x:x+(width-w)/2,y:y+(height-h)/2,width:w,height:h};
}
/** A portrait grid uses the same geometry for drawing and pointer hit testing. */
export function portraitGrid(count,width,height){
 const availableWidth=Math.max(1,width-48),availableHeight=Math.max(1,height-180),ratio=1.5;
 const cols=Math.max(1,Math.ceil(Math.sqrt(count*availableWidth*ratio/availableHeight))),rows=Math.max(1,Math.ceil(count/cols));
 const cell=Math.min(availableWidth/cols,availableHeight/(rows*ratio)),rowHeight=cell*ratio;
 return{cols,cell,rowHeight,left:(width-cols*cell)/2,top:100+(availableHeight-rows*rowHeight)/2};
}
