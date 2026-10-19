"""Create a small, reproducible portrait-scene index from the merged author data."""
import gzip
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / 'dist'
directory = json.loads((root / 'authors-data.json').read_text())
# An identified profile avoids presenting OCR fragments as people. Missing portraits
# remain represented by initials; a candidate portrait does not confirm an identity.
eligible = [a for a in directory['authors'] if a.get('bio') or a.get('portrait')]
selected = sorted(eligible, key=lambda a: (-a['recordCount'], a['id']))[:48]
shards = {}
rows = []
for author in selected:
    prefix = author['id'][1:3]
    if prefix not in shards:
        shards[prefix] = json.loads(gzip.decompress((root / 'author-records' / (prefix + '.json.gz')).read_bytes()))
    record_ids = sorted({r['id'] for r in shards[prefix][author['id']]})
    assert len(record_ids) == author['recordCount'], author['id']
    rows.append(dict(id=author['id'], name=author['displayName'], count=len(record_ids),
                     portrait=author.get('portrait'), imageKind=author.get('imageKind'),
                     confidence=author.get('confidence', {}).get('overall', 'unresolved'), records=record_ids))
output = dict(authors=rows, countBasis='Distinct catalogue records linked to each merged author entry, including cross-references.',
              selection='The 48 most-mentioned authors with identified profiles.', eligibleAuthors=len(eligible))
(root / 'cards-assets' / 'authors.json').write_text(json.dumps(output, ensure_ascii=False, separators=(',', ':')))
print(f'{len(rows)} authors; {sum(bool(a["portrait"]) for a in rows)} reference portraits; counts verified against linked catalogue records.')
