import unittest
from weergave import euro, factuurregel


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


class FactuurregelTest(unittest.TestCase):
    def test_standaard(self):
        self.assertEqual(
            factuurregel("Lesuur", 10000),
            "Lesuur: € 100,00 + 21% btw € 21,00 = € 121,00",
        )

    def test_verlaagd(self):
        self.assertEqual(
            factuurregel("Boek", 2000, "verlaagd"),
            "Boek: € 20,00 + 6% btw € 1,20 = € 21,20",
        )

    def test_nul(self):
        self.assertEqual(
            factuurregel("Bon", 500, "nul"),
            "Bon: € 5,00 + 0% btw € 0,00 = € 5,00",
        )

    def test_negatief_bedrag(self):
        with self.assertRaises(ValueError):
            factuurregel("Lesuur", -1)

    def test_onbekend_tarief(self):
        with self.assertRaises(ValueError):
            factuurregel("Lesuur", 100, "onbekend")

    def test_lege_omschrijving(self):
        for leeg in ("", "   ", "\t"):
            with self.assertRaisesRegex(ValueError, "omschrijving"):
                factuurregel(leeg, 100)


if __name__ == "__main__":
    unittest.main()
