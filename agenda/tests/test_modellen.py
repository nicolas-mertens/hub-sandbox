import unittest
from dataclasses import FrozenInstanceError
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from agenda.fouten import AgendaFout, BuitenBeschikbaarheid, DubbeleBoeking
from agenda.modellen import (
    Boeking,
    Materiaal,
    Medewerker,
    controleer_binnen_een_dag,
)

UTC = timezone.utc
BXL = ZoneInfo("Europe/Brussels")


def dt(uur, minuut=0, dag=1):
    return datetime(2027, 6, dag, uur, minuut, tzinfo=BXL)


def medewerker(**kw):
    args = dict(id="m1", naam="An", werktijden={0: [(time(9), time(12))]})
    args.update(kw)
    return Medewerker(**args)


class FoutenTest(unittest.TestCase):
    def test_hierarchie(self):
        self.assertTrue(issubclass(AgendaFout, Exception))
        self.assertTrue(issubclass(DubbeleBoeking, AgendaFout))
        self.assertTrue(issubclass(BuitenBeschikbaarheid, AgendaFout))


class MedewerkerTest(unittest.TestCase):
    def test_geldig(self):
        m = Medewerker(
            "m1",
            "An",
            {0: [(time(9), time(12)), (time(13), time(17))]},
            pauzes={0: [(time(10), time(10, 15))]},
            afwezig=[(dt(9), dt(10))],
        )
        self.assertEqual(len(m.werktijden[0]), 2)
        self.assertEqual(m.pauzes[0], ((time(10), time(10, 15)),))

    def test_aansluitende_tijdvakken_mogen(self):
        medewerker(werktijden={0: [(time(9), time(12)), (time(12), time(13))]})

    def test_lege_dag_en_geen_werktijden(self):
        medewerker(werktijden={})
        medewerker(werktijden={3: []})

    def test_ongeldig(self):
        gevallen = {
            "weekdag 7": dict(werktijden={7: [(time(9), time(10))]}),
            "weekdag ma": dict(werktijden={"ma": [(time(9), time(10))]}),
            "weekdag True": dict(werktijden={True: [(time(9), time(10))]}),
            "weekdag None": dict(werktijden={None: []}),
            "start na einde": dict(werktijden={0: [(time(10), time(9))]}),
            "start gelijk aan einde": dict(werktijden={0: [(time(9), time(9))]}),
            "overlap": dict(werktijden={0: [(time(9), time(12)), (time(11), time(13))]}),
            "datetime als time": dict(werktijden={0: [(dt(9), dt(10))]}),
            "aware time": dict(werktijden={0: [(time(9, tzinfo=UTC), time(10))]}),
            "str als time": dict(werktijden={0: [("09:00", "10:00")]}),
            "werktijden None": dict(werktijden=None),
            "werktijden lijst": dict(werktijden=[(time(9), time(10))]),
            "vakken None": dict(werktijden={0: None}),
            "vak str": dict(werktijden={0: "ab"}),
            "vak te kort": dict(werktijden={0: [(time(9),)]}),
            "vak str paar": dict(werktijden={0: ["ab"]}),
            "pauze overlap": dict(pauzes={0: [(time(9), time(10)), (time(9, 30), time(11))]}),
            "pauze weekdag 7": dict(pauzes={7: []}),
            "naieve afwezigheid": dict(afwezig=[(datetime(2027, 6, 1, 9), datetime(2027, 6, 1, 10))]),
            "afwezig einde gelijk": dict(afwezig=[(dt(9), dt(9))]),
            "afwezig einde voor start": dict(afwezig=[(dt(10), dt(9))]),
            "afwezig date": dict(afwezig=[(date(2027, 6, 1), date(2027, 6, 2))]),
            "afwezig None": dict(afwezig=None),
            "afwezig str": dict(afwezig="ab"),
            "id int": dict(id=1),
            "id None": dict(id=None),
            "naam int": dict(naam=5),
        }
        for naam, kw in gevallen.items():
            with self.subTest(naam):
                with self.assertRaises(AgendaFout):
                    medewerker(**kw)

    def test_diepe_kopie(self):
        vakken = [(time(9), time(12))]
        werk = {0: vakken}
        pauze_vakken = [(time(10), time(11))]
        pauzes = {0: pauze_vakken}
        afwezig = [(dt(9), dt(10))]
        m = medewerker(werktijden=werk, pauzes=pauzes, afwezig=afwezig)
        vakken.append((time(13), time(14)))
        werk[1] = [(time(9), time(10))]
        pauze_vakken.clear()
        pauzes[2] = []
        afwezig.clear()
        self.assertEqual(m.werktijden[0], ((time(9), time(12)),))
        self.assertNotIn(1, m.werktijden)
        self.assertEqual(m.pauzes[0], ((time(10), time(11)),))
        self.assertNotIn(2, m.pauzes)
        self.assertEqual(len(m.afwezig), 1)

    def test_alleen_lezen(self):
        m = medewerker()
        with self.assertRaises(FrozenInstanceError):
            m.naam = "x"
        with self.assertRaises(FrozenInstanceError):
            m.werktijden = {}
        with self.assertRaises(TypeError):
            m.werktijden[1] = ()
        with self.assertRaises(TypeError):
            del m.werktijden[0]
        with self.assertRaises(TypeError):
            m.pauzes[0] = ()
        with self.assertRaises(AttributeError):
            m.werktijden[0].append((time(1), time(2)))
        with self.assertRaises(AttributeError):
            m.afwezig.append(1)


