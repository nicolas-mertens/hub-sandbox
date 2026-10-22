def euro(bedrag_centen):
    """Toon een bedrag in centen in Belgische notatie: 123456 -> "€ 1.234,56"."""
    teken = "-" if bedrag_centen < 0 else ""
    euros, centen = divmod(abs(bedrag_centen), 100)
    duizendtallen = f"{euros:,}".replace(",", ".")
    return f"{teken}€ {duizendtallen},{centen:02d}"
