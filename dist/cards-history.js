/* Addressable views, with a session-local parent for closing nested panels. */
(() => {
 'use strict';
 window.LibraryCardHistory={create(onChange){
  const session=Math.random().toString(36).slice(2);
  const current=()=>{const p=new URL(location.href).searchParams;return {card:p.get('card'),author:p.get('author'),full:p.get('authorView')==='full'};};
  function href(changes,standalone=false){
   const url=new URL(location.href);
   if(standalone){url.search='';url.hash='';}
   for(const [key,value] of Object.entries(changes))value==null?url.searchParams.delete(key):url.searchParams.set(key,value);
   return url.pathname+url.search+url.hash;
  }
  function write(changes,{replace=false,kind=null,notify=true}={}){
   const next=href(changes);if(next===location.pathname+location.search+location.hash)return;
   const state=replace?history.state:{libraryCards:session,kind,parent:location.pathname+location.search+location.hash};
   history[replace?'replaceState':'pushState'](state,'',next);if(notify)onChange(current());
  }
  function close(kind){
   if(history.state?.libraryCards===session&&history.state.kind===kind){history.back();return;}
   write(kind==='author'?{author:null,authorView:null}:{card:null,author:null,authorView:null},{replace:true});
  }
  window.addEventListener('popstate',()=>onChange(current()));
  return {current,href,write,close};
 }};
})();
