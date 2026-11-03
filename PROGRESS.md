# Progress

## Contant afronden op 5 cent
- `contant_afronden(bedrag_centen)` toegevoegd in `prijzen.py`, met gehele berekening naar het dichtstbijzijnde veelvoud van vijf cent.
- Negatieve bedragen en niet-gehele waarden (ook `float` en `bool`) geven een `ValueError` met Nederlandse melding.
- Tests in `tests/test_prijzen.py` voor alle eindcijfers, nul, grote bedragen en ongeldige invoer. Eerst rood bevestigd doordat de functie ontbrak.
- Validatie: `python3 -m unittest discover -s tests -t .`; alle 37 tests groen.
- Openstaand: niets.

## Bedrag in euro tonen
- `weergave.py` met `euro(bedrag_centen)` toegevoegd (Belgische notatie).
- Tests in `tests/test_weergave.py`; `prijzen.py` onaangeroerd.
- Openstaand: niets.

## Btw-bedrag apart berekenen
- `btw_bedrag(bedrag_centen, tarief)` toegevoegd in `prijzen.py`: `met_btw - bedrag`, dus altijd consistent met `met_btw`.
- Onbekend tarief geeft nu een `ValueError` (met de geldige tarieven) in `met_btw`, `zonder_btw` en `btw_bedrag`, in plaats van `KeyError`.
- Tests in `tests/test_prijzen.py` (voorbeelden, 0..1000 cent x alle tarieven, negatief, onbekend tarief).
- Openstaand: niets.

## Factuurregel tonen
- `factuurregel(omschrijving, bedrag_centen, tarief="standaard")` toegevoegd in `weergave.py`; gebruikt `euro()`, `btw_bedrag`, `met_btw` en `BTW_TARIEVEN`, de btw wordt niet opnieuw berekend.
- Negatief bedrag of onbekend tarief geeft de `ValueError` uit `prijzen.py` (niet opgevangen); lege omschrijving (ook alleen spaties) geeft een `ValueError` ("omschrijving mag niet leeg zijn").
- Tests in `tests/test_weergave.py`.
- Openstaand: niets.

## Korting toepassen
- `met_korting(bedrag_centen, procent)` toegevoegd in `prijzen.py`: `(bedrag * (100 - procent) + 50) // 100`, dezelfde afronding (halve centen omhoog) als de btw-functies.
- Negatief bedrag, korting buiten 0..100 of geen `int` (ook geen `float` of `bool`) geeft een `ValueError` met Nederlandse melding.
- Tests in `tests/test_prijzen.py` (`KortingTest`).
- Openstaand: niets.

## Factuurtotaal over meerdere regels
- `factuurtotaal(regels)` toegevoegd in `weergave.py`: elke regel via `factuurregel`, daaronder `Totaal: <incl. btw> (waarvan btw <btw>)`. Totalen zijn de som van `met_btw` en `btw_bedrag` per regel (hele centen, dus consistent met de getoonde regels).
- Lege lijst geeft een `ValueError` ("een factuur heeft minstens één regel nodig"); onbekend tarief of negatief bedrag geeft de `ValueError` uit `prijzen.py`.
- Tests in `tests/test_weergave.py` (`FactuurtotaalTest`).
- Openstaand: niets.

## Contant te betalen op de factuur
- `factuurtotaal_contant(regels)` toegevoegd in `weergave.py`: de tekst van `factuurtotaal(regels)` plus `Contant te betalen: € …`, het totaal incl. btw afgerond met `contant_afronden`. `factuurtotaal` zelf is ongewijzigd.
- Lege lijst geeft dezelfde `ValueError` als `factuurtotaal` (die wordt eerst aangeroepen); ook een generator als invoer werkt.
- Tests in `tests/test_weergave.py` (`FactuurtotaalContantTest`).
- Openstaand: niets.

## Skelet van het pakket agenda/
- `agenda/` met `__init__.py`, `fouten.py` (`AgendaFout`, `DubbeleBoeking`, `BuitenBeschikbaarheid`) en `tests/` met `test_omgeving.py` (tijdzone Europe/Brussels laden, foutenhierarchie).
- Omgevingsresultaat in `agenda/OMGEVING.md` (Python 3.11.2, tijdzonedata aanwezig, 44 tests groen).
- Openstaand: niets.

## Half-open intervallen aftrekken en samenvoegen
- `agenda/intervallen.py` toegevoegd met `samenvoegen`, `aftrekken` en `overlap` voor generieke vergelijkbare grenzen. Alleen standaardbibliotheek, geen grensrekenkunde, `match` of union-types.
- Samenvoegen neemt overlap en aansluiting mee; overlap zelf sluit aansluiting uit. Aftrekken normaliseert beide invoerreeksen en ondersteunt meerdere verwijderingen over meerdere basisintervallen, zonder invoer te wijzigen.
- Ongeldige intervallen (`start >= einde`) geven `ValueError`; de module documenteert de invoervorm en UTC-gebruik bij tijdzones.
- Vaste tests voor minuutgrenzen, midden/rand/volledig aftrekken, lege en ongesorteerde invoer, generators en verschillende grenstypes. Eerst rood bevestigd door de ontbrekende module.
- Validatie: `python3 -m unittest discover -s . -t . -p "test_*.py"`: alle 52 tests groen; `git diff --check` groen.
- Openstaand: niets. Geen commit gemaakt.

