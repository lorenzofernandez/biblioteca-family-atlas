"""Editorial source notes for the 18 October 2026 biography review.

Each entry was checked against the cited sources and the connected catalogue
records. This writes the review manifest; enrichment is a separate, repeatable step.
"""
import json
from pathlib import Path

entries = []
def add(ids, name, dates, origins, short, bio, sources, reason, **options):
    entries.append(dict(authorIds=ids.split(), name=name, birth=dates[0], death=dates[1],
                        origins=origins, short=short, biography=bio,
                        sources=[dict(title=t, url=u) for t,u in sources],
                        identityReason=reason, identityLevel='high', **options))

add('a773a245cb082', 'Nicolò Rorario', (None,None), ['Italy'],
    'A sixteenth-century physician and surgeon in Udine, Rorario compared the teachings of ancient medical authorities.',
    'Nicolò Rorario, also recorded as Nicola Rorario and Nicolaus Rorarius, was a physician from Udine whose family came from Pordenone. His birth is placed approximately in the 1510s; his exact birth and death dates are not established. He graduated at Padua on 17 April 1542 and served as Udine’s municipal surgeon from 1551 to 1570.\n\nHis Contradictiones, dubia et paradoxa, published in Venice in 1566, examined disagreements among Hippocrates, Celsus, Galen, Aetius, Paul of Aegina and Avicenna, attempting to reconcile their medical teachings. Its discussions also encompass eye medicine and medicinal plants. A revised edition followed in 1572. The title, author and 1566 date on this catalogue card provide a strong match to that work.',
    [('Bruno Lucci · Dizionario Biografico dei Friulani','https://www.dizionariobiograficodeifriulani.it/rorario-nicolo'),
     ('University of Padua · Una vita da medico','https://mostre.cab.unipd.it/caimo/it/79/una-vita-da-medico-spigolature')],
    'The author name, distinctive medical title and 1566 Venetian publication agree with the biographical dictionary and the University of Padua exhibition.',
    lifeLabel='Born c.1510s · active 1542–1572')

add('a4dd44c6f4fdf', 'Roberto Piontelli', (1909,1971), ['Italy'],
    'An Italian physical chemist and electrochemist, Piontelli studied metal deposition, electrode reactions and industrial electrochemical processes.',
    'Roberto Piontelli was born in Lodi and built his scientific career at the Politecnico di Milano. His training crossed electrical engineering, physics and chemistry. He worked with Oscar Scarpa and succeeded him in the electrochemistry chair in 1948, later directing an institute that brought together electrochemistry, physical chemistry and metallurgy.\n\nHis research connected the theory of electrode reactions with industrial problems, including the deposition and dissolution of metals and the extra voltage needed to drive electrochemical reactions. He helped establish the international committee CITCE, which developed into the International Society of Electrochemistry. Elected to the Accademia dei Lincei in 1969, he died in Milan in 1971.',
    [('Treccani · Roberto Piontelli','https://www.treccani.it/enciclopedia/roberto-piontelli/'),
     ('Società Chimica Italiana · The electrochemistry school at the Politecnico','https://www.societachimica.it/sites/default/files/chimind/pdf/2014_3_3607_on.pdf')],
    'Full name, electrochemistry publications and the Politecnico research context match the documented scientist.')

add('a79050fa903c8', 'Ferdinand Anne Kröger', (1915,2006), ['Netherlands'],
    'A Dutch physical chemist, Kröger researched imperfections in crystals and semiconductor materials in industry and at the University of Southern California.',
    'Ferdinand Anne Kröger was born in Amsterdam and earned a doctorate in physical chemistry there in 1937. He worked at Philips from 1937 to 1958, then at Mullard in Britain until 1964, before joining the University of Southern California as a founding professor of materials science.\n\nHis work concerned the properties of solids, semiconductors and the defects that affect how crystals behave. His book The Chemistry of Imperfect Crystals, published in Amsterdam in 1964, brought this research together. The crystal-chemistry publications in the family catalogue trace these interests across his industrial and academic career.',
    [('Family obituary · San Diego Union-Tribune','https://www.legacy.com/us/obituaries/sandiegouniontribune/name/f-kroger-obituary?id=25938821'),
     ('CINiBA university library · The Chemistry of Imperfect Crystals','https://integro.ciniba.edu.pl/integro/191901546731/kroger-ferdinand-anne/the-chemistry-of-imperfect-crystals')],
    'The full name and 1964 book on imperfect crystals identify the materials scientist. The former legal-historian match is incompatible with these works.',
    corrected=True, wikidata='Q27863073', resetIdentity=True)

