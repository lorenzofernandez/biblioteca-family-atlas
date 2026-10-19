import importlib.util
spec=importlib.util.spec_from_file_location('geography','scripts/build-card-geography.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
def locate(text,**extra):return g.locate({'text':text,**extra})
assert locate('Paris, Gauthier-Villars, 1884.')[0]=='FRA'
assert locate('CREMONA, Luigi.\nParis, Gauthier-Villars, 1884.',heading='CREMONA, Luigi')[0]=='FRA'
assert locate('Cremona, Luigi.\nParis, Gauthier-Villars, 1884.',heading='Cremona, Luigi')[0]=='FRA'
assert locate('New York, London, Wiley, 1963.')[0]=='MULTI'
assert locate('A history of Paris, London and Rome') is None
assert locate('Cambridge, s.n., 1900.') is None
assert locate('Cambridge, University Press, 1900.')[0]=='GBR'
assert locate('Cambridge, Mass., Harvard, 1961.')[0]=='USA'
assert locate('London, Macmillan, 1900.',crossReference=True) is None
assert locate('London, Macmillan, 1900.',continuation=True) is None
assert locate('s.l., s.n., 1855.') is None
print('Publication-place checks passed: author names, joint imprints, ambiguous places, continuations and cross-references.')
