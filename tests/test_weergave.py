import unittest
from weergave import euro, factuurregel, factuurtotaal, factuurtotaal_contant


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


class FactuurtotaalTest(unittest.TestCase):
    def test_twee_regels(self):
        tekst = factuurtotaal([("Les", 5000, "standaard"), ("Boek", 2000, "verlaagd")])
        self.assertEqual(
            tekst.split("\n"),
            [
                factuurregel("Les", 5000, "standaard"),
                factuurregel("Boek", 2000, "verlaagd"),
                "Totaal: € 81,70 (waarvan btw € 11,70)",
            ],
        )

    def test_een_regel(self):
        self.assertEqual(
            factuurtotaal([("Lesuur", 10000, "standaard")]),
            factuurregel("Lesuur", 10000, "standaard")
            + "\nTotaal: € 121,00 (waarvan btw € 21,00)",
        )

    def test_lege_lijst(self):
        with self.assertRaisesRegex(ValueError, "minstens één regel"):
            factuurtotaal([])

    def test_onbekend_tarief(self):
        with self.assertRaisesRegex(ValueError, "onbekend btw-tarief"):
            factuurtotaal([("Les", 5000, "luxe")])

    def test_afronding_per_regel(self):
        # Per regel: 3 cent + 21% = 4 cent (btw 1). Twee regels: 8 cent, btw 2.
        # Op het totaal afronden zou 7 cent (btw 1) geven.
        tekst = factuurtotaal([("A", 3, "standaard"), ("B", 3, "standaard")])
        self.assertEqual(
            tekst.split("\n")[-1], "Totaal: € 0,08 (waarvan btw € 0,02)"
        )

    def test_negatief_bedrag(self):
        with self.assertRaisesRegex(ValueError, "negatief"):
            factuurtotaal([("Les", 5000, "standaard"), ("Fout", -1, "nul")])


class FactuurtotaalContantTest(unittest.TestCase):
    def test_eindigt_op_totaal_en_contant(self):
        tekst = factuurtotaal_contant(
            [("Knippen", 2479, "standaard"), ("Shampoo", 899, "verlaagd")]
        )
        self.assertEqual(
            tekst.split("\n")[-2:],
            ["Totaal: € 39,53 (waarvan btw € 5,75)", "Contant te betalen: € 39,55"],
        )

    def test_begint_met_dezelfde_tekst_als_factuurtotaal(self):
        regels = [("Knippen", 2479, "standaard"), ("Shampoo", 899, "verlaagd")]
        self.assertTrue(
            factuurtotaal_contant(regels).startswith(factuurtotaal(regels) + "\n")
        )

    def test_totaal_op_nul_of_vijf_blijft_gelijk(self):
        tekst = factuurtotaal_contant([("Knippen", 2479, "standaard")])
        self.assertEqual(
            tekst.split("\n")[-2:],
            ["Totaal: € 30,00 (waarvan btw € 5,21)", "Contant te betalen: € 30,00"],
        )

    def test_lege_lijst(self):
        with self.assertRaises(ValueError) as fout:
            factuurtotaal_contant([])
        with self.assertRaises(ValueError) as verwacht:
            factuurtotaal([])
        self.assertEqual(str(fout.exception), str(verwacht.exception))

    def test_generator_als_invoer(self):
        tekst = factuurtotaal_contant(r for r in [("Knippen", 2479, "standaard")])
        self.assertTrue(tekst.endswith("Contant te betalen: € 30,00"))


if __name__ == "__main__":
    unittest.main()
