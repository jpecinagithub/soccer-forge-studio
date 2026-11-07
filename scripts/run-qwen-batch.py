#!/usr/bin/env python3
"""Envía fotogramas con tiempos explícitos a Qwen2.5-VL vía OpenRouter.

Uso (en Oracle, con la clave solo como variable de entorno):
    set -a; . /home/ubuntu/appforge-ai-studio-edu/.env; set +a
    python3 scripts/run-qwen-batch.py --frames-dir DIR --prompt-file PROMPT \\
        --out-prefix /tmp/soccer-exp2/frag_1fps

La clave OPENROUTER_API_KEY se lee de os.environ; nunca se imprime ni se
guarda. Guarda <out>_raw.json (respuesta completa de OpenRouter),
<out>_pred.json (JSON parseado de la predicción) y <out>_manifest.json
(configuración, tiempos, tokens y coste). Reintenta 429/5xx (máx. 3).
Falla rápido ante 400/401/402/404.
"""

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import time

import requests

MODEL = "qwen/qwen2.5-vl-72b-instruct"
URL = "https://openrouter.ai/api/v1/chat/completions"
PRICE_PROMPT = 0.80 / 1_000_000      # $/token
PRICE_COMPLETION = 1.00 / 1_000_000  # $/token

FRAME_RE = re.compile(r"_rel([0-9.]+)_abs([0-9.]+)\.jpg$")


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--frames-dir", required=True)
    p.add_argument("--prompt-file", required=True)
    p.add_argument("--out-prefix", required=True)
    p.add_argument("--model", default=MODEL)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--max-tokens", type=int, default=4096)
    p.add_argument("--max-retries", type=int, default=3)
    p.add_argument("--timeout", type=int, default=600)
    return p.parse_args()


def load_frames(frames_dir):
    frames = []
    for name in sorted(os.listdir(frames_dir)):
        m = FRAME_RE.search(name)
        if not m:
            continue
        path = os.path.join(frames_dir, name)
        with open(path, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode("ascii")
        frames.append(
            {"file": name, "t_rel": float(m.group(1)),
             "t_abs": float(m.group(2)), "b64": b64,
             "bytes": os.path.getsize(path)}
        )
    frames.sort(key=lambda f: f["t_rel"])
    return frames


def extract_json(text):
    """Extrae el objeto JSON de la respuesta (con o sin cercas markdown)."""
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    start = s.find("{")
    end = s.rfind("}")
    if start < 0 or end < 0:
        raise ValueError("la respuesta no contiene un objeto JSON")
    return json.loads(s[start:end + 1])


def call_api(args, prompt_text, frames):
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        print("ERROR: OPENROUTER_API_KEY vacía o ausente", file=sys.stderr)
        return None, 0, 0
    content = [{"type": "text", "text": prompt_text}]
    for i, fr in enumerate(frames):
        content.append({
            "type": "text",
            "text": f"Fotograma {i + 1}/{len(frames)}: "
                    f"t_rel={fr['t_rel']:.2f} s, t_abs={fr['t_abs']:.2f} s.",
        })
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{fr['b64']}"},
        })
    body = {
        "model": args.model,
        "messages": [{"role": "user", "content": content}],
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/jpecinagithub/soccer-forge-studio",
        "X-Title": "Soccer Forge Studio exp2",
    }
    retries = 0
    wait = 10
    while True:
        t0 = time.time()
        try:
            resp = requests.post(URL, headers=headers, json=body,
                                 timeout=args.timeout)
        except requests.RequestException as exc:
            if retries < args.max_retries:
                retries += 1
                print(f"  reintento {retries}/{args.max_retries} tras error "
                      f"de red ({exc}); espera {wait}s", file=sys.stderr)
                time.sleep(wait)
                wait *= 3
                continue
            raise
        wall = time.time() - t0
        if resp.status_code in (429, 500, 502, 503, 504) \
                and retries < args.max_retries:
            retries += 1
            print(f"  reintento {retries}/{args.max_retries} tras HTTP "
                  f"{resp.status_code}; espera {wait}s", file=sys.stderr)
            time.sleep(wait)
            wait *= 3
            continue
        return resp, wall, retries


def main():
    args = parse_args()
    prompt_text = open(args.prompt_file, encoding="utf-8").read()
    prompt_sha = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
    frames = load_frames(args.frames_dir)
    if not frames:
        print(f"ERROR: sin fotogramas en {args.frames_dir}", file=sys.stderr)
        return 2
    print(f"Fotogramas: {len(frames)} "
          f"(t_rel {frames[0]['t_rel']:.2f}-{frames[-1]['t_rel']:.2f} s)")
    print(f"Prompt: {args.prompt_file} (sha256 {prompt_sha[:12]}...)")
    resp, wall, retries = call_api(args, prompt_text, frames)
    if resp is None:
        return 1
    print(f"HTTP {resp.status_code} en {wall:.1f} s "
          f"(reintentos: {retries})")
    if resp.status_code != 200:
        print("ERROR:", resp.text[:1000], file=sys.stderr)
        return 1
    raw = resp.json()
    with open(f"{args.out_prefix}_raw.json", "w", encoding="utf-8") as fh:
        json.dump(raw, fh, ensure_ascii=False, indent=1)
    usage = raw.get("usage", {})
    ptok = usage.get("prompt_tokens", 0)
    ctok = usage.get("completion_tokens", 0)
    cost_p = ptok * PRICE_PROMPT
    cost_c = ctok * PRICE_COMPLETION
    content = raw["choices"][0]["message"]["content"]
    try:
        pred = extract_json(content)
        parse_ok = True
    except Exception as exc:
        print(f"ERROR: no se pudo parsear el JSON: {exc}", file=sys.stderr)
        pred = None
        parse_ok = False
    if pred is not None:
        with open(f"{args.out_prefix}_pred.json", "w",
                  encoding="utf-8") as fh:
            json.dump(pred, fh, ensure_ascii=False, indent=1)
    manifest = {
        "model": args.model,
        "frames_dir": args.frames_dir,
        "frames": [{"file": f["file"], "t_rel": f["t_rel"],
                    "t_abs": f["t_abs"], "bytes": f["bytes"]}
                   for f in frames],
        "prompt_file": args.prompt_file,
        "prompt_sha256": prompt_sha,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "http_status": resp.status_code,
        "retries": retries,
        "wall_seconds": round(wall, 1),
        "usage": {"prompt_tokens": ptok, "completion_tokens": ctok,
                  "total_tokens": ptok + ctok},
        "cost_usd": {"prompt": round(cost_p, 4),
                     "completion": round(cost_c, 4),
                     "total": round(cost_p + cost_c, 4)},
        "response_id": raw.get("id"),
        "json_parse_ok": parse_ok,
        "finish_reason": raw["choices"][0].get("finish_reason"),
    }
    with open(f"{args.out_prefix}_manifest.json", "w",
              encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    print(f"Tokens: prompt {ptok} + completion {ctok} = {ptok + ctok}")
    print(f"Coste: ${cost_p + cost_c:.4f} "
          f"(prompt ${cost_p:.4f} + completion ${cost_c:.4f})")
    print(f"JSON parseable: {parse_ok}")
    return 0 if parse_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
