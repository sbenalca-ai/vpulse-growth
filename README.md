# vpulse-growth

Landing pública y materiales de lanzamiento de V-Pulse.

**Repositorio público.** El workflow **Guarda** (`scripts/guarda.py`) corre en cada push y en cada PR, y falla si encuentra:

- un nombre prohibido, en cualquier palabra o par de palabras de los archivos de texto o en las rutas. La lista vive solo como hashes SHA-256 en `.github/guarda/nombres.sha256`;
- una imagen idéntica a un sprite privado (`.github/guarda/imagenes.sha256`);
- un `species.json` o un paquete de Android (`.apk`, `.aab`, `.apks`).

Para actualizar las listas: se regeneran fuera del repositorio a partir del paquete privado y se sube solo el archivo de hashes.

**Límites conocidos** (aceptados por el Technical Lead, 3 nov.):

- Los hashes de nombres no llevan «pepper»: las palabras cortas y conocidas se pueden revertir probando un diccionario. La guarda evita que alguien suba algo por descuido; no guarda un secreto. Un pepper como secreto rompería la guarda en los PR desde forks.
- Los sprites se comparan por hash exacto: una copia reescalada, recortada o recomprimida no se detecta. Si algún día se suben capturas al repositorio, se revisa.
