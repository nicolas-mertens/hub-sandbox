import re
import unittest
from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"


class ReadmeVoorbeeldTest(unittest.TestCase):
    def test_voorbeeld_uit_readme_wordt_uitgevoerd(self):
        tekst = README.read_text(encoding="utf-8")
        blokken = re.findall(r"```python\n(.*?)```", tekst, re.DOTALL)
        self.assertEqual(len(blokken), 1)
        code = compile(blokken[0], "README.md", "exec")
        exec(code, {"__name__": "readme_voorbeeld"})

    def test_readme_noemt_de_verplichte_onderdelen(self):
        tekst = README.read_text(encoding="utf-8")
        for onderdeel in ("Versie: 1.0", "lentegat", "nieuwe hoofdversie", "git subtree split",
                          "pyproject.toml", "1.0.0", "Foutentabel", "Stappenraster", "Python 3.11"):
            self.assertIn(onderdeel, tekst)
        self.assertNotIn("Python 3.9", tekst.replace("op 3.9 of nieuwer", ""))

    def test_readme_beschrijft_lentegat_zoals_het_werkt(self):
        tekst = " ".join(README.read_text(encoding="utf-8").split())
        self.assertNotIn("dichtstbijzijnde bestaande tijd", tekst)
        self.assertIn("02:50", tekst)
        self.assertIn("03:50", tekst)


if __name__ == "__main__":
    unittest.main()
