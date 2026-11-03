import unittest
from datetime import date, datetime, time, timezone

from agenda.agenda import Agenda
from agenda.fouten import AgendaFout, BuitenBeschikbaarheid, DubbeleBoeking
from agenda.modellen import Boeking, Materiaal, Medewerker

UTC = timezone.utc


def juni(dag):
    return date(2027, 6, dag)


def truck(beschikbaar=None, **kw):
    if beschikbaar is None:
        beschikbaar = [(juni(1), juni(30))]
    return Materiaal(kw.pop("id", "t1"), "Foodtruck", beschikbaar)


def agenda(*boekingen, **kw):
    return Agenda([truck(**kw)], boekingen)


class BezettingTest(unittest.TestCase):
    def test_meerdaagse_boeking_bezet_drie_dagen(self):
        a = agenda(Boeking("b1", "t1", juni(5), juni(7)))
        self.assertEqual(a.vrije_dagen("t1", juni(3), juni(9)),
                         [juni(3), juni(4), juni(8), juni(9)])
        self.assertTrue(a.is_vrij("t1", juni(4), juni(4)))
        self.assertTrue(a.is_vrij("t1", juni(8), juni(8)))
        for dag in (5, 6, 7):
            self.assertFalse(a.is_vrij("t1", juni(dag), juni(dag)))

    def test_eendaagse_boeking_bezet_een_dag(self):
        a = agenda(Boeking("b1", "t1", juni(5), juni(5)))
        self.assertEqual(a.vrije_dagen("t1", juni(4), juni(6)), [juni(4), juni(6)])

    def test_aansluitende_boekingen_slagen(self):
        a = agenda(Boeking("b1", "t1", juni(5), juni(7)))
        a2 = a.boek(Boeking("b2", "t1", juni(8), juni(9)))
        self.assertEqual(a2.vrije_dagen("t1", juni(4), juni(10)), [juni(4), juni(10)])
        self.assertEqual(len(a.boekingen), 1)

    def test_overlap_geeft_dubbele_boeking(self):
        a = agenda(Boeking("b1", "t1", juni(5), juni(7)))
        for start, einde in ((juni(7), juni(8)), (juni(4), juni(5)), (juni(6), juni(6)),
                             (juni(1), juni(30))):
            with self.assertRaises(DubbeleBoeking):
                a.boek(Boeking("b2", "t1", start, einde))
            self.assertFalse(a.is_vrij("t1", start, einde))

    def test_buiten_beschikbaar(self):
        a = agenda(beschikbaar=[(juni(10), juni(12)), (juni(14), juni(15))])
        for start, einde in ((juni(9), juni(10)), (juni(12), juni(14)), (juni(15), juni(16))):
            with self.assertRaises(BuitenBeschikbaarheid):
                a.boek(Boeking("b", "t1", start, einde))
            self.assertFalse(a.is_vrij("t1", start, einde))
        self.assertTrue(a.is_vrij("t1", juni(10), juni(12)))

    def test_aansluitende_beschikbaarheid_wordt_samengevoegd(self):
        a = agenda(beschikbaar=[(juni(10), juni(12)), (juni(13), juni(15))])
        self.assertTrue(a.is_vrij("t1", juni(11), juni(14)))


class VrijeDagenTest(unittest.TestCase):
    def test_inclusief_en_buiten_beschikbaar_weggelaten(self):
        a = agenda(beschikbaar=[(juni(10), juni(12)), (juni(11), juni(13))])
        self.assertEqual(a.vrije_dagen("t1", juni(9), juni(14)),
                         [juni(10), juni(11), juni(12), juni(13)])
        self.assertEqual(a.vrije_dagen("t1", juni(12), juni(12)), [juni(12)])
        self.assertEqual(a.vrije_dagen("t1", juni(1), juni(9)), [])

    def test_van_na_tot(self):
        with self.assertRaises(AgendaFout):
            agenda().vrije_dagen("t1", juni(5), juni(4))

    def test_lege_beschikbaar(self):
        a = Agenda([Materiaal("t1", "x", [])])
        self.assertEqual(a.vrije_dagen("t1", juni(1), juni(30)), [])
        self.assertFalse(a.is_vrij("t1", juni(1), juni(1)))

    def test_ongeldige_argumenten(self):
        a = agenda()
        nu = datetime(2027, 6, 5, tzinfo=UTC)
        for van, tot in ((nu, juni(6)), (juni(5), nu), (None, juni(6)), ("2027-06-05", juni(6))):
            with self.assertRaises(AgendaFout):
                a.vrije_dagen("t1", van, tot)

    def test_grensdatums(self):
        a = Agenda([Materiaal("t1", "x", [(date.min, date.max)])])
        self.assertEqual(a.vrije_dagen("t1", date.max, date.max), [date.max])
        self.assertEqual(a.vrije_dagen("t1", date.min, date.min), [date.min])
        self.assertTrue(a.is_vrij("t1", date.min, date.max))

    def test_lijst_zonder_dubbelen_oplopend(self):
        a = agenda(Boeking("b2", "t1", juni(20), juni(21)), Boeking("b1", "t1", juni(5), juni(7)))
        dagen = a.vrije_dagen("t1", juni(1), juni(30))
        self.assertEqual(dagen, sorted(set(dagen)))
        self.assertEqual(len(dagen), 30 - 5)


