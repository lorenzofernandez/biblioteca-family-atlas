import glob,gzip,json,re,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parent
R={}
for f in glob.glob(str(ROOT.parent/'library-site/dist/book-records/*.json.gz')):R.update(json.load(gzip.open(f,'rt')))
C=json.loads((ROOT/'signal-candidates.json').read_text())
DATE='2026-10-17'
byloc={(r['file'],r['page']):r for r in R.values()}
# Catalogue OCR does not reliably mark continuation cards. Explicit card headings
# and the manually inspected Torricelli continuation are handled separately.
extra_cont={};last=None
for r in sorted((r for r in R.values() if 'MMS' in r['file']),key=lambda r:r['page']):
 if re.match(r'\s*(?:seconda|terza|quarta)\s+sche',r['text'],re.I):extra_cont[r['id']]=last
 else:last=r['id']
tor_parent=byloc[('00_002_T00000001.pdf',13)]['id']
extra_cont['wb258bf990e81']=tor_parent
reject_incomplete=set('wcae49c695db0 w6122ee9def67 wd08cc20f2c5f w5a83c550354f w610060392490 w0ea5f8b42100 wc8d230582f90 w3a966d0d9e1b wf804e622c703'.split())
reproduction_reject=set('w1c40c1bad5f9 w922df4f0f92a wbfa25c387cb8 w6e4ea1756d0b'.split())
full_manuscripts=set('w5fdaca69b93e wb2538876a26b w998b24b97477 wddb0b6149d9f'.split())
components=set('w34e849930ac1 w94b95c87f90a we2a74044ae04 w73c198d806da wc336e1d74fbb w26e95932487b w10c6a20b65b2 w1ee3a5ec2e68 w779a293af969 w5a2896c0878b wc6444f598b05 w6d3d45f747dd w9a5cd7acecf0 w8a74aac234c5'.split())
offprint_reject=set('wc90b07ce0e7c wb03c2d1aef31 wdae937f449d1 w2720fa531e2a wc7a60420ff43 w3c9e2d39b7c1 wd61c7cf27925 wb43d940c125e w98a0e3f04c08'.split())
offprint=re.compile(r'\b(?:estr|extr|estratt)\.(?=\s|[A-Za-z\"\'])|\b(?:estratt[oi]|offprints?|sonderdruck|separatum)\b',re.I)
continued=re.compile(r'(?im)^\s*(?:seconda|terza|quarta|II[-°]?|III[-°]?)\s+sche[dnh]a')
crossref=re.compile(r'(?im)^\s*V[eé][dcl][il1]\s*[:;.]')
normalize=lambda t:t.replace('£','f').replace('ﬁ','fi')
positive={}; index={};reviews=[]

def quote_at(t,start,end,limit=24):
 # Keep a short exact contiguous OCR excerpt, preferably the containing line.
 a=t.rfind('\n',0,start)+1;b=t.find('\n',end)
 if b<0:b=len(t)
 # Continue briefly when abbreviation and source title span lines.
 if b-a<35:b=min(len(t),b+110)
 s=t[a:b].strip();words=list(re.finditer(r'\S+',s))
 return s[:words[limit-1].end()] if len(words)>limit else s

def evidence(r,type,match,meaning,scope='catalogue record',confidence='medium',review='automated OCR pattern; context displayed',**kw):
 t=r['text'];q=quote_at(t,match.start(),match.end()) if hasattr(match,'start') else match
 return {'type':type,'confidence':confidence,'scope':scope,'ocrExcerpt':q,'meaning':meaning,'review':review,'source':{'title':'Family catalogue, '+r['file']+', scan '+str(r['page']),'url':'originals/'+r['file']+'#page='+str(r['page']),'file':r['file'],'page':r['page'],'recordId':r['id']},**kw}