add('a4bac48d3223d', 'Alfred Lacroix', (1863,1948), ['France'],
    'A French mineralogist and petrographer, Lacroix studied rock-forming minerals and volcanic eruptions, including Montagne Pelée in 1902.',
    'Alfred Lacroix was born in Mâcon and trained in pharmacy before turning to mineralogy and the microscopic study of rocks. Working in the circle of Ferdinand Fouqué and Auguste Michel-Lévy, he co-authored Les minéraux des roches in 1888 and completed a doctorate in 1889 on rocks containing pyroxene and wernerite. He became professor of mineralogy at the Muséum national d’histoire naturelle in 1893.\n\nHis research ranged from the identification of minerals to the study of volcanoes, notably the 1902 eruption of Montagne Pelée. The catalogue’s papers on wernerite and volcanic rocks strongly support Alfred Lacroix as the author behind “A. Lacroix.”',
    [('Société géologique de France · Alfred Lacroix','https://geosoc.fr/propos-html/historique/presidents-de-la-sgf/64-presidents-sgf/1044-francois-antoine-alfred-lacroix.html'),
     ('Charles Bedel · 1948 obituary','https://www.persee.fr/doc/pharm_0035-2349_1948_num_36_121_9696'),
     ('CNRS/MNHN · Journées Lacroix','https://cak.ehess.fr/system/files/2024-09/document%20d%E2%80%99accompagnement%20des%20Journ%C3%A9es%20Lacroix.pdf')],
    'The initials, dates, wernerite studies and volcanic-rock papers correspond to Alfred Lacroix, not the previously selected Adolphe Lacroix.',
    corrected=True, wikidata='Q586570', resetIdentity=True)

add('ab627d370df4d', 'Giovanni Guglielmo', (None,None), ['Italy'],
    'An experimental physicist, Guglielmo taught in Turin, Sassari and Cagliari, where he directed the physics laboratory for decades.',
    'Giovanni Guglielmo was an Italian experimental physicist. After graduating in physics at Turin in 1878, he worked there as an assistant and moved to Sassari as a professor in 1886. He subsequently held the experimental physics chair at Cagliari from 1891 to 1928, directing its physics laboratory for 37 years and serving as dean.\n\nA University of Cagliari study documents more than a hundred scientific publications, along with teaching notes and correspondence. The family catalogue includes his work on electrometers, electrical measurements and voltaic cells. Exact life dates have not yet been verified for this profile.',
    [('Cristiana Carrus · University of Cagliari doctoral research','https://iris.unica.it/handle/11584/266519'),
     ('Dizionario Biografico degli Italiani · Andrea Naccari','https://www.treccani.it/enciclopedia/andrea-naccari_%28Dizionario-Biografico%29/'),
     ('Gazzetta Ufficiale · 2 May 1891','https://www.gazzettaufficiale.it/eli/gu/1891/05/02/103/sg/pdf')],
    'The full name and nineteenth-century physics publications fit the Cagliari physicist. They predate the career of hematologist Giovanni Di Guglielmo.',
    corrected=True, resetIdentity=True, lifeLabel='Active late 19th–early 20th century')

