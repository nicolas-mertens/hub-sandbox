"""Zuivere bewerkingen op half-open intervallen [start, einde).

Grenzen moeten onderling vergelijkbaar zijn; er wordt niet mee gerekend.
Elk interval moet start < einde hebben, anders volgt ValueError.
Reeksen mogen ongesorteerd zijn en worden nooit gewijzigd. Resultaten zijn
nieuwe lijsten van tuples, gesorteerd en zonder overlap of aansluiting.
Gebruik bij tijdzones UTC-grenzen om absolute tijdstippen te vergelijken.
"""

from typing import Iterable, List, Tuple, TypeVar


T = TypeVar("T")


def _controleer(interval: Tuple[T, T]) -> None:
    if not interval[0] < interval[1]:
        raise ValueError("een interval moet start < einde hebben")


def overlap(eerste: Tuple[T, T], tweede: Tuple[T, T]) -> bool:
    """Geef aan of twee intervallen overlappen; aansluiting telt niet mee."""
    _controleer(eerste)
    _controleer(tweede)
    return eerste[0] < tweede[1] and tweede[0] < eerste[1]


def samenvoegen(intervallen: Iterable[Tuple[T, T]]) -> List[Tuple[T, T]]:
    """Voeg overlappende en aansluitende intervallen samen."""
    gesorteerd = []
    for start, einde in intervallen:
        _controleer((start, einde))
        gesorteerd.append((start, einde))
    gesorteerd.sort(key=lambda interval: interval[0])
    resultaat = []
    for start, einde in gesorteerd:
        if not resultaat or resultaat[-1][1] < start:
            resultaat.append((start, einde))
        elif resultaat[-1][1] < einde:
            resultaat[-1] = (resultaat[-1][0], einde)
    return resultaat


def aftrekken(
    intervallen: Iterable[Tuple[T, T]],
    verwijderen: Iterable[Tuple[T, T]],
) -> List[Tuple[T, T]]:
    """Trek de vereniging van verwijderen af van de vereniging van intervallen.

    Ook één interval wordt als reeks aangeleverd, bijvoorbeeld [(1, 10)].
    Lege invoer levert een lege lijst op; leeg verwijderen normaliseert alleen.
    """
    basis = samenvoegen(intervallen)
    weg = samenvoegen(verwijderen)
    resultaat = []
    index = 0
    for start, einde in basis:
        while index < len(weg) and not start < weg[index][1]:
            index += 1
        while index < len(weg) and weg[index][0] < einde:
            weg_start, weg_einde = weg[index]
            if start < weg_start:
                resultaat.append((start, weg_start))
            if not weg_einde < einde:
                start = einde
                break
            start = weg_einde
            index += 1
        if start < einde:
            resultaat.append((start, einde))
    return resultaat