for id,r in R.items():
 t=r.get('text','');n=normalize(t);ev=[]
 nonind=bool(r.get('crossReference') or r.get('continuation') or crossref.search(t) or continued.search(t) or id in extra_cont)
 if id in extra_cont:parent=extra_cont[id]
 else:parent=None
 # Explicit Italian extract notation is bibliographic format evidence. It does
 # not prove a separately printed offprint rather than a journal clipping.
 m=offprint.search(t)
 if m and 'MMS' not in r['file'] and not nonind and id not in offprint_reject:
  ev.append(evidence(r,'extract_or_offprint_notation',m,'The catalogue marks this as an extract/offprint. A separately printed issue and a journal clipping have not been distinguished.','physical format',rarityEffect='none'))
 if 'MMS' in r['file'] and not nonind:
  ev.append(evidence(r,'manuscript',t.split('\n')[0],'Listed in the manuscript catalogue with manuscript codicological description. The individual object is handwritten; other copies or printed versions of its text may exist.','catalogued handwritten object','medium','manuscript-section headings and continuations manually reviewed',rarityEffect='individual manuscript object; no worldwide text population estimate'))
 elif id in full_manuscripts:
  m=re.search(r'(?i)manoscritt[oaie]|scritto autografo',n)
  ev.append(evidence(r,'manuscript',m,'The catalogue explicitly describes a handwritten item or transcription. Authorship and the existence of other textual copies remain unverified.','catalogued handwritten object','medium','manual OCR context review',rarityEffect='individual manuscript object; no survivor estimate'))
 elif id in components:
  m=re.search(r'(?i)manoscritt[oaie]|autograf[oaie]|\bms[s]?\.',n)
  ev.append(evidence(r,'manuscript_component',m,'The catalogue records handwritten material, annotation or an inserted letter in this particular copy; this does not classify the printed edition as rare.','copy-specific material','medium','manual OCR context review',rarityEffect='copy-specific distinction only'))
 m=re.search(r'(?i)(?:I?Invio|dedica).{0,25}autogra[f£][oaie]',t)
 if m and not nonind:
  ev.append(evidence(r,'autograph_presentation',m,'The catalogue records an autograph presentation or dedication. This distinguishes the family copy but supplies no count of surviving copies of the edition.','family copy','medium','manual contextual review of autograph notes',rarityEffect='copy-specific distinction only'))
 m=re.search(r'(?i)dattiloscr[iIl]tt[oaie]',n)
 if m and not nonind:
  ev.append(evidence(r,'typescript',m,'The catalogue describes a typescript. This does not establish whether it is an original, carbon copy, or duplicated text, or how many were made.','physical format',rarityEffect='none without distribution evidence'))
 m=re.search(r'(?i)ciclost[iìl][lti][oaet]',n)
 if not m:m=re.search(r'(?i)ciclost',n)
 if m and not nonind:
  ev.append(evidence(r,'duplicated_copy',m,'The catalogue describes a mimeographed/duplicated copy. Production quantity and circulation are unknown.','physical format',rarityEffect='none without distribution evidence'))
 if id in C and 'reproduction' in C[id]['signals'] and id not in reproduction_reject and not nonind:
  m=re.search(r'(?i)fotocopi[ae]|fac[.\s-]?simil[eié]s?|ristamp[ae]|reprint(?:ed)?|anastatic[oaie]|riproduzione',n)
  if m:
   typ='photocopy' if 'fotocopi' in m.group().lower() else 'reprint_or_facsimile'
   ev.append(evidence(r,typ,m,'Reproduction or reprinted material is explicitly described. Any scarcity estimate must refer to this reproduced edition or copy, not automatically to the earlier original.','edition or component as quoted','medium','all reproduction-pattern candidates manually reviewed',rarityEffect='edition-scope safeguard'))
 # Additional OCR spellings missed by the initial exact pattern.
 if id in ['w6aff8edc0f21','wce51568136f3']:
  m=re.search(r'(?i)(?:[f£]ac.?simile|anastat)',t)
  ev.append(evidence(r,'reprint_or_facsimile',m,'The catalogue explicitly identifies a facsimile/anastatic edition; do not transfer the original edition’s rarity.','edition','medium','manual OCR and context review',rarityEffect='edition-scope safeguard'))
 m=re.search(r'(?i)(?:nouveau|deuxi[eè]me)\s+tirage|nuova\s+tiratura',n)
 if m and not nonind:
  ev.append(evidence(r,'later_impression',m,'The catalogue describes a new or subsequent impression. Its production total is not stated.','edition or impression','medium','manual review of printing candidates',rarityEffect='edition-scope safeguard'))
 if id in C and 'incomplete' in C[id]['signals'] and id not in reject_incomplete:
  s=C[id]['signals']['incomplete'][0];m=re.search(re.escape(s['match']),t,re.I)
  ev.append(evidence(r,'copy_incomplete',m,'The catalogue reports missing or incomplete material. This concerns the listed copy/set, not scarcity of the whole edition.','family copy or set','medium','all incomplete-pattern candidates manually reviewed',rarityEffect='completeness qualification'))
 if 'SCOMPLETI' in r['file'] and not nonind and not any(z['type']=='copy_incomplete' for z in ev):
  ev.append(evidence(r,'incomplete_collection_section',t.split('\n')[0],'Filed in the catalogue section for incomplete holdings. The precise missing portion is not stated on this card.','family copy or set','low','section provenance; individual omission not established',rarityEffect='completeness qualification'))
 if ev:
  positive[id]={'id':id,'file':r['file'],'page':r['page'],'catalogueTitle':r.get('title'),'nonIndependentRecord':nonind,'continuationOf':parent,'signals':ev,'worldwideSurvivingCopies':None}
 index[id]={'status':'non_independent_record' if nonind else 'catalogue_signals_found' if ev else 'no_explicit_signal_found','flags':list(dict.fromkeys(e['type'] for e in ev))}
 if parent:index[id]['continuationOf']=parent
 # All keyword positives in the high-risk classes receive a recorded disposition.
 for kind in ['scarcity','printing','manuscript','reproduction','incomplete']:
  if id in C and kind in C[id]['signals']:
   reviews.append({'id':id,'candidateType':kind,'disposition':'excluded_non_independent_record' if nonind else 'source_evidence_retained' if any(e['type'] in {'scarcity':[], 'printing':['later_impression'], 'manuscript':['manuscript','manuscript_component','autograph_presentation'], 'reproduction':['photocopy','reprint_or_facsimile'], 'incomplete':['copy_incomplete']}[kind] for e in ev) else 'rejected_context_not_evidence','note':'Rare terminology describes subject matter/title, not scarcity of this edition.' if kind=='scarcity' else 'Reviewed in full OCR context; dimensions, pagination, publisher Limited and title references are not print-run/manuscript evidence.'})

