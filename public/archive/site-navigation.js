'use strict';
/* Shared navigation and page organization. Keeps catalogue research scripts independent. */
(() => {
  const file=location.pathname.split('/').pop().replace(/\.html$/,'')||'index';
  const active=file==='catalogue'?'catalogue':['book','books'].includes(file)?'books':['author','authors'].includes(file)?'authors':'index';
  document.body.classList.add('library-page-'+file);
  const nav=document.querySelector('header nav');
  if(nav){
    nav.setAttribute('aria-label','Main navigation');
    nav.replaceChildren(...[['index','Home'],['books','The books'],['authors','The authors'],['catalogue','The catalogue']].map(([path,label])=>{
      const a=document.createElement('a');a.href=path+'.html';a.textContent=label;
      if(path===active)a.setAttribute('aria-current','page');return a;
    }));
  }
  const brand=document.querySelector('header .brand');if(brand)brand.href='index.html';
  const make=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
  function arrangeAuthors(){
    const hero=document.querySelector('.authors-hero');if(!hero)return false;
    hero.querySelector('h1').textContent='The authors';
    const heading=document.querySelector('#directory h2');if(heading)heading.textContent='The author catalogue';
    return true;
  }
  async function arrangeBooks(){
    const directory=document.querySelector('.book-directory'),tools=directory?.querySelector('.book-tools');
    if(!directory||!tools)return false;
    if(directory.querySelector('#bookOverview'))return true;
    directory.querySelector('h1').textContent='The books';
    const overview=make('section',undefined,'book-overview');overview.id='bookOverview';
    overview.append(make('div','THE COLLECTION AT A GLANCE','eyebrow'),make('h2','The books, in numbers.'));
    tools.before(overview);
    const heading=make('div',undefined,'catalogue-section-heading');heading.id='bookCatalogue';
    heading.append(make('div','BROWSE THE RECORDS','eyebrow'),make('h2','The book catalogue'));
    tools.before(heading);
    try{
      const data=await LibraryData.json('books-data.json'),books=data.books||[],dated=books.filter(b=>Number.isFinite(b.year));
      const metrics=make('div',undefined,'book-overview-metrics');
      [[books.length,'Catalogue records'],[dated.length,'With a detected year'],[books.filter(b=>b.researched).length,'With online research'],[books.filter(b=>b.image).length,'With reference images']].forEach(([n,label])=>{const d=make('div');d.append(make('b',n.toLocaleString()),make('span',label));metrics.append(d)});
      overview.append(metrics);
      const charts=make('div',undefined,'book-overview-charts');
      function chart(title,rows,note){const box=make('div');box.append(make('h3',title));const max=Math.max(1,...rows.map(r=>r[1]));rows.forEach(([label,count])=>{const row=make('div',undefined,'book-overview-row'),track=make('div',undefined,'book-overview-track'),bar=make('i');bar.style.width=(count/max*100)+'%';track.append(bar);row.append(make('span',label),track,make('b',count.toLocaleString()));box.append(row)});box.append(make('p',note,'caption'));return box;}
      const centuries=new Map(),sections=new Map();books.forEach(b=>{sections.set(b.section,(sections.get(b.section)||0)+1);if(Number.isFinite(b.year)){const y=Math.floor(b.year/100)*100;centuries.set(y,(centuries.get(y)||0)+1)}});
      if(window.LibraryBookTimeline)LibraryBookTimeline.mount(charts,books);
      charts.append(chart('Across the catalogue',[...sections].sort((a,b)=>b[1]-a[1]).map(([id,n])=>[data.sections[id]?.name||id,n]),'Records include books, papers, volumes, and cross-references. These totals are not a count of distinct physical books.'));
      overview.append(charts);
      if(window.LibraryRarity)await LibraryRarity.mount(overview);
    }catch(error){console.error(error);overview.append(make('p','The collection overview could not load. The catalogue remains available below.','caption'))}
    return true;
  }
  function waitForRoot(selector,fn){const root=document.querySelector(selector);if(!root)return;let busy=false;const observer=new MutationObserver(async()=>{if(busy)return;busy=true;if(await fn())observer.disconnect();else busy=false;});observer.observe(root,{childList:true,subtree:true});Promise.resolve(fn()).then(done=>{if(done)observer.disconnect()});}
  // Home stays an overview; selecting a chart may reveal its existing card drill-down.
  if(file==='index'){
    const selection=document.querySelector('#resultsInfo'),explore=document.querySelector('#explore');
    if(selection&&explore)new MutationObserver(()=>{explore.classList.add('has-selected-cards');explore.scrollIntoView({behavior:'smooth'});}).observe(selection,{childList:true,characterData:true,subtree:true});
  }
  if(file==='books'&&!new URLSearchParams(location.search).has('id'))waitForRoot('#bookApp',arrangeBooks);
  if(file==='authors'&&!new URLSearchParams(location.search).has('id'))waitForRoot('#authorApp',arrangeAuthors);
})();