class MateriaalTest(unittest.TestCase):
    def test_geldig(self):
        m = Materiaal("t1", "Foodtruck", [(date(2027, 6, 1), date(2027, 6, 30))])
        self.assertEqual(m.beschikbaar, ((date(2027, 6, 1), date(2027, 6, 30)),))

    def test_eendaags_en_leeg(self):
        Materiaal("t1", "x", [(date(2027, 6, 1), date(2027, 6, 1))])
        self.assertEqual(Materiaal("t1", "x", []).beschikbaar, ())

    def test_ongeldig(self):
        d1, d2 = date(2027, 6, 1), date(2027, 6, 2)
        gevallen = {
            "tot voor van": [(d2, d1)],
            "datetime": [(datetime(2027, 6, 1), datetime(2027, 6, 2))],
            "datetime tot": [(d1, datetime(2027, 6, 2))],
            "str": [("2027-06-01", "2027-06-02")],
            "None": [(None, d2)],
            "geen reeks": None,
            "str reeks": "ab",
            "te kort": [(d1,)],
            "geen paar": [d1],
        }
        for naam, beschikbaar in gevallen.items():
            with self.subTest(naam):
                with self.assertRaises(AgendaFout):
                    Materiaal("t1", "x", beschikbaar)
        with self.assertRaises(AgendaFout):
            Materiaal(1, "x", [])
        with self.assertRaises(AgendaFout):
            Materiaal("t1", None, [])

    def test_kopie_en_alleen_lezen(self):
        lijst = [(date(2027, 6, 1), date(2027, 6, 2))]
        m = Materiaal("t1", "x", lijst)
        lijst.append((date(2027, 7, 1), date(2027, 7, 2)))
        self.assertEqual(len(m.beschikbaar), 1)
        with self.assertRaises(FrozenInstanceError):
            m.beschikbaar = ()
        with self.assertRaises(AttributeError):
            m.beschikbaar.append(1)


class BoekingTest(unittest.TestCase):
    def test_geldig_medewerker(self):
        b = Boeking("b1", "m1", dt(9), dt(10))
        self.assertEqual(b.start, dt(9))

    def test_geldig_andere_zone(self):
        Boeking("b1", "m1", datetime(2027, 6, 1, 7, tzinfo=UTC), dt(10))

    def test_geldig_materiaal(self):
        Boeking("b1", "t1", date(2027, 6, 5), date(2027, 6, 7))
        Boeking("b2", "t1", date(2027, 6, 5), date(2027, 6, 5))

    def test_ongeldig(self):
        d = date(2027, 6, 5)
        naief = datetime(2027, 6, 1, 9)
        gevallen = {
            "naief": ("b", "m", naief, dt(10)),
            "naief einde": ("b", "m", dt(9), naief),
            "einde gelijk": ("b", "m", dt(9), dt(9)),
            "omgekeerd": ("b", "m", dt(10), dt(9)),
            "date waar datetime": ("b", "m", d, dt(10)),
            "datetime waar date": ("b", "m", dt(9), d),
            "naieve datetimes": ("b", "m", naief, naief),
            "str": ("b", "m", "09:00", "10:00"),
            "None": ("b", "m", None, None),
            "None en datetime": ("b", "m", None, dt(10)),
            "materiaal omgekeerd": ("b", "m", date(2027, 6, 7), date(2027, 6, 5)),
            "id int": (1, "m", dt(9), dt(10)),
            "middel_id None": ("b", None, dt(9), dt(10)),
            "middel_id int": ("b", 5, dt(9), dt(10)),
        }
        for naam, args in gevallen.items():
            with self.subTest(naam):
                with self.assertRaises(AgendaFout):
                    Boeking(*args)

    def test_alleen_lezen(self):
        b = Boeking("b1", "m1", dt(9), dt(10))
        with self.assertRaises(FrozenInstanceError):
            b.start = dt(8)


