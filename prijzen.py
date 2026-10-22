"""Klein oefenproject voor de AI Development Hub: prijsberekening met btw."""

BTW_TARIEVEN = {"standaard": 21, "verlaagd": 6, "nul": 0}


def _percentage(tarief: str) -> int:
    try:
        return BTW_TARIEVEN[tarief]
    except KeyError:
        geldig = ", ".join(f"'{t}'" for t in BTW_TARIEVEN)
        raise ValueError(f"onbekend btw-tarief '{tarief}'; geldige tarieven: {geldig}") from None


def met_btw(bedrag_centen: int, tarief: str = "standaard") -> int:
    """Bedrag inclusief btw, in hele centen, afgerond volgens de gewone regel."""
    if bedrag_centen < 0:
        raise ValueError("bedrag mag niet negatief zijn")
    pct = _percentage(tarief)
    return (bedrag_centen * (100 + pct) + 50) // 100


def zonder_btw(bedrag_centen: int, tarief: str = "standaard") -> int:
    """Bedrag exclusief btw, in hele centen, afgerond volgens de gewone regel."""
    if bedrag_centen < 0:
        raise ValueError("bedrag mag niet negatief zijn")
    deler = 100 + _percentage(tarief)
    return (bedrag_centen * 100 + deler // 2) // deler


def btw_bedrag(bedrag_centen: int, tarief: str = "standaard") -> int:
    """Btw-bedrag in hele centen; altijd bedrag + btw_bedrag == met_btw."""
    return met_btw(bedrag_centen, tarief) - bedrag_centen
