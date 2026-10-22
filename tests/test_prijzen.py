import unittest
from prijzen import met_btw


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


if __name__ == "__main__":
    unittest.main()