## Modellen, fouten en validatie (agenda/)
- `agenda/modellen.py`: frozen dataclasses `Medewerker`, `Materiaal`, `Boeking`; alle invoer wordt gevalideerd (alleen `AgendaFout`) en diep gekopieerd naar tuples en `MappingProxyType`. Geen `match`, geen `X | Y`.
- Weekdag-mappings: sleutels `int` 0-6 (geen `bool`), naieve `time`, `start < einde`, geen overlap per dag (ook bij pauzes). `Boeking` kiest datetime- of date-modus; het middeltype controleert `Agenda` later.
- `controleer_binnen_een_dag(boeking, tz)` weigert een boeking over middernacht in `Agenda.tz` (een `Boeking` kent zelf geen zone); `Agenda` moet dit aanroepen.
- Foutenhierarchie stond al in `agenda/fouten.py`; nu ook getest. Tests: `agenda/tests/test_modellen.py`.
- Openstaand: `Agenda` moet middeltype tegenover boekingssoort controleren en `controleer_binnen_een_dag` gebruiken.

## Review ronde 1: fold-volgorde in modellen
- Bevinding bevestigd met `FoldVolgordeTest` (4 tests rood): bij dezelfde `ZoneInfo` negeert Python `fold` in `<`/`<=`, zodat `02:15 fold=1 → 02:45 fold=0` (31 okt 2027, Brussel) werd aanvaard en het geldige omgekeerde geweigerd.
- Herstel: `_einde_na_start` in `agenda/modellen.py` vergelijkt in UTC; gebruikt door `Medewerker.afwezig` en `Boeking` (datetime). Alle 76 tests groen.
- Openstaand: `agenda.py` moet later ook in UTC vergelijken. Geen commit gemaakt.