class MiddernachtTest(unittest.TestCase):
    def test_zelfde_dag_mag(self):
        controleer_binnen_een_dag(Boeking("b", "m", dt(9), dt(10)), "Europe/Brussels")
        controleer_binnen_een_dag(Boeking("b", "m", dt(23), dt(23) + timedelta(hours=1)), "Europe/Brussels")

    def test_over_middernacht(self):
        b = Boeking("b", "m", dt(23), dt(1, dag=2))
        with self.assertRaises(AgendaFout):
            controleer_binnen_een_dag(b, "Europe/Brussels")

    def test_andere_zone_telt_lokale_dag(self):
        # 22:30-23:30 UTC is 00:30-01:30 lokaal op 2 juni: dezelfde lokale dag
        b = Boeking("b", "m", datetime(2027, 6, 1, 22, 30, tzinfo=UTC), datetime(2027, 6, 1, 23, 30, tzinfo=UTC))
        controleer_binnen_een_dag(b, "Europe/Brussels")
        # 21:30-22:30 UTC is 23:30-00:30 lokaal: over middernacht
        b = Boeking("b", "m", datetime(2027, 6, 1, 21, 30, tzinfo=UTC), datetime(2027, 6, 1, 22, 30, tzinfo=UTC))
        with self.assertRaises(AgendaFout):
            controleer_binnen_een_dag(b, "Europe/Brussels")

    def test_onbekende_zone_en_materiaal(self):
        with self.assertRaises(AgendaFout):
            controleer_binnen_een_dag(Boeking("b", "m", dt(9), dt(10)), "Nergens/Niets")
        with self.assertRaises(AgendaFout):
            controleer_binnen_een_dag(Boeking("b", "m", dt(9), dt(10)), None)
        controleer_binnen_een_dag(Boeking("b", "t", date(2027, 6, 5), date(2027, 6, 7)), "Europe/Brussels")


class FoldVolgordeTest(unittest.TestCase):
    """Dezelfde ZoneInfo: Python vergelijkt dan kloktijden zonder fold; vergelijk als absolute tijd."""

    # 31 oktober 2027, Brussel: 02:15 komt twee keer voor (fold=0 CEST, fold=1 CET)
    EERSTE = datetime(2027, 10, 31, 2, 15, tzinfo=BXL)
    TWEEDE = datetime(2027, 10, 31, 2, 15, fold=1, tzinfo=BXL)
    LATER = datetime(2027, 10, 31, 2, 45, tzinfo=BXL)  # fold=0: ligt vóór TWEEDE

    def test_boeking_omgekeerd_wordt_geweigerd(self):
        with self.assertRaises(AgendaFout):
            Boeking("b", "m", self.TWEEDE, self.LATER)

    def test_boeking_over_herfstovergang_is_geldig(self):
        Boeking("b", "m", self.LATER, self.TWEEDE)

    def test_afwezig_omgekeerd_wordt_geweigerd(self):
        with self.assertRaises(AgendaFout):
            medewerker(afwezig=[(self.TWEEDE, self.LATER)])

    def test_afwezig_over_herfstovergang_is_geldig(self):
        medewerker(afwezig=[(self.LATER, self.TWEEDE)])


if __name__ == "__main__":
    unittest.main()