add('ab38c7cd9e817', 'David Caldwell Grahame', (1912,1958), ['United States'],
    'An Amherst chemist, Grahame investigated the electrical double layer where a metal electrode meets a solution.',
    'David Caldwell Grahame was born in St Paul, Minnesota. He earned his bachelor’s degree at the University of Minnesota in 1935 and his chemistry doctorate at Berkeley in 1937. After two further years at Berkeley, he joined Amherst College in 1939 and remained there until his death in London in 1958, during a Guggenheim fellowship.\n\nHis papers at Amherst document sustained research on the electrical double layer, electrode capacitance and the effects of different ions at an electrode surface, including mercury in aqueous solutions. These are also the subjects of the Grahame papers in the family catalogue.',
    [('Amherst College Archives · David C. Grahame papers','https://archivesspace.amherst.edu/repositories/2/resources/651'),
     ('Amherst College Archives · Electrochemical research papers','https://archivesspace.amherst.edu/repositories/2/archival_objects/277060')],
    'Name, initials and the distinctive electrical-double-layer publications match the Amherst archive.',
    corrected=True, resetIdentity=True)

add('ae2fd855e09e7 a8b906e5c69bd', 'Antonio Rius Miró', (1890,1973), ['Spain'],
    'A Spanish chemist, Rius Miró helped establish physical chemistry and electrochemistry research at the CSIC’s Rocasolano Institute.',
    'Antonio Rius Miró was a Spanish chemist whose career helped shape university and institutional electrochemistry in Spain. He taught electrochemistry in Zaragoza from the 1920s and became the first director of the Instituto de Química Física Rocasolano, created within the CSIC in 1946.\n\nAt Rocasolano he led research in electrochemistry and industrial physical chemistry. Work on electrode behaviour, corrosion and passivation connected fundamental chemistry with industrial applications. The catalogue’s electrochemical papers under “A. Rius” and the reversed name “Antonio Miró Rius” fit this career.',
    [('Historia Contemporánea · Antonio Rius Miró (1890–1973)','https://ojs.ehu.eus/index.php/HC/article/view/23730'),
     ('Real Sociedad Española de Química · History of Spanish electrochemistry','https://www.uco.es/electroquimica-rseq/Costa.pdf')],
    'The name forms, mid-century dates and electrode research support Antonio Rius Miró. Initial-only attributions remain provisional.',
    correctedIds=['ae2fd855e09e7'], resetIdentity=True, mediumIds=['ae2fd855e09e7'])

add('ad4eeb96524e8 a6ca1ea3916cc', 'Juan Francisco Llopis Marí', (None,None), ['Spain'],
    'An electrochemist at Madrid’s Rocasolano Institute, Llopis researched platinum-group metals and supervised Francisco Colom’s doctoral work.',
    'Juan Francisco Llopis Marí worked in electrochemistry at the Instituto de Química Física Rocasolano in Madrid. A historical account published by the Real Sociedad Española de Química identifies him as the supervisor of Francisco Colom’s 1954 doctorate and describes their research on platinum-group metals. Their later collaboration included chapters on platinum, iridium, osmium and palladium for the Encyclopedia of Electrochemistry of the Elements in 1976.\n\nThe catalogue’s Llopis papers on platinum electrodes and passivation are consistent with this researcher. Because some headings give only an initial or surname, this attribution remains tentative. His birth and death dates have not been established here.',
    [('Anales de Química · Francisco Colom obituary and research history (2012)','https://analesdequimica.es/index.php/AnalesQuimica/issue/download/19/49'),
     ('Boletín Oficial del Estado · Juan Francisco Llopis Marí (1964)','https://www.boe.es/boe/dias/1964/11/26/pdfs/A15592-15593.pdf')],
    'Platinum electrochemistry and the research context support Juan Francisco Llopis Marí. Initial/surname-only headings do not establish every attribution. Previous physician and historian matches are unsupported.',
    corrected=True, resetIdentity=True, mediumIds=['ad4eeb96524e8','a6ca1ea3916cc'], lifeLabel='Active mid-20th century')

