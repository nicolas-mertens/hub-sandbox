import unittest
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from agenda.agenda import Agenda
from agenda.fouten import AgendaFout, BuitenBeschikbaarheid, DubbeleBoeking
from agenda.modellen import Boeking, Medewerker

UTC = timezone.utc
BXL = ZoneInfo("Europe/Brussels")
MAANDAG = date(2027, 6, 7)
LENTE = date(2027, 3, 28)
HERFST = date(2027, 10, 31)


def dt(uur, minuut=0, dag=MAANDAG):
    return datetime(dag.year, dag.month, dag.day, uur, minuut, tzinfo=BXL)


def dagwerk(**kw):
    args = dict(
        id="m1", naam="An",
        werktijden={0: [(time(9), time(12)), (time(13), time(17))]},
        pauzes={0: [(time(10), time(10, 15))]},
    )
    args.update(kw)
    return Medewerker(**args)


def uren(lijst):
    return [(t.hour, t.minute) for t in lijst]


class ConstructorTest(unittest.TestCase):
    def test_onbekende_tz(self):
        with self.assertRaises(AgendaFout):
            Agenda([dagwerk()], tz="Mars/Olympus")

    def test_onbekend_middel(self):
        with self.assertRaises(AgendaFout):
            Agenda([dagwerk()], [Boeking("b", "x", dt(9), dt(10))])

    def test_dubbele_middel_id(self):
        with self.assertRaises(AgendaFout):
            Agenda([dagwerk(), dagwerk()])

    def test_dubbele_boeking_id(self):
        with self.assertRaises(AgendaFout):
            Agenda([dagwerk()], [Boeking("b", "m1", dt(9), dt(9, 30)),
                                 Boeking("b", "m1", dt(11), dt(11, 30))])

    def test_overlap(self):
        with self.assertRaises(DubbeleBoeking):
            Agenda([dagwerk()], [Boeking("a", "m1", dt(9), dt(9, 30)),
                                 Boeking("b", "m1", dt(9, 29), dt(10))])

    def test_buiten_beschikbaarheid(self):
        with self.assertRaises(BuitenBeschikbaarheid):
            Agenda([dagwerk()], [Boeking("a", "m1", dt(7), dt(8))])

    def test_over_pauze_heen(self):
        with self.assertRaises(BuitenBeschikbaarheid):
            Agenda([dagwerk()]).boek(Boeking("a", "m1", dt(9, 45), dt(10, 30)))

    def test_over_middernacht(self):
        with self.assertRaises(AgendaFout):
            Agenda([dagwerk()]).boek(Boeking("a", "m1", dt(23), dt(23) + timedelta(hours=2)))

    def test_alleen_boeking_van_medewerker(self):
        with self.assertRaises(AgendaFout):
            Agenda([dagwerk()]).boek("boeking")
        with self.assertRaises(AgendaFout):
            Agenda([dagwerk()]).boek(Boeking("a", "m1", MAANDAG, MAANDAG))

    def test_alleen_lezen(self):
        agenda = Agenda([dagwerk()])
        with self.assertRaises(AttributeError):
            agenda.tz = "UTC"

    def test_lijst_wijzigen_heeft_geen_effect(self):
        boekingen = [Boeking("a", "m1", dt(9), dt(9, 30))]
        agenda = Agenda([dagwerk()], boekingen)
        boekingen.append(Boeking("b", "m1", dt(11), dt(11, 30)))
        self.assertEqual(len(agenda.boekingen), 1)


