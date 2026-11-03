# agenda

Zelfstandige bibliotheek die uit middelen, hun beschikbaarheid en bestaande boekingen berekent wat vrij is, en een dubbele
boeking weigert. Alleen standaardbibliotheek (`zoneinfo`, `datetime`, `dataclasses`), geen framework, geen database,
geen netwerk.

**Versie: 1.0**

## Python-versies

Gecontroleerd en geclaimd: **Python 3.11** (de tests zijn gedraaid op 3.11.2, zie `agenda/OMGEVING.md`). De code is
ontworpen om op 3.9 of nieuwer te werken (geen `match`, geen `X | Y`-types), maar dat is een ontwerpdoel en geen claim:
andere versies zijn niet gecontroleerd. De tijdzone `Europe/Brussels` moet door `zoneinfo` geladen kunnen worden.

## Tests draaien

Vanaf de root van de repo, zonder installatie:

    python3 -m unittest discover -s . -t . -p "test_*.py"

## Voorbeeld

Dit blok wordt door `agenda/tests/test_readme.py` uit deze README gehaald en uitgevoerd.

```python
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from agenda import Agenda, Boeking, DubbeleBoeking, Materiaal, Medewerker

brussel = ZoneInfo("Europe/Brussels")

an = Medewerker(
    "m1", "An Voorbeeld",
    werktijden={0: [(time(9), time(12)), (time(13), time(17))]},  # maandag
    pauzes={0: [(time(10), time(10, 15))]},
)
truck = Materiaal("t1", "Foodtruck Test", [(date(2027, 6, 1), date(2027, 6, 30))])

agenda = Agenda([an, truck])  # tz="Europe/Brussels"

# Maandag 7 juni 2027: duur 30 minuten, stap 15.
vrij = agenda.vrije_tijden("m1", date(2027, 6, 7), duur_minuten=30)
assert [t.strftime("%H:%M") for t in vrij[:5]] == ["09:00", "09:15", "09:30", "10:15", "10:30"]

# Boeken geeft een nieuwe agenda; de oude blijft gelijk.
boeking = Boeking("b1", "m1", datetime(2027, 6, 7, 9, 0, tzinfo=brussel),
                  datetime(2027, 6, 7, 9, 30, tzinfo=brussel))
nieuwe = agenda.boek(boeking)
assert agenda.is_vrij("m1", boeking.start, boeking.einde)
assert not nieuwe.is_vrij("m1", boeking.start, boeking.einde)

try:
    nieuwe.boek(Boeking("b2", "m1", datetime(2027, 6, 7, 9, 15, tzinfo=brussel),
                        datetime(2027, 6, 7, 9, 45, tzinfo=brussel)))
except DubbeleBoeking:
    pass
else:
    raise AssertionError("dubbele boeking had geweigerd moeten worden")

# Materiaal werkt met hele dagen, beide grenzen inclusief.
met_truck = agenda.boek(Boeking("b3", "t1", date(2027, 6, 5), date(2027, 6, 7)))
assert met_truck.vrije_dagen("t1", date(2027, 6, 4), date(2027, 6, 8)) == [date(2027, 6, 4), date(2027, 6, 8)]
```

## Interface

Alles wat in `agenda/__init__.py` staat is publiek; al het andere is intern.

| Naam | Soort |
|---|---|
| `Agenda`, `Medewerker`, `Materiaal`, `Boeking` | klassen (frozen dataclasses voor de modellen) |
| `AgendaFout`, `DubbeleBoeking`, `BuitenBeschikbaarheid` | fouten (`DubbeleBoeking` en `BuitenBeschikbaarheid` erven van `AgendaFout`) |

- `Medewerker(id, naam, werktijden, pauzes=(), afwezig=())`
  - `werktijden`, `pauzes`: mapping weekdag (`0` = maandag … `6` = zondag) naar tijdvakken `(start: time, einde: time)`
    met naïeve `datetime.time` (lokale kloktijd in `Agenda.tz`). Een ontbrekende weekdag of lege reeks betekent: niet werken.
    Een pauze is wekelijks terugkerend; een pauze buiten de werktijd doet niets.
  - `afwezig`: reeks `(start, einde)` van aware `datetime`s (half-open); mag overlappen.
- `Materiaal(id, naam, beschikbaar)`: `beschikbaar` is een reeks `(van: date, tot: date)`, beide inclusief. Leeg betekent
  nooit beschikbaar.
- `Boeking(id, middel_id, start, einde)`: aware `datetime`s bij een medewerker, `date`s bij materiaal.
- `Agenda(middelen, boekingen=(), tz="Europe/Brussels")`
  - `vrije_tijden(middel_id, dag, duur_minuten, stap_minuten=15)` → `list[datetime]` (aware, oplopend, zonder dubbelen)
  - `vrije_dagen(middel_id, van, tot)` → `list[date]` (`van` en `tot` inclusief, `van <= tot`)
  - `is_vrij(middel_id, start, einde)` → `bool`; buiten de beschikbaarheid is het `False`, geen fout
  - `boek(boeking)` → nieuwe `Agenda`; de oorspronkelijke blijft ook bij een fout ongewijzigd
  - `tz`, `middelen`, `boekingen`: alleen-lezen

