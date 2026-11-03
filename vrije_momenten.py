from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from agenda import Agenda, Boeking, Materiaal, Medewerker

BRUSSEL = ZoneInfo("Europe/Brussels")


def voorbeeld_agenda():
    """Een verzonnen set middelen: twee medewerkers en een foodtruck, met twee boekingen."""
    werkdagen = {dag: [(time(9), time(12)), (time(13), time(17))] for dag in range(5)}
    pauzes = {dag: [(time(10), time(10, 15))] for dag in range(5)}
    middelen = [
        Medewerker("m1", "An Voorbeeld (an@example.test)", werkdagen, pauzes),
        Medewerker("m2", "Bram Proef (bram@example.test)", {1: [(time(10), time(12))]}),
        Materiaal("t1", "Foodtruck Test", [(date(2027, 6, 1), date(2027, 6, 30))]),
    ]
    boekingen = [
        Boeking("b1", "m1", datetime(2027, 6, 7, 9, 0, tzinfo=BRUSSEL),
                datetime(2027, 6, 7, 10, 0, tzinfo=BRUSSEL)),
        Boeking("b2", "t1", date(2027, 6, 5), date(2027, 6, 7)),
    ]
    return Agenda(middelen, boekingen)


def vrije_momenten(agenda, dag, duur_minuten=30, stap_minuten=15):
    """Regels tekst met de vrije starttijden van elke medewerker op `dag` en de vrije dagen van elk materiaal in die maand."""
    regels = []
    for middel in agenda.middelen:
        if isinstance(middel, Medewerker):
            tijden = agenda.vrije_tijden(middel.id, dag, duur_minuten, stap_minuten)
            tekst = ", ".join(t.strftime("%H:%M") for t in tijden) or "geen"
            regels.append(f"{middel.naam} op {dag.isoformat()}: {tekst}")
        else:
            volgende = date(dag.year + (dag.month == 12), dag.month % 12 + 1, 1)
            laatste = date.fromordinal(volgende.toordinal() - 1)
            vrij = agenda.vrije_dagen(middel.id, dag.replace(day=1), laatste)
            tekst = ", ".join(str(d.day) for d in vrij) or "geen"
            regels.append(f"{middel.naam} vrije dagen in {dag.year}-{dag.month:02d}: {tekst}")
    return regels


if __name__ == "__main__":
    print("\n".join(vrije_momenten(voorbeeld_agenda(), date(2027, 6, 7))))