manual={
 'wceeacceca787':{'type':'limited_print_run','ocrExcerpt':'(Edizione di 120 esemplari £uori commercio)','verifiedTranscription':'Edizione di 120 esemplari fuori commercio','originalPrintRun':120,'conditionalSurvivorUpperBound':120,'confidence':'medium','scope':'1956 private/non-trade issue of Rolandi, Il piombo','meaning':'The family catalogue states120 copies for this issue. If exhaustive and accurate,120 is a ceiling for surviving originals; it is not an estimate of how many survive.','assumptions':['The statement describes the entire issue, not a numbered subset.','Later editions, reproductions and any unrecorded impressions are excluded.']},
 'w6aff8edc0f21':{'type':'limited_print_run','ocrExcerpt':'Edizione di 500 esemplari, Esemplare n.353.','verifiedTranscription':'Edizione di 500 esemplari, Esemplare n.353.','originalPrintRun':500,'numberedCopy':353,'conditionalSurvivorUpperBound':500,'confidence':'medium','scope':'Galvani notebook facsimile, not the original handwritten notebook','meaning':'The scan confirms a500-copy edition and copy353. This limits the facsimile issue conditionally, not the manuscript or all Galvani editions.','assumptions':['The500-copy statement describes the whole facsimile issue.','The catalogue’s printed1837date conflicts with the bicentenary context;1937is independently supported.'],'dateConflict':{'catalogueDate':1837,'proposedDate':1937,'sourceUrl':'https://www.bibliotecasalaborsa.it/bolognaonline/lang/en/cronologia-di-bologna/1937','reason':'Bologna Library records the1937Galvani bicentenary and presentation of the notebook facsimile. The catalogue date error is present in the scan, not only OCR.'}},
 'wc090b7af60a9':{'type':'limited_print_run_conflict','ocrExcerpt':'(Edlzione dl 300 esemplari numerati\n328)','verifiedTranscription':'Edizione di 300 esemplari numerati - n°328','reportedPrintRun':300,'numberedCopy':328,'conditionalSurvivorUpperBound':None,'confidence':'low','scope':'Boffito, Gli strumenti della scienza, Firenze:Seeber,1929','meaning':'The scan confirms the contradictory300-copy limitation and copy328. Retain as a numbered/limited-edition lead, but no numeric bound is safe until the book’s limitation leaf is checked.','assumptions':['At least one catalogue number may be wrong, or numbering may cover a broader issue.']},
 tor_parent:{'type':'special_issue_print_run','ocrExcerpt':'Se ne\nsono tirate due sole copie in carta turchina\ndi Parma','verifiedTranscription':'Se ne sono tirate due sole copie in carta turchina di Parma','specialIssuePrintRun':2,'conditionalSurvivorUpperBound':None,'confidence':'low','scope':'Special Parma blue-paper issues of the two bound works; not the entire regular edition','meaning':'The continuation quotes a two-copy special-paper limitation from the colophons. It does not explicitly confirm that the family copy is on this paper. Do not apply a two-copy ceiling to the family entry until its paper is checked.','assumptions':['The bound works are Torricelli’s Lezioni accademiche,1823,and Scinà’s Introduzione,1817.','The family copy’s paper remains unverified.'],'evidenceRecordId':'wb258bf990e81'}
}
for id,v in manual.items():
 r=R[id];sr=R[v.get('evidenceRecordId',id)]
 ev=evidence(sr,v.pop('type'),v.pop('ocrExcerpt'),v.pop('meaning'),v.pop('scope'),v.pop('confidence'),'original scanned card visually checked',rarityEffect='tentative source-backed limited-issue signal',**v)
 positive.setdefault(id,{'id':id,'file':r['file'],'page':r['page'],'catalogueTitle':r.get('title'),'nonIndependentRecord':False,'continuationOf':None,'signals':[],'worldwideSurvivingCopies':None})['signals'].append(ev)
 index[id]={'status':'catalogue_signals_found','flags':list(dict.fromkeys(e['type'] for e in positive[id]['signals']))}
 # Update printing review disposition after manual scan validation.
 for rr in reviews:
  if rr['id']==sr['id'] and rr['candidateType']=='printing':rr.update(disposition='manually_verified_print_run_note',note='Original scanned card visually inspected. Scope/conflicts are retained in the evidence; continuation is attached to the preceding entry.')

