"""Fouten van de agendamodule."""


class AgendaFout(Exception):
    """Basis van alle fouten uit de agendamodule."""


class DubbeleBoeking(AgendaFout):
    """Het tijdvak is al geboekt."""


class BuitenBeschikbaarheid(AgendaFout):
    """Het tijdvak valt buiten de beschikbaarheid."""
