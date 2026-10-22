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
