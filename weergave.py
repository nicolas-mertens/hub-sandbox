from prijzen import BTW_TARIEVEN, btw_bedrag, met_btw


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
