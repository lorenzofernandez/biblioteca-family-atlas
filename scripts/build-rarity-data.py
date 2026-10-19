"""Build a small, auditable rarity-chart dataset from the published records."""
import gzip
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / 'dist'
catalogue = json.loads((root / 'books-data.json').read_text()) if (root / 'books-data.json').exists() else json.loads(gzip.decompress((root / 'books-data.json.gz').read_bytes()))
books = {book['id']: book for book in catalogue['books']}
records = []
for path in sorted((root / 'book-records').glob('*.json.gz')):
    for record in json.loads(gzip.decompress(path.read_bytes())).values():
        evidence = record.get('survivalResearch') or {}
        qualitative = record.get('bibliographyAssessment')
        if not evidence and not qualitative:
            continue
        book = books[record['id']]
        records.append({
            'id': record['id'], 'title': book['title'], 'year': book.get('year'),
            'author': ' · '.join(book.get('authorNames', [])),
            'editionConfidence': evidence.get('editionMatchConfidence', 'unknown'),
            'evidenceConfidence': evidence.get('evidenceConfidence', 'unknown'),
            'minimum': evidence.get('documentedLowerBound'),
            'range': evidence.get('worldwideSurvivingRange'),
            'conditionalBounds': evidence.get('conditionalSurvivalBounds'),
            'census': any(source.get('type') == 'published edition census' for source in evidence.get('evidence', [])),
            'unit': evidence.get('countUnit'), 'note': evidence.get('note'),
            'editionRelationship': evidence.get('editionRelationship'),
            'sources': evidence.get('evidence', []),
            'qualitative': qualitative,
            'hasCountResearch': bool(evidence),
        })
records.sort(key=lambda item: (item['year'] or 9999, item['title']))
assert len({r['id'] for r in records}) == len(records)
assert all(r['id'] in books for r in records)
result = {
    'total': len(books), 'researched': len(records),
    'fullCatalogue': catalogue.get('fullCataloguePass'),
    'checked': catalogue.get('checked'), 'defaultThreshold': 100,
    'definition': 'For this exploratory chart, rare means fewer than the selected number of surviving copies worldwide. This is an adjustable copy-scarcity rule, not a market valuation or a universal definition of rarity.',
    'methodSource': {'title': 'RBMS: Your Old Books', 'url': 'https://rbms.info/yob/'},
    'records': records,
}
(root / 'rarity-data.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'total': result['total'], 'researched': len(records), 'withCopyCounts': sum(r['minimum'] is not None for r in records)}))
