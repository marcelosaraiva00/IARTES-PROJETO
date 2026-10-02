#!/usr/bin/env python3
"""Detecta redundâncias: frases/números repetidos em páginas distintas do TCC."""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

import fitz

PDF = Path(__file__).resolve().parent.parent / "docs" / "TCC_IARTES___Janio_Macelo_Renilson.pdf"


def norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9à-ÿ %,]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    doc = fitz.open(str(PDF))
    pages = [doc[i].get_text() for i in range(doc.page_count)]

    # ---- A. Frases longas repetidas (shingles de ~10 palavras) ----
    print("=" * 70)
    print("A. TRECHOS LONGOS REPETIDOS (>= 9 palavras, em páginas distintas)")
    print("=" * 70)
    shingle_pages = defaultdict(set)
    shingle_text = {}
    K = 9
    for pno, t in enumerate(pages):
        words = norm(t).split()
        for i in range(len(words) - K):
            sh = " ".join(words[i : i + K])
            shingle_pages[sh].add(pno + 1)
            shingle_text[sh] = sh
    repeated = {sh: pgs for sh, pgs in shingle_pages.items() if len(pgs) >= 2}
    # filtra ruído (números soltos, sumário)
    shown = 0
    seen_pairs = set()
    for sh, pgs in sorted(repeated.items(), key=lambda x: -len(x[1])):
        if len(sh) < 45:
            continue
        # ignora sumário/listas (páginas iniciais 1-12)
        body_pgs = sorted(p for p in pgs)
        key = (sh[:30], tuple(body_pgs))
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        print(f"  p.{body_pgs}: \"{sh[:95]}\"")
        shown += 1
        if shown >= 40:
            print("  ... (truncado)")
            break
    if shown == 0:
        print("  Nenhum trecho longo repetido relevante.")
    print()

    # ---- B. Números-chave: onde cada dado aparece ----
    print("=" * 70)
    print("B. DADOS NUMÉRICOS-CHAVE (páginas onde aparecem)")
    print("=" * 70)
    full = "\n".join(f"[P{i+1}]" + t for i, t in enumerate(pages))
    metrics = {
        "120 casos": r"120\s*(?:casos|test)",
        "927 passos": r"927",
        "54,1% (tempo QP3)": r"54[,.]1",
        "44,9% (NASA-TLX)": r"44[,.]9",
        "56,7% (C2 total)": r"56[,.]7",
        "373-493x": r"373|493",
        "2,6% S1": r"2[,.]6\s*%|2[,.]60",
        "8,2%/8,21% S2": r"8[,.]2",
        "19,6% S3": r"19[,.]6|19[,.]4",
        "12,9% S4": r"12[,.]9",
        "136 passos economizados": r"136\s*passos",
        "n=5 / cinco testadores": r"n\s*=\s*5|cinco testadores",
        "51,7 min": r"51[,.]7",
        "24,4 min": r"24[,.]4",
    }
    for label, pat in metrics.items():
        pgs = sorted(set(int(m) for m in re.findall(r"\[P(\d+)\]", "".join(
            f"[P{i+1}]" for i, t in enumerate(pages) if re.search(pat, t)
        ))))
        print(f"  {label:<28} -> p.{pgs}  ({len(pgs)}x)")
    print()

    # ---- C. Repetição de definições/frases-conceito ----
    print("=" * 70)
    print("C. CONCEITOS POSSIVELMENTE REPETIDOS (contagem de páginas)")
    print("=" * 70)
    concepts = {
        "teste manual permanece essencial": r"teste\s+manual\s+permanece\s+essencial|permanece\s+essencial",
        "custo/carga cognitiv": r"cust[oa]\s+cognitiv|carga\s+cognitiv",
        "redundância de passos": r"redund[âa]ncia\s+(?:de\s+passos|estrutural|operacional)",
        "prefixos compartilhados": r"prefixos\s+compartilhados",
        "normalização semântica": r"normaliza[çc][ãa]o\s+sem[âa]ntica",
        "human-in-the-loop": r"human[- ]in[- ]the[- ]loop",
        "sem substituir julgamento humano": r"sem\s+substituir\s+o?\s+julgamento",
        "trade-off consolidação/detecção": r"trade[- ]?off",
        "gpt-4o-mini equilíbrio custo": r"equil[íi]brio\s+entre\s+custo",
    }
    for label, pat in concepts.items():
        pgs = sorted(set(i + 1 for i, t in enumerate(pages) if re.search(pat, t, re.I)))
        flag = "  <-- muitas" if len(pgs) >= 6 else ""
        print(f"  {label:<38} p.{pgs}{flag}")
    print()


if __name__ == "__main__":
    main()
