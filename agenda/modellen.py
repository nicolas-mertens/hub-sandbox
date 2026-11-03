"""Modellen van de agendamodule: onveranderlijk en volledig gevalideerd.

Elke ongeldige invoer geeft AgendaFout, nooit een toevallige TypeError of
ValueError. Collecties worden diep gekopieerd naar tuples of MappingProxyType.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from types import MappingProxyType
from typing import Any, List, Tuple
from zoneinfo import ZoneInfo

from agenda.fouten import AgendaFout


def _tekst(waarde: Any, veld: str) -> str:
    if not isinstance(waarde, str):
        raise AgendaFout("%s moet een str zijn" % veld)
    return waarde


def _aware(waarde: Any, veld: str) -> datetime:
    if not isinstance(waarde, datetime):
        raise AgendaFout("%s moet een datetime zijn" % veld)
    if waarde.tzinfo is None or waarde.utcoffset() is None:
        raise AgendaFout("%s moet een aware datetime zijn" % veld)
    return waarde


def _einde_na_start(start: datetime, einde: datetime) -> bool:
    # Bij dezelfde ZoneInfo vergelijkt Python kloktijden zonder fold; reken in UTC.
    return einde.astimezone(timezone.utc) > start.astimezone(timezone.utc)


def _dag(waarde: Any, veld: str) -> date:
    if not isinstance(waarde, date) or isinstance(waarde, datetime):
        raise AgendaFout("%s moet een date zijn" % veld)
    return waarde


def _tijd(waarde: Any, veld: str) -> time:
    if not isinstance(waarde, time):
        raise AgendaFout("%s moet een time zijn" % veld)
    if waarde.tzinfo is not None:
        raise AgendaFout("%s moet een naïeve time zijn" % veld)
    return waarde


def _reeks(waarde: Any, veld: str) -> List[Any]:
    if isinstance(waarde, (str, bytes, dict, MappingProxyType)):
        raise AgendaFout("%s moet een reeks zijn" % veld)
    try:
        return list(waarde)
    except TypeError:
        raise AgendaFout("%s moet een reeks zijn" % veld) from None


def _paar(waarde: Any, veld: str) -> Tuple[Any, Any]:
    paar = _reeks(waarde, veld)
    if len(paar) != 2:
        raise AgendaFout("%s moet uit twee waarden bestaan" % veld)
    return paar[0], paar[1]


def _tijdvakken(waarde: Any, veld: str) -> Tuple[Tuple[time, time], ...]:
    vakken = []
    for item in _reeks(waarde, veld):
        start, einde = _paar(item, veld)
        start = _tijd(start, veld + " start")
        einde = _tijd(einde, veld + " einde")
        if start >= einde:
            raise AgendaFout("%s: start moet voor einde liggen" % veld)
        vakken.append((start, einde))
    vakken.sort()
    for vorig, volgend in zip(vakken, vakken[1:]):
        if volgend[0] < vorig[1]:
            raise AgendaFout("%s: tijdvakken overlappen" % veld)
    return tuple(vakken)


def _per_weekdag(waarde: Any, veld: str) -> MappingProxyType:
    if isinstance(waarde, tuple) and not waarde:
        waarde = {}  # de standaardwaarde ()
    if not hasattr(waarde, "items"):
        raise AgendaFout("%s moet een mapping zijn" % veld)
    resultaat = {}
    for dag, vakken in waarde.items():
        if isinstance(dag, bool) or not isinstance(dag, int) or not 0 <= dag <= 6:
            raise AgendaFout("%s: weekdag moet een int van 0 tot en met 6 zijn" % veld)
        resultaat[dag] = _tijdvakken(vakken, "%s[%d]" % (veld, dag))
    return MappingProxyType(resultaat)


def _vast(zelf: Any, veld: str, waarde: Any) -> None:
    object.__setattr__(zelf, veld, waarde)


@dataclass(frozen=True)
class Medewerker:
    id: str
    naam: str
    werktijden: Any
    pauzes: Any = ()
    afwezig: Any = ()

    def __post_init__(self) -> None:
        _tekst(self.id, "id")
        _tekst(self.naam, "naam")
        _vast(self, "werktijden", _per_weekdag(self.werktijden, "werktijden"))
        _vast(self, "pauzes", _per_weekdag(self.pauzes, "pauzes"))
        afwezig = []
        for item in _reeks(self.afwezig, "afwezig"):
            start, einde = _paar(item, "afwezig")
            start = _aware(start, "afwezig start")
            einde = _aware(einde, "afwezig einde")
            if not _einde_na_start(start, einde):
                raise AgendaFout("afwezig: einde moet na start liggen")
            afwezig.append((start, einde))
        _vast(self, "afwezig", tuple(afwezig))


@dataclass(frozen=True)
class Materiaal:
    id: str
    naam: str
    beschikbaar: Any

    def __post_init__(self) -> None:
        _tekst(self.id, "id")
        _tekst(self.naam, "naam")
        reeksen = []
        for item in _reeks(self.beschikbaar, "beschikbaar"):
            van, tot = _paar(item, "beschikbaar")
            van = _dag(van, "van")
            tot = _dag(tot, "tot")
            if tot < van:
                raise AgendaFout("beschikbaar: tot mag niet voor van liggen")
            reeksen.append((van, tot))
        _vast(self, "beschikbaar", tuple(reeksen))


@dataclass(frozen=True)
class Boeking:
    """Medewerker: aware datetimes, start < einde. Materiaal: dates, start <= einde."""

    id: str
    middel_id: str
    start: Any
    einde: Any

    def __post_init__(self) -> None:
        _tekst(self.id, "id")
        _tekst(self.middel_id, "middel_id")
        if isinstance(self.start, datetime) or isinstance(self.einde, datetime):
            start = _aware(self.start, "start")
            einde = _aware(self.einde, "einde")
            if not _einde_na_start(start, einde):
                raise AgendaFout("einde moet na start liggen")
        else:
            start = _dag(self.start, "start")
            einde = _dag(self.einde, "einde")
            if einde < start:
                raise AgendaFout("einde mag niet voor start liggen")


def _zone(naam: Any) -> ZoneInfo:
    if not isinstance(naam, str):
        raise AgendaFout("tz moet een str zijn")
    try:
        return ZoneInfo(naam)
    except Exception:
        raise AgendaFout("onbekende tijdzone: %s" % naam) from None


def controleer_binnen_een_dag(boeking: Boeking, tz: Any) -> None:
    """Weiger een datetime-boeking die niet op één lokale dag in tz ligt."""
    zone = _zone(tz)
    if not isinstance(boeking.start, datetime):
        return
    start = boeking.start.astimezone(zone)
    einde = boeking.einde.astimezone(zone)
    # einde is exclusief: een boeking tot precies middernacht valt nog op de startdag
    if (einde - timedelta(microseconds=1)).date() != start.date():
        raise AgendaFout("een boeking mag niet over middernacht lopen")
