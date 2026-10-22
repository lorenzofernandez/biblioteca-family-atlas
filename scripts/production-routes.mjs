import{writeFile}from'node:fs/promises';
const base=process.env.PAGES_BASE||'/';
const routes={cards:'',authors:'authors',author:'authors',books:'catalogue',book:'catalogue',catalogue:'catalogue',research:'catalogue'};
for(const[entry,section]of Object.entries(routes)){
 const script=`const p=new URLSearchParams(location.search),q=new URLSearchParams();let section=${JSON.stringify(section)};if(${JSON.stringify(entry)}==='cards'&&p.has('catalogue'))section='catalogue';const card=p.get('card')||(${JSON.stringify(entry)}==='book'?p.get('id'):null),author=p.get('author')||(${JSON.stringify(entry)}==='author'?p.get('id'):null);if(card)q.set('card',card);if(author)q.set('author',author);location.replace(${JSON.stringify(base)}+'#/'+section+(q.size?'?'+q:''));`;
 await writeFile('dist/'+entry+'.html',`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>La Biblioteca</title></head><body><a href="${base}#/${section}">Open La Biblioteca</a><script>${script}</script></body></html>`);
}