class BoekenTest(unittest.TestCase):
    def test_boek_geeft_nieuwe_agenda(self):
        oud = Agenda([dagwerk()], tz="Europe/Amsterdam")
        voor = oud.vrije_tijden("m1", MAANDAG, 30)
        nieuw = oud.boek(Boeking("a", "m1", dt(9), dt(9, 30)))
        self.assertEqual(oud.vrije_tijden("m1", MAANDAG, 30), voor)
        self.assertEqual(oud.boekingen, ())
        self.assertEqual(nieuw.tz, "Europe/Amsterdam")
        tweede = nieuw.boek(Boeking("b", "m1", dt(11), dt(11, 30)))
        self.assertEqual(len(tweede.boekingen), 2)
        self.assertEqual(len(nieuw.boekingen), 1)

    def test_is_vrij_met_boeking_id_vraag(self):
        agenda = Agenda([dagwerk()], [Boeking("_vraag", "m1", dt(9), dt(9, 30))])
        self.assertTrue(agenda.is_vrij("m1", dt(11), dt(11, 30)))
        self.assertFalse(agenda.is_vrij("m1", dt(9), dt(9, 30)))

    def test_mislukte_boek_laat_agenda_gelijk(self):
        agenda = Agenda([dagwerk()], [Boeking("a", "m1", dt(9), dt(9, 30))])
        voor = agenda.vrije_tijden("m1", MAANDAG, 30)
        for fout, boeking in [
            (DubbeleBoeking, Boeking("b", "m1", dt(9, 15), dt(9, 45))),
            (BuitenBeschikbaarheid, Boeking("c", "m1", dt(18), dt(19))),
            (AgendaFout, Boeking("d", "x", dt(9), dt(10))),
        ]:
            with self.assertRaises(fout):
                agenda.boek(boeking)
        self.assertEqual(agenda.vrije_tijden("m1", MAANDAG, 30), voor)
        self.assertEqual(len(agenda.boekingen), 1)

    def test_aansluitend_slaagt_en_een_minuut_overlap_niet(self):
        agenda = Agenda([dagwerk()]).boek(Boeking("a", "m1", dt(9), dt(9, 30)))
        agenda = agenda.boek(Boeking("b", "m1", dt(9, 30), dt(10)))
        agenda = agenda.boek(Boeking("e", "m1", dt(10, 15), dt(11)))
        with self.assertRaises(DubbeleBoeking):
            agenda.boek(Boeking("c", "m1", dt(10, 59), dt(11, 30)))
        with self.assertRaises(DubbeleBoeking):
            agenda.boek(Boeking("d", "m1", dt(9, 59), dt(10)))

    def test_andere_zone_botst(self):
        agenda = Agenda([dagwerk()]).boek(
            Boeking("a", "m1", datetime(2027, 6, 7, 7, 0, tzinfo=UTC),
                    datetime(2027, 6, 7, 7, 30, tzinfo=UTC)))  # 09:00-09:30 Brussel
        with self.assertRaises(DubbeleBoeking):
            agenda.boek(Boeking("b", "m1", dt(9, 15), dt(9, 45)))
        agenda.boek(Boeking("c", "m1", dt(9, 30), dt(10)))
        self.assertFalse(agenda.is_vrij("m1", dt(9), dt(9, 30)))
        self.assertTrue(agenda.is_vrij("m1", dt(9, 30), dt(10)))

    def test_is_vrij(self):
        agenda = Agenda([dagwerk()])
        self.assertTrue(agenda.is_vrij("m1", dt(9), dt(9, 30)))
        self.assertFalse(agenda.is_vrij("m1", dt(7), dt(8)))
        self.assertFalse(agenda.is_vrij("m1", dt(9, 45), dt(10, 30)))
        with self.assertRaises(AgendaFout):
            agenda.is_vrij("x", dt(9), dt(10))
        with self.assertRaises(AgendaFout):
            agenda.is_vrij("m1", dt(10), dt(9))
        with self.assertRaises(AgendaFout):
            agenda.is_vrij("m1", datetime(2027, 6, 7, 9), dt(10))


