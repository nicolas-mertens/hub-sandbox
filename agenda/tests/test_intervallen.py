import unittest
from datetime import date, time

from agenda.intervallen import aftrekken, overlap, samenvoegen


class IntervallenTest(unittest.TestCase):
    def test_aansluiting_is_geen_overlap_een_minuut_wel(self):
        eerste = (time(9), time(10))
        self.assertFalse(overlap(eerste, (time(10), time(11))))
        self.assertFalse(overlap((time(10), time(11)), eerste))
        self.assertTrue(overlap(eerste, (time(9, 59), time(11))))
        self.assertTrue(overlap((time(9, 59), time(11)), eerste))
        self.assertTrue(overlap(eerste, eerste))
        self.assertFalse(overlap(eerste, (time(11), time(12))))

    def test_samenvoegen_ongesorteerd_overlappend_en_aansluitend(self):
        invoer = [(8, 10), (2, 4), (3, 5), (1, 2), (8, 9), (12, 13)]
        self.assertEqual(samenvoegen(invoer), [(1, 5), (8, 10), (12, 13)])
        self.assertEqual(invoer, [(8, 10), (2, 4), (3, 5), (1, 2), (8, 9), (12, 13)])

    def test_aftrekken_midden_rand_volledig_en_buiten(self):
        for weg, verwacht in [
            ([(4, 6)], [(1, 4), (6, 10)]),
            ([(0, 4)], [(4, 10)]),
            ([(8, 12)], [(1, 8)]),
            ([(1, 10)], []),
            ([(0, 12)], []),
            ([(0, 1), (10, 12)], [(1, 10)]),
        ]:
            with self.subTest(weg=weg):
                self.assertEqual(aftrekken([(1, 10)], weg), verwacht)

    def test_aftrekken_meerdere_ongesorteerde_intervallen(self):
        self.assertEqual(
            aftrekken([(20, 30), (5, 12), (1, 6)],
                      [(25, 28), (8, 10), (3, 5), (4, 7), (11, 22)]),
            [(1, 3), (7, 8), (10, 11), (22, 25), (28, 30)],
        )

    def test_verwijdering_over_meerdere_losse_basisintervallen(self):
        self.assertEqual(
            aftrekken([(1, 4), (6, 9), (11, 14)], [(3, 12)]),
            [(1, 3), (12, 14)],
        )

    def test_lege_invoer_en_generators(self):
        self.assertEqual(samenvoegen([]), [])
        self.assertEqual(aftrekken([], []), [])
        self.assertEqual(aftrekken([], [(1, 2)]), [])
        self.assertEqual(aftrekken([(3, 5), (1, 3)], []), [(1, 5)])
        self.assertEqual(aftrekken(iter([(1, 10)]), iter([(3, 7)])),
                         [(1, 3), (7, 10)])

    def test_generieke_grenzen_zonder_rekenen(self):
        self.assertEqual(samenvoegen([('b', 'c'), ('a', 'b')]), [('a', 'c')])
        self.assertEqual(
            aftrekken([(date(2027, 6, 1), date(2027, 6, 10))],
                      [(date(2027, 6, 3), date(2027, 6, 7))]),
            [(date(2027, 6, 1), date(2027, 6, 3)),
             (date(2027, 6, 7), date(2027, 6, 10))],
        )

    def test_lege_of_omgekeerde_intervallen_worden_geweigerd(self):
        for ongeldig in [(2, 2), (3, 1)]:
            with self.subTest(interval=ongeldig):
                with self.assertRaises(ValueError):
                    samenvoegen([ongeldig])
                with self.assertRaises(ValueError):
                    aftrekken([(0, 4)], [ongeldig])
                with self.assertRaises(ValueError):
                    aftrekken([ongeldig], [])
                with self.assertRaises(ValueError):
                    overlap(ongeldig, (0, 4))
                with self.assertRaises(ValueError):
                    overlap((0, 4), ongeldig)