add('ad5304850f719', 'Louis Cohen', (None,None), [],
    'An author of early twentieth-century electrical research, Cohen co-authored a detailed reference on calculating inductance with Edward B. Rosa.',
    'Louis Cohen contributed to early twentieth-century research on electrical circuits and inductance. With Edward B. Rosa, he compiled Formulae and Tables for the Calculation of Mutual and Self-Inductance, listed among the US Bureau of Standards’ scientific publications in 1907. The work assembled formulas, corrections, tables and worked examples for coils and conductors.\n\nThis publication provides a specific match to the inductance material in the family catalogue. It supports identifying an electrical researcher of this name, but does not establish his life dates or a full career history.',
    [('US Bureau of Standards · Scientific publications catalogue','https://nvlpubs.nist.gov/nistpubs/Legacy/circ/nbscircular24e4.pdf')],
    'The Rosa–Cohen inductance publication matches the catalogue. The author’s broader personal identity and life dates remain unresolved.',
    corrected=True, resetIdentity=True, mediumIds=['ad5304850f719'], lifeLabel='Active early 20th century')

add('aad7b3b8d8f82 a63fbea8ee908 af2b518266bb2', 'Oscar Scarpa', (1876,1955), ['Italy'],
    'An Italian physical chemist and electrochemist, Scarpa taught in Naples, Turin and Milan and was a mentor to Roberto Piontelli.',
    'Oscar Scarpa was born in Venice and trained in physics and electrochemistry at Turin. He helped introduce physical chemistry and electrochemistry teaching at Naples, where he taught physical chemistry from 1909 to 1917. He later worked in Turin and moved to the Politecnico di Milano in the late 1920s.\n\nScarpa’s career connected experimental physical chemistry with the study of electrochemical processes. Roberto Piontelli worked with him and later succeeded him in Milan; Piontelli also wrote his commemoration for the Accademia dei Lincei. The family catalogue preserves numerous Scarpa papers and cross-references, under both his full name and abbreviated headings.',
    [('Roberto Piontelli · Commemoration of Oscar Scarpa (1962)','https://www.bdim.eu/item?fmt=pdf&id=RLINA_1962_8_32_3_419_0'),
     ('University of Naples · History of the chemistry department','https://www.scienzechimiche.unina.it/en/il-dipartimento/la-nostra-storia')],
    'The full name and physical-chemistry works match Oscar Scarpa. Abbreviated headings and the bare-surname cross-reference remain less certain.',
    correctedIds=['af2b518266bb2'], resetIdentity=True, wikidata='Q109876811', mediumIds=['a63fbea8ee908','af2b518266bb2'])

add('a62492000705d', 'Franciscus Antonius Hubertus Schreinemakers', (1864,1945), ['Netherlands'],
    'A Leiden physical chemist, Schreinemakers developed methods for understanding the equilibrium of mixtures and representing it in phase diagrams.',
    'Franciscus Antonius Hubertus Schreinemakers was a Dutch chemist who became professor of inorganic and physical chemistry at Leiden in 1901 and remained there until his retirement in 1934. He was elected to the Royal Netherlands Academy of Arts and Sciences in 1906.\n\nHis research concerned phase equilibria: the conditions under which different forms or components of a chemical system coexist. He studied mixtures and used geometric representations to make their relationships intelligible. The catalogue’s papers on vapour pressure and binary and ternary systems belong to this sustained programme of physical-chemistry research.',
    [('Royal Netherlands Chemical Society · F.A.H. Schreinemakers','https://chg.kncv.nl/geschiedenis/biografieen/s/schreinemakers%2C-f.a.h.'),
     ('H.A.M. Snelders · History of chemistry in the Netherlands','https://www.dbnl.org/tekst/snel016gesc02_01/snel016gesc02_01_0005.php')],
    'Distinctive initials, surname and phase-equilibrium publications identify the Leiden chemist.')

