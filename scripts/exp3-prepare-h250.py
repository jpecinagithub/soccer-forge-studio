#!/usr/bin/env python3
"""Experimento 3 — Preparación de datos H250 para el fine-tuning YOLOv8n.

NO EJECUTADO: este script se entrega sin correr. Lo ejecuta quien lance la
receta (docs/decisions/exp3/finetune-recipe.md) en la instancia GPU.

Hace, en orden:
  1. Descarga YOLO.zip de Zenodo (DOI 10.5281/zenodo.7808511) si no existe.
  2. Verifica el md5 publicado: cdc2401a3275615da894a1b8edfec119.
  3. Extrae el ZIP en --out (por defecto data/h250).
  4. Comprueba los conteos publicados: train 14.368 / val 2.726 / test 2.692.
  5. Comprueba que solo hay 2 clases (0 ball, 1 person) en las etiquetas.
  6. Si la estructura de directorios conserva el identificador de partido
     o secuencia de origen, verifica que ningún identificador aparece en
     más de una partición (separación por partido) e informa del resultado.
     Si la estructura NO conserva el origen, lo registra como tal y no
     inventa ninguna comprobación.
  7. Escribe data.yaml efectivo con la ruta real de extracción.

No descarga vídeos, no toca B2, no entrena, no modifica B1/B3.

Uso:
    python3 scripts/exp3-prepare-h250.py --out data/h250 --verify-md5

Requiere: Python 3.8+ (solo stdlib), ~3 GB libres (2,5 GB del ZIP + extracción).
"""

import argparse
import hashlib
import sys
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

ZENODO_URL = "https://zenodo.org/records/7808511/files/YOLO.zip?download=1"
EXPECTED_MD5 = "cdc2401a3275615da894a1b8edfec119"
EXPECTED_COUNTS = {"train": 14368, "val": 2726, "test": 2692}
EXPECTED_CLASSES = {0, 1}


def md5_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        while True:
            data = f.read(chunk)
            if not data:
                break
            h.update(data)
    return h.hexdigest()


