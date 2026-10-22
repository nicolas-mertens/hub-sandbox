import unittest
from weergave import euro


class WeergaveTest(unittest.TestCase):
    def test_duizendtallen(self):
        self.assertEqual(euro(123456), "€ 1.234,56")

    def test_miljoenen(self):
        self.assertEqual(euro(123456789), "€ 1.234.567,89")

    def test_nul(self):
        self.assertEqual(euro(0), "€ 0,00")

    def test_negatief(self):
        self.assertEqual(euro(-500), "-€ 5,00")

    def test_twee_decimalen(self):
        self.assertEqual(euro(5), "€ 0,05")
        self.assertEqual(euro(1000), "€ 10,00")


if __name__ == "__main__":
    unittest.main()