class VrijeTijdenTest(unittest.TestCase):
    def test_gewone_dag(self):
        verwacht = [
            (9, 0), (9, 15), (9, 30), (10, 15), (10, 30), (10, 45), (11, 0), (11, 15), (11, 30),
            (13, 0), (13, 15), (13, 30), (13, 45), (14, 0), (14, 15), (14, 30), (14, 45),
            (15, 0), (15, 15), (15, 30), (15, 45), (16, 0), (16, 15), (16, 30),
        ]
        resultaat = Agenda([dagwerk()]).vrije_tijden("m1", MAANDAG, 30, 15)
        self.assertEqual(uren(resultaat), verwacht)
        self.assertTrue(all(t.tzinfo is not None for t in resultaat))

    def test_raster_blijft_na_pauze(self):
        m = Medewerker("m1", "An", {0: [(time(9, 7), time(12, 7))]},
                       {0: [(time(10), time(10, 10))]})
        verwacht = [(9, 7), (9, 22), (10, 22), (10, 37), (10, 52), (11, 7), (11, 22), (11, 37)]
        self.assertEqual(uren(Agenda([m]).vrije_tijden("m1", MAANDAG, 30, 15)), verwacht)

    def test_boeking_schuift_raster_niet(self):
        m = dagwerk(werktijden={0: [(time(9), time(11))]}, pauzes={})
        agenda = Agenda([m], [Boeking("a", "m1", dt(9, 20), dt(9, 40))])
        self.assertEqual(uren(agenda.vrije_tijden("m1", MAANDAG, 30, 15)),
                         [(9, 45), (10, 0), (10, 15), (10, 30)])

    def test_volledig_bezet(self):
        m = dagwerk(werktijden={0: [(time(9), time(10))]}, pauzes={})
        agenda = Agenda([m], [Boeking("a", "m1", dt(9), dt(10))])
        self.assertEqual(agenda.vrije_tijden("m1", MAANDAG, 30), [])

    def test_afwezig_en_samengevoegd(self):
        afwezig = [(dt(9), dt(11)), (dt(10, 30), dt(12)), (dt(13), dt(17))]
        self.assertEqual(Agenda([dagwerk(afwezig=afwezig)]).vrije_tijden("m1", MAANDAG, 30), [])
        deels = dagwerk(afwezig=[(dt(9), dt(11)), (dt(10, 30), dt(11, 30))])
        self.assertEqual(uren(Agenda([deels]).vrije_tijden("m1", MAANDAG, 30))[:2],
                         [(11, 30), (13, 0)])

    def test_meerdere_pauzes(self):
        m = dagwerk(werktijden={0: [(time(9), time(12))]},
                    pauzes={0: [(time(10), time(10, 30)), (time(11), time(11, 30))]})
        self.assertEqual(uren(Agenda([m]).vrije_tijden("m1", MAANDAG, 30, 30)),
                         [(9, 0), (9, 30), (10, 30), (11, 30)])

    def test_geen_werkdag(self):
        self.assertEqual(Agenda([dagwerk()]).vrije_tijden("m1", date(2027, 6, 8), 30), [])

    def test_middelen_onafhankelijk(self):
        agenda = Agenda([dagwerk(), dagwerk(id="m2")])
        voor = agenda.vrije_tijden("m2", MAANDAG, 30)
        agenda = agenda.boek(Boeking("x", "m1", dt(9), dt(10)))
        self.assertEqual(agenda.vrije_tijden("m2", MAANDAG, 30), voor)
        self.assertNotEqual(agenda.vrije_tijden("m1", MAANDAG, 30), voor)

    def test_ongeldige_argumenten(self):
        agenda = Agenda([dagwerk()])
        for duur, stap in [(0, 15), (-5, 15), (True, 15), (30, 0), (30, -1), (30, True),
                           (30.0, 15), (30, "15")]:
            with self.assertRaises(AgendaFout):
                agenda.vrije_tijden("m1", MAANDAG, duur, stap)
        with self.assertRaises(AgendaFout):
            agenda.vrije_tijden("x", MAANDAG, 30)
        with self.assertRaises(AgendaFout):
            agenda.vrije_tijden("m1", datetime(2027, 6, 7), 30)


