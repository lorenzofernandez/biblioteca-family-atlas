/* Possible contents inferred from the title or an existing sourced description.
   Scores are deliberately coarse editorial assessments, never probabilities. */

'use strict';
const rules=[
 // Specific subjects precede broad disciplines. Never match against a journal citation.
 ['submarine-telephony',/telephoni.*(?:marin|submarin)|(?:marin|submarin).*telephon/i,'Undersea communication','Ways to improve telephone communication through submarine cables.','Signal transmission','It may examine how electrical arrangements affect the quality of long-distance telephone signals.'],
 ['freezing',/gef.*punkte?|freezing|congel|congelamento|cryoscop|crioscop/i,'Freezing points','A study of how solutions freeze and how their composition affects the freezing point.','Comparing solutions','It may compare measurements at different concentrations to explore the behaviour of dissolved substances.'],
 ['corrosion',/corrosi|rostbild/i,'Corrosion','How metals deteriorate through chemical or environmental attack.','Protecting metals','It may compare materials or treatments intended to reduce corrosion.'],
 ['plating',/electroplat|plating|galvanoplast|galvanosteg|elettrodepo|electrodepo|electrolyti.*depo|nickelage|dorure|doreur/i,'Metal coatings','The deposition of a metal layer onto another surface.','Controlling the finish','It may explore how operating conditions affect the quality of a metal coating.'],
 ['electrolysis',/elettrolisi|electrolys|elektrolyse/i,'Electrolysis','Chemical changes produced by passing an electric current through a substance or solution.','Reaction conditions','It may compare the substances formed under different electrical or chemical conditions.'],
 ['electrochemistry',/electroch|elettroch|elektroch|electrode|elettrod|elektrod|polarisation|polarizz|depolari|uberfuhrungszahl/i,'Electrochemical behaviour','The relationship between chemical reactions and electrical behaviour.','At the electrode','It may explore how materials and solutions behave at an electrode surface.'],
 ['batteries',/batter|accumulat|galvanic couples|piles? electri|coppia elettric|fuel cell/i,'Electrical cells','How chemical cells produce or store electrical energy.','Cell performance','It may compare cell materials and the conditions that influence their performance.'],
 ['metallurgy',/metallurg|smelt|refin.*metal|metall.*refin|mines et les metaux|docimast/i,'Working with metals','Methods for extracting, refining or testing metals.','Metallurgical practice','It may compare practical processes and the properties of their products.'],
 ['alloys',/alloy|leghe|alliage|legier/i,'Metal alloys','How combinations of metals behave as materials.','Composition and properties','It may compare how alloy composition or treatment changes material properties.'],
 ['crystals',/cristal|crystall|kristall|cristall/i,'Crystal structure','The forms and properties of crystalline materials.','Identifying crystals','It may describe ways to compare crystals through their shape or physical behaviour.'],
 ['minerals',/mineral|mineraux|[il]apidibus|gemmarum|gemmis|pietre|gemstone|gebirgsarten/i,'Minerals and stones','A description of minerals, stones or gems and their distinguishing properties.','Classification','It may compare specimens and explain how different kinds of mineral material are recognised.'],
 ['mining',/\bmining\b|\bmines\b|bergwerk|bergbau|lagerstat|giaciment|minerari/i,'Mining and deposits','Mineral deposits and the work of finding or extracting them.','Resources and methods','It may discuss the character of deposits or the methods used to exploit them.'],
 ['magnetism',/magnet|aimant/i,'Magnetism','The behaviour of magnetic materials or magnetic fields.','Physical influences','It may explore how changing physical conditions alters magnetic effects.'],
 ['spectra',/spectr|spettr|spektr/i,'Spectra','The patterns of radiation emitted, absorbed or separated by substances.','Reading the patterns','It may compare spectra to investigate the properties of materials.'],
 ['ultraviolet',/ultraviolet|ultraviolett|ultraviolett/i,'Ultraviolet light','How ultraviolet radiation interacts with substances.','Absorption and composition','It may compare the absorption of ultraviolet light to investigate a substance’s properties.'],
 ['optics',/optique|ottica|optik|optics|birefr|birifr|polarisationsebene|lumiere|luce|\blicht/i,'Light and optics','How light behaves and interacts with matter.','Optical effects','It may investigate reflection, transmission or other changes in light under experimental conditions.'],
 ['x-rays',/rontgen|roentgen|x.ray|rayons x|raggi x|cathodi/i,'Rays and radiation','The production or behaviour of penetrating rays or cathode rays.','Experimental observations','It may describe apparatus and observations used to investigate these rays.'],
 ['radioactivity',/radioactiv|radioattiv|radioaktiv/i,'Radioactivity','The behaviour and effects of radioactive substances.','Uses of radiation','It may consider how radiation can reveal the properties or behaviour of matter.'],
 ['heat',/thermodynam|termodinam|thermisch|calor|chaleur|warme|\bheat\b|temperatur/i,'Heat and temperature','How heat or temperature influences physical systems and materials.','Thermal behaviour','It may compare observations with an explanation of how heat is transferred or stored.'],
 ['electricity',/elettric|electri|elektri|galvanis|stromversorg/i,'Electrical phenomena','The properties, effects or practical uses of electricity.','Experiments and apparatus','It may explain electrical behaviour through experiments or descriptions of equipment.'],
 ['telegraphy',/telegraph|telegraf|wireless|radiotelegraf/i,'Sending messages','Communication over distance using electrical or wireless signals.','Communication equipment','It may describe the instruments and arrangements used to transmit and receive messages.'],
 ['engines',/steam engine|macchin.*vapor|machine.*vapeur|dampfmaschine|motori|engines/i,'Engines and power','The operation of engines and the conversion of energy into mechanical work.','Engineering practice','It may describe construction, performance or practical improvements to engines.'],
 ['mechanics',/mechanic|meccanic|mecanique|mechanik|friction|attrito|poulies|gravitation|principia mathematica/i,'Motion and forces','How forces govern the motion or equilibrium of bodies.','Mathematical explanation','It may use calculations or experiments to relate forces to observable motion.'],
 ['fluids',/hydraul|idraul|hydrodynam|idrodinam|hydrostat|idrostat|viscos|capillar|fluid/i,'Fluids','The movement and physical behaviour of liquids or gases.','Flow and resistance','It may compare the conditions that influence flow or resistance to motion.'],
 ['osmosis',/osmoti|osmosi|osmotisch|diffusi/i,'Transport in solutions','The movement of substances within or between solutions.','Concentration differences','It may examine how concentration and other conditions influence that movement.'],
 ['adsorption',/adsorp|adsorb/i,'Adsorption','How substances accumulate on the surfaces of other materials.','Surface interactions','It may compare how different materials or conditions affect the amount taken up.'],
 ['catalysis',/cataly|cataliz|kataly/i,'Catalysis','How a catalyst influences a chemical reaction.','Reaction rates','It may compare reactions under different conditions to understand the catalyst’s effect.'],
 ['solutions',/\bsoluzion|\bsolutions?\b|\blosungen\b|solubili|solubilite/i,'Solutions','The properties and behaviour of substances dissolved in a liquid.','Dissolving and mixing','It may examine how composition or surrounding conditions changes the behaviour of a solution.'],
 ['metals',/\bmetals?\b|metall|metaux|steels?|acciai|acier|kupfer|cuivre|copper|nickel|platin|mercure|mercurio|quecksilber|\bferro\b|\beisen\b|alumin|alumin|bronze|bronz|laiton|ottone|\bzinc|\bzink|silber|argento|antimon|tantal|columbium/i,'Properties of metals','The behaviour or processing of the metal named in the title.','Material performance','It may compare how composition or treatment affects that metal’s useful properties.'],
 ['chemical-reactions',/chlorur|chlorid|chlorure|bromur|iodur|oxyde|oxide|ossid|acidi|acido|\bacid\b|\bacide|sauerstoff|nitrat|nitrit|alkalin|halogen|oxygen|sulfat|solfat|yttrium|cyanid|permanganat/i,'Chemical compounds','The preparation, properties or reactions of the substances named in the title.','Comparing substances','It may examine how these compounds change or interact under different conditions.'],
 ['chemistry',/\b(?:chemistry|chemisch\w*|chemical\w*|chemiae|chemia|chimic\w*|chimique\w*|chimie|chym\w*|alchem\w*|alchim\w*|chemie)\b/i,'Chemical substances','The properties, preparation or reactions of chemical substances.','Chemical investigation','It may describe experiments or methods for understanding and comparing substances.'],
 ['gases',/\bgas(?:es|e|en)?\b|\bgaz\b|wasserstoff|hydrogen|helium/i,'Gases','The physical or chemical behaviour of gases.','Conditions and behaviour','It may examine how pressure, temperature or composition affects a gas.'],
 ['sound',/acoust|acusti|akusti|microphon|microfon|phonograph|vibrat|schall/i,'Sound and vibration','How vibrations produce, transmit or record sound.','Instruments and effects','It may describe experiments or devices used to investigate these effects.'],
 ['telephony',/telephon|telefon/i,'Telephone communication','The transmission of speech over a distance by electrical means.','Transmission quality','It may examine equipment or arrangements intended to improve telephone signals.'],
 ['measurement',/barometr|manometr|measurement|mesure|misuraz|messung|metrolog/i,'Measurement','Methods or instruments for measuring physical quantities.','Accuracy and comparison','It may compare measurements or examine the reliability of an instrument.'],
 ['astronomy',/astronom|solare|solar|stelle|\bstars\b|celest|comet|planet/i,'The sky','The observation or explanation of celestial bodies and phenomena.','Measuring the heavens','It may use measurements or calculations to explain patterns observed in the sky.'],
 ['geology',/geolog|vulcan|volcan|vulkan|terremot|earthquake|sism|fossil/i,'The Earth','The materials, structures or processes that shape the Earth.','Reading geological evidence','It may interpret rocks, fossils or observations of natural events.'],
 ['weather',/meteorolog|trombes|foudre|atmospher|atmosfer|weather|climat/i,'Weather and atmosphere','Atmospheric conditions and the natural phenomena associated with them.','Observations of weather','It may compare recorded events or measurements to explain how these phenomena develop.'],
 ['natural-history',/natur.*histori|histori.*natur|storia naturale|histoire naturelle|naturgeschichte/i,'The natural world','An account of the natural world and its plants, animals or materials.','Observing and classifying','It may organise observations to compare different kinds of natural objects.'],
 ['botany',/botani|plantarum|\bplants\b|vegetal|vegetaz|flore\b|flora\b/i,'Plants','The description, properties or classification of plants.','Plant knowledge','It may compare plant forms or discuss their practical uses.'],
 ['animals',/zoolog|animali|animals|insect|fauna/i,'Animals','The description or study of animals.','Forms and behaviour','It may compare animal characteristics, habits or ways of classifying them.'],
 ['medicine',/medicin|medical|medico|therapeut|terapeut|patholog|patolog/i,'Medicine and treatment','The understanding of illness or the use of substances and methods in treatment.','Medical practice','It may discuss observations, proposed remedies or approaches to care.'],
 ['physiology',/physiolog|fisiolog|muscul|nerveus|nervos/i,'Living systems','How organs, tissues or other parts of living systems function.','Experimental physiology','It may examine bodily responses through observations or experiments.'],
 ['geometry',/geometr/i,'Geometry','The properties and relationships of shapes, lines and surfaces.','Geometric reasoning','It may develop these ideas through proofs, constructions or exercises.'],
 ['mathematics',/mathemat|matematic|arithmet|aritmet|algebr|polynom|polinom|calcolo|calculus|equation|equazion|fluxion|funzioni|fonctions|probabilit/i,'Mathematical methods','Mathematical relationships and the methods used to work with them.','Problems and applications','It may develop techniques through worked problems or applications.'],
 ['physics',/physiqu|fisica|physik|physics|physica/i,'Physical principles','The principles used to describe matter, motion or energy.','Theory and observation','It may connect explanations of physical phenomena with observations or experiments.'],
 ['photography',/photograph|fotograf/i,'Photography','The processes and materials used to produce photographic images.','Image-making practice','It may compare techniques or explain how processing affects the resulting image.'],
 ['economics',/econom|commerc|industrie|industrial|produzione/i,'Industry and production','The production, organisation or trade of industrial goods.','Practical developments','It may discuss technologies, commercial conditions or changes in industrial practice.'],
 ['biography',/commemoraz|biograph|biograf|\bnecrolog|elogio|eulogy/i,'A life and its work','An account or commemoration of a person’s life and achievements.','Intellectual legacy','It may place that person’s work in the context of their contemporaries.'],
 ['philosophy',/philosoph|filosof|aristotel/i,'Philosophical ideas','An exploration or commentary on philosophical ideas.','Arguments and interpretation','It may explain an earlier thinker’s arguments or compare different ways of understanding its subject.'],
 ['history',/\bhistory\b|\bhistoire\b|\bstoria\b|geschichte|antiquitat/i,'Historical account','An account of how its subject developed over time.','People and developments','It may connect important people, events or discoveries within that history.']
];
const clean=s=>String(s||'').replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim();
const normal=s=>clean(s).normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/£/g,'f').toLowerCase();
const wordCount=s=>s.split(/\s+/).filter(Boolean).length;
// Recover the title's continuation, but never treat a journal, imprint or shelfmark as contents.
function titleOf(record){
 const displayed=clean(record.displayTitle||record.title).replace(/£/g,'f');
 const compact=s=>normal(s).replace(/[^a-z0-9]/g,'');
 const lines=String(record.text||'').replace(/£/g,'f').replace(/([a-zÀ-ÿ])[=\-]\s*\n\s*([a-zà-ÿ])/g,'$1$2').split(/\r?\n/).map(clean);
 const prefix=compact(displayed).slice(0,28);
 const start=prefix.length>=12?lines.findIndex((line,i)=>compact(line+' '+(lines[i+1]||'')).startsWith(prefix)):-1;
 const boundary=/^(?:["' ]*(?:Estr\.?|Extr\.?|Extrait|Extract)\b|cm\s*[.\d,;:]|pp?\s*\.|Leg\s*\.|altra cop[iî]a\b|\(?[12]\d{3}[.,)]?$|(?:Paris|Parls|London|Londra|Firenze|Milano|Napoli|Roma|Rome|Berlin|Wien|Leipzig|Venezia|Venetia|Venetiis|New York|Torino|Bologna|Cambridge|Mediolani|Padova|Pisa|Lyon|La Haye)\s*[,>])/i;
 const body=[];if(start>=0)for(const line of lines.slice(start)){if(boundary.test(line))break;body.push(line);}
 let title=body.length?body.join(' '):displayed;
 title=title.replace(/^(?:Extrait de|Extract from)\s+/i,'').split(/\b(?:Estr\.?|Extr\.?|Extrait de|Extract from|Vedi:)\s/i)[0];
 title=title.split(/\b(?:cm\s*[.,;:]?\s*\d|pp\.\s*\d)/i)[0];
 return clean(title);
}
const proseList=items=>items.length<2?items[0]||'':items.length===2?items.join(' and '):items.slice(0,-1).join(', ')+', and '+items.at(-1);
const materialNames=[
 ['hydrogen chloride',/chlorwasserstoff|hydrogen chloride|chlorure d.hydrogene|cloruro di idrogeno/],
 ['silver permanganate',/silberpermanganat|permanganate d.argent|silver permanganate/],
 ['zinc sulfide',/zinc sul(?:f|ph)ide|sulfure de zinc|solfuro di zinco|zinksulfid/],
 ['zinc oxide',/zinc oxide|oxyde de zinc|ossido di zinco|zinkoxid/],
 ['carbon monoxide',/carbon monoxide|oxyde de carbone|monossido di carbonio|kohlenmonoxid/],
 ['hydrochloric acid',/acid[oe]?\s+(?:chlorhydri|cloridr)|salzsaure|hydrochloric acid/],
 ['hydrofluoric acid',/acid[oe]?\s+f\s*luor|fluorwasserstoff|hydrofluoric acid/],
 ['sulfuric acid',/acid[oe]?\s+(?:sulfur|solfor)|schwefelsaure|sulph?uric acid/],
 ['nitric acid',/acid[oe]?\s+nitr|salpetersaure|nitric acid/],
 ['acetic acid',/acid[oe]?\s+acet|essigsaure|acetic acid/],
 ['silver halides',/silberhalogen|silver halides|halogenur.{0,8}argent/],
 ['silver chloride',/chlorure d.argent|cloruro d.argento|silberchlorid|silver chloride/],
 ['potassium iodide',/ioduro di potassio|iodure de potassium|kaliumiodid|potassium iodide/],
 ['mercury halides',/quecksilberhal|mercury halides|halogenur.{0,8}mercur/],
 ['mercuric bromide',/bromure mercurique|mercuric bromide/],
 ['mercuric chloride',/chlorure mercurique|mercuric chloride/],
 ['vanadium sulfate',/sulfate de vanadium|vanadium sul[fph]+ate/],
 ['uranium salts',/uranium salts|sels d.uranium|sali d.uranio/],
 ['organic acids',/organisch\w* sauren|acidi organici|acides organiques|organic acids/],
 ['aldehydes',/aldehyd|aldeid/],['asparagine',/asparagin/],['aspartic acid',/acide? aspart|aspartic acid/],
 ['ammonia',/ammoniac|ammoniaca|\bammonia\b|ammoniak/],
 ['tungsten',/wolfram|tungsten|scheelmetall/],['chromium',/chromium|cromo\b|\bchrom\b/],
 ['nickel',/nickel|nichel/],['copper',/copper|cuivre|kupfer|rame\b/],['silver',/silver|argent[ou]?\b|silber/],
 ['gold',/\bgold\b|\boro\b|\bd.or\b/],['mercury',/mercury|mercure|mercurio|quecksilber/],
 ['zinc',/\bzinc\w*|\bzink\w*/],['cadmium',/cadmium|cadtnium|cadmio/],['iron',/\biron\b|\bfer\b|ferro\b|eisen\b/],
 ['steel',/\bsteels?\b|\bacciai\w*|\bacier\w*|\bstahl\w*/],['aluminium',/al[ul]mini\w*/],
 ['platinum',/platinum|platine|platino|\bplatin\b/],['arsenic',/arsenic|arsenico|arsenik/],
 ['chlorine',/\bchlorine\b|\bchlore\b|\bcloro\b|\bchlor\b/],['oxygen',/\boxygen\w*|\bossigen\w*|\bsauerstoff/],
 ['hydrogen',/\bhydrogen\w*|\bidrogen\w*|\bwasserstoff/],['helium',/helium|\belio\b/],
 ['tourmaline',/tourmalin|turmalin/],['alum',/\balum\b|\ballume\b|\balun\b/],
 ['carbon',/\bcarbon(?:e|io)?\b|kohlenstoff/],['rubber',/rubber|caoutchouc|caucciu/],['gutta-percha',/gutta[ -]?percha/],['benzoin resin',/benjoin|benzoin/],
 ['senna',/\bsene\b|\bsenna\b/]
];
function namedMaterials(text){
 let rest=text;const found=[];
 // Consume compound names first so “silver chloride” does not also become separate silver/chlorine.
 for(const [name,pattern]of materialNames)if(pattern.test(rest)){found.push(name);rest=rest.replace(new RegExp(pattern.source,'g'),' ');}
 return found.slice(0,4);
}
function detailedReadings(title){
 const text=normal(title).replace(/medlcinal/g,'medicinal').replace(/acldul/g,'acidul').replace(/arti\s+fic[il]al/g,'artificial').replace(/elektro-?\s*ch/,'elektroch');
 const out=[],add=(heading,description,score=60)=>out.push({title:heading,text:description,score});
 if(/(?:acqua del mare|eau de (?:la )?mer|sea[ -]?water)/.test(text)&&/luce|lumiere|luminescen|\blight\b/.test(text)){add('Light from seawater','Observations of light emitted by seawater.');return out;}
 const water=/\bacqu[ae]\b|\beaux?\b|\bwaters?\b|\bwassers?\b/.test(text);
 const waterAnalysis=water&&/analis|analys|untersuch|examen|esamen|medico.chimic/.test(text)&&!/(?:mathemat|matemat|ecoulement|hydraul|idraul)/.test(text);
 const medicinal=water&&/medicinal|mineral|termal|thermal/.test(text);
 const sea=/acqua del mare|eau de (?:la )?mer|sea[ -]?water|meerwasser/.test(text);
 const spring=/\bfonte\b|\bfontaine\b|\bspring\b|\bsorgent\w*/.test(text);
 if(waterAnalysis||medicinal||sea||(water&&spring)){
  const places=[];
  if(/upsal|uppsala/.test(text))places.push('Uppsala');
  if(/\bnocera\b/.test(text))places.push('Nocera');
  if(/\brapolano\b/.test(text))places.push('Rapolano');
  if(/\brecoaro\b/.test(text))places.push('Recoaro');
  const artificial=medicinal&&/artific|kunstlich/.test(text);
  for(const place of ['Mont d’or','Lucca','Pisa','Ischia','Bormio','Masino','Valdieri','Vinadio','Saint-Vincent'])if(text.includes(normal(place).replace('’',"'"))||text.includes(normal(place)))places.push(place);
  const waterKind=/medicinal/.test(text)?'medicinal waters':/termal|thermal/.test(text)?'thermal waters':'mineral waters';
  const natural=[...places.map(place=>'the waters of '+place),...(spring?[/danimarchense/.test(text)?'the Danimarchense acidic spring':/acidul/.test(text)?'an acidic spring':'spring water']:[]),...(sea?['seawater']:[])];
  const topics=[...natural,...(artificial?['artificially prepared medicinal waters']:medicinal?[waterKind]:[])];
  add(waterAnalysis?'Water analysis':medicinal?waterKind.charAt(0).toUpperCase()+waterKind.slice(1):'Natural waters',waterAnalysis?'Chemical analysis of water'+(topics.length?', covering '+proseList(topics):' and its constituents')+'.':'A study of '+proseList(topics.length?topics:['natural waters'])+'.');
  if(artificial)add('Preparing medicinal waters','How to prepare artificial'+(/fredde|froides|cold/.test(text)?' cold':'')+' medicinal waters.',55);
  if(natural.length>1)add('Comparing natural waters','It may compare the composition of '+proseList(natural)+'.',45);
  return out;
 }
 const specific=[
  [/thermochem|termochim/,'Thermochemistry','The heat changes associated with chemical reactions'+(/calculat|calcol/.test(text)?' and how to calculate them':'')+'.'],
  [/electrodeposition of nickel in the bores/,'Plating inside tubes','Depositing nickel inside tubes using insoluble anodes.'],
  [/catalysante|catalytic/,'Aluminium as a catalyst','The catalytic action of aluminium in preparing chlorinated benzenes.',/aluminium/.test(text)&&/benzen/.test(text)],
  [/time|tempo/,'Measuring time','How the concept and measurement of time changed from the eighteenth to the nineteenth century.',/decimottavo|eighteenth/.test(text)&&/decimonono|nineteenth/.test(text)],
  [/somnambul/,'Historical sleepwalking theories','Historical explanations of sleepwalking'+(/magnet/.test(text)?' and its association with animal magnetism':'')+'.'],
  [/history of science/,'Science in the eighteenth century','The history of science, technology, and philosophy in the eighteenth century.',/eighteenth/.test(text)&&/philosoph/.test(text)],
  [/viscosita dielettrica|dielectric viscosity/,'Dielectric behaviour','The delayed electrical response described as dielectric viscosity in capacitors.',/condensator|capacitor/.test(text)],
  [/anodic oxidation|oxidation anodique|ossidazione anodica/,'Anodising aluminium','The surface treatment of aluminium and its alloys by anodic oxidation.',/al[ul]mini/.test(text)],
  [/chlorine.*caust|caust.*chlorine/,'Chlor-alkali electrolysis','How impurities in the electrolyte affect the mercury-cell process for producing chlorine and caustic alkali.',/impur/.test(text)&&/mercury cell/.test(text)],
  [/magnetisme terrestre/,'Magnetism and silver precipitation','How Earth’s magnetic field affects the precipitation of silver.',/precip/.test(text)&&/argent/.test(text)],
  [/electrodeposited coatings/,'Nickel and chromium coatings','Electrodeposited nickel and chromium coatings on zinc and zinc-based alloys.',/nickel/.test(text)&&/chromium/.test(text)&&/on zinc/.test(text)],
  [/dissolved oxygen|dlssolved oxygen/,'Measuring dissolved oxygen','Measuring dissolved oxygen'+(/cambridge analyzer/.test(text)?' with the Cambridge Analyzer':'')+'.'],
  [/chlorwasserstoff/,'Hydrogen chloride and chlorine','The density of hydrogen chloride and the atomic weight of chlorine.',/dichte/.test(text)&&/atomgewicht/.test(text)],
  [/double layer|doppelschicht|double couche|doppio strato/,'Diffuse electrical layers','The diffuse electrical double layer in electrolytes with unequal ionic valences.',/unsymmetrical valence/.test(text)],
  [/photochemisch/,'Photochemical energy','Energy changes in photochemical processes in gases.',/energie/.test(text)&&/gas/.test(text)],
  [/pottery|poterie|ceramica/,'Making pottery','Methods for manufacturing pottery'+(/anglaise|english/.test(text)?' in the English style':'')+'.'],
  [/concretions animales/,'Animal and plant concretions','A comparative analysis of concretions formed in animals and plants.',/vegetal/.test(text)],
  [/activation|actlvatlon/,'Hydrogen at electrodes','The activation energy required for hydrogen ions to discharge at metal electrodes.',/hydrogen.*ions/.test(text)&&/discharge/.test(text)&&/electrode/.test(text)],
  [/double layer|doppelschicht|double couche|doppio strato/,'The electrode interface','The electrical double layer'+(/mercury|mercure|mercurio|quecksilber/.test(text)?' at a mercury electrode':/electrode|elettrod/.test(text)?' at an electrode':/electrolyt/.test(text)?' in electrolytes':' at an interface')+(/capacity|capacita|capacitance/.test(text)?', including its capacitance':'')+'.'],
  [/lamp|lampe|lampad/,'Discharge lamps','The operation of a mercury-discharge lamp'+(/water.cooled/.test(text)?' cooled by water':'')+(/direct.current/.test(text)?' and powered by direct current':'')+'.',/mercury|mercure|mercurio/.test(text)&&/discharge|decharge|scarica/.test(text)],
  [/entladungsrohre/,'Hydrogen discharge tubes','The design or operation of a hydrogen-filled discharge tube.',/wasserstoff/.test(text)],
  [/history|histoire|storia/,'History of machines','The origins and development of machines'+(/antiquit|antichita/.test(text)?' from antiquity':'')+(/xix|19th|nineteenth/.test(text)?' to the nineteenth century':'')+'.',/machines|macchine/.test(text)],
  [/aluminiumschilder/,'Aluminium signs','The manufacture of aluminium signs.'],
  [/cathodoluminescen/,'Luminescent materials','How the firing atmosphere affects the cathodoluminescence of silver-activated zinc sulfide phosphors.',/zinc sul[fph]+ide/.test(text)&&/silver/.test(text)&&/firing/.test(text)],
  [/silberpermanganat/,'Decomposition of silver permanganate','The rate at which silver permanganate decomposes.',/zerfall|decompos/.test(text)],
  [/copper.*alloys|alloys.*copper/,'Copper alloys','The properties of copper-based alloys'+(/elevated.temperature|high.temperature/.test(text)?' at elevated temperatures':'')+'.'],
  [/c[ee]mentation.*acier|carburis|carburiz/,'Treating steel with carbon','The use of carbon in the cementation treatment of steel.',/carbone|carbon|kohlenstoff/.test(text)&&/acier|steel|stahl/.test(text)],
  [/as[hc]en|ashes|cendres/,'Metals in plant ash','The copper content of plant ashes.',/kupfer|copper|cuivre/.test(text)&&/pfl[a-z ]*as[hc]en|plant|vegetal/.test(text)],
  [/drop test|thickness/,'Measuring a metal coating','Using the drop test to measure the thickness of chromium deposited on nickel.',/chromium/.test(text)&&/nickel/.test(text)&&/drop test/.test(text)],
  [/oxido.riduzione|oss[il]do.r[il]duzione|redox potential/,'Redox potentials','The oxidation–reduction potentials of chlorine-substituted toluquinones.',/toluchinon|toluquinon/.test(text)],
  [/polarograf|polarograph/,'Polarography of N-oxides','The polarographic behaviour of aromatic N-oxides.',/n.ossidi|n.oxides/.test(text)&&/aromatic|aro matic/.test(text)],
  [/qu[il]latador/,'Assaying precious materials','The testing of silver, gold, and precious stones.',/plata/.test(text)&&/oro/.test(text)&&/piedras/.test(text)],
  [/protein.*biosynth|biosintesi.*protein/,'Making proteins','The biosynthesis of proteins'+(/membran/.test(text)?' and the biochemistry of membranes':'')+'.'],
  [/storia della chimica|histoire de la chimie|history of chemistry|geschichte der chemie/,'History of chemistry','How chemistry developed'+(/cinesi|chinese|chinois/.test(text)?', including chemical knowledge in China':'')+'.'],
  [/dizionario.*(?:fisica|chimica)|dictionary.*(?:physics|chemistry)/,'A scientific dictionary','A reference work explaining concepts in physics and chemistry'+(/applicat.*arti/.test(text)?' and their applications to the arts and trades':'')+'.'],
  [/denomina.{0,12}chym|nomenclatur.*chim|chemical nomenclature/,'Naming chemical substances','The terminology used to name chemical substances and the rules proposed for standardising it.'],
  [/barrages.*cheminees/,'Monitoring structures','The examination and monitoring of dams and chimneys.'],
  [/ancient chines.*bronze|bronzes.*chinois/,'Ancient Chinese bronzes','Bronze objects from ancient China.'],
  [/thickness.*chromium.*nickel.*drop test/,'Measuring a metal coating','Using the drop test to measure the thickness of chromium deposited on nickel.'],
  [/metallic elements/,'Metal hydrides','Compounds formed between hydrogen and metallic elements.',/hydrogen/.test(text)],
  [/titr[ai]|titrimetr|acidimetr|alcalimetr/,'Chemical measurement','Measuring '+(/sil\s*ber|silver|argent/.test(text)?'silver by titration':/acidimetr|alcalimetr/.test(text)?'acidity or alkalinity by titration':'the quantity of a substance by titration')+(/indicat/.test(text)?', including the use of indicators':'')+'.'],
  [/arsenic.*(?:wall.?papers|tissues)|(?:wall.?papers|tissues).*arsenic/,'Arsenic in everyday materials','Measuring arsenic in wallpaper and fabrics.'],
  [/acquamet|aquamet/,'Measuring water content','Reagents and methods for measuring the water content of materials.'],
  [/ner[vf].*(?:sensibil|motilit)|(?:sensibil|motilit).*ner[vf]/,'Chemical effects on nerves','How '+(/cloridr|chlorhydri|hydrochloric/.test(text)?'dilute hydrochloric acid':'the substance named in the title')+' affects nerve sensitivity and movement.'],
  [/radiazioni ionizz|ionising radiation|ionizing radiation/,'Radiation and the body','The harmful effects of ionising radiation on the human body.',/patolog|patholog|human|umano|organism/.test(text)],
  [/atomphysik|atomic physics|fisica atomica|physique atomique/,'Atomic physics','The structure and physical behaviour of atoms.'],
  [/physique amusante|recreations physiques|recreational physics/,'Experiments for amusement','Entertaining experiments and demonstrations of physical phenomena.'],
  [/lytholog|litholog/,'Rocks and landscapes','Geological observations of '+(/campanie|campania/.test(text)?'Campania'+(/rome|roma/.test(text)?' and Rome':''):'rocks and landscapes')+'.'],
  [/pneumati.*machine|machine pneumati/,'Experiments with an air pump','Experiments using a pneumatic machine'+(/smeaton/.test(text)?' built according to Smeaton’s principles':'')+'.'],
  [/niveau.*eau/,'A water-level instrument','The design of an instrument that uses water to establish a level.'],
  [/plaies des arbres/,'How trees heal','The closing and healing of wounds in trees.'],
  [/incombustib.*tissus|tissus.*incombustib/,'Resistance to burning',/salin/.test(text)?'Using salts to make fabrics resistant to burning.':'The temporary resistance of living tissues to burning.'],
  [/dissoudre.*metaux|dissolving metals/,'Dissolving metals','A method for bringing metals into solution.'],
  [/combinai\s*sons chimiques/,'Mixtures and compounds','Mathematical and experimental methods for distinguishing mixtures from chemical compounds.',/melanges/.test(text)],
  [/capillar/,'Capillary effects',/areo.*metr|hydromet/.test(text)?'Correcting errors caused by capillary effects in hydrometers.':/schwimm|floating|gallegg/.test(text)?'How capillary forces affect the equilibrium of floating bodies.':'The behaviour of liquids under capillary forces.'],
  [/viscos|visqueu/,'Viscosity',/vitreu|glass|vetro/.test(text)?'The resistance to flow of glassy materials.':/molekular|molecular/.test(text)?'The relationship between viscosity measurements and molecular weight.':/ondes|waves/.test(text)?'The propagation of waves in a viscous liquid.':'The resistance of liquids or materials to flow.'],
  [/hydrostati|idrostatic|statique des fluides/,'Fluids at rest','The equilibrium and pressure of fluids at rest.'],
  [/homeopath|omeopat/,'Historical homeopathy','The remedies and therapeutic ideas proposed in a historical work on homeopathy.']
 ];
 for(const [pattern,heading,description,condition=true]of specific)if(condition&&pattern.test(text)){add(heading,description);break;}
 if(out.length)return out.slice(0,3);
 const materials=namedMaterials(text),subject=proseList(materials);
 const properties=[
  [/absor[bp].*(?:ultraviolet|ultraviolett)|(?:ultraviolet|ultraviolett).*absor[bp]/,'Ultraviolet absorption','The absorption of ultraviolet light by'],
  [/fluorescen/,'Fluorescence','The fluorescence of'],
  [/leitf|conductiv|conducibil/,'Conductivity',/therm|term|calor|warme/.test(text)?'The thermal conductivity of':'The electrical conductivity of'],
  [/resistivit|electrical resistance|elektrisch\w* widerstand|resistance.*thin metal films/,'Electrical resistance','The electrical resistance of'],
  [/compressibil|kompressibil/,'Compressibility','The compressibility of'],
  [/densit|dichte|specific gravity|peso specifico/,'Density','The density of'],
  [/freezing|gefrier|congel|cryoscop/,'Freezing points','The freezing behaviour of'],
  [/melting|schmelzpunkt|fusione|fusion des/,'Melting points','The melting behaviour of'],
  [/solubili|loslichkeit|dissolving|dissoluzion/,'Solubility','The solubility of'],
  [/spectr|spettr|spektr/,'Spectra','Spectroscopic studies involving'],
  [/magnet/,'Magnetic properties','Magnetic effects involving'],
  [/corros/,'Corrosion','Corrosion processes involving'],
  [/electrolys|elettrolisi|elektrolyse/,'Electrolysis','Electrolysis processes involving'],
  [/oxidation|ossidazione|oxydation/,'Oxidation','Oxidation reactions involving'],
  [/electrodepo|elettrodepo|electroplat|galvanoplast/,'Metal deposition','Electrodeposited coatings involving'],
  [/preparaz|preparation|darstellung/,'Preparing substances','Preparation methods involving'],
  [/purific|reinigung/,'Purifying substances','Purification methods involving'],
  [/analys|analis|estimation|determination|esamen chimique|examen chimique/,'Chemical analysis','Chemical analysis involving']
 ];
 if(materials.length){
  if(materials.includes('chlorine')&&/luce|light|lumiere/.test(text)){add('Light and chlorine','How exposure to light affects the physical properties of chlorine.');return out;}
  const property=properties.find(([pattern])=>pattern.test(text));
  if(property){
   const conditions=[];if(/influenc|einfluss|effet|effect|variaz|dipenden|druckkoeff|temperature dependence|torsion/.test(text)){
    if(/pressur|pression|druck/.test(text))conditions.push('pressure');if(/temperatur/.test(text))conditions.push('temperature');if(/torsion/.test(text))conditions.push('torsion');
   }
   add(property[1],property[2]+' '+subject+(conditions.length?', including the influence of '+proseList(conditions):'')+'.');
  }else if(/compound|verbindung|compos[et]|combina(?:z|is)/.test(text))add('Chemical compounds','Compounds involving '+subject+'.',55);

 }
 return out;
}

function subjects(title){const text=normal(title);return rules.filter(rule=>rule[1].test(text));}
function catalogueSource(record){return {title:'Original catalogue card',url:record.source?record.source+'#page='+record.page:'originals/'+record.file+'#page='+record.page};}
function build(record){
 const result=[],seen=new Set(),r=record.research,original=catalogueSource(record);
 const cross=record.crossReference||record.continuation||/cross.reference|continuation/i.test(record.catalogueScreening?.formatLabel||'');
 const add=item=>{const key=normal(item.text);if(!seen.has(key)){seen.add(key);result.push(item);}};
 // Curated flags also exist on bibliographic-only records: reject administrative prose.
 const summary=clean(r?.summary),administrative=/^(Source catalogue note|Bibliographic note|The cited edition bibliography)|content summary has not|not yet.*verified/i.test(summary);
 if(r?.curated&&summary&&!administrative&&r.summarySources?.length){
  const first=summary.split(/(?<=[.!?])\s+/)[0];
  if(wordCount(first)<=42)add({title:'In brief',text:first,score:record.confidence?.metadata?.level==='high'?85:70,basis:'A description in the existing research, supported by the linked sources. Confidence concerns the broad subject; edition details may still differ.',sources:r.summarySources});
 }
 const title=titleOf(record),specific=detailedReadings(title),matched=subjects(title);
 const titleBasis='Inferred from the title and its continuation on the catalogue card. The transcription may contain errors; the full text has not been checked.';
 for(const item of specific)add({...item,score:cross?Math.min(item.score,40):item.score,basis:(cross?'This is a cross-reference or continuation card. ':'')+titleBasis,sources:[original]});
 function fromRule(rule,score,source,basis,angle=true){
  add({title:rule[2],text:rule[3],score,basis,sources:[source]});
  if(angle)add({title:rule[4],text:rule[5],score:Math.max(20,score-20),basis:'A possible emphasis inferred from the subject. No chapter list or full text has been checked. '+basis,sources:[source]});
 }
 if(!specific.length&&matched.length){
  const basis=cross?'The subject is inferred from a cross-reference or continuation card, which may point to another record.':'The subject is inferred from the catalogue title. Its transcription may contain errors; the contents have not been checked.';
  fromRule(matched[0],cross?35:50,original,basis,false);
  // Do not pad the carousel with additional discipline-level guesses.
 }
 // Medium/high references only. Low-confidence title overlaps can be entirely different works.
 if(!specific.length&&result.length<3)for(const candidate of record.onlineCandidates||[]){
  if(!['high','medium'].includes(candidate.confidence?.level)||/rejected|excluded|different work/i.test(candidate.reviewDecision?.status||candidate.editionRelation||''))continue;
  const rule=subjects(candidate.title)[0];if(!rule||matched.some(m=>m[0]===rule[0]))continue;
  fromRule(rule,candidate.confidence.level==='high'?60:40,{title:candidate.title,url:candidate.url},'Inferred from the title of a possible online match. This reference may describe a different edition. '+clean(candidate.editionRelation),false);
  if(result.length>=3)break;
 }
 return result.sort((a,b)=>b.score-a.score).slice(0,4);
}

export {build};
