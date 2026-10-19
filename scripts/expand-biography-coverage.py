"""Apply a source-backed biography pass without changing catalogue transcriptions.

Full prose lives in compressed profiles. The directory carries short summaries.
Unresolved entries receive explicitly labelled catalogue evidence, never fake bios.
"""
import collections, copy, importlib.util, json, re, urllib.parse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'dist'; R=ROOT/'research/biography-expansion'; CACHE=ROOT.parent/'biography-expansion/cache'
spec=importlib.util.spec_from_file_location('helpers',ROOT/'scripts/merge-author-duplicates.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
read,save,shards,save_shards,unique=(getattr(h,n) for n in ['read','save','shards','save_shards','unique'])
DATE='2026-10-19'; BASELINE='8bf668ea7580ee255b9fde026521c9a775c01011'
PLACEHOLDER=re.compile(r'biography remains unresearched|biograph(?:y|ical details).*not yet|biography is not yet available',re.I)
def meaningful(a): return bool((a.get('bio')or'').strip()) and not PLACEHOLDER.search(a['bio']) and a.get('biographyStatus') not in ['catalogue-only','unresolved','non-person']
def short(text,n=220):
    text=' '.join((text or '').split())
    return text if len(text)<=n else text[:n].rsplit(' ',1)[0].rstrip('.,;:')+'…'
def english_list(items):
    items=list(dict.fromkeys(items))
    return items[0] if len(items)==1 else ', '.join(items[:-1])+' and '+items[-1]
def val(f,prop): return list(dict.fromkeys(v['value'] for v in f.get(prop,[])))
def labels(f,prop): return list(dict.fromkeys(v['label'] for v in f.get(prop,[]) if v.get('label')))
def year(f,prop):
    years={int(re.match(r'\+?(\d{4,})-',v).group(1)) for v in val(f,prop) if re.match(r'\+?(\d{4,})-',v)}
    return next(iter(years)) if len(years)==1 else None
def human(f): return 'http://www.wikidata.org/entity/Q5' in val(f,'P31')
def wiki_excerpt(text):
    if not text:return ''
    text=re.sub(r'\[\d+\]','',text)
    text=re.sub(r'\s+',' ',text).strip()
    # Keep complete source sentences; never generate missing life events.
    sentences=re.split(r'(?<=[.!?])\s+(?=[A-ZÀ-Ý“])',text)
    out=[]
    for s in sentences:
        if out and len(' '.join(out+[s]).split())>210:break
        out.append(s)
        if len(' '.join(out).split())>=160:break
    joined=' '.join(out)
    # Avoid a huge unpunctuated formula/list masquerading as prose.
    if len(joined.split())>260 or len(joined)<80:return ''
    return joined
def structured_bio(qid,f):
    name=(val(f,'label')or[''])[0];description=(val(f,'description')or[''])[0]
    if not name:return ''
    birth,death=year(f,'P569'),year(f,'P570')
    bp,dp=labels(f,'P19'),labels(f,'P20')
    occupations=[v for v in labels(f,'P106') if v not in ['human','person','natural person']]
    sentences=[]
    if description and description.lower() not in ['human','person','individual'] and not re.search(r'Wikimedia|disambiguation|family name|given name',description,re.I):
        sentences.append(name+' '+('was' if death else 'is')+' '+('an' if description[0].lower() in 'aeiou' else 'a')+' '+description.rstrip('.')+'.')
    elif occupations:sentences.append(name+' '+('worked' if death else 'works')+' as '+english_list(occupations[:3])+'.')
    if birth:sentences.append('Born in '+str(birth)+(' in '+bp[0] if len(bp)==1 else '')+'.')
    elif len(bp)==1:sentences.append('The authority record gives '+bp[0]+' as the birthplace.')
    if len(labels(f,'P101')):sentences.append('Fields of work included '+english_list(labels(f,'P101')[:3])+'.')
    schools=labels(f,'P69')[:3]
    if schools:sentences.append('The authority record lists studies at '+english_list(schools)+'.')
    employers=labels(f,'P108')[:3]
    if employers:sentences.append('Professional appointments are recorded at '+english_list(employers)+'.')
    works=labels(f,'P800')[:2]
    if works:sentences.append('Notable works listed in the authority record include '+english_list(works)+'.')
    awards=labels(f,'P166')[:2]
    if awards:sentences.append('Recorded honours include '+english_list(awards)+'.')
    if death:sentences.append('Died in '+str(death)+(' in '+dp[0] if len(dp)==1 else '')+'.')
    return ' '.join(sentences) if sentences else ''
def confidence(identity,kind):
    level=identity.get('level','low')
    level='medium' if level=='high' else level if level in ['medium','low','very-low'] else 'low'
    source='an attributed encyclopedia lead' if kind=='encyclopedia-excerpt' else 'structured public authority facts'
    return {'level':level,'reason':'Biography drawn from '+source+'. This automated expansion has not been individually source-reviewed. '+('The catalogue identity remains tentative; these details describe the candidate person.' if identity.get('level')!='high' else 'The identity has previously been reviewed; the new prose has not.')}
def enrich(target,qid,f,wiki,identity):
    if not human(f):return False
    excerpt=wiki_excerpt(wiki.get(qid,{}).get('extract'))
    biography=excerpt or structured_bio(qid,f)
    if not biography:return False
    if excerpt:
        page=wiki[qid];url=page['fullurl'];kind='encyclopedia-excerpt'
        sources=[{'title':page['title']+' — Wikipedia contributors','url':url},
                 {'title':'Revision history and contributors','url':'https://en.wikipedia.org/w/index.php?title='+urllib.parse.quote(page['title'])+'&action=history'},
                 {'title':'CC BY-SA 4.0 — shortened excerpt','url':'https://creativecommons.org/licenses/by-sa/4.0/'}]
        license='Wikipedia contributors · CC BY-SA 4.0 · shortened excerpt'
        target['biographySourceRevision']=page.get('lastrevid')
    else:
        url='https://www.wikidata.org/wiki/'+qid;kind='authority-facts'
        sources=[{'title':(val(f,'label')or[qid])[0]+' — Wikidata authority facts','url':url}]
        license='Wikidata · CC0'
    target.update(bio=biography,bioShort=short(biography),bioSources=sources,bioSource=url,bioSourceTitle=sources[0]['title'],
        bioSourceKind=kind,bioLicense=license,biographyStatus='source-summary' if excerpt else 'authority-facts',biographyExpandedAt=DATE)
    birth,death=year(f,'P569'),year(f,'P570')
    if birth is not None:target['birth']=birth
    if death is not None:target['death']=death
    if birth is not None and death is not None:target['lifeLabel']=f'{birth}–{death}'
    countries=labels(f,'P27')
    if countries:target['origins']=countries[:3]
    bc=confidence(identity,kind)
    if 'authorId' in target:
        target['biographyConfidence']=bc
    else:target.setdefault('confidence',{})['biography']=bc
    return True
def context(a,records):
    examples=[]
    for r in records:
        if r.get('title') and not r.get('crossReference') and not r.get('continuation'):
            t=short(r['title'],160)
            if t not in examples:examples.append(t)
        if len(examples)==2:break
    count=len(records)
    text='The catalogue links '+str(count)+' '+('record' if count==1 else 'records')+' to the heading “'+a['name']+'”.'
    dates=sorted({r['year'] for r in records if isinstance(r.get('year'),int) and 1400<=r['year']<=2026})
    if dates:text+=' Transcribed publication '+('dates range from '+str(dates[0])+' to '+str(dates[-1]) if len(dates)>1 else 'date: '+str(dates[0]))+'.'
    if examples:text+=' '+('A linked title is ' if len(examples)==1 else 'Linked titles include ')+english_list(['“'+x+'”' for x in examples])+'.'
    text+=' These cards do not yet establish a verified personal biography.'
    return text
def main():
    profiles=shards('author-profiles'); records=shards('author-records')
    bp=CACHE/'baseline-profiles.json.gz'
    if not bp.exists():save(bp,profiles)
    before=read(bp);assert set(before)==set(profiles)
    profiles=copy.deepcopy(before)
    facts=read(CACHE/'facts.json.gz');wiki=read(CACHE/'wikipedia.json.gz')
    matched=read(CACHE/'name-matches.json.gz');mapping=read(CACHE/'name-author-map.json.gz')
    directory=read(D/'authors-data.json'); index={a['id']:a for a in directory['authors']}
    nonpersons={e['authorId']:e for e in read(R/'non-person-review.json')['nonPersons']}
    manual=[e for path in sorted(R.glob('manual-*.json')) for e in read(path)['entries']]
    reviewed_ids={a for e in manual for a in e['authorIds']}
    proposed=collections.defaultdict(set)
    for name,rows in matched.items():
        for aid in mapping.get(name,[]):proposed[aid].update(r['id'] for r in rows)
    new_matches=[];held=[]
    for aid,ids in proposed.items():
        a=profiles[aid]
        if aid in nonpersons or aid in reviewed_ids or a.get('wikidata'):continue
        eligible=[]
        for qid in ids:
            f=facts.get(qid,{}).get('facts',{})
            birth,death=year(f,'P569'),year(f,'P570')
            first=a.get('firstYear');last=a.get('lastYear')
            # Exact full-name match + known, compatible chronology. Homonyms are held.
            if not human(f) or not birth or not isinstance(first,int) or first<birth+10 or first>birth+180:continue
            if death and isinstance(last,int) and last>death+150:continue
            eligible.append(qid)
        if len(eligible)!=1:
            held.append({'authorId':aid,'candidates':sorted(ids),'reason':'No unique human identity with compatible recorded dates.'});continue
        qid=eligible[0];f=facts[qid]['facts']
        identity={'level':'medium','reason':'Exact full-name label or historical alias in Wikidata, with compatible publication dates. This unique candidate is provisional: linked works have not been checked individually.'}
        name=(val(f,'label')or[a['name']])[0];birth,death=year(f,'P569'),year(f,'P570')
        a.update(wikidata=qid,possibleIdentity=name,birth=birth,death=death,
            lifeLabel=(str(birth)+'–'+(str(death) if death else '')),
            origins=labels(f,'P27')[:3])
        a['confidence'].update(identity=identity,overall='medium')
        candidate={'authorId':aid,'catalogueName':a['name'],'candidateId':qid,'candidateName':name,
            'wikidataId':qid,'authorityUrl':'https://www.wikidata.org/wiki/'+qid,'sourceUrl':'https://www.wikidata.org/wiki/'+qid,
            'confidence':identity,'matchMethod':'exact-full-name-alias-and-compatible-dates','retrievedAt':DATE,
            'birth':birth,'death':death,'lifeLabel':a['lifeLabel'],'origins':a['origins'],'imageUrl':None,'imageCreditUrl':None}
        a['identityCandidates']=[candidate];a['candidateId']=qid
        new_matches.append({'authorId':aid,'candidateId':qid,'name':name,'confidence':'medium'})
    chronology=[]
    for aid,a in profiles.items():
        if aid in reviewed_ids or a.get('bioSourceKind')=='research-summary':continue
        last=a.get('lastYear')
        if not isinstance(last,int) or not 1400<=last<=2026:continue
        def conflicts(qid,fallback=None):
            birth=year(facts.get(qid,{}).get('facts',{}),'P569') or fallback
            return isinstance(birth,int) and last<birth+8
        rejected=[candidate for candidate in a.get('identityCandidates',[]) if conflicts(candidate.get('wikidataId'),candidate.get('birth'))]
        selected_rejected=conflicts(a.get('wikidata'))
        if not rejected and not selected_rejected:continue
        survivors=[candidate for candidate in a.get('identityCandidates',[]) if candidate not in rejected]
        a['identityCandidates']=survivors
        reason='The latest transcribed publication date predates a plausible writing lifetime for the previous candidate. OCR dates can be wrong, so this is held for review rather than a confirmed replacement.'
        audit={'authorId':aid,'lastCatalogueYear':last,'previousSelectedId':a.get('wikidata'),
               'excludedCandidates':[{'id':x.get('wikidataId'),'name':x.get('candidateName'),'birth':x.get('birth')} for x in rejected],'reason':reason}
        if selected_rejected:
            a.update(bio=None,bioShort=None,bioSource=None,bioSources=None,bioSourceKind=None,
                possibleIdentity=None,wikidata=None,birth=None,death=None,lifeLabel=None,origins=[],portrait=None,portraitSource=None,candidateId=None)
            a['confidence'].update(overall='unresolved',identity={'level':'unresolved','reason':reason},image={'level':'unresolved','reason':'The reference image was attached to an incompatible candidate.'})
            a['biographyChronologyHold']=reason
            if len(survivors)==1:
                candidate=survivors[0];qid=candidate.get('wikidataId');f=facts.get(qid,{}).get('facts',{})
                if human(f) and year(f,'P569'):
                    identity={'level':'low','reason':'One previously proposed candidate remains after chronology screening. The catalogue titles still need individual source verification.'}
                    a.update(wikidata=qid,possibleIdentity=candidate.get('candidateName'),candidateId=qid,
                             birth=candidate.get('birth'),death=candidate.get('death'),lifeLabel=candidate.get('lifeLabel'),origins=candidate.get('origins')or[])
                    a['confidence'].update(overall='low',identity=identity);candidate['confidence']=identity
                    a.pop('biographyChronologyHold',None);audit['remainingProvisionalCandidate']=qid
        chronology.append(audit)
    expanded=[]
    for aid,a in profiles.items():
        identity=a.get('confidence',{}).get('identity',{'level':'low'})
        a['catalogueContext']=context(a,records.get(aid,[]))
        for candidate in a.get('identityCandidates',[]):
            if candidate.get('bioSourceKind')=='research-summary' and meaningful(candidate):
                candidate['biographyStatus']='reviewed'
                candidate['biographyConfidence']=a.get('confidence',{}).get('biography',{'level':'medium','reason':'Source-reviewed biography of this candidate.'})
                continue
            qid=candidate.get('wikidataId');f=facts.get(qid,{}).get('facts',{})
            if qid in facts and not human(f):
                candidate.update(bio=None,biographyStatus='unresolved',biographyConfidence={'level':'unresolved','reason':'This authority match does not establish a human biography.'})
                continue
            if not enrich(candidate,qid,f,wiki,candidate.get('confidence',{})) and not meaningful(candidate):
                candidate['bio']=None;candidate['biographyStatus']='unresolved'
                candidate['biographyConfidence']={'level':'unresolved','reason':'No sourced biography established for this candidate.'}
        if aid in nonpersons:
            a.update(bio=None,bioShort=None,biographyStatus='non-person',catalogueEntityType=nonpersons[aid]['classification'],
                catalogueContext=nonpersons[aid]['reason']+' '+a['catalogueContext'].replace('a verified personal biography.','an individual author.'))
            if nonpersons[aid].get('resetIdentity'):
                a.update(possibleIdentity=None,wikidata=None,candidateId=None,identityCandidates=[],birth=None,death=None,
                    lifeLabel=None,origins=[],portrait=None,portraitSource=None,bioSource=None,bioSources=None,bioSourceKind=None,bioLicense=None)
                a['confidence'].update(overall='unresolved',identity={'level':'unresolved','reason':'This catalogue subject heading was incorrectly matched to a person.'},
                    image={'level':'unresolved','reason':'No portrait applies to this catalogue subject heading.'})
            a['confidence']['biography']={'level':'unresolved','reason':'This is a catalogue heading, institution or transcription artifact, not an identified person.'}
            continue
        if a.get('bioSourceKind')=='research-summary' and meaningful(a):
            a['biographyStatus']='reviewed';continue
        qid=a.get('wikidata');f=facts.get(qid,{}).get('facts',{})
        if qid in facts and not human(f):
            a.update(bio=None,bioShort=None,biographyStatus='unresolved')
            a['confidence']['biography']={'level':'unresolved','reason':'The previous authority match does not establish a human biography. Further identity research is required.'}
            continue
        if qid and enrich(a,qid,f,wiki,identity):expanded.append(aid)
        elif meaningful(a):
            a['biographyStatus']='source-summary'
            a['confidence']['biography']=a.get('confidence',{}).get('biography') or {'level':'low','reason':'Existing source description; further individual review needed.'}
        else:
            a.update(bio=None,bioShort=None,biographyStatus='unresolved' if a.get('biographyChronologyHold') else 'catalogue-only')
            a['confidence']['biography']={'level':'unresolved','reason':a.get('biographyChronologyHold') or 'Catalogue records are available, but a sourced biography has not yet been established for this name.'}
    # Source-reviewed work wins over automated descriptions and incorrect namesakes.
    corrected=[]
    for e in manual:
        for aid in e['authorIds']:
            a=profiles[aid];prior=copy.deepcopy(a)
            reset=e.get('resetIdentity') or aid in e.get('resetAuthorIds',[])
            canonical=profiles.get(e.get('canonicalId'),{})
            qid=e.get('wikidata') or canonical.get('wikidata') or (None if reset else a.get('wikidata'))
            if reset:
                approved=next((c for c in before[aid].get('identityCandidates',[]) if qid and c.get('wikidataId')==qid),{})
                a.update(portrait=approved.get('imageUrl'),portraitSource=approved.get('imageCreditUrl'),wikidata=qid)
                if before[aid].get('wikidata') and before[aid].get('wikidata')!=qid:corrected.append(aid)
            if qid:a['wikidata']=qid
            a.update(displayName=e['name'],possibleIdentity=e['name'],birth=e['birth'],death=e['death'],
                lifeLabel=e['lifeLabel'],origins=e['origins'],bio=e['biography'],bioShort=e['short'],description=e['short'],
                bioSources=e['sources'],bioSource=e['sources'][0]['url'],bioSourceTitle=e['sources'][0]['title'],
                bioSourceKind='research-summary',bioLicense=None,biographyStatus='reviewed',biographyReviewedAt=DATE)
            a['aliases']=unique(a.get('aliases',[])+[before[aid]['name'],before[aid]['displayName']]+e.get('aliases',[]))
            identity={'level':e['identityLevel'],'reason':e['identityReason']}
            bc={'level':e['identityLevel'],'reason':'Source-reviewed biography with the catalogue identity checked against the linked titles and historical name variants.'}
            a['confidence'].update(overall=e['identityLevel'],identity=identity,biography=bc)
            if not a.get('portrait'):a['confidence']['image']={'level':'unresolved','reason':'No verified portrait has been added for this author.'}
            cid=qid or 'reviewed-'+aid;a['candidateId']=cid
            a['identityCandidates']=[dict(authorId=aid,catalogueName=a['name'],candidateId=cid,candidateName=e['name'],wikidataId=qid,
                sourceUrl=a['bioSource'],authorityUrl=a['bioSource'],bioSource=a['bioSource'],bioSourceTitle=a['bioSourceTitle'],
                bioSourceKind='research-summary',bio=a['bio'],bioShort=a['bioShort'],bioSources=a['bioSources'],bioLicense=None,
                biographyStatus='reviewed',biographyConfidence=bc,description=e['short'],birth=e['birth'],death=e['death'],
                lifeLabel=e['lifeLabel'],origins=e['origins'],imageUrl=a.get('portrait'),imageCreditUrl=a.get('portraitSource'),
                confidence=identity,matchMethod='manual-biographical-and-work-title-review',retrievedAt=DATE)]
    for aid,a in profiles.items():
        row=index[aid]
        for key in ['displayName','possibleIdentity','birth','death','lifeLabel','origins','portrait','imageKind','biographyStatus','biographyReviewedAt','biographyExpandedAt','catalogueEntityType']:
            if key in a:row[key]=a[key]
        row['bio']=a.get('bioShort') or short(a.get('bio')) or None
        row['confidence']={'overall':a['confidence'].get('overall','unresolved'),'biography':{'level':a['confidence']['biography']['level']}}
        row['candidateNames']=unique([c.get('candidateName') for c in a.get('identityCandidates',[]) if c.get('candidateName')]);row['candidateCount']=len(row['candidateNames'])
        # Directory context deliberately stays compact; full evidence is in profiles.
        row.pop('catalogueContext',None)
        for key in ['id','name','key','recordCount','referenceCount','firstYear','lastYear']:
            assert a.get(key)==before[aid].get(key),(aid,key)
        assert a['confidence']['biography']['level'] in ['high','medium','low','very-low','unresolved']
        if meaningful(a):assert a.get('bioSource') or a.get('bioSources'),aid
    statuses=collections.Counter(a['biographyStatus'] for a in profiles.values())
    count=sum(meaningful(a) for a in profiles.values());old_count=sum(meaningful(a) for a in before.values())
    report={'date':DATE,'baselineCommit':BASELINE,'entriesAudited':len(profiles),'entriesWithBiographyBefore':old_count,
        'entriesWithBiographyAfter':count,'coverageBefore':round(100*old_count/len(profiles),2),'coverageAfter':round(100*count/len(profiles),2),
        'nonPersonEntries':statuses['non-person'],'personEntryCoverageAfter':round(100*count/(len(profiles)-statuses['non-person']),2),
        'detailedBiographiesBefore':sum(meaningful(a) and len(a['bio'].split())>=80 for a in before.values()),
        'detailedBiographiesAfter':sum(meaningful(a) and len(a['bio'].split())>=80 for a in profiles.values()),
        'detailedBiographyDefinition':'A source-backed biography containing at least 80 words.',
        'statuses':dict(statuses),'newExactNameCandidates':len(new_matches),'expandedProfiles':len(expanded),
        'manuallyReviewedPeopleThisPass':len(manual),'manuallyReviewedEntriesThisPass':len(reviewed_ids),
        'correctedIdentityEntries':corrected,'chronologyScreenedEntries':len(chronology),'chronologyHolds':sum(bool(a.get('biographyChronologyHold')) for a in profiles.values()),'biographyConfidence':dict(collections.Counter(a['confidence']['biography']['level'] for a in profiles.values())),
        'methodology':'All entries audited. Placeholders and catalogue-only descriptions are excluded from biography coverage. Exact name/alias matches with compatible dates remain provisional; ambiguous matches are held. Encyclopedia excerpts retain contributor and CC BY-SA attribution. Structured facts use Wikidata CC0. Individual source-reviewed biographies take precedence. Author entries are not necessarily unique people.'}
    save_shards('author-profiles',profiles);save(D/'authors-data.json',directory)
    if (D/'authors-data.json.gz').exists():save(D/'authors-data.json.gz',directory)
    save(R/'coverage-report.json',report);save(R/'exact-name-candidates.json',new_matches);save(R/'held-name-candidates.json',held)
    save(R/'chronology-screening.json',chronology)
    queue=[{'id':a['id'],'name':a['name'],'records':a['recordCount'],'status':a['biographyStatus'],'candidate':a.get('possibleIdentity'),'reason':a['confidence']['biography']['reason']} for a in profiles.values() if not meaningful(a) and a['biographyStatus']!='non-person']
    save(R/'unresolved-research-queue.json.gz',sorted(queue,key=lambda a:-a['records']))
    research=read(D/'research-data.json');research.update(authorEntries=len(profiles),authorBiographies=count,authorBiographyCoverage=report)
    save(D/'research-data.json',research)
    if (D/'research-data.json.gz').exists():save(D/'research-data.json.gz',research)
    # Propagate only reviewed display-name corrections, preserving raw OCR and links.
    renamed={aid:profiles[aid]['displayName'] for aid in reviewed_ids if profiles[aid]['displayName']!=before[aid]['displayName']}
    books=shards('book-records');affected={}
    def rename_record(r):
        if any(a in renamed for a in r.get('authors',[])) and 'authorNames' in r:
            names=[renamed.get(a,r['authorNames'][i] if i<len(r['authorNames']) else profiles[a]['displayName']) for i,a in enumerate(r['authors'])]
            if names!=r['authorNames']:r.setdefault('catalogueAuthorNames',r['authorNames']);r['authorNames']=names
    for bid,b in books.items():
        rename_record(b)
        if any(a in renamed for a in b['authors']):affected[bid]=' · '.join(b['authorNames'])
    for rows in records.values():
        for r in rows:rename_record(r)
    save_shards('book-records',books);save_shards('author-records',records)
    book_index=read(D/'books-data.json.gz')
    for row in book_index['books']:rename_record(row)
    for row in book_index['authors']:
        if row['id'] in renamed:row['name']=renamed[row['id']]
    save(D/'books-data.json.gz',book_index)
    story=read(D/'cards-assets/data.json')
    for row in story['cards']:
        if row['id'] in affected:row['author']=affected[row['id']]
    save(D/'cards-assets/data.json',story)
    compact=read(D/'cards-assets/catalogue-index.json.gz')
    for row in compact['cards']:
        if row[0] in affected:row[2]=affected[row[0]]
    save(D/'cards-assets/catalogue-index.json.gz',compact)
    rarity=read(D/'rarity-data.json')
    for row in rarity['records']:
        if row['id'] in affected:row['author']=affected[row['id']]
    save(D/'rarity-data.json',rarity)
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
