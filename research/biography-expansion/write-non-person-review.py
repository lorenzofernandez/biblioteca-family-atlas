import json,gzip
from pathlib import Path
p=Path('dist');authors={a['id']:a for a in json.loads((p/'authors-data.json').read_text())['authors']}
def records(i):return json.loads(gzip.decompress((p/'author-records'/f'{i[1:3]}.json.gz').read_bytes())).get(i,[])
def evidence(i,n=2):
 return [dict(recordId=r['id'],file=r['file'],page=r['page'],heading=r.get('heading'),title=r.get('title'),excerpt=r.get('text',''),sourceUrl=f"originals/{r['file']}#page={r['page']}") for r in records(i)[:n]]
def entry(i,kind,reason,recommendation):
 a=authors[i];return dict(authorId=i,name=a['name'],catalogueRecordCount=a.get('recordCount'),classification=kind,confidence='high',reason=reason,recommendation=recommendation,evidence=evidence(i))
nonpersons=[
 entry('ad4795137848d','subject-heading','TECHNOLOGIE heads a sequence of unrelated articles about industrial devices and processes, such as bottling wine and charcoal manufacture. It names a subject, not a person.','Do not generate a human biography. Classify as a catalogue subject heading; individual article authors remain unidentified where absent.'),
 entry('a5cce8a31d2a7','subject-heading','HYDRAULIQUE groups articles about pumps, drilling machines and canals. The heading is a subject classification.','Do not generate a human biography; retain a short subject-heading description and exclude from human-author coverage.'),
 entry('a7f7ff80a22e3','subject-heading','AGRICULTURE groups wheat planting, agricultural labour and farm-machinery articles. It is not a named person.','Do not generate a human biography; classify as a subject heading.'),
 entry('a31bacc4f26e3','subject-heading','CHIMIE is used as a subject/title heading for chemistry plates and extracts on tinplate and medicinal iron.','Do not generate a human biography; preserve the catalogue grouping without inventing authorship.'),
 entry('adc38509b79c2','subject-or-series-heading','MACHINES is the first word of the recurring title Machines ou inventions approuvées par l’Académie. Cards give different years of that recurring report.','Treat as a title/series grouping, not a human author.'),
 entry('a80b1f8c12bd7','ocr-shelfmark-artifact','The displayed name lÖl Iii.A is derived from shelfmark text. Its records have incompatible true headings including ABRIDGMENTS, ALMANACCO, BECKER H., BROGLIE Louis de, and COHN Emil, all carrying III.A shelfmarks.','Exclude from person biographies. Review and repair each book-author link separately; never assign one biography across this mixed group.'),
 entry('a2f8b7c05f3dc','corporate-author','The cards name the Académie royale des sciences, Paris, and its Histoire/Mémoires publications. This is a scientific institution.','Provide an institutional history if researched; exclude from human biography denominators and do not invent birth/death or a portrait.'),
 entry('a2c2bf966e706','corporate-author','Academia Caesareo-Leopoldina Naturae Curisorum is an OCR form of the academy named on the Ephemerides medico-physicarum cards.','Classify as a scientific academy/corporate author, retaining original spelling. Any institutional history requires its own authority match.'),
 entry('aea9a87c14e1c','corporate-author','The record is SOCIETA’ REALE DI NAPOLI, Atti dell’Accademia delle Scienze Fisiche e Matematiche; a society/publication rather than a person.','Use corporate-author treatment; fix encoding only with retained original name.'),
 entry('a680942baae8e','journal-or-publisher-mention','The sole card’s heading is VANNI, G.; Società di Naturalisti in Napoli occurs inside the cited Bollettino title. It is not the person who wrote the article.','Exclude from human biographies and flag the author relationship separately as a cited journal/society mention.'),
 entry('a466b093f2f36','ocr-volume-fragment','IV Ii has been extracted from Ragionamenti filosofici, Parte I, II, IV. Roman numerals identify volume/part numbers.','Do not generate a person biography; inspect this incomplete-title record separately.'),
 entry('aba7b99bd0f7b','ocr-shelfmark-artifact','Misc.lOÖ Ii.B is shelfmark material. The linked card begins DUFRENOX and concerns iron cementation.','Exclude from human biographies and review the book’s actual heading; do not assume Dufrenox’s identity without another check.'),
 entry('a576600087c22','title-fragment','Recherches Physiques Sur La Lumière is the beginning of the book title, continuing la pesanteur, les marées, le cours des astres. The fragment la pe= belongs to a wrapped title line.','Do not create a biography for the title. Authorship requires an independent bibliographic match.')
]
ambiguous=[
 {'authorId':'ae4a302c99119','name':'O Lehmann','reason':'Likely Otto Lehmann given liquid-crystal papers, but the initial alone is not sufficient evidence for a biography. Requires an authority match and distinctive-title verification.','recommendation':'Preserve catalogue-based context and unresolved identity status until researched. Do not expand initials from a name similarity alone.','evidence':evidence('ae4a302c99119')},
 {'authorId':'a4f0eda16c540','name':'E Mathias','reason':'Initial-only author, with geophysical and experimental-physics works. A plausible full-name match must be verified against the article titles; do not invent life dates from the initial.','recommendation':'Human candidate, not a subject heading; retain uncertainty pending source review.','evidence':evidence('a4f0eda16c540')},
 {'authorId':'a6e1dfb17fd96','name':'LOIqGUEVILLE et Langlois','reason':'Name combines two people, while linked records mix LANGLOIS alone, LANGLOIS et JACQUOT and other headings. One personal biography cannot describe this composite reliably.','recommendation':'Hold for contributor-role/name splitting and individual authority research.','evidence':evidence('a6e1dfb17fd96',3)},
 {'authorId':'a392017c6cffb','name':'MM Fine','reason':'M.M. Fine appears as an initialled Bureau of Mines contributor on technical reports. This is likely a person, but the full given names and life dates have not been established by these cards.','recommendation':'Do not classify as non-person merely because MM resembles an honorific; retain initialled name until external identification.','evidence':evidence('a392017c6cffb')}
]
cabart={
 'recordId':'w0704f7b9eaf6','file':'00_005_C00000001.pdf','page':1,'shelfmark':'II.B.Misc.389/3',
 'sourceUrl':'originals/00_005_C00000001.pdf#page=1',
 'originalScanVisuallyChecked':True,'renderedEvidence':'research/biography-expansion/cabart-original-card.png',
 'headingAsPrinted':'CABART','titleAsPrinted':'Description de la caisse du calorimètre de M. Dulong.',
 'citationAsPrinted':'Estr. da "Ann. de Chim. et de Phys.", III série, T. VIII (Juin 1843). cm. 20,5; pp. 183–189.',
 'currentLinkedAuthorId':'adbcca23f70fb','currentLinkedAuthorName':'J Dulong',
 'currentAttributionReason':'Surname-only heading matches one current catalogue entry; a homonym remains possible.',
 'currentAttributionEvidence':'Dulong',
 'finding':'The original card clearly prints CABART on the author-heading line. Dulong appears only after de M. in the title as the person whose calorimeter is described. The current automated attribution extracted the subject of the title and treated it as an author heading.',
 'certainty':'high that the present card does not support Dulong as author; CABART’s expanded identity and external article attribution remain unverified',
 'recommendedSeparateAction':'Review the book-author association in a distinct attribution pass. Preserve the raw heading CABART; remove or relabel Dulong as a related-person mention only after deciding the relationship schema. Do not use this card as evidence for Dulong’s authorship or silently attach a Cabart biography.'
}
out={'reviewedAt':'2026-10-19','method':'Targeted inspection of the largest unresolved names, expanded to obvious title/shelfmark/institution cases. Evidence is the preserved catalogue text; CABART page additionally rendered and visually checked. No dataset changes.','nonPersons':nonpersons,'ambiguous':ambiguous,'separateAttributionIssue':cabart}
f=Path('research/biography-expansion/non-person-review.json');f.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('wrote',len(nonpersons),'non-person entries;',len(ambiguous),'ambiguous cases; CABART evidence')
print('counts',sum(x['catalogueRecordCount'] or 0 for x in nonpersons))
