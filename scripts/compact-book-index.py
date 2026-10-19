"""Compress the expanded public index, matching the existing profile-data loader."""
import json,gzip
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'dist'
p=root/'books-data.json'
if p.exists():
 raw=p.read_bytes();json.loads(raw);out=gzip.compress(raw,mtime=0);(root/'books-data.json.gz').write_bytes(out);p.unlink();print({'beforeBytes':len(raw),'afterBytes':len(out)})
