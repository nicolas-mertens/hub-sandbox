import unittest
from prijzen import met_btw, zonder_btw


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


if __name__ == "__main__":
    unittest.main()
