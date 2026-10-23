# Progress

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

## Contant afronden op 5 cent
- `contant_afronden(bedrag_centen)` toegevoegd in `prijzen.py`: `(bedrag + 2) // 5 * 5` (rest 1,2 omlaag; 3,4 omhoog).
- Negatief bedrag of geen `int` (ook geen `float` of `bool`) geeft een `ValueError` met Nederlandse melding.
- Tests in `tests/test_prijzen.py` (`ContantAfrondenTest`).
- Openstaand: niets.

## Factuurtotaal over meerdere regels
- `factuurtotaal(regels)` toegevoegd in `weergave.py`: elke regel via `factuurregel`, daaronder `Totaal: <incl. btw> (waarvan btw <btw>)`. Totalen zijn de som van `met_btw` en `btw_bedrag` per regel (hele centen, dus consistent met de getoonde regels).
- Lege lijst geeft een `ValueError` ("een factuur heeft minstens één regel nodig"); onbekend tarief of negatief bedrag geeft de `ValueError` uit `prijzen.py`.
- Tests in `tests/test_weergave.py` (`FactuurtotaalTest`).
- Openstaand: niets.
