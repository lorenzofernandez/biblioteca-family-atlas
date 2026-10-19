"""Conservative publication-place extraction from the original catalogue OCR.
No author nationality or language inference. Unmatched records remain unlocated.
"""
import collections, gzip, json, pathlib, re, unicodedata
ROOT = pathlib.Path(__file__).resolve().parents[1]
ALIASES = {
'ITA': 'Milano|Milan|Mllano|Mediolani;Roma|Rome|Romae;Torino|Turin|Torlno;Firenze|Florence|Flrenze|Florentiae;Venezia|Venice|Venetiis|Venetia|Venezla;Napoli|Naples|Neapoli|Napoll;Bologna|Bononiae;Pisa|Pisis;Padova|Padua|Patavii;Pavia|Ticini;Modena;Genova|Genoa;Como;Verona;Lucca;Ferrara;Livorno;Palermo;Mantova;Siena;Parma;Brescia;Catania;Bergamo;Messina;Perugia;Trieste;Cremona;Reggio Emilia;Vicenza;Udine;Ravenna;Varese;Pistoia;Bari;Cagliari;Sassari;Trento;Treviso;Pordenone;Pesaro;Urbino;Rimini;Arezzo;Lecce',
'FRA': 'Paris|Parigi|Parls|Parisiis;Lyon|Lione|Lugduni;Tours;Bordeaux;Lille;Strasbourg|Strasburgo|Strassburg;Grenoble;Toulouse;Marseille;Montpellier;Nancy;Rouen;Besançon;Dijon;Caen;Versailles',
'GBR': 'London|Londres|Londra|Londini;Oxford|Oxf ord;Edinburgh|Edimburgo;Aberdeen;Glasgow;Manchester;Bristol;Leeds;Liverpool;Birmingham;Newcastle;Nottingham;Cambridge',
'DEU': 'Berlin|Berlino|Berlln;Leipzig|Lipsia|Lipsiae|Leipzlg;Stuttgart;Dresden;Halle|Halis;Braunschweig;München|Munchen|Munich|Monaco di Baviera;Wiesbaden;Darmstadt;Frankfurt|Frankfurt am Main|Frankfurt a. M.;Göttingen|Gottingen;Heidelberg;Hamburg;Jena|Iena;Bonn;Erlangen;Tübingen|Tubingen;Karlsruhe;Köln|Koln|Cologne;Freiburg|Freiburg im Breisgau;Nürnberg|Nurnberg;Augsburg;Marburg;Düsseldorf|Dusseldorf;Kiel;Dortmund;Mannheim;Ulm;Mainz;Wittenberg;Wittenbergae',
'CHE': 'Genève|Geneve|Geneva|Genevae|Ginevra;Basel|Basileae|Basilea;Zürich|Zurich|Zurigo;Bern|Berne|Berna;Lausanne;Neuchâtel|Neuchatel;Fribourg;Lugano',
'NLD': 'Amsterdam|Amstelodami;Leiden|Leyden|Lugduni Batavorum;Utrecht|Trajecti ad Rhenum;Eindhoven;Rotterdam;Groningen;Delft;Den Haag|The Hague|La Haye',
'BEL': 'Bruxelles|Brussels|Brussel;Liège|Liege;Leuven|Louvain;Gent|Gand|Ghent;Antwerpen|Antwerp|Anvers',
'AUT': 'Wien|Vienna|Vienne;Graz;Innsbruck;Salzburg',
'USA': 'New York|New-York|NewYork;Washington;Philadelphia;Chicago;Boston;Princeton;Baltimore;Cleveland;Pittsburgh;San Francisco;Los Angeles;New Haven;Ithaca;Ann Arbor;Cambridge Mass.|Cambridge, Mass.|Cambridge Massachusetts',
'ESP': 'Madrid;Barcelona;Zaragoza;Sevilla;Salamanca',
'PRT': 'Lisboa|Lisbon;Porto|Oporto;Coimbra',
'SWE': 'Stockholm;Uppsala|Upsala;Lund;Göteborg|Goteborg',
'NOR': 'Oslo;Christiania|Kristiania;Bergen;Trondheim',
'DNK': 'København|Kobenhavn|Copenhagen|Copenhague;Aarhus',
'FIN': 'Helsinki|Helsingfors;Turku|Åbo',
'POL': 'Warszawa|Warsaw|Varsavia;Kraków|Krakow|Cracovia;Wrocław|Wroclaw|Breslau;Gdańsk|Gdansk|Danzig;Poznań|Poznan',
'CZE': 'Praha|Prague|Praga;Brno',
'HUN': 'Budapest;Buda',
'RUS': 'Moscow|Moskva|Mosca;Leningrad;St. Petersburg|Saint Petersburg|Sankt Petersburg|Petersburg',
'CAN': 'Toronto;Ottawa;Montreal|Montréal;Quebec|Québec;Vancouver',
'IRL': 'Dublin', 'GRC': 'Athens|Athènes|Atene', 'ROU': 'Bucuresti|Bucarest|Bucharest',
'ARG': 'Buenos Aires', 'BRA': 'Rio de Janeiro;São Paulo|Sao Paulo', 'MEX': 'Mexico|México',
'AUS': 'Sydney;Melbourne;Canberra;Adelaide', 'NZL': 'Wellington;Auckland',
'JPN': 'Tokyo|Tokio;Kyoto', 'IND': 'Calcutta|Kolkata;Bombay|Mumbai;New Delhi;Madras|Chennai',
'ZAF': 'Cape Town;Johannesburg;Pretoria', 'EGY': 'Cairo|Le Caire', 'CHN': 'Peking|Beijing;Shanghai',
'CHL': 'Santiago de Chile', 'PER': 'Lima', 'CUB': 'La Habana|Havana', 'TUR': 'Istanbul|Constantinople',
}
def norm(s):
 return ''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c)).lower().strip()