## Agenda-klasse voor medewerkers, boeken en zomertijd (agenda/)
- `agenda/agenda.py`: `Agenda(middelen, boekingen=(), tz="Europe/Brussels")` met `boek()`, `is_vrij()` en `vrije_tijden()` voor `Medewerker`. Alles rekent in UTC; werktijden en pauzes worden per dag met zoneinfo omgezet (`fold=0`). Het raster begint bij elk werktijdvak en loopt door in verstreken minuten.
- De constructor valideert exact als `boek()` (onbekend middel, dubbele id's, `DubbeleBoeking`, `BuitenBeschikbaarheid`, middernacht, onbekende tz). `boek()` geeft een nieuwe agenda; de oude blijft gelijk.
- `agenda/__init__.py` exporteert nu `Agenda`, de modellen en de fouten.
- Tests: `agenda/tests/test_agenda_medewerkers.py` (gewone dag, raster 09:07, lente, herfst met fold/utcoffset, eigenschappentest). Alle tests groen.
- Openstaand: `Materiaal` en `vrije_dagen` (andere taak; `Agenda` weigert `Materiaal` nu met `AgendaFout`), README, hub-sandbox-toepassing.

## Review ronde 1 (Agenda): boeking-id `_vraag` brak `is_vrij()`
- Bevinding bevestigd met `test_is_vrij_met_boeking_id_vraag` (rood: `AgendaFout: dubbele boeking-id: _vraag`): `is_vrij` gebruikte een vaste hulp-id die met een bestaande boeking kon botsen.
- Herstel: `Agenda._controleer(..., controleer_id=False)` voor `is_vrij`; de id-controle blijft in constructor en `boek()`. 107 tests groen. Geen commit gemaakt.

## Grensdatums: AgendaFout in plaats van OverflowError
- Bevestigd met `GrensDatumTest` (rood): `_einde_na_start` zette om naar UTC via `astimezone` en gaf `OverflowError` bij `0001-01-01 00:10+01:00` en `9999-12-31 23:10-01:00`, voor `Boeking` en `Medewerker.afwezig`.
- Herstel: `_utc_sleutel` in `agenda/modellen.py` vergelijkt absolute tijden als geheel getal (microseconden), zonder buiten het bereik van `datetime` te gaan; die gevallen zijn nu geldig. `controleer_binnen_een_dag` zet een overflow bij de omzetting naar `Agenda.tz` om in `AgendaFout`. 80 tests groen.
- Openstaand: `agenda.py` moet dezelfde sleutel gebruiken en `astimezone` tegen overflow bewaken. Geen commit gemaakt.

## Agenda: materiaal op dagniveau (vrije_dagen en boeken)
- `agenda/agenda.py`: `Agenda` accepteert nu ook `Materiaal`. Boeken en `is_vrij` met `date`s (einde inclusief) rekenen met half-open dagnummers `[start, einde + 1)` via `aftrekken`/`overlap`; nieuw `vrije_dagen(middel_id, van, tot)` (inclusief, oplopend, zonder dubbelen). Rekent op intervallen, niet per dag, dus ook `date.min`..`date.max` werkt.
- Fouten: `datetime` bij materiaal, `date` bij medewerker, `vrije_dagen` op een medewerker, `vrije_tijden` op materiaal, `van > tot` en onbekend middel geven `AgendaFout`; overlap `DubbeleBoeking`; buiten `beschikbaar` `BuitenBeschikbaarheid`. Constructor en `boek()` delen `_controleer`, dus dezelfde uitzondering.
- Tests: `agenda/tests/test_agenda_materiaal.py`. Alle 133 tests groen met het testcommando uit de kop.
- Openstaand: README, hub-sandbox-toepassing. Geen commit gemaakt.

## Agenda: interface, onafhankelijkheid en isolatie
- `agenda/tests/test_structuur.py` toegevoegd: controleert exact de zeven contractnamen in `__all__`, wildcard-export en imports van `agenda/__init__.py`. De publieke exports stonden al correct; geen productiecode gewijzigd.
- AST-controle over alle Python-bestanden in `agenda/`, inclusief de tests zelf en imports binnen functies: alleen agenda en standaardbibliotheek toegestaan; relatieve imports mogen het pakket niet verlaten. Met standaardbibliotheekdetectie voor Python 3.9 en nieuwer.
- Isolatietest kopieert uitsluitend `agenda/` (zonder bytecodecache) naar een tijdelijke map en start een subproces met `-I -S` vanuit een andere werkmap. Controleert afwezigheid van de repo-root op `sys.path`, de exacte gekopieerde `agenda.__file__`, concrete vrije tijden en een boeking via de publieke interface; de oorspronkelijke agenda blijft ongewijzigd.
- Tests gebruiken geen netwerk, geheimen of omgevingsvariabelen. Validatie: `python3 -m unittest discover -s . -t . -p "test_*.py"`: alle 136 tests groen, inclusief de drie nieuwe tests; `git diff --check` groen.
- Openstaand binnen deze taak: niets. Geen commit gemaakt.

## agenda: README en toepassing in hub-sandbox
- `agenda/README.md`: interface, intervallen per type, zomertijd (met lentegat), stappenraster, foutentabel, versie 1.0, wijzigingsregel en verhuispad (`git subtree split`, `pyproject.toml` 1.0.0). Claimt alleen Python 3.11 (gedraaid op 3.11.2, zie `agenda/OMGEVING.md`); 3.9 staat er als ontwerpdoel, niet als claim.
- `agenda/tests/test_readme.py` haalt het codeblok uit de README en voert het uit.
- `vrije_momenten.py` (root): kleine toepassing met `from agenda import ...`, verzonnen namen en `.test`-adressen; `python3 vrije_momenten.py` drukt vrije momenten af. Test: `tests/test_vrije_momenten.py` (staat in `tests/`, zodat ook de CI die vindt).
- Testcommando uit de kop: 140 tests groen. Bestaande hub-sandbox-code ongewijzigd. De CI draait alleen `tests/` en dus niet `agenda/tests/`; dat is niet aangepast (buiten scope), eigenaar kan beslissen.
- Openstaand: niets. Geen commit gemaakt.

## agenda: review ronde 1 (lentegat in README)
- Bevinding: README beweerde dat een werktijd in het lentegat naar de dichtstbijzijnde bestaande tijd schuift; echt gedrag (`fold=0`) behoudt de offset van vóór de overgang (02:50 wordt 03:50 CEST). README aangepast; code ongewijzigd (contract noemt `fold=0`).
- Tests: `test_lente_werktijd_begint_in_het_gat` (gedrag vastgelegd) en `test_readme_beschrijft_lentegat_zoals_het_werkt` (faalde eerst). 142 tests groen. Geen commit gemaakt.

## agenda vervolg: grensdatums in Agenda en aansluitende werktijdvakken
- Grensdatums: eerst `GrensDatumAgendaTest` (rood: `OverflowError` uit `boek`, `is_vrij`, constructor, `vrije_tijden` op `date.min`/`date.max`). Herstel in `agenda/agenda.py`: tijdstippen worden als geheel getal (microseconden, `_utc_sleutel` uit `modellen.py`) vergeleken in plaats van via `astimezone(UTC)`; omzettingen naar `Agenda.tz` die buiten het bereik vallen geven `AgendaFout`. Een boeking die niet naar `Agenda.tz` omgezet kan worden, geeft dus `AgendaFout` (ook bij `is_vrij`), geen `False`.
- Aansluitende werktijdvakken: besloten NIET samen te voegen. Reden: het masterplan zegt "Een boeking mag meerdere werktijdvakken niet overspannen" en de rekenregel is per werktijdvak; samenvoegen zou het contract wijzigen (stopvoorwaarde c). Vastgelegd in `AansluitendeVakkenTest` en in de README.
- 151 tests groen met het testcommando uit de kop. Geen commit gemaakt.
