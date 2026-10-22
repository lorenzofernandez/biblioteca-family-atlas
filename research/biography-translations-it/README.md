# Italian biography translations

Generated locally from the existing public-source English biographies, candidate
biographies and previews. English records, links, attribution and confidence
assessments are unchanged. This is an automatic translation layer, not a new
biographical authority or an independent verification of the underlying identity.

Engine: CTranslate2 with the Argos Translate English–Italian 1.0 model.
Model: https://argos-net.com/v1/translate-en_it-1_0.argosmodel
Upstream: https://github.com/argosopentech/argos-translate

`dist/biographies-it/*.json` contains small on-demand dictionaries keyed by
original text. A UTF-16 FNV-1a hash selects one of 256 shards. Existing editorial
translations in `dist/translations-it.json` take precedence.

Rebuild with `scripts/translate-author-biographies-it.py /path/to/en_it` in an
environment with ctranslate2 and sentencepiece installed. The sentence cache is a
local build intermediate. Run `scripts/repair-biography-translation-numbers.py
/path/to/en_it` after translation, then rerun the generator to rebuild the
shipping shards from the corrected cache. Numeric correction uses source-preserving fragments
when a translated sentence changes a source number. The shipping check is
`scripts/check-biography-translations-it.py`.

The browser labels translated biographies, retains source and license credits,
and restores the exact English text when English is selected. Automatic
translations can still contain linguistic errors and have not all been reviewed
individually.
