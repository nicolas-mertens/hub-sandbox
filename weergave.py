from prijzen import BTW_TARIEVEN, btw_bedrag, contant_afronden, met_btw


def euro(bedrag_centen):
    """Toon een bedrag in centen in Belgische notatie: 123456 -> "€ 1.234,56"."""
    teken = "-" if bedrag_centen < 0 else ""
    euros, centen = divmod(abs(bedrag_centen), 100)
    duizendtallen = f"{euros:,}".replace(",", ".")
    return f"{teken}€ {duizendtallen},{centen:02d}"


def factuurregel(omschrijving, bedrag_centen, tarief="standaard"):
    """Eén factuurregel: omschrijving, bedrag, btw-percentage, btw-bedrag en totaal."""
    if not omschrijving or not omschrijving.strip():
        raise ValueError("omschrijving mag niet leeg zijn")
    btw = btw_bedrag(bedrag_centen, tarief)
    totaal = met_btw(bedrag_centen, tarief)
    return (
        f"{omschrijving}: {euro(bedrag_centen)} + {BTW_TARIEVEN[tarief]}% btw "
        f"{euro(btw)} = {euro(totaal)}"
    )


def factuurtotaal(regels):
    """Alle factuurregels onder elkaar, met een totaalregel incl. btw en het btw-deel."""
    regels = list(regels)
    if not regels:
        raise ValueError("een factuur heeft minstens één regel nodig")
    tekst = [factuurregel(*regel) for regel in regels]
    totaal = sum(met_btw(bedrag, tarief) for _, bedrag, tarief in regels)
    btw = sum(btw_bedrag(bedrag, tarief) for _, bedrag, tarief in regels)
    tekst.append(f"Totaal: {euro(totaal)} (waarvan btw {euro(btw)})")
    return "\n".join(tekst)


def factuurtotaal_contant(regels):
    """Het factuurtotaal, met daaronder het contant te betalen bedrag (afgerond op 5 cent)."""
    regels = list(regels)
    tekst = factuurtotaal(regels)
    totaal = sum(met_btw(bedrag, tarief) for _, bedrag, tarief in regels)
    return f"{tekst}\nContant te betalen: {euro(contant_afronden(totaal))}"
