"""Bewaak het publieke contract en de zelfstandigheid van het pakket."""

import ast
import pkgutil
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import textwrap
import unittest

import agenda


PAKKET = Path(__file__).resolve().parents[1]
PUBLIEK = {
    "Agenda", "Medewerker", "Materiaal", "Boeking", "AgendaFout",
    "DubbeleBoeking", "BuitenBeschikbaarheid",
}


def standaardmodules():
    # stdlib_module_names bestaat pas vanaf Python 3.10.
    if hasattr(sys, "stdlib_module_names"):
        return set(sys.stdlib_module_names)
    stdlib = Path(sysconfig.get_path("stdlib"))
    return set(sys.builtin_module_names) | {
        module.name
        for module in pkgutil.iter_modules([str(stdlib), str(stdlib / "lib-dynload")])
    }


class PubliekeInterfaceTest(unittest.TestCase):
    def test_exact_de_contractnamen_worden_geexporteerd(self):
        self.assertCountEqual(agenda.__all__, PUBLIEK)
        namespace = {}
        exec("from agenda import *", namespace)
        self.assertEqual(set(namespace) - {"__builtins__"}, PUBLIEK)
        for naam in PUBLIEK:
            self.assertIs(namespace[naam], getattr(agenda, naam))

        # Ook een extra import in __init__.py die niet in __all__ staat faalt.
        boom = ast.parse((PAKKET / "__init__.py").read_text(encoding="utf-8"))
        bindings = set()
        for knoop in ast.walk(boom):
            if isinstance(knoop, (ast.Import, ast.ImportFrom)):
                for alias in knoop.names:
                    bindings.add(alias.asname or alias.name.split(".")[0])
        self.assertEqual(bindings, PUBLIEK)


class OnafhankelijkheidTest(unittest.TestCase):
    def test_alle_pythonbestanden_importeren_alleen_agenda_of_standaardbibliotheek(self):
        toegestaan = standaardmodules() | {"agenda", "unittest"}
        bestanden = sorted(PAKKET.rglob("*.py"))
        self.assertIn(Path(__file__).resolve(), bestanden)
        for bestand in bestanden:
            boom = ast.parse(bestand.read_text(encoding="utf-8"), filename=str(bestand))
            for knoop in ast.walk(boom):
                if isinstance(knoop, ast.Import):
                    modules = [alias.name for alias in knoop.names]
                elif isinstance(knoop, ast.ImportFrom):
                    if knoop.level:
                        # Relatieve imports mogen niet boven agenda/ uitkomen.
                        diepte = len(bestand.parent.relative_to(PAKKET).parts) + 1
                        with self.subTest(bestand=str(bestand), regel=knoop.lineno):
                            self.assertLessEqual(knoop.level, diepte)
                        continue
                    modules = [knoop.module]
                else:
                    continue
                for module in modules:
                    with self.subTest(bestand=str(bestand), regel=knoop.lineno, module=module):
                        self.assertIn(module.split(".")[0], toegestaan)

    def test_alleen_gekopieerd_pakket_werkt_buiten_de_repo(self):
        with tempfile.TemporaryDirectory() as tijdelijk:
            basis = Path(tijdelijk).resolve()
            shutil.copytree(PAKKET, basis / "agenda", ignore=shutil.ignore_patterns("__pycache__"))
            werkmap = basis / "andere_werkmap"
            werkmap.mkdir()
            script = werkmap / "controle.py"
            script.write_text(textwrap.dedent('''\
                from datetime import date, datetime, time
                from pathlib import Path
                import sys
                import unittest
                from zoneinfo import ZoneInfo

                controle = unittest.TestCase()
                basis = Path(sys.argv[1]).resolve()
                repo = Path(sys.argv[2]).resolve()
                controle.assertNotIn(repo, [Path(p).resolve() for p in sys.path])
                controle.assertNotEqual(Path.cwd(), repo)
                sys.path.insert(0, str(basis))
                import agenda
                from agenda import Agenda, Boeking, Medewerker

                controle.assertEqual(Path(agenda.__file__).resolve(), basis / "agenda" / "__init__.py")
                controle.assertNotIn(repo, [Path(p).resolve() for p in sys.path])
                zone = ZoneInfo("Europe/Brussels")
                dag = date(2027, 6, 7)
                def tijd(uur, minuut=0):
                    return datetime(2027, 6, 7, uur, minuut, tzinfo=zone)

                origineel = Agenda([Medewerker("m1", "Voorbeeld", {0: [(time(9), time(10))]})])
                controle.assertEqual(origineel.vrije_tijden("m1", dag, 30),
                                     [tijd(9), tijd(9, 15), tijd(9, 30)])
                geboekt = origineel.boek(Boeking("b1", "m1", tijd(9), tijd(9, 30)))
                controle.assertEqual(geboekt.vrije_tijden("m1", dag, 30), [tijd(9, 30)])
                controle.assertEqual(origineel.vrije_tijden("m1", dag, 30),
                                     [tijd(9), tijd(9, 15), tijd(9, 30)])
                print("isolatie geslaagd")
                '''), encoding="utf-8")
            resultaat = subprocess.run(
                [sys.executable, "-I", "-S", str(script), str(basis), str(PAKKET.parent)],
                cwd=str(werkmap), capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(resultaat.returncode, 0, resultaat.stdout + resultaat.stderr)
            self.assertEqual(resultaat.stdout, "isolatie geslaagd\n")