class ZomertijdTest(unittest.TestCase):
    def medewerker(self, dag):
        return Medewerker("m1", "An", {dag.weekday(): [(time(1), time(4))]})

    def test_lente(self):
        resultaat = Agenda([self.medewerker(LENTE)]).vrije_tijden("m1", LENTE, 60, 60)
        self.assertEqual(uren(resultaat), [(1, 0), (3, 0)])
        self.assertEqual([t.utcoffset() for t in resultaat],
                         [timedelta(hours=1), timedelta(hours=2)])

    def test_lente_werktijd_begint_in_het_gat(self):
        # 02:50 bestaat niet; fold=0 gebruikt de offset van vóór de overgang (+01:00): 03:50 CEST.
        m = Medewerker(id="m1", naam="An", werktijden={6: [(time(2, 50), time(4))]})
        resultaat = Agenda([m]).vrije_tijden("m1", LENTE, 10, 10)
        self.assertEqual(uren(resultaat), [(3, 50)])

    def test_lente_boeking_over_gat(self):
        agenda = Agenda([self.medewerker(LENTE)])
        start, einde = dt(1, 30, LENTE), dt(3, 30, LENTE)
        self.assertEqual(einde.astimezone(UTC) - start.astimezone(UTC), timedelta(hours=1))
        nieuw = agenda.boek(Boeking("a", "m1", start, einde))
        self.assertEqual(nieuw.vrije_tijden("m1", LENTE, 60, 60), [])
        self.assertEqual(uren(nieuw.vrije_tijden("m1", LENTE, 30, 30)), [(1, 0), (3, 30)])

    def test_herfst(self):
        resultaat = Agenda([self.medewerker(HERFST)]).vrije_tijden("m1", HERFST, 60, 60)
        self.assertEqual(len(resultaat), 4)
        self.assertEqual(uren(resultaat), [(1, 0), (2, 0), (2, 0), (3, 0)])
        self.assertEqual([t.fold for t in resultaat], [0, 0, 1, 0])
        self.assertEqual([t.utcoffset() for t in resultaat],
                         [timedelta(hours=2), timedelta(hours=2),
                          timedelta(hours=1), timedelta(hours=1)])
        utc = [t.astimezone(UTC) for t in resultaat]
        self.assertEqual(utc, sorted(set(utc)))

    def test_herfst_tweede_voorkomen_boeken(self):
        agenda = Agenda([self.medewerker(HERFST)])
        tweede = agenda.vrije_tijden("m1", HERFST, 60, 60)[2]
        nieuw = agenda.boek(Boeking("a", "m1", tweede, tweede + timedelta(hours=1)))
        self.assertEqual(len(nieuw.vrije_tijden("m1", HERFST, 60, 60)), 3)


class EigenschapTest(unittest.TestCase):
    def test_aangeboden_start_is_boekbaar(self):
        nacht = Medewerker("m1", "An", {6: [(time(1), time(4))]})
        scenarios = [
            (MAANDAG, dagwerk(), 30, 15),
            (MAANDAG, dagwerk(), 45, 20),
            (MAANDAG, Medewerker("m1", "An", {0: [(time(9, 7), time(12, 7))]},
                                 {0: [(time(10), time(10, 10))]}), 30, 15),
            (LENTE, nacht, 60, 60),
            (LENTE, nacht, 30, 7),
            (LENTE, Medewerker("m1", "An", {6: [(time(2), time(3, 30))]}), 15, 15),
            (HERFST, nacht, 60, 60),
            (HERFST, nacht, 90, 30),
            (HERFST, Medewerker("m1", "An", {6: [(time(0), time(23))]},
                                {6: [(time(2, 30), time(2, 45))]}), 20, 25),
        ]
        for dag, m, duur, stap in scenarios:
            agenda = Agenda([m])
            tijden = agenda.vrije_tijden("m1", dag, duur, stap)
            self.assertTrue(tijden, (dag, duur, stap))
            for start in tijden:
                einde = (start.astimezone(UTC) + timedelta(minutes=duur)).astimezone(BXL)
                nieuw = agenda.boek(Boeking("a", "m1", start, einde))
                self.assertEqual(len(nieuw.boekingen), 1)
                self.assertTrue(agenda.is_vrij("m1", start, einde))


