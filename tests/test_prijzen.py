import unittest
from prijzen import BTW_TARIEVEN, btw_bedrag, met_btw, met_korting, zonder_btw


class PrijzenTest(unittest.TestCase):
    def test_standaard(self):
        self.assertEqual(met_btw(1000), 1210)

    def test_verlaagd(self):
        self.assertEqual(met_btw(1000, "verlaagd"), 1060)

    def test_afronding(self):
        self.assertEqual(met_btw(1, "standaard"), 1)

    def test_negatief_geweigerd(self):
        with self.assertRaises(ValueError):
            met_btw(-1)

    def test_zonder_btw_standaard(self):
        self.assertEqual(zonder_btw(1210), 1000)

    def test_zonder_btw_verlaagd(self):
        self.assertEqual(zonder_btw(1060, "verlaagd"), 1000)

    def test_zonder_btw_nul(self):
        self.assertEqual(zonder_btw(500, "nul"), 500)

    def test_zonder_btw_afronding(self):
        self.assertEqual(zonder_btw(1), 1)  # 0,83 -> 1
        self.assertEqual(zonder_btw(60), 50)  # 49,59 -> 50
        self.assertEqual(zonder_btw(1, "verlaagd"), 1)  # 0,94 -> 1
        self.assertEqual(zonder_btw(2, "verlaagd"), 2)  # 1,89 -> 2
        self.assertEqual(zonder_btw(0), 0)

    def test_zonder_btw_negatief_geweigerd(self):
        with self.assertRaises(ValueError):
            zonder_btw(-1)

    def test_btw_bedrag_voorbeelden(self):
        self.assertEqual(btw_bedrag(10000), 2100)
        self.assertEqual(btw_bedrag(10000, "verlaagd"), 600)
        self.assertEqual(btw_bedrag(10000, "nul"), 0)

    def test_btw_bedrag_klopt_met_met_btw(self):
        for tarief in BTW_TARIEVEN:
            for bedrag in range(1001):
                self.assertEqual(bedrag + btw_bedrag(bedrag, tarief), met_btw(bedrag, tarief))

    def test_btw_bedrag_negatief_geweigerd(self):
        with self.assertRaises(ValueError):
            btw_bedrag(-1)

    def test_onbekend_tarief_geeft_valueerror_met_geldige_tarieven(self):
        for functie in (met_btw, zonder_btw, btw_bedrag):
            with self.assertRaises(ValueError) as ctx:
                functie(100, "luxe")
            for tarief in BTW_TARIEVEN:
                self.assertIn(tarief, str(ctx.exception))


class KortingTest(unittest.TestCase):
    def test_voorbeelden(self):
        self.assertEqual(met_korting(10000, 10), 9000)
        self.assertEqual(met_korting(999, 15), 849)  # 849,15 -> 849
        self.assertEqual(met_korting(1001, 50), 501)  # 500,5 -> 501

    def test_grenzen(self):
        self.assertEqual(met_korting(10000, 0), 10000)
        self.assertEqual(met_korting(10000, 100), 0)

    def test_ongeldige_invoer(self):
        for bedrag, procent in [(-1, 10), (100, -1), (100, 101), (100, 10.5), (100, 10.0), (100, "10"), (100, True)]:
            with self.subTest(bedrag=bedrag, procent=procent):
                with self.assertRaises(ValueError) as ctx:
                    met_korting(bedrag, procent)
                self.assertTrue(str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
