"""De klasse Agenda: vrije tijden, controle en boeken voor medewerkers en materiaal.

Medewerkers rekenen in UTC; lokale werktijden en pauzes worden per dag met
zoneinfo omgezet (fold=0 voor niet-bestaande of dubbele kloktijden).
Materiaal rekent met hele dagen, als half-open reeksen dagnummers [start, einde + 1).
"""

from datetime import date, datetime, time, timedelta, timezone
from types import MappingProxyType
from typing import Any, Dict, Iterable, List, Tuple, Union

from agenda.fouten import AgendaFout, BuitenBeschikbaarheid, DubbeleBoeking
from agenda.intervallen import aftrekken, overlap
from agenda.modellen import (Boeking, Materiaal, Medewerker, _dag, _utc_sleutel, _zone,
                             controleer_binnen_een_dag)

_UTC = timezone.utc
Interval = Tuple[int, int]
_MICRO = timedelta(microseconds=1)
_NUL = _utc_sleutel(datetime(1, 1, 1, tzinfo=_UTC))
_MINUUT = 60000000


def _utc(waarde: datetime) -> int:
    """Absoluut tijdstip als geheel getal (microseconden); loopt nooit over de datetime-grens."""
    return _utc_sleutel(waarde)


def _datetime(sleutel: int, zone: Any) -> datetime:
    try:
        return (datetime(1, 1, 1, tzinfo=_UTC) + _MICRO * (sleutel - _NUL)).astimezone(zone)
    except OverflowError:
        raise AgendaFout("tijdstip ligt te dicht bij de grens van datetime") from None


def _minuten(waarde: Any, veld: str) -> int:
    if isinstance(waarde, bool) or not isinstance(waarde, int) or waarde <= 0:
        raise AgendaFout("%s moet een int groter dan 0 zijn" % veld)
    return waarde


