"""Klein oefenproject voor de AI Development Hub: prijsberekening met btw."""

BTW_TARIEVEN = {"standaard": 21, "verlaagd": 6, "nul": 0}


def met_btw(bedrag_centen: int, tarief: str = "standaard") -> int:
    """Bedrag inclusief btw, in hele centen, afgerond volgens de gewone regel."""
    if bedrag_centen < 0:
        raise ValueError("bedrag mag niet negatief zijn")
    pct = BTW_TARIEVEN[tarief]
    return (bedrag_centen * (100 + pct) + 50) // 100


def zonder_btw(bedrag_centen: int, tarief: str = "standaard") -> int:
    """Bedrag exclusief btw, in hele centen, afgerond volgens de gewone regel."""
    if bedrag_centen < 0:
        raise ValueError("bedrag mag niet negatief zijn")
    deler = 100 + BTW_TARIEVEN[tarief]
    return (bedrag_centen * 100 + deler // 2) // deler
