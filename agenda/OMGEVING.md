# Omgevingscontrole agenda/

Datum: 2026-11-03

- Python: 3.11.2 (`python3 --version`).
- Testcommando: `python3 -m unittest discover -s . -t . -p "test_*.py"`
  - Voor het skelet: 42 tests, OK.
  - Na het skelet: 44 tests, OK (twee nieuwe in `agenda/tests/test_omgeving.py`).
- `zoneinfo.ZoneInfo("Europe/Brussels")`: laadt zonder fout. De test `TijdzoneTest` bevestigt wintertijd (UTC+1, januari) en zomertijd (UTC+2, juli).
- Geen afwijkingen gevonden; er is niets omzeild en `QUESTIONS.md` is niet nodig.
- Geen nieuwe afhankelijkheden, geen netwerk, bestaande code ongewijzigd.