add('a79f3ad72ecb6', 'Ernst Julius Cohen', (1869,1944), ['Netherlands'],
    'A Dutch physical chemist and historian of chemistry, Cohen studied chemical transformations through electrical measurements.',
    'Ernst Julius Cohen trained with Jacobus Henricus van ’t Hoff and completed his doctorate in Amsterdam in 1893, investigating how electrical measurements could reveal transitions in chemical systems. He became a professor at Utrecht in 1902. His research addressed physical chemistry, phase changes and the relationship between chemical transformations and electromotive force.\n\nCohen also wrote about the history of chemistry and earlier scientists, a strand represented alongside his experimental papers in this catalogue. He was murdered at Auschwitz in March 1944. His biographical dates should not be confused with the much earlier dates appearing in titles about historical figures.',
    [('Utrecht University · Ernst Julius Cohen','https://profs.library.uu.nl/hoogleraar/cohen-e-j/'),
     ('DBNL · Ernst Julius Cohen (1869–1944)','https://www.dbnl.org/auteurs/auteur.php?id=cohe026'),
     ('Utrecht University · Bibliography of Cohen scholarship','https://biguu.library.uu.nl/keywords/cohen-ernst-julius-1869-1944/')],
    'The name and physical-chemistry works match Cohen. Early dates in works about historical scientists are not treated as his publication lifetime.')

add('a3289de323518', 'Alphonse Mailhe', (1872,1932), ['France'],
    'A French chemist, Mailhe worked on chemical reactions and artificial liquid fuels, moving from Toulouse to a fuel-chemistry chair in Paris.',
    'Alphonse Pierre Bernard Mailhe was born at Trie-sur-Baïse in 1872. He worked at the Toulouse faculties of medicine and science and completed a doctorate in 1902 on metal oxides, hydrates and mixtures of salts. He later led chemical research for the Paris gas company and held a chair in fuel chemistry in Paris from 1926 until his death in 1932.\n\nHis career linked laboratory chemistry with the practical production of fuels. He published Les combustibles liquides artificiels in 1929. The family catalogue also contains earlier Mailhe papers on chemical reduction and nickel catalysis, showing a wider range of his experimental work.',
    [('Christophe Charle and Eva Telkès · Alphonse Mailhe biography','https://www.persee.fr/doc/inrp_0298-5632_1989_ant_25_1_8725')],
    'The abbreviated first name, surname, dates and chemistry publications support Alphonse Mailhe.')

add('a01a1481cd023', 'Louis Georges Gouy', (1854,1926), ['France'],
    'A French experimental physicist at Lyon, Gouy worked across optics, electricity, magnetism and electrochemical phenomena.',
    'Louis Georges Gouy was born at Vals-les-Bains in 1854 and worked as a physicist at the University of Lyon. His investigations ranged across optics, electricity and meteorology, reflecting the breadth of experimental physics around the turn of the twentieth century.\n\nHe studied electrokinetic phenomena and electrical cells and is associated with a method for measuring magnetic susceptibility. The catalogue’s Gouy papers belong to this physical and electrochemical research context.',
    [('Treccani · Louis Georges Gouy','https://www.treccani.it/enciclopedia/louis-georges-gouy/')],
    'The surname, initial, dates and physical/electrochemical subjects are consistent with Louis Georges Gouy.')

add('a7bb0919d3efc', 'Guillaume Homberg', (1652,1715), [],
    'A physician and experimental chemist in Paris, Homberg investigated phosphorus, acids and mineral substances at the Académie des sciences.',
    'Guillaume Homberg, also known as Wilhelm Homberg, was born in Batavia in 1652. Trained as a physician, he pursued chemistry through travel, practical experimentation and contact with European scientific networks. He joined the Académie des sciences in Paris in 1691 and later worked for Philippe, Duke of Orléans.\n\nHis chemical investigations included phosphorus, the preparation of boric acid from borax and quantitative experiments on the neutralization of acids. The Homberg papers in the family catalogue, including work on phosphorus and mineral transformations, reflect this experimental approach to substances and their reactions.',
    [('Grete Ronge · Neue Deutsche Biographie: Homberg','https://www.deutsche-biographie.de/sfz33645.html')],
    'Name, dates and the phosphorus papers in the catalogue agree with the documented Paris chemist.')

