#!/usr/bin/env python3
"""Revisão automatizada do PDF do TCC."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pypdf

PDF = Path(__file__).resolve().parent.parent / "docs" / "TCC_IARTES___Janio_Macelo_Renilson.pdf"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    reader = pypdf.PdfReader(str(PDF))
    pages = [p.extract_text() or "" for p in reader.pages]
    full = "\n".join(pages)

    print(f"PÁGINAS: {len(pages)}")
    print(f"CARACTERES: {len(full)}")
    print()

    # Broken refs
    print("=== REFERÊNCIAS QUEBRADAS (??) ===")
    for m in re.finditer(r"\?\?", full):
        start = max(0, m.start() - 40)
        end = min(len(full), m.end() + 40)
        ctx = full[start:end].replace("\n", " ")
        print(f"  ...{ctx}...")
    if "??" not in full:
        print("  Nenhuma encontrada.")
    print()

    # Appendix mentions
    print("=== APÊNDICES MENCIONADOS ===")
    for pat in [
        r"Apêndice\s+[A-D]",
        r"apêndice\s+[A-D]",
        r"quatro apêndices",
        r"três apêndices",
    ]:
        hits = re.findall(pat, full, re.I)
        if hits:
            print(f"  {pat}: {len(hits)} ocorrências — ex: {hits[:5]}")
    print()

    # Key numbers consistency
    print("=== NÚMEROS-CHAVE (ocorrências) ===")
    patterns = {
        "120 casos": r"120\s*casos",
        "927 passos": r"927\s*passos",
        "S1 2,6%": r"2[,.]6\s*%",
        "S4 12,9%": r"12[,.]9\s*%",
        "54,1% tempo": r"54[,.]1\s*%",
        "44,9% NASA": r"44[,.]9\s*%",
        "373": r"373",
        "c0d5ed6": r"c0d5ed6",
        "gpt-4o-mini": r"gpt-4o-mini",
        "Apêndice C": r"Apêndice\s+C",
        "capturas de tela": r"capturas de tela",
    }
    for label, pat in patterns.items():
        print(f"  {label}: {len(re.findall(pat, full, re.I))}")
    print()

    # Table of contents extraction
    print("=== SUMÁRIO (primeiras entradas) ===")
    toc_text = pages[10] if len(pages) > 10 else ""
    for line in toc_text.split("\n")[:35]:
        if line.strip():
            print(f"  {line[:100]}")
    print()

    # Per-chapter page ranges (heuristic)
    print("=== MARCOS DE CAPÍTULOS ===")
    chapter_markers = []
    for i, t in enumerate(pages):
        for m in re.finditer(r"^(\d+)\s*\n([1-6])\s+([A-ZÁÉÍÓÚÃÕÇ][^\n]{5,60})", t, re.M):
            chapter_markers.append((i + 1, m.group(2), m.group(3)[:50]))
    seen = set()
    for pg, num, title in chapter_markers:
        key = num
        if key not in seen:
            seen.add(key)
            print(f"  Cap {num} ~ p.{pg}: {title}")
    print()

    # Typos / common issues
    print("=== POSSÍVEIS PROBLEMAS DE FORMATAÇÃO ===")
    issues = []
    if re.search(r"pipeline(?![\s\-])", full, re.I):
        issues.append("palavra 'pipeline' colada sem espaço/itálico")
    if "Macelo" in full:
        issues.append("'Macelo' no nome (Marcelo?)")
    if re.search(r"Figura\s+\?\?", full):
        issues.append("Figura ??")
    if re.search(r"Seção\s+\?\?", full):
        issues.append("Seção ??")
    if "estudo humano" in full.lower() and "n=5" not in full.lower() and "cinco testadores" not in full.lower():
        issues.append("estudo humano sem n explícito")
    glued = re.findall(r"[a-záéíóúãõç]{2,}[A-ZÁÉÍÓÚÃÕ][a-záéíóúãõç]{2,}", full)
    glued = [g for g in glued if g not in ("iPhone", "OpenAI", "Wellbeing", "Google")]
    if glued[:10]:
        issues.append(f"palavras coladas: {glued[:8]}")
    for iss in issues:
        print(f"  - {iss}")
    if not issues:
        print("  Nenhum padrão automático crítico.")
    print()

    # Extract each chapter start snippet
    print("=== INÍCIO DE CADA CAPÍTULO (trecho) ===")
    chap_re = re.compile(
        r"(\d+)\s+(INTRODUÇÃO|FUNDAMENTAÇÃO|TRABALHOS RELACIONADOS|MATERIAIS E MÉTODOS|RESULTADOS|CONSIDERAÇÕES FINAIS)",
        re.I,
    )
    for i, t in enumerate(pages):
        m = chap_re.search(t)
        if m:
            pos = m.start()
            snippet = t[pos : pos + 500].replace("\n", " ")
            print(f"\n--- P{i+1} Cap {m.group(1)} ---")
            print(snippet[:450])

    # Appendices in PDF
    print("\n=== APÊNDICES NO PDF ===")
    for i, t in enumerate(pages):
        if re.search(r"APÊNDICE|Apêndice\s+[A-D]|SUÍTES DE TESTE|Esquema do Banco", t, re.I):
            lines = [ln.strip() for ln in t.split("\n") if ln.strip()]
            relevant = [ln for ln in lines if re.search(r"apêndice|APÊNDICE|Suítes|Pipeline|SQLite|Esquema", ln, re.I)]
            if relevant:
                print(f"  P{i+1}: {relevant[0][:90]}")

    # S2 step count variants
    print("\n=== CONTAGEM S2 (134 vs 136) ===")
    print(f"  '134 passos': {len(re.findall(r'134\s*passos', full, re.I))}")
    print(f"  '136 passos': {len(re.findall(r'136\s*passos', full, re.I))}")

    # context_switches S1
    print("\n=== S1 context_switches ===")
    for m in re.finditer(r"context.{0,30}25|context.{0,30}22", full, re.I):
        print(f"  ...{full[max(0,m.start()-20):m.end()+30].replace(chr(10),' ')}...")


if __name__ == "__main__":
    main()
