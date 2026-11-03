#!/usr/bin/env python3
"""Guarda contra el contenido privado del Director en vpulse-growth (repositorio público).

Falla si algún archivo versionado:
  1. contiene un nombre prohibido: cada palabra y cada par y trío de palabras seguidas, separados
     («a b», «a b c») y unidos («ab», «abc»), se pasa a minúsculas sin tildes y se compara su SHA-256 con
     .github/guarda/nombres.sha256 (la lista nunca está en texto plano; registro 8.35). También se
     revisan las rutas de los archivos;
  2. es una imagen cuyo SHA-256 está en .github/guarda/imagenes.sha256 (sprites de vpulse-species);
  3. es un species.json o un paquete de Android (.apk, .aab, .apks).

Uso: python3 scripts/guarda.py [raíz]   (por defecto, la raíz del repositorio git actual)
Variables para los tests: GUARDA_NOMBRES y GUARDA_IMAGENES (rutas a otras listas).
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

LISTAS = Path(".github/guarda")
PROHIBIDOS_NOMBRE = {"species.json"}
PROHIBIDOS_EXT = {".apk", ".aab", ".apks"}
PALABRA = re.compile(r"[a-z0-9]+")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cargar(ruta: Path) -> set[str]:
    if not ruta.is_file():
        return set()
    return {
        linea.strip()
        for linea in ruta.read_text(encoding="utf-8").splitlines()
        if linea.strip() and not linea.startswith("#")
    }


def normalizar(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()


def candidatos(texto: str):
    """Palabras, pares y tríos seguidos, separados por espacio («a b», «a b c») y unidos («ab», «abc»)."""
    palabras = PALABRA.findall(normalizar(texto))
    for i, palabra in enumerate(palabras):
        yield palabra
        for n in (2, 3):
            if i + n <= len(palabras):
                grupo = palabras[i : i + n]
                yield " ".join(grupo)
                yield "".join(grupo)


def nombres_prohibidos(texto: str, hashes: set[str]) -> int:
    return sum(1 for c in candidatos(texto) if sha256(c.encode()) in hashes)


def archivos(raiz: Path) -> list[Path]:
    salida = subprocess.run(
        ["git", "-C", str(raiz), "ls-files", "-z"], check=True, capture_output=True
    ).stdout.decode()
    return [Path(p) for p in salida.split("\0") if p]


def revisar(raiz: Path) -> list[str]:
    hashes_nombres = cargar(Path(os.environ.get("GUARDA_NOMBRES", raiz / LISTAS / "nombres.sha256")))
    hashes_imagenes = cargar(Path(os.environ.get("GUARDA_IMAGENES", raiz / LISTAS / "imagenes.sha256")))
    if not hashes_nombres or not hashes_imagenes:
        return ["Faltan las listas de hashes en .github/guarda/: la guarda no puede revisar nada."]

    errores = []
    for rel in archivos(raiz):
        ruta = raiz / rel
        if rel.name.lower() in PROHIBIDOS_NOMBRE or rel.suffix.lower() in PROHIBIDOS_EXT:
            errores.append(f"{rel}: archivo prohibido (species.json o paquete de Android).")
            continue
        if nombres_prohibidos(str(rel), hashes_nombres):
            errores.append(f"{rel}: la ruta contiene un nombre prohibido.")
        if not ruta.is_file():
            continue
        if rel.parts[:2] == LISTAS.parts:
            continue  # las propias listas de hashes
        datos = ruta.read_bytes()
        if sha256(datos) in hashes_imagenes:
            errores.append(f"{rel}: es un sprite privado de vpulse-species.")
            continue
        try:
            texto = datos.decode("utf-8")
        except UnicodeDecodeError:
            continue  # binario sin coincidencia de imagen
        n = nombres_prohibidos(texto, hashes_nombres)
        if n:
            errores.append(f"{rel}: contiene {n} nombre(s) prohibido(s).")
    return errores


def main() -> int:
    raiz = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        subprocess.run(["git", "rev-parse", "--show-toplevel"], check=True, capture_output=True, text=True).stdout.strip()
    )
    errores = revisar(raiz)
    for error in errores:
        archivo = error.split(":", 1)[0]
        print(f"::error file={archivo}::{error}")
    if errores:
        print(f"Guarda: {len(errores)} problema(s). Este repositorio es público: nada del paquete privado (regla de oro).")
        return 1
    print(f"Guarda: OK ({len(archivos(raiz))} archivos revisados).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
