#!/usr/bin/env python3
"""Genera el prompt para una ventana (lote) a partir de la plantilla del
fragmento, adaptando duración, desplazamiento y resolución de los fotogramas.

Uso:
    python3 scripts/make-window-prompt.py --length 30 --offset 35.0 \\
        --out /tmp/soccer-exp2/prompt_batch_030-060.txt
"""

import argparse

TEMPLATE = "docs/evaluation/fragment-prompt.txt"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--length", type=float, required=True,
                   help="duración de la ventana en segundos")
    p.add_argument("--offset", type=float, required=True,
                   help="segundo inicial de la ventana en el vídeo original")
    p.add_argument("--resolution", default="960×540",
                   help="resolución de los fotogramas enviados")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    text = open(TEMPLATE, encoding="utf-8").read()
    text = text.replace(
        "Analiza este fragmento de vídeo de fútbol (30 segundos, 1920x1080, retransmisión de TV).",
        f"Analiza este fragmento de vídeo de fútbol ({args.length:.2f} segundos, "
        f"fotogramas de {args.resolution} extraídos de una retransmisión de TV).",
    )
    text = text.replace(
        "El fragmento empieza en el segundo 35.00 del vídeo original.",
        f"El fragmento empieza en el segundo {args.offset:.2f} del vídeo original.",
    )
    text = text.replace(
        "Todos los tiempos que des deben ser RELATIVOS al fragmento (de 0.00 a 30.00).",
        "Todos los tiempos que des deben ser RELATIVOS al fragmento "
        f"(de 0.00 a {args.length:.2f}).",
    )
    text = text.replace(
        "Los segmentos deben cubrir los 30.00 segundos completos, sin huecos ni solapamientos.",
        "Los segmentos deben cubrir los "
        f"{args.length:.2f} segundos completos, sin huecos ni solapamientos.",
    )
    open(args.out, "w", encoding="utf-8").write(text)
    print(f"Prompt de ventana escrito en {args.out} "
          f"(longitud {args.length:.2f} s, offset {args.offset:.2f} s)")


if __name__ == "__main__":
    main()