counts=collections.Counter(e['type'] for r in positive.values() if not r['nonIndependentRecord'] for e in r['signals'])
stats={'checkedAt':DATE,'recordsScreened':len(R),'screenedTextField':'original catalogue OCR only','positiveRecords':len(positive),'independentPositiveRecords':sum(not r['nonIndependentRecord'] for r in positive.values()),'nonIndependentRecords':sum(r['status']=='non_independent_record' for r in index.values()),'noExplicitSignalFound':sum(r['status']=='no_explicit_signal_found' for r in index.values()),'signalCounts':dict(counts),'manuallyReviewedCandidateCounts':{k:sum(r['candidateType']==k for r in reviews) for k in ['scarcity','printing','manuscript','reproduction','incomplete']},'directEditionScarcityAssertionsFound':0,'visuallyCheckedNumericalNotes':4,'usableConditionalPrintRunCeilings':2,'worldwideSurvivalEstimatesCreated':0,'caution':'These are catalogue-derived evidence flags, not49,780external edition investigations. No signal found does not mean common; offprint, typescript, age and small known-holdings counts do not by themselves establish rarity.'}
(ROOT/'catalogue-signals.json').write_text(json.dumps({'methodVersion':'1.0','stats':stats,'records':positive},ensure_ascii=False,separators=(',',':')))
(ROOT/'catalogue-assessment-index.json').write_text(json.dumps(index,ensure_ascii=False,separators=(',',':')))
(ROOT/'catalogue-signals-stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2))
(ROOT/'manual-review-decisions.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2))
print(json.dumps(stats,ensure_ascii=False,indent=2));print('Torricelli parent',tor_parent)