aliases = {}
for country, cities in ALIASES.items():
 for city in cities.split(';'):
  variants=city.split('|')
  for alias in variants: aliases[norm(alias)] = (country,variants[0])
pattern=re.compile(r'^('+ '|'.join(re.escape(x) for x in sorted(aliases,key=len,reverse=True))+r')\s*[,;:]\s*(\S.{2,})$')

def locate(record):
 if record.get('crossReference') or record.get('continuation'): return None
 found=[]
 for raw in record.get('text','').splitlines():
  line=norm(raw)
  if line.rstrip('.')==norm(record.get('heading','')).rstrip('.'): continue
  if raw.split(',')[0].strip().isupper(): continue
  match=pattern.match(line)
  if not match: continue
  alias,tail=match.groups(); country,city=aliases[alias]
  # An unqualified Cambridge can be on either side of the Atlantic.
  if alias=='cambridge':
   if re.match(r'(mass\b|massachusetts\b|harvard\b|mit\b)',tail): country='USA'
   elif not re.match(r'(at the university|university press|cambridge university|c\.u\.p\b)',tail): continue
  # A further city printed immediately after a comma is a joint imprint.
  other=pattern.match(tail)
  if other:
   found.append((aliases[other.group(1)][0],aliases[other.group(1)][1],raw.strip()))
  found.append((country,city,raw.strip()))
 if not found: return None
 countries=sorted({x[0] for x in found})
 return [countries[0] if len(countries)==1 else 'MULTI', '; '.join(dict.fromkeys(x[1] for x in found)), ' / '.join(dict.fromkeys(x[2] for x in found))]

def main():
 records={}
 for shard in (ROOT/'dist/book-records').glob('*.json.gz'):
  records.update(json.loads(gzip.decompress(shard.read_bytes())))
 matches={key:hit for key,record in records.items() if (hit:=locate(record))}
 source=ROOT/'scripts/data/natural-earth-countries.geojson'
 world=json.loads(source.read_text())
 countries={f['properties']['ADM0_A3']:{'name':f['properties']['NAME_LONG'], 'anchor':[f['properties']['LABEL_X'],f['properties']['LABEL_Y']]} for f in world['features']}
 countries['MULTI']={'name':'Multiple countries'}
 counts=collections.Counter(hit[0] for hit in matches.values()); counts['UNKNOWN']=len(records)-len(matches)
 countries['UNKNOWN']={'name':'Place unknown'}
 data={'total':len(records),'matched':len(matches),'confidence':'medium','method':'Explicit imprint-like place names at line starts in the catalogue transcription; ambiguous and unmatched records are not mapped. Modern countries, not historical borders.','source':'Original catalogue card transcriptions','mapSource':'https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/','countries':{key:countries[key] for key in counts},'counts':dict(counts),'records':matches}
 out=ROOT/'dist/cards-assets/geography.json.gz';out.write_bytes(gzip.compress(json.dumps(data,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
 features=[]
 def rounded(coords):
  if isinstance(coords[0],(float,int)): return [round(x,3) for x in coords]
  return [rounded(x) for x in coords]
 for f in world['features']:
  if f['properties']['ADM0_A3']=='ATA':continue
  features.append({'code':f['properties']['ADM0_A3'],'polygons':rounded(f['geometry']['coordinates'] if f['geometry']['type']=='MultiPolygon' else [f['geometry']['coordinates']])})
 (ROOT/'dist/cards-assets/world-outlines.json').write_text(json.dumps({'source':data['mapSource'],'countries':features},separators=(',',':')))
 print(json.dumps({'matched':len(matches),'counts':counts.most_common(),'compressedBytes':out.stat().st_size},indent=2))
 # Stable review sample retains evidence and scan source, not just aggregate counts.
 review=[{'id':key,'country':hit[0],'place':hit[1],'evidence':hit[2],'source':records[key]['source']} for key,hit in sorted(matches.items()) if int(key[1:5],16)%37==0]
 (ROOT/'scripts/geography-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