class FoutenTest(unittest.TestCase):
    def test_datetime_in_plaats_van_date(self):
        nu = datetime(2027, 6, 5, 10, tzinfo=UTC)
        with self.assertRaises(AgendaFout):
            Agenda([truck()], [Boeking("b", "t1", nu, nu.replace(hour=11))])
        with self.assertRaises(AgendaFout):
            agenda().boek(Boeking("b", "t1", nu, nu.replace(hour=11)))
        with self.assertRaises(AgendaFout):
            agenda().is_vrij("t1", nu, nu.replace(hour=11))
        with self.assertRaises(AgendaFout):
            agenda().is_vrij("t1", datetime(2027, 6, 5), datetime(2027, 6, 6))

    def test_date_bij_medewerker(self):
        m = Medewerker("m1", "An", {0: [(time(9), time(12))]})
        with self.assertRaises(AgendaFout):
            Agenda([m], [Boeking("b", "m1", juni(7), juni(7))])
        with self.assertRaises(AgendaFout):
            Agenda([m]).is_vrij("m1", juni(7), juni(7))

    def test_einde_voor_start(self):
        with self.assertRaises(AgendaFout):
            Boeking("b", "t1", juni(6), juni(5))
        with self.assertRaises(AgendaFout):
            agenda().is_vrij("t1", juni(6), juni(5))

    def test_verkeerd_middeltype(self):
        m = Medewerker("m1", "An", {0: [(time(9), time(12))]})
        a = Agenda([m, truck()])
        with self.assertRaises(AgendaFout):
            a.vrije_dagen("m1", juni(1), juni(2))
        with self.assertRaises(AgendaFout):
            a.vrije_tijden("t1", juni(7), 30)
        with self.assertRaises(AgendaFout):
            a.vrije_dagen("onbekend", juni(1), juni(2))

    def test_gecombineerd_geval_zelfde_uitzondering(self):
        # dubbele id, overlap en buiten beschikbaarheid tegelijk
        basis = Boeking("b1", "t1", juni(5), juni(7))
        slecht = Boeking("b1", "t1", juni(6), date(2027, 7, 2))
        with self.assertRaises(AgendaFout) as c1:
            Agenda([truck()], [basis, slecht])
        with self.assertRaises(AgendaFout) as c2:
            agenda(basis).boek(slecht)
        self.assertIs(type(c1.exception), type(c2.exception))

    def test_constructor_weigert_zoals_boek(self):
        b = Boeking("b1", "t1", juni(5), juni(7))
        with self.assertRaises(DubbeleBoeking):
            Agenda([truck()], [b, Boeking("b2", "t1", juni(7), juni(8))])
        with self.assertRaises(BuitenBeschikbaarheid):
            Agenda([truck()], [Boeking("b", "t1", date(2027, 7, 1), date(2027, 7, 2))])
        with self.assertRaises(AgendaFout):
            Agenda([truck()], [Boeking("b", "x", juni(5), juni(5))])

    def test_mislukte_boek_laat_agenda_gelijk(self):
        a = agenda(Boeking("b1", "t1", juni(5), juni(7)))
        voor = a.vrije_dagen("t1", juni(1), juni(30))
        with self.assertRaises(DubbeleBoeking):
            a.boek(Boeking("b2", "t1", juni(6), juni(8)))
        self.assertEqual(a.vrije_dagen("t1", juni(1), juni(30)), voor)

    def test_is_vrij_met_boeking_id_vraag(self):
        a = agenda(Boeking("_vraag", "t1", juni(5), juni(7)))
        self.assertTrue(a.is_vrij("t1", juni(8), juni(8)))

    def test_dubbele_middel_id(self):
        with self.assertRaises(AgendaFout):
            Agenda([truck(), truck()])


class GemengdTest(unittest.TestCase):
    def test_middelen_beinvloeden_elkaar_niet(self):
        a = Agenda([truck(id="t1"), truck(id="t2")], [Boeking("b1", "t1", juni(5), juni(7))])
        self.assertEqual(len(a.vrije_dagen("t2", juni(1), juni(30))), 30)


if __name__ == "__main__":
    unittest.main()
