"""De klasse Agenda: vrije tijden, controle en boeken voor medewerkers.

Alles wordt in UTC berekend; lokale werktijden en pauzes worden per dag met
zoneinfo omgezet (fold=0 voor niet-bestaande of dubbele kloktijden).
"""

from datetime import date, datetime, time, timedelta, timezone
from types import MappingProxyType
from typing import Any, Dict, Iterable, List, Tuple

from agenda.fouten import AgendaFout, BuitenBeschikbaarheid, DubbeleBoeking
from agenda.intervallen import aftrekken, overlap
from agenda.modellen import Boeking, Medewerker, _zone, controleer_binnen_een_dag

_UTC = timezone.utc
Interval = Tuple[datetime, datetime]


def _utc(waarde: datetime) -> datetime:
    return waarde.astimezone(_UTC)


def _minuten(waarde: Any, veld: str) -> int:
    if isinstance(waarde, bool) or not isinstance(waarde, int) or waarde <= 0:
        raise AgendaFout("%s moet een int groter dan 0 zijn" % veld)
    return waarde


class Agenda:
    """Onveranderlijke agenda met medewerkers en hun boekingen."""

    __slots__ = ("_tz", "_zone", "_middelen", "_boekingen")

    def __init__(self, middelen: Iterable[Medewerker], boekingen: Iterable[Boeking] = (),
                 tz: str = "Europe/Brussels") -> None:
        zone = _zone(tz)
        try:
            lijst = list(middelen)
            boekingenlijst = list(boekingen)
        except TypeError:
            raise AgendaFout("middelen en boekingen moeten reeksen zijn") from None
        per_id: Dict[str, Medewerker] = {}
        for middel in lijst:
            if not isinstance(middel, Medewerker):
                raise AgendaFout("alleen een Medewerker wordt ondersteund")
            if middel.id in per_id:
                raise AgendaFout("dubbele middel-id: %s" % middel.id)
            per_id[middel.id] = middel
        object.__setattr__(self, "_tz", tz)
        object.__setattr__(self, "_zone", zone)
        object.__setattr__(self, "_middelen", MappingProxyType(per_id))
        object.__setattr__(self, "_boekingen", ())
        aanvaard: List[Boeking] = []
        for boeking in boekingenlijst:
            self._controleer(boeking, aanvaard)
            aanvaard.append(boeking)
        object.__setattr__(self, "_boekingen", tuple(aanvaard))

    def __setattr__(self, naam: str, waarde: Any) -> None:
        raise AttributeError("Agenda is onveranderlijk")

    @property
    def tz(self) -> str:
        return self._tz

    @property
    def middelen(self) -> Tuple[Medewerker, ...]:
        return tuple(self._middelen.values())

    @property
    def boekingen(self) -> Tuple[Boeking, ...]:
        return self._boekingen

    # -- rekenwerk ---------------------------------------------------------

    def _medewerker(self, middel_id: Any) -> Medewerker:
        if not isinstance(middel_id, str) or middel_id not in self._middelen:
            raise AgendaFout("onbekend middel: %r" % (middel_id,))
        return self._middelen[middel_id]

    def _lokaal(self, dag: date, tijd: time) -> datetime:
        return _utc(datetime.combine(dag, tijd, tzinfo=self._zone))

    def _intervallen(self, dag: date, vakken: Iterable[Tuple[time, time]]) -> List[Interval]:
        resultaat = []
        for start, einde in vakken:
            begin, eind = self._lokaal(dag, start), self._lokaal(dag, einde)
            if begin < eind:
                resultaat.append((begin, eind))
        return resultaat

    def _vrij_per_vak(self, medewerker: Medewerker, dag: date,
                      boekingen: Iterable[Boeking] = ()) -> List[Tuple[Interval, List[Interval]]]:
        """Per werktijdvak: (vak, vrije stukken na aftrek van pauze, afwezigheid, boekingen)."""
        weekdag = dag.weekday()
        weg = self._intervallen(dag, medewerker.pauzes.get(weekdag, ()))
        weg += [(_utc(s), _utc(e)) for s, e in medewerker.afwezig]
        weg += [(_utc(b.start), _utc(b.einde)) for b in boekingen if b.middel_id == medewerker.id]
        vakken = self._intervallen(dag, medewerker.werktijden.get(weekdag, ()))
        return [(vak, aftrekken([vak], weg)) for vak in vakken]

    def _controleer(self, boeking: Any, bestaand: Iterable[Boeking]) -> None:
        if not isinstance(boeking, Boeking):
            raise AgendaFout("een boeking moet een Boeking zijn")
        medewerker = self._medewerker(boeking.middel_id)
        if not isinstance(boeking.start, datetime):
            raise AgendaFout("een medewerker wordt met datetimes geboekt")
        controleer_binnen_een_dag(boeking, self._tz)
        bestaand = list(bestaand)
        if any(b.id == boeking.id for b in bestaand):
            raise AgendaFout("dubbele boeking-id: %s" % boeking.id)
        interval = (_utc(boeking.start), _utc(boeking.einde))
        dag = boeking.start.astimezone(self._zone).date()
        if not any(a <= interval[0] and interval[1] <= b
                   for _, vrij in self._vrij_per_vak(medewerker, dag) for a, b in vrij):
            raise BuitenBeschikbaarheid("de boeking valt buiten de beschikbaarheid")
        for andere in bestaand:
            if andere.middel_id == boeking.middel_id and overlap(
                    interval, (_utc(andere.start), _utc(andere.einde))):
                raise DubbeleBoeking("de boeking overlapt boeking %s" % andere.id)

    # -- publieke interface ------------------------------------------------

    def boek(self, boeking: Boeking) -> "Agenda":
        """Geef een nieuwe Agenda met de boeking erbij; deze agenda blijft gelijk."""
        self._controleer(boeking, self._boekingen)
        return Agenda(self._middelen.values(), self._boekingen + (boeking,), self._tz)

    def is_vrij(self, middel_id: str, start: datetime, einde: datetime) -> bool:
        """Is [start, einde) boekbaar? Buiten de beschikbaarheid is False, geen fout."""
        boeking = Boeking("_vraag", middel_id, start, einde)
        try:
            self._controleer(boeking, self._boekingen)
        except (BuitenBeschikbaarheid, DubbeleBoeking):
            return False
        return True

    def vrije_tijden(self, middel_id: str, dag: date, duur_minuten: int,
                     stap_minuten: int = 15) -> List[datetime]:
        """Starttijden (aware, oplopend) waarop duur_minuten volledig vrij is."""
        medewerker = self._medewerker(middel_id)
        duur = timedelta(minutes=_minuten(duur_minuten, "duur_minuten"))
        stap = timedelta(minutes=_minuten(stap_minuten, "stap_minuten"))
        if not isinstance(dag, date) or isinstance(dag, datetime):
            raise AgendaFout("dag moet een date zijn")
        starts = set()
        for (begin, eind), vrij in self._vrij_per_vak(medewerker, dag, self._boekingen):
            moment = begin
            while moment + duur <= eind:
                if any(a <= moment and moment + duur <= b for a, b in vrij):
                    starts.add(moment)
                moment += stap
        return [s.astimezone(self._zone) for s in sorted(starts)]
