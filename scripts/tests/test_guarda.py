"""Tests de scripts/guarda.py con listas de hashes de prueba (nombres inventados, no los reales).

Uso: python3 -m unittest discover -s scripts/tests
"""

import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "guarda.py"
# Nombres de prueba: no son de ninguna franquicia.
PROHIBIDOS = ["zorbulon", "kraxi", "luna verde"]
SPRITE = b"\x89PNG\r\n\x1a\nsprite-privado-de-prueba"


def h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class GuardaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        listas = Path(self.tmp.name)
        (listas / "nombres.sha256").write_text("\n".join(h(n.encode()) for n in PROHIBIDOS) + "\n")
        (listas / "imagenes.sha256").write_text(h(SPRITE) + "\n")
        self.env = {**os.environ, "GUARDA_NOMBRES": str(listas / "nombres.sha256"),
                    "GUARDA_IMAGENES": str(listas / "imagenes.sha256")}
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        self.escribir("README.md", "Una mascota que imita lo que haces.\n")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def escribir(self, rel: str, contenido) -> None:
        ruta = self.repo / rel
        ruta.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(contenido, bytes):
            ruta.write_bytes(contenido)
        else:
            ruta.write_text(contenido, encoding="utf-8")
        subprocess.run(["git", "add", rel], cwd=self.repo, check=True)

    def guarda(self) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCRIPT), str(self.repo)], env=self.env,
                              capture_output=True, text=True)

    def test_repositorio_limpio_pasa(self) -> None:
        self.assertEqual(self.guarda().returncode, 0)

    def test_nombre_prohibido_en_texto_falla(self) -> None:
        self.escribir("docs/index.html", "<p>Conoce a Zorbulon</p>")
        r = self.guarda()
        self.assertEqual(r.returncode, 1)
        self.assertIn("docs/index.html", r.stdout)

    def test_nombre_con_tilde_y_mayusculas_falla(self) -> None:
        self.escribir("a.md", "KRÁXI llegó")
        self.assertEqual(self.guarda().returncode, 1)

    def test_par_de_palabras_falla(self) -> None:
        self.escribir("a.md", "La Luna   Verde brilla")
        self.assertEqual(self.guarda().returncode, 1)

    def test_par_unido_con_guion_falla(self) -> None:
        self.escribir("a.md", "zorbu-lon")
        h_unido = h(b"zorbulon")
        self.assertIn(h_unido, (Path(self.tmp.name) / "nombres.sha256").read_text())
        self.assertEqual(self.guarda().returncode, 1)

    def test_palabra_parecida_pasa(self) -> None:
        self.escribir("a.md", "zorbulones kraxis luna")
        self.assertEqual(self.guarda().returncode, 0)

    def test_nombre_en_la_ruta_falla(self) -> None:
        self.escribir("img/zorbulon-final.txt", "nada")
        self.assertEqual(self.guarda().returncode, 1)

    def test_sprite_privado_falla_aunque_cambie_de_nombre(self) -> None:
        self.escribir("docs/img/mascota.png", SPRITE)
        r = self.guarda()
        self.assertEqual(r.returncode, 1)
        self.assertIn("sprite privado", r.stdout)

    def test_imagen_propia_pasa(self) -> None:
        self.escribir("docs/img/propia.png", b"\x89PNG\r\n\x1a\notra-imagen")
        self.assertEqual(self.guarda().returncode, 0)

    def test_species_json_falla(self) -> None:
        self.escribir("cualquier/species.json", "{}")
        self.assertEqual(self.guarda().returncode, 1)

    def test_apk_falla(self) -> None:
        self.escribir("dist/app.apk", b"PK\x03\x04")
        self.assertEqual(self.guarda().returncode, 1)

    def test_aab_falla(self) -> None:
        self.escribir("dist/app.aab", b"PK\x03\x04")
        self.assertEqual(self.guarda().returncode, 1)

    def test_sin_listas_falla(self) -> None:
        env = {**self.env, "GUARDA_NOMBRES": str(Path(self.tmp.name) / "no-existe")}
        r = subprocess.run([sys.executable, str(SCRIPT), str(self.repo)], env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
