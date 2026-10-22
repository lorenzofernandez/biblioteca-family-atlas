'use strict';
// Large profile datasets are stored as gzip files to fit the hosted archive.
window.LibraryData={async json(path){
 const response=await fetch(path+'.gz',{cache:'no-cache'});
 if(!response.ok)throw new Error('Profile data could not load: '+response.status);
 const bytes=new Uint8Array(await response.arrayBuffer());
 if(bytes[0]===31&&bytes[1]===139){
  if(typeof DecompressionStream==='undefined')throw new Error('This browser cannot open compressed profile data. Please use a current browser.');
  return await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).json();
 }
 // Some hosts apply HTTP content decoding before handing bytes to the browser.
 return JSON.parse(new TextDecoder().decode(bytes));
}};
