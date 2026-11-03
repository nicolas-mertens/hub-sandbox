import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from agenda.fouten import AgendaFout, BuitenBeschikbaarheid, DubbeleBoeking


class TijdzoneTest(unittest.TestCase):
    def test_brussel_laadt_met_zomer_en_wintertijd(self):
        zone = ZoneInfo("Europe/Brussels")
        winter = datetime(2026, 1, 15, 12, 0, tzinfo=zone)
        zomer = datetime(2026, 7, 15, 12, 0, tzinfo=zone)
        self.assertEqual(winter.utcoffset().total_seconds(), 3600)
        self.assertEqual(zomer.utcoffset().total_seconds(), 7200)


class FoutenTest(unittest.TestCase):
    def test_foutenhierarchie(self):
        self.assertTrue(issubclass(DubbeleBoeking, AgendaFout))
        self.assertTrue(issubclass(BuitenBeschikbaarheid, AgendaFout))
        with self.assertRaises(AgendaFout):
            raise DubbeleBoeking("al geboekt")