class Agenda:
    """Onveranderlijke agenda met medewerkers en hun boekingen."""

    __slots__ = ("_tz", "_zone", "_middelen", "_boekingen")

    def __init__(self, middelen: Iterable[Union[Medewerker, Materiaal]], boekingen: Iterable[Boeking] = (),
                 tz: str = "Europe/Brussels") -> None:
        zone = _zone(tz)
        try:
            lijst = list(middelen)
            boekingenlijst = list(boekingen)
        except TypeError:
            raise AgendaFout("middelen en boekingen moeten reeksen zijn") from None
        per_id: Dict[str, Union[Medewerker, Materiaal]] = {}
        for middel in lijst:
            if not isinstance(middel, (Medewerker, Materiaal)):
                raise AgendaFout("een middel moet een Medewerker of Materiaal zijn")
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
    def middelen(self) -> Tuple[Union[Medewerker, Materiaal], ...]:
        return tuple(self._middelen.values())

    @property
    def boekingen(self) -> Tuple[Boeking, ...]:
        return self._boekingen

    # -- rekenwerk ---------------------------------------------------------

    def _middel(self, middel_id: Any) -> Union[Medewerker, Materiaal]:
        if not isinstance(middel_id, str) or middel_id not in self._middelen:
            raise AgendaFout("onbekend middel: %r" % (middel_id,))
        return self._middelen[middel_id]

    def _medewerker(self, middel_id: Any) -> Medewerker:
        middel = self._middel(middel_id)
        if not isinstance(middel, Medewerker):
            raise AgendaFout("%s is geen medewerker" % middel_id)
        return middel

    def _materiaal(self, middel_id: Any) -> Materiaal:
        middel = self._middel(middel_id)
        if not isinstance(middel, Materiaal):
            raise AgendaFout("%s is geen materiaal" % middel_id)
        return middel

    def _vrije_dagnummers(self, materiaal: Materiaal,
                          boekingen: Iterable[Boeking]) -> List[Tuple[int, int]]:
        """Vrije dagen als half-open reeksen dagnummers (ordinals)."""
        beschikbaar = [(van.toordinal(), tot.toordinal() + 1) for van, tot in materiaal.beschikbaar]
        bezet = [(b.start.toordinal(), b.einde.toordinal() + 1)
                 for b in boekingen if b.middel_id == materiaal.id]
        return aftrekken(beschikbaar, bezet)

    def _lokaal(self, dag: date, tijd: time) -> int:
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

    def _controleer(self, boeking: Any, bestaand: Iterable[Boeking],
                    controleer_id: bool = True) -> None:
        if not isinstance(boeking, Boeking):
            raise AgendaFout("een boeking moet een Boeking zijn")
        middel = self._middel(boeking.middel_id)
        bestaand = list(bestaand)
        if isinstance(middel, Materiaal):
            if isinstance(boeking.start, datetime):
                raise AgendaFout("materiaal wordt met dates geboekt")
            if controleer_id and any(b.id == boeking.id for b in bestaand):
                raise AgendaFout("dubbele boeking-id: %s" % boeking.id)
            dagen = (boeking.start.toordinal(), boeking.einde.toordinal() + 1)
            if not any(a <= dagen[0] and dagen[1] <= b
                       for a, b in self._vrije_dagnummers(middel, ())):
                raise BuitenBeschikbaarheid("de boeking valt buiten de beschikbaarheid")
            for andere in bestaand:
                if andere.middel_id == boeking.middel_id and overlap(
                        dagen, (andere.start.toordinal(), andere.einde.toordinal() + 1)):
                    raise DubbeleBoeking("de boeking overlapt boeking %s" % andere.id)
            return
        medewerker = middel
        if not isinstance(boeking.start, datetime):
            raise AgendaFout("een medewerker wordt met datetimes geboekt")
        controleer_binnen_een_dag(boeking, self._tz)
        if controleer_id and any(b.id == boeking.id for b in bestaand):
            raise AgendaFout("dubbele boeking-id: %s" % boeking.id)
        interval = (_utc(boeking.start), _utc(boeking.einde))
        try:
            dag = boeking.start.astimezone(self._zone).date()
        except OverflowError:
            raise AgendaFout("tijdstip ligt te dicht bij de grens van datetime") from None
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

    def is_vrij(self, middel_id: str, start: Union[datetime, date],
                einde: Union[datetime, date]) -> bool:
        """Is [start, einde) (medewerker) of start t/m einde (materiaal) boekbaar? Buiten de beschikbaarheid is False, geen fout."""
        boeking = Boeking("_vraag", middel_id, start, einde)
        try:
            self._controleer(boeking, self._boekingen, controleer_id=False)
        except (BuitenBeschikbaarheid, DubbeleBoeking):
            return False
        return True

    def vrije_dagen(self, middel_id: str, van: date, tot: date) -> List[date]:
        """Vrije dagen van materiaal binnen [van, tot], beide inclusief, oplopend."""
        materiaal = self._materiaal(middel_id)
        van = _dag(van, "van")
        tot = _dag(tot, "tot")
        if tot < van:
            raise AgendaFout("tot mag niet voor van liggen")
        begin, eind = van.toordinal(), tot.toordinal() + 1
        return [date.fromordinal(n)
                for a, b in self._vrije_dagnummers(materiaal, self._boekingen)
                for n in range(max(a, begin), min(b, eind))]

    def vrije_tijden(self, middel_id: str, dag: date, duur_minuten: int,
                     stap_minuten: int = 15) -> List[datetime]:
        """Starttijden (aware, oplopend) waarop duur_minuten volledig vrij is."""
        medewerker = self._medewerker(middel_id)
        duur = _minuten(duur_minuten, "duur_minuten") * _MINUUT
        stap = _minuten(stap_minuten, "stap_minuten") * _MINUUT
        if not isinstance(dag, date) or isinstance(dag, datetime):
            raise AgendaFout("dag moet een date zijn")
        starts = set()
        for (begin, eind), vrij in self._vrij_per_vak(medewerker, dag, self._boekingen):
            moment = begin
            while moment + duur <= eind:
                if any(a <= moment and moment + duur <= b for a, b in vrij):
                    starts.add(moment)
                moment += stap
        return [_datetime(s, self._zone) for s in sorted(starts)]