add('aec73c93fa0cf a731e968cb70e', 'Nicolas Lémery', (1645,1715), ['France'],
    'A French apothecary and chemistry teacher, Lémery made practical chemical demonstrations widely accessible through his Cours de chimie.',
    'Nicolas Lémery was a French apothecary and chemist whose teaching combined explanations of substances with practical laboratory demonstrations. After working in Montpellier, he established himself in Paris, where his courses attracted a broad audience. His Cours de chimie became a widely circulated guide to chemical operations and preparations.\n\nHe also investigated such subjects as underground fires, camphor, honey, urine and corrosive sublimate. The catalogue includes editions and translations of his chemistry course as well as papers under the spelling “Nicole Lemery.” Those abbreviated or variant headings require care: Nicolas should not be confused with his son Louis Lémery, who was also a scientist.',
    [('Société d’Histoire de la Pharmacie · Nicolas Lémery exhibition','https://www.shp-asso.org/expositionlemery/'),
     ('Mediachimie · Nicolas Lémery (1645–1715)','https://www.mediachimie.org/ressource/nicolas-lemery-1645-1715')],
    'Cours de chimie identifies Nicolas Lémery. The Nicole spelling and matching paper subjects are compatible, but individual later-dated records remain provisional.',
    mediumIds=['a731e968cb70e'])

add('a3645f4cbb126', 'Nicolas Louis de Lacaille', (1713,1762), ['France'],
    'A French astronomer, Lacaille observed the southern sky from the Cape of Good Hope and worked on the measurement of the Earth.',
    'Nicolas Louis de Lacaille was a French astronomer and geodesist. He taught at the Collège Mazarin in Paris, where he established an observatory, and combined astronomical observation with the measurement of the Earth. His expedition to the Cape of Good Hope enabled an extensive survey of southern stars and the introduction of fourteen constellations.\n\nThe catalogue contains observations associated with the Mazarin observatory, fitting his work before and around the southern expedition. His name appears in several forms, including La Caille and Lacaille; the catalogue’s “Nicole Louis” is a transcription variant.',
    [('University of St Andrews · Nicolas Louis de Lacaille','https://mathshistory.st-andrews.ac.uk/Biographies/Lacaille/')],
    'The near-complete name and Mazarin astronomical observations identify Nicolas Louis de Lacaille.')

add('a92681c956eeb a5e9e27d738b9', 'Alexis Claude Clairaut', (1713,1765), ['France'],
    'A French mathematician, Clairaut applied Newtonian mechanics to the shape of the Earth, the Moon’s motion and the return of Halley’s comet.',
    'Alexis Claude Clairaut was a French mathematician recognized for his work while still very young. He joined the Académie des sciences in 1731 and took part in the 1736–1737 expedition to Lapland that investigated the shape of the Earth. His Théorie de la figure de la Terre appeared in 1743.\n\nHe also developed mathematical accounts of the Moon’s motion and helped calculate the return of Halley’s comet. He assisted Émilie du Châtelet with her work on Newton. The family catalogue includes his geometry and lunar-theory publications. An anomalous 1716 date under the abbreviated heading needs checking against the scan and is not evidence of a publication by the three-year-old Clairaut.',
    [('University of St Andrews · Alexis Claude Clairaut','https://mathshistory.st-andrews.ac.uk/Biographies/Clairaut/')],
    'The distinctive name and geometry/lunar-theory titles fit Clairaut. The abbreviated entry contains an incompatible early date that remains unresolved.',
    mediumIds=['a5e9e27d738b9'])

add('afc6b8eecb475 a29d5c1943a79', 'Henri Louis Duhamel du Monceau', (1700,1782), ['France'],
    'A French botanist and agronomist, Duhamel du Monceau connected experimental research with forestry, agriculture and naval administration.',
    'Henri Louis Duhamel du Monceau was a French scientist whose work joined botany, agriculture and forestry with practical questions of production and public administration. A member of the Académie des sciences, he also served as inspector-general of the navy. His career illustrates the close relationship between scientific investigation, useful trades and state service in eighteenth-century France.\n\nThe family catalogue reflects that breadth: it includes material on the physiology of trees, botanical observations, chemical substances and sugar refining. These works help identify the longer and shorter forms of his name as references to the same historical figure, while the original catalogue headings remain preserved.',
    [('Académie d’agriculture de France · Duhamel du Monceau','https://www.academie-agriculture.fr/actualites/academie/colloque/academie/duhamel-du-monceau-academicien-agronome-et-sylviculteur'),
     ('Condorcet · Académie des sciences eulogy','https://www.academie-sciences.fr/pdf/eloges/duhamel_p131_vol3581.pdf')],
    'Distinctive surname forms and the botanical, forestry and technical works support Duhamel du Monceau.')