if __name__ == "__main__":
    unittest.main()


class GrensDatumAgendaTest(unittest.TestCase):
    """Grensdatums geven een AgendaFout of een gewoon antwoord, nooit een OverflowError."""

    PLUS = timezone(timedelta(hours=1))
    MIN = timezone(timedelta(hours=-1))

    def gevallen(self):
        yield datetime(1, 1, 1, 0, 10, tzinfo=self.PLUS), datetime(1, 1, 1, 0, 20, tzinfo=self.PLUS)
        yield (datetime(9999, 12, 31, 23, 40, tzinfo=self.MIN),
               datetime(9999, 12, 31, 23, 50, tzinfo=self.MIN))

    def agenda(self, **kw):
        return Agenda([dagwerk()], **kw)

    def antwoord(self, functie):
        try:
            return functie()
        except AgendaFout:
            return None

    def test_boek(self):
        for start, einde in self.gevallen():
            with self.subTest(start=start):
                with self.assertRaises(AgendaFout):  # buiten werktijd, geen OverflowError
                    self.agenda().boek(Boeking("b", "m1", start, einde))

    def test_is_vrij(self):
        for start, einde in self.gevallen():
            with self.subTest(start=start):
                self.assertIn(self.antwoord(lambda: self.agenda().is_vrij("m1", start, einde)), (None, False))

    def test_constructor(self):
        for start, einde in self.gevallen():
            with self.subTest(start=start):
                with self.assertRaises(AgendaFout):
                    Agenda([dagwerk()], [Boeking("b", "m1", start, einde)])

    def test_afwezig_op_grensdag(self):
        for start, einde in self.gevallen():
            with self.subTest(start=start):
                m = dagwerk(werktijden={d: [(time(0), time(23, 30))] for d in range(7)},
                            afwezig=[(start, einde)])
                agenda = Agenda([m])
                self.antwoord(lambda: agenda.vrije_tijden("m1", date.min, 30))
                self.antwoord(lambda: agenda.vrije_tijden("m1", date.max, 30))
                self.antwoord(lambda: agenda.is_vrij("m1", start, einde))

    def test_vrije_tijden_op_grensdagen(self):
        m = dagwerk(werktijden={d: [(time(0), time(23, 30))] for d in range(7)})
        agenda = Agenda([m])
        for dag in (date.min, date.max):
            with self.subTest(dag=dag):
                self.antwoord(lambda: agenda.vrije_tijden("m1", dag, 30))

    def test_boek_op_grensdag_met_werktijd(self):
        m = dagwerk(werktijden={d: [(time(0, 30), time(23, 30))] for d in range(7)})
        for start, einde in self.gevallen():
            with self.subTest(start=start):
                agenda = Agenda([m], tz="UTC")
                self.antwoord(lambda: agenda.boek(Boeking("b", "m1", start, einde)))
                self.antwoord(lambda: agenda.is_vrij("m1", start, einde))


class AansluitendeVakkenTest(unittest.TestCase):
    """Besluit (masterplan: 'een boeking mag meerdere werktijdvakken niet overspannen'):
    aansluitende vakken worden niet samengevoegd."""

    def agenda(self):
        return Agenda([dagwerk(werktijden={0: [(time(9), time(10)), (time(10), time(11))]}, pauzes={})])

    def test_boeking_over_de_aansluiting_wordt_geweigerd(self):
        with self.assertRaises(BuitenBeschikbaarheid):
            self.agenda().boek(Boeking("b", "m1", dt(9, 30), dt(10, 30)))
        self.assertFalse(self.agenda().is_vrij("m1", dt(9, 30), dt(10, 30)))

    def test_vrije_tijden_noemt_starts_over_de_aansluiting_niet(self):
        self.assertEqual(uren(self.agenda().vrije_tijden("m1", MAANDAG, 60, 30)), [(9, 0), (10, 0)])

    def test_boeking_binnen_een_vak_slaagt(self):
        self.agenda().boek(Boeking("b", "m1", dt(10), dt(11)))
