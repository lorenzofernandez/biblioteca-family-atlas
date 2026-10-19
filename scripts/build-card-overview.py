"""Build one lightweight lookup for the overview's otherwise unpictured cards."""
from pathlib import Path
import gzip
import json

root = Path(__file__).resolve().parents[1] / 'dist'
scene = json.loads((root / 'cards-assets/data.json').read_text())
sampled = {c['id'] for c in scene['cards']}
books = json.loads(gzip.decompress((root / 'books-data.json.gz').read_bytes()))['books']
locations = {}
for path in sorted((root / 'book-records').glob('*.json.gz')):
    for record in json.loads(gzip.decompress(path.read_bytes())).values():
        locations[record['id']] = (record['file'], record['page'])
assert len({b['id'] for b in books}) == scene['total']
assert sampled <= {b['id'] for b in books}
files = sorted({file for file, page in locations.values()})
file_ids = {file: i for i, file in enumerate(files)}
date_corrections = {c['id']: c['year'] for c in scene.get('dateCorrections', [])}
rows = []
for book in sorted(books, key=lambda b: locations[b['id']]):
    if book['id'] in sampled:
        continue
    file, page = locations[book['id']]
    assert (root / 'originals' / file).is_file()
    rows.append([book['id'], book['title'], ' · '.join(book.get('authorNames', [])), date_corrections.get(book['id'], book.get('year')), file_ids[file], page])
assert len(rows) + len(sampled) == scene['total']
output = root / 'cards-assets/catalogue-index.json.gz'
output.write_bytes(gzip.compress(json.dumps({'files': files, 'cards': rows}, ensure_ascii=False, separators=(',', ':')).encode(), compresslevel=9, mtime=0))
print(f'{len(rows):,} additional cards; {output.stat().st_size:,} bytes')
