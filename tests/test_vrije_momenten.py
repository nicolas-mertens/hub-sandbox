import ast
import unittest
from datetime import date
from pathlib import Path

import agenda
import vrije_momenten
from vrije_momenten import vrije_momenten as toon


class VrijeMomentenTest(unittest.TestCase):
    def test_vrije_momenten_voor_voorbeeldset(self):
        regels = toon(vrije_momenten.voorbeeld_agenda(), date(2027, 6, 7))
        ochtend = ["10:15", "10:30", "10:45", "11:00", "11:15", "11:30"]
        middag = ["%02d:%02d" % (u, m) for u in range(13, 17) for m in (0, 15, 30, 45)][:-1]
        self.assertEqual(regels, [
            "An Voorbeeld (an@example.test) op 2027-06-07: " + ", ".join(ochtend + middag),
            "Bram Proef (bram@example.test) op 2027-06-07: geen",
            "Foodtruck Test vrije dagen in 2027-06: 1, 2, 3, 4, " + ", ".join(str(d) for d in range(8, 31)),
        ])

    def test_gebruikt_de_module_via_import(self):
        self.assertIs(vrije_momenten.Agenda, agenda.Agenda)
        bron = Path(vrije_momenten.__file__).read_text(encoding="utf-8")
        imports = [n for n in ast.walk(ast.parse(bron)) if isinstance(n, ast.ImportFrom) and n.module == "agenda"]
        self.assertEqual(len(imports), 1)
        self.assertNotIn("class Agenda", bron)


if __name__ == "__main__":
    unittest.main()
