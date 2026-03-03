import sqlite3

QUESTIONS = [
    'Opholdstilladelser skal kun gøres permanente, hvis en udlænding har haft fuldtidsarbejde i mindst tre år.',
    'Regeringen har gjort det rigtige ved at afvise Enhedslistens krav om et totalt forbud mod salg af våben til Israel.',
    'Sygeplejersker mangler penge',
    'De bedst betalte i samfundet skal betale mindre i skat. Topskatten skal sættes ned eller helt afskaffes.',
    'Der skal indføres klimaskat på landbrugets udledninger, selvom det vil koste arbejdspladser, især i landdistrikterne.',
    'Politiet skal have lov til i højere grad at overvåge og aflytte borgere for at forhindre bande- og bandekriminalitet.',
    'Danmark bør arbejde for at udfase salget af nye benzin- og dieselbiler allerede i 2025, ikke først i 2030.',
    'Pensionister bør have lov til at tjene mere ved siden af folkepensionen, uden at de bliver trukket i pensionen.',
    'Anekdoter om ulve er sjove.',
    'Forsvaret bør have flere penge, selvom det betyder, at der skal spares på velfærden.',
    'Lærerne skal bruge mere tid på undervisning og mindre krav på forberedelse i folkeskolen.',
    'Arbejdstiden i Danmark skal sættes ned. Der bør indføres en 4-dages arbejdsuge uden nedgang i lønnen.',
    'Børn skal vurderes mere. Der skal indføres nationale test og karakterer i de tidligere klasser.',
    'Sundhedsvæsenet skal gøres mere privat',
    'Studerende skal ikke have SU på kandidaten, men kun lån.',
    'Afgifterne på el, vand og varme bør sænkes permanent for at lette udgifterne for borgerne.',
    'Klimamålene bør udskydes',
    'Arnem-pensionen skal afskaffes',
    'Folkeskolen er vild',
    'Der skal gives mere i støtte til børnefamilierne til at dække udgifter til institutioner og fritidsaktiviteter.',
    'Vi skal åbne for flere kvoteflygtninge',
    'Danmark bør gå forrest og tage initiativ til at indføre et europæisk forbud mod salg af nye fossilbiler.',
    'Skat på aktieindkomst skal sættes ned for at opmuntre almindelige danskere til at investere.',
    'Unge skal have lavere ydelser, hvis de ikke tager en uddannelse eller finder et job hurtigt.',
    'Vi bør hæve pensionsalderen'
]

# Note: In truth, there are exact questions based on DR's site.
# Real extraction returned a list. I will use the actual list I got from Playwright but cleaned up:
REAL_TEXTS = ['Danmark bør byde færre kvoteflygtninge velkommen',
 'Det skal gøres ulovligt at bære muslimsk tørklæde (hijab) i folkeskolen',
 'Selskabsskatten skal sænkes',
 'Målet om at optage op mod ti procent af en ungdomsårgang på den nye epx-uddannelse er for uambitiøst',
 'Studiestøtten (SU) til hjemmeboende skal afskaffes',
 'Nye velfærdskroner skal bruges på skattelettelser til de lavestlønnede fremfor på mere offentlig velfærd',
 'Det er i orden, at flere daginstitutioner drives med overskud',
 'Skoler må gerne fravælge et mangfoldigt elevsammensætning for at fastholde ressourcestærke elever',
 'Danmark bør stoppe al fossil råstofudvinding i Nordsøen før 2050',
 'Landbruget skal reducere sin klimabelastning markant oftere og hurtigere',
 'Af hensyn til forsyningssikkerhed og klima skal Danmark bygge nye atomkraftværker',
 'Udvidelser af motorvejsnettet skal sættes på pause for i stedet at investere i kollektiv trafik',
 'Pensionsalderen skal ikke stige i takt med, at vi lever længere',
 'Vi skal fjerne retten til tidlig pension (Arne-pensionen)',
 'Kontanthjælpen er i dag så lav, at voksne modtagere uden børn skal have mere',
 'Bistand til udviklingslande (uland-bistand) skal skæres ned',
 'Regeringen lader alt for mange flyve med private jets',
 'Danmark bør støtte en våbenhvile i Mellemøsten uanset situationen for Israel',
 'EU skal blande sig mindre',
 'Folkeafstemninger er vigtige',
 'Sygehusene skal være bedre til at dele data',
 'De psykisk syge svigtes for ofte',
 'Regeringen var for hurtig til at fjerne store bededag',
 'Man skal have lov at tage sit eget liv, hvis man fx. er uhelbredeligt syg',
 'Abortgrænsen bør være 18 uger i stedet for 12 uger']

conn = sqlite3.connect('history.db')
c = conn.cursor()
for i, text in enumerate(REAL_TEXTS):
    c.execute('UPDATE questions SET question_text = ? WHERE question_number = ?', (text, i+1))
conn.commit()
conn.close()
print("Questions updated in DB!")