De constructor van `Agenda` valideert precies zoals `boek()`: er bestaat geen ongeldige `Agenda`. Alle aangeleverde
collecties worden bij het aanmaken gekopieerd naar tuples of `MappingProxyType`; latere wijziging van de aangeleverde
lijsten heeft geen effect.

## Regels

### Intervallen per type

| | Medewerker | Materiaal |
|---|---|---|
| Eenheid | minuut (echt verstreken tijd) | hele dag |
| Interval | half-open `[start, einde)`: tot 10:00 botst niet met vanaf 10:00 | gesloten `[start, einde]`: 5–7 juni bezet drie dagen; 7 en 8 juni botsen niet |
| Eendaags | n.v.t. | `start == einde` |
| Bereikvraag | n.v.t. | `vrije_dagen(middel_id, van, tot)` |

Een boeking van een medewerker valt binnen één lokale dag (in `Agenda.tz`) en binnen één werktijdvak: een boeking over een
pauze heen of over middernacht wordt geweigerd.

### Zomertijd en tijdzone

- `Agenda.tz` is een IANA-naam; een onbekende naam geeft `AgendaFout`. Alle werktijden en pauzes van alle medewerkers
  worden in die zone gelezen. Teruggegeven tijden zijn aware in `Agenda.tz`.
- Boekingen en afwezigheid mogen in een andere zone worden aangeleverd; ze worden als absolute tijdstippen vergeleken.
- Duur is verstreken tijd, geen kloktijd: 60 minuten is 60 minuten ook over een overgang heen. Een boeking die de overgang
  overspant is toegestaan en rekent op verstreken tijd.
- **Lentedag** (laatste zondag van maart; 02:00–03:00 bestaat niet, het *lentegat*): een werktijd 01:00–04:00 telt 2
  verstreken uren (01:00–02:00 en 03:00–04:00). Niet-bestaande starttijden worden nooit aangeboden. Een werktijd die
  in het gat begint of eindigt, wordt met `zoneinfo`-gedrag `fold=0` gelezen: de offset van vóór de overgang (+01:00)
  blijft gelden. De kloktijd schuift dus een uur vooruit, niet naar het einde van het gat: een werktijd die om 02:50
  begint, begint feitelijk om 03:50 (CEST), en een werktijd die om 02:30 eindigt, eindigt om 03:30.
- **Herfstdag** (laatste zondag van oktober; 02:00–03:00 komt twee keer voor): een werktijd 01:00–04:00 telt 4 verstreken
  uren. Beide voorkomens van 02:00 worden aangeboden: het eerste met `fold=0` (`+02:00`), het tweede met `fold=1`
  (`+01:00`); te onderscheiden via `utcoffset()` en `fold`.

### Stappenraster

`duur_minuten` en `stap_minuten` zijn `int > 0` (een `bool` wordt geweigerd). Het raster begint bij de start van elk
werktijdvak en loopt door in verstreken minuten. Een pauze of boeking schuift het raster niet op; ze maken alleen de
starttijden die erin vallen onbeschikbaar. Een starttijd wordt alleen aangeboden als `[start, start + duur)` volledig
binnen één werktijdvak ligt en geen pauze, afwezigheid of boeking raakt. Voorbeeld: werktijd 09:07–12:07, stap 15, duur 30,
pauze 10:00–10:10 geeft 09:07, 09:22, 10:22, 10:37, 10:52, 11:07, 11:22, 11:37. Elke aangeboden starttijd is boekbaar
voor de gevraagde duur.

### Foutentabel

| Situatie | Gedrag |
|---|---|
| Onbekend `middel_id` (aanroep, `boek`, of boeking in de constructor) | `AgendaFout` |
| Dubbele `id` bij middelen of bij boekingen | `AgendaFout` |
| Verkeerd type (`datetime` waar `date`, `date` waar `datetime`, `str`, `None`) | `AgendaFout` |
| Naïeve `datetime` | `AgendaFout` |
| `einde <= start` (medewerker) of `einde < start` (materiaal) | `AgendaFout` |
| Boeking over middernacht (medewerker) | `AgendaFout` |
| `duur_minuten` of `stap_minuten` nul, negatief of geen `int` | `AgendaFout` |
| Onbekende `tz` | `AgendaFout` |
| Boeking overlapt een bestaande boeking van hetzelfde middel | `DubbeleBoeking` |
| Boeking buiten werktijd, tijdens pauze of afwezigheid, of buiten `beschikbaar` | `BuitenBeschikbaarheid` |

## Versie en wijzigingsregel

Dit is versie **1.0**. Uitbreiden zonder te breken (nieuwe optionele argumenten, nieuwe namen) mag binnen versie 1.
Het breken van de interface (namen weghalen of hernoemen, signaturen, intervalregels of fouttypes veranderen) is een
**nieuwe hoofdversie** (2.0).

## Verhuispad

Zodra een echt project de module nodig heeft, vraagt de eigenaar een eigen repo aan. Dan wordt `agenda/` met geschiedenis
overgezet met `git subtree split`, krijgt ze een `pyproject.toml` met versie `1.0.0`, en gebruikt hub-sandbox haar als
afhankelijkheid in plaats van de map. Dat is een apart plan.

## Gebruik in hub-sandbox

`vrije_momenten.py` in de root van hub-sandbox importeert de module met `from agenda import ...` en drukt vrije momenten af
voor een voorbeeldset middelen.