add('a05f52587e1e1', 'Voltaire', (1694,1778), ['France'],
    'The Enlightenment writer François-Marie Arouet, known as Voltaire, also helped introduce Newton’s science to French readers.',
    'Voltaire was the pen name of François-Marie Arouet, the French writer, dramatist and philosopher. Alongside his literary and political work, he played a substantial role in making English philosophy and Newtonian science familiar to French readers during the 1730s.\n\nAt Cirey, where he lived and worked with Émilie du Châtelet, scientific study formed part of a much wider intellectual collaboration. His Éléments de la philosophie de Newton appeared in 1738. Editions and translations of that work in the family catalogue place Voltaire here in his role as an interpreter and popularizer of natural philosophy.',
    [('University of Oxford · Voltaire Foundation biography','https://voltaire.ox.ac.uk/about-voltaire/')],
    'The complete catalogue name and Newtonian-philosophy title identify Voltaire.')

add('a41e782c44f40', 'Conrad Gessner', (1516,1565), ['Switzerland'],
    'A Zurich physician, naturalist and bibliographer, Gessner gathered observations and illustrations of animals, plants and other natural objects.',
    'Conrad Gessner, also written Konrad Gesner, was a Zurich physician and scholar who combined natural history with the collection and organization of knowledge. His Historia animalium brought together ancient accounts, contemporary observations and illustrations of animals. He also made detailed botanical studies and compiled the Bibliotheca universalis, a major bibliographical undertaking.\n\nThe family catalogue represents another aspect of this wide-ranging activity through books on fossils, stones and gems and the remedies associated with his Euonymus publications. Gessner died during a plague outbreak in Zurich in 1565, aged forty-nine.',
    [('University of Zurich · Conrad Gessner anniversary','https://www.news.uzh.ch/de/articles/2016/gessner.html'),
     ('University of Zurich Zoological Museum · Gessner exhibition','https://www.zm.uzh.ch/en/sonderausstellungen/2016gessner.html')],
    'The Gesner/Gessner name and distinctive natural-history and Euonymus titles provide a strong match.')

add('a7039c7c7b03f', 'Paracelsus', (1493,1541), [],
    'A physician and natural philosopher, Paracelsus challenged established medical teaching and gave chemical substances a central place in his medicine.',
    'Paracelsus was the name used by Philipp Theophrast Bombast von Hohenheim, born near Einsiedeln in 1493. A travelling physician and natural philosopher, he challenged reliance on inherited medical authorities and developed an approach that gave chemical substances and practical experience a central role.\n\nAs city physician in Basel in 1527–1528, he taught in German and came into conflict with the university’s medical faculty. He died in Salzburg in 1541. The later editions and collected medical works in the family catalogue reflect the continued circulation of his writings after his death; their publication dates are not dates from his lifetime.',
    [('Treccani · Paracelso','https://www.treccani.it/enciclopedia/paracelso/'),
     ('University of Basel · University history','https://www.unibas.ch/en/University/About-University/History.html')],
    'The distinctive name and collected medical works identify Paracelsus; later imprint dates are posthumous editions.')

output = Path(__file__).with_name('reviewed-biographies.json')
output.write_text(json.dumps(dict(reviewedAt='2026-10-18',
    method='Manual source review with catalogue title, subject and date comparisons. Personal life dates are left unset where not verified. No portrait is invented. Original profiles and rejected name matches are retained in the research archive.',
    entries=entries), ensure_ascii=False, indent=2)+'\n')
print(f'{len(entries)} biographies covering {sum(len(e["authorIds"]) for e in entries)} catalogue author entries')
