#!/usr/bin/env python3
"""Foco: termos EN em ROMANO apenas no corpo (13-74), com contexto de frase."""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

import fitz

PDF = Path(__file__).resolve().parent.parent / "docs" / "TCC_IARTES___Janio_Macelo_Renilson.pdf"

# Corpo textual (exclui capa/sumário 1-12, apêndices 75-103, referências 104+)
BODY_START, BODY_END = 13, 74

# Termos que DEVEM ficar em itálico (empréstimos técnicos não assimilados).
# 'software' foi EXCLUÍDO (loanword consagrado em PT, romano é correto).
TARGET = [
    "pipeline", "benchmark", "trie", "framework", "frameworks", "template",
    "templates", "endpoint", "endpoints", "cache", "checkpoint", "outlier",
    "merge", "prompt", "prompts", "upload", "download", "backtracking",
    "baseline", "dataset", "datasets", "overhead", "setup", "resetup",
    "insight", "insights", "feedback", "score", "trade-off", "tradeoff",
]
COMPOUND = [
    "Design Science Research", "human-in-the-loop", "Knowledge Base",
    "re-setup", "machine learning", "deep learning",
]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    doc = fitz.open(str(PDF))

    roman = defaultdict(list)  # term -> [(page, snippet)]
    for pno in range(doc.page_count):
        page_num = pno + 1
        if not (BODY_START <= page_num <= BODY_END):
            continue
        d = doc[pno].get_text("dict")
        # reconstruir texto da página + mapa itálico por palavra
        for block in d.get("blocks", []):
            for line in block.get("lines", []):
                line_text = "".join(s.get("text", "") for s in line.get("spans", []))
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    if not text.strip():
                        continue
                    font = span.get("font", "")
                    flags = span.get("flags", 0)
                    is_italic = bool(flags & 2) or ("italic" in font.lower()) or ("oblique" in font.lower())
                    if is_italic:
                        continue
                    tl = text.lower()
                    for term in TARGET:
                        if re.search(rf"\b{re.escape(term)}\b", tl):
                            roman[term].append((page_num, line_text.strip()[:90]))
                    for c in COMPOUND:
                        head = re.split(r"[ \-]", c)[0].lower()
                        if re.search(rf"\b{re.escape(head)}\b", tl):
                            # confirmar frase completa na linha
                            if re.search(re.escape(c).replace(r"\ ", r"[ \-]"), line_text, re.I):
                                roman[c].append((page_num, line_text.strip()[:90]))

    print("TERMOS EM INGLÊS SEM ITÁLICO — CORPO (p.13-74)\n")
    for term in TARGET + COMPOUND:
        hits = roman.get(term, [])
        if not hits:
            continue
        # dedup por (page, snippet)
        seen = []
        for pg, sn in hits:
            if (pg, sn) not in seen:
                seen.append((pg, sn))
        pages = sorted(set(p for p, _ in seen))
        print(f"### {term}  — páginas: {pages}")
        shown = set()
        for pg, sn in seen:
            if pg in shown:
                continue
            shown.add(pg)
            print(f"    p.{pg}: {sn}")
        print()


if __name__ == "__main__":
    main()