def count_split(images_dir: Path) -> Counter:
    """Cuenta imágenes por subdirectorio inmediato (train/val/test)."""
    counts = Counter()
    for split in ("train", "val", "test"):
        d = images_dir / split
        if not d.is_dir():
            continue
        counts[split] = sum(1 for p in d.rglob("*")
                            if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    return counts


def check_labels(labels_dir: Path) -> Counter:
    """Cuenta clases presentes en los .txt YOLO (primera columna)."""
    classes = Counter()
    n_files = 0
    for txt in labels_dir.rglob("*.txt"):
        n_files += 1
        for line in txt.read_text(errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                classes[int(line.split()[0])] += 1
            except (ValueError, IndexError):
                print(f"  AVISO: línea no parseable en {txt}: {line!r}", file=sys.stderr)
    return classes, n_files


def check_party_separation(root: Path) -> None:
    """Intenta verificar la separación por partido/secuencia de origen.

    Solo es posible si la estructura de directorios conserva el
    identificador de origen (p. ej. .../<partido>/... o nombres de
    fichero con el id de partido). Si no se puede determinar el origen,
    se registra como NO VERIFICABLE y no se afirma nada.
    """
    print("Comprobación de separación por partido/secuencia de origen:")
    # Heurística conservadora: buscar un nivel de directorio bajo
    # images/<split>/ que se repita entre particiones como identificador.
    # Si los ficheros están planos (sin subdirectorios por partido),
    # el origen no es recuperable de la estructura.
    origins = {}
    for split in ("train", "val", "test"):
        d = root / "images" / split
        if not d.is_dir():
            continue
        subdirs = sorted(p.name for p in d.iterdir() if p.is_dir())
        origins[split] = set(subdirs)
        print(f"  {split}: {len(subdirs)} subdirectorios inmediatos")
    if not origins:
        print("  NO VERIFICABLE: no se encontró images/<split>/ en la extracción.")
        return
    if all(len(v) == 0 for v in origins.values()):
        print("  NO VERIFICABLE: los fotogramas están planos, sin subdirectorios")
        print("  por partido/secuencia. El origen por fotograma no es recuperable")
        print("  de la estructura del ZIP. La separación descansa únicamente en")
        print("  la partición publicada (heredada de SoccerNet-v3, split por")
        print("  partido 290/55/55 según arXiv:2311.06892 §II.A.3).")
        return
    overlap = set()
    splits = list(origins)
    for i in range(len(splits)):
        for j in range(i + 1, len(splits)):
            overlap |= origins[splits[i]] & origins[splits[j]]
    if overlap:
        print(f"  FALLO: {len(overlap)} identificadores aparecen en más de una")
        print(f"  partición: {sorted(overlap)[:10]}")
        sys.exit(1)
    print("  OK: ningún subdirectorio de origen aparece en más de una partición.")
    print("  (Esto verifica la separación solo si esos subdirectorios son")
    print("  realmente identificadores de partido/secuencia; registrar el")
    print("  nivel de directorio comprobado en el informe de ejecución.)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="data/h250",
                    help="directorio de extracción (por defecto data/h250)")
    ap.add_argument("--zip", default=None,
                    help="ruta al YOLO.zip ya descargado (si no se indica, se descarga)")
    ap.add_argument("--verify-md5", action="store_true",
                    help="verificar el md5 publicado antes de extraer")
    ap.add_argument("--url", default=ZENODO_URL, help="URL de descarga del ZIP")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    zip_path = Path(args.zip) if args.zip else out / "YOLO.zip"

    if not zip_path.exists():
        print(f"Descargando {args.url} -> {zip_path} (2,5 GB)...")
        urllib.request.urlretrieve(args.url, zip_path)
    else:
        print(f"Usando ZIP existente: {zip_path}")

    if args.verify_md5 or not args.zip:
        print("Verificando md5...")
        got = md5_of(zip_path)
        print(f"  md5: {got}")
        if got != EXPECTED_MD5:
            print(f"  FALLO: md5 esperado {EXPECTED_MD5}", file=sys.stderr)
            return 1
        print("  OK: md5 coincide con el publicado en Zenodo.")

    print(f"Extrayendo {zip_path} en {out}...")
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(out)

    # Localizar images/ (en la raíz de --out o un nivel más abajo).
    images_dir = out / "images"
    if not images_dir.is_dir():
        candidates = [p for p in out.iterdir() if p.is_dir() and (p / "images").is_dir()]
        if len(candidates) == 1:
            images_dir = candidates[0] / "images"
        else:
            print(f"  FALLO: no se encontró images/ bajo {out}", file=sys.stderr)
            return 1
    print(f"  images/ en: {images_dir}")

    counts = count_split(images_dir)
    print(f"Conteos de imágenes: {dict(counts)} (publicados: {EXPECTED_COUNTS})")
    for split, expected in EXPECTED_COUNTS.items():
        if counts.get(split, 0) != expected:
            print(f"  AVISO: {split} tiene {counts.get(split, 0)}, publicados {expected}.",
                  file=sys.stderr)
            print("  Registrar la discrepancia; no continuar sin entenderla.",
                  file=sys.stderr)

    labels_dir = out / "labels"
    if not labels_dir.is_dir():
        candidates = [p for p in out.iterdir() if p.is_dir() and (p / "labels").is_dir()]
        labels_dir = candidates[0] / "labels" if len(candidates) == 1 else None
    if labels_dir is not None:
        classes, n_files = check_labels(labels_dir)
        print(f"Clases en etiquetas ({n_files} ficheros .txt): {dict(classes)}")
        if set(classes) - EXPECTED_CLASSES:
            print(f"  FALLO: clases inesperadas: {set(classes) - EXPECTED_CLASSES}",
                  file=sys.stderr)
            return 1
    else:
        print("  AVISO: no se encontró labels/; no se pudo comprobar las clases.",
              file=sys.stderr)

    check_party_separation(out)

    data_yaml = out / "data.yaml"
    data_yaml.write_text(
        f"# Generado por scripts/exp3-prepare-h250.py (experimento 3).\n"
        f"# H250: train {counts.get('train', '?')} / val {counts.get('val', '?')} "
        f"/ test {counts.get('test', '?')} imágenes.\n"
        f"# Condiciones: ver docs/decisions/exp3/conditions-verification.md\n"
        f"# (solo investigación, no comercial; pesos resultantes AGPL-3.0).\n"
        f"path: {out.resolve()}\n"
        f"train: images/train\n"
        f"val: images/val\n"
        f"test: images/test\n"
        f"\n"
        f"nc: 2\n"
        f"names:\n"
        f"  0: ball\n"
        f"  1: person\n"
    )
    print(f"data.yaml efectivo escrito en: {data_yaml}")
    print("Preparación completada. Siguiente paso: ver finetune-recipe.md §6.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
