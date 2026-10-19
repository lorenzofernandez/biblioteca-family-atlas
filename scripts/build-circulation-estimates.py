"""Build a separate, explicitly speculative estimate layer; preserve research facts."""
import collections
import gzip
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'dist'
MODEL = json.loads((ROOT / 'circulation-model.json').read_text())
COHORTS = {c['id']: c for c in MODEL['cohorts']}


def round_out(value, upper=False):
    if value <= 1:
        return 1
    unit = 10 ** math.floor(math.log10(value))
    return max(1, int((math.ceil if upper else math.floor)(value / unit) * unit))


def estimate(record):
    screening = record.get('catalogueScreening') or {}
    signals = {s.get('label') for s in screening.get('signals', [])}
    format_label = screening.get('formatLabel', '')
    research = record.get('research') or {}
    survival = record.get('survivalResearch') or {}
    review = record.get('editionReview') or {}
    if record.get('crossReference') or record.get('continuation') or format_label == 'Cross-reference / continuation':
        return None, 'Cross-reference or continuation'
    if format_label in {'Handwritten item', 'Typescript', 'Photocopy', 'Duplicated copy', 'Reprint / facsimile'}:
        return None, 'Nonstandard or separately reproduced item'
    if signals & {'Filed among incomplete holdings', 'Incomplete copy or set'}:
        return None, 'Incomplete copy or set scope needs review'
    if signals & {'Limited print run', 'Conflicting limitation numbers', 'Special-paper issue'}:
        return None, 'Specific printing limitation needs review'
    if review.get('decision') == 'different_edition':
        return None, 'Conflicting edition'
    if survival.get('worldwideEstimate') or survival.get('conditionalSurvivalBounds') or record.get('reportedCensus') or any(e.get('type') == 'published edition census' for e in survival.get('evidence', [])):
        return None, 'Specific census or printing evidence takes priority'
    source_range = survival.get('worldwideSurvivingRange') or {}
    if source_range.get('max') is not None:
        return None, 'Existing sourced range takes priority'
    text = record.get('text', '')
    if re.search(r'\b(?:1[5-9]|20)\d{2}\s*[-–]\s*(?:1[5-9]|20)\d{2}\b', text):
        return None, 'Multi-year publication scope needs review'
    offprint = format_label == 'Catalogue extract / offprint'
    year = record.get('year')
    if not offprint and (not isinstance(year, int) or not 1450 <= year <= 2026):
        return None, 'No usable date or separate-print clue'
    if not offprint and re.search(r'\b(?:volumi|volumes|voll\.|tomi)\s*\d|\b\d+\s*(?:volumi|volumes|voll\.|tomi)\b', text, re.I):
        return None, 'Multi-volume set scope needs review'
    cohort = COHORTS['offprint'] if offprint else next(c for c in MODEL['cohorts'] if c.get('from', 9999) <= year <= c.get('to', -1))
    run, fraction = cohort['printRun'], cohort['survivingFraction']
    low, high = round_out(run[0] * fraction[0]), round_out(run[1] * fraction[1], True)
    minimum = survival.get('documentedLowerBound')
    floor_applies = survival.get('editionMatchConfidence') in {'high', 'medium'} and isinstance(minimum, (int, float)) and minimum > 0
    # A minimum for a component, a different issue or incomplete sets cannot constrain a whole-volume model.
    scope = ' '.join(str(survival.get(k) or '') for k in ['note', 'editionRelationship', 'scope'])
    if floor_applies and re.search(r'component|different edition|not comparable|complete.set|separately paginated', scope, re.I):
        return None, 'Documented-copy scope needs individual modelling'
    if floor_applies and minimum > high:
        return None, 'Documented minimum exceeds scenario ceiling'
    if floor_applies:
        low = max(low, math.ceil(minimum))
    reviewed = review.get('decision') in {'verified_edition', 'probable_edition'}
    confidence = 'low' if reviewed else 'very-low'
    sources = [{'title': 'Family catalogue · scan ' + str(record['page']), 'url': record['source'] + '#page=' + str(record['page']), 'role': 'Catalogue date, wording and format clues; transcription not a physical-copy census.'}]
    for source in (review.get('sources') or research.get('summarySources') or [])[:2]:
        if source.get('url'):
            sources.append({'title': source.get('title', 'Bibliographic reference'), 'url': source['url'], 'role': 'Edition or work context, not a worldwide count.'})
    notes = []
    if not reviewed:
        notes.append('Edition/date unverified; this range is conditional on the catalogue description being correct.')
    if offprint:
        notes.append('Assumes a separate offprint/extract; excludes all copies in its parent journal.')
    else:
        notes.append('Assumes an ordinary printed edition or individual volume. Popular reprints and unusually small issues can fall outside this range.')
    if record.get('id') == 'w0ddcff4e34a0':
        sources.append({'title': 'Worcester Cathedral Library · its 1728 Pemberton copy', 'url': 'https://worcestercathedrallibrary.wordpress.com/2021/07/08/an-eighteenth-century-isaac-newton-for-dummies-henry-pembertons-1728-a-view-of-sir-isaac-newtons-philosophy/', 'role': 'Independent institutional copy and subscription-publication context. No total print run or surviving-copy census is supplied.'})
        notes.append('The Worcester source confirms another institutional example and subscription publication; it does not establish the size of the edition or its worldwide survival.')
    return {'min': low, 'max': high, 'confidence': confidence, 'cohort': cohort['id'], 'year': year,
            'scope': 'Separate offprint/extract printing' if offprint else 'Described printing or individual volume; not complete sets',
            'documentedMinimumApplied': minimum if floor_applies else None, 'sources': sources, 'notes': notes,
            'editionConfidence': review.get('confidence') or (record.get('confidence') or {}).get('metadata', {}).get('level', 'unresolved')}, None


def main():
    out = ROOT / 'circulation-estimates'
    out.mkdir(exist_ok=True)
    index, excluded, confidence, cohorts = {}, collections.Counter(), collections.Counter(), collections.Counter()
    total = 0
    for path in sorted((ROOT / 'book-records').glob('*.json.gz')):
        shard = {}
        for key, record in json.loads(gzip.decompress(path.read_bytes())).items():
            total += 1
            result, reason = estimate(record)
            if result:
                shard[key] = result
                index[key] = {k: result[k] for k in ['min', 'max', 'confidence']}
                confidence[result['confidence']] += 1
                cohorts[result['cohort']] += 1
            else:
                excluded[reason] += 1
        (out / path.name).write_bytes(gzip.compress(json.dumps(shard, ensure_ascii=False, separators=(',', ':')).encode(), mtime=0))
    payload = {'version': MODEL['version'], 'checked': MODEL['checked'], 'total': total, 'estimated': len(index),
               'confidenceCounts': dict(confidence), 'cohorts': dict(cohorts), 'excluded': dict(excluded), 'records': index}
    (ROOT / 'circulation-estimates-index.json.gz').write_bytes(gzip.compress(json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode(), mtime=0))
    (ROOT / 'circulation-coverage.json').write_text(json.dumps({k: v for k, v in payload.items() if k != 'records'}, indent=2) + '\n')
    print(json.dumps({k: v for k, v in payload.items() if k != 'records'}, indent=2))


if __name__ == '__main__':
    main()
