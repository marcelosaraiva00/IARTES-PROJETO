#!/usr/bin/env python3
"""Auditoria completa do PDF do TCC: ??, referências e termos EN fora de itálico."""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

import fitz  # pymupdf

PDF = Path(__file__).resolve().parent.parent / "docs" / "TCC_IARTES___Janio_Macelo_Renilson.pdf"

# Termos em inglês que convenção editorial costuma exigir em itálico.
EN_TERMS = [
    "pipeline", "benchmark", "trie", "Design Science Research", "human-in-the-loop",
    "Human-in-the-Loop", "trade-off", "tradeoff", "Knowledge Base", "framework",
    "frameworks", "template", "templates", "endpoint", "endpoints", "cache",
    "checkpoint", "outlier", "merge", "prompt", "prompts", "software", "step",
    "steps", "upload", "download", "backtracking", "hash", "commit", "provider",
    "providers", "insight", "insights", "baseline", "dataset", "datasets",
    "overhead", "setup", "re-setup", "resetup", "web", "online", "offline",
    "review", "release", "deploy", "score", "feedback", "test case", "test cases",
    "machine learning", "deep learning", "natural language processing",
]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    doc = fitz.open(str(PDF))
    n_pages = doc.page_count
    print(f"PÁGINAS: {n_pages}\n")

    # Coleta spans com info de itálico
    # italic_map[palavra_lower] -> {'italic': set(pages), 'roman': set(pages)}
    term_status = defaultdict(lambda: {"italic": [], "roman": []})
    full_text_parts = []
    # Guardar (page, texto, italic_bool) por span para varredura de frases
    spans_all = []  # (page_no, text, is_italic)

    for pno in range(n_pages):
        page = doc[pno]
        d = page.get_text("dict")
        page_text = []
        for block in d.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    if not text.strip():
                        continue
                    font = span.get("font", "")
                    flags = span.get("flags", 0)
                    # bit 1 (value 2) = italic; também checa nome da fonte
                    is_italic = bool(flags & 2) or ("italic" in font.lower()) or ("oblique" in font.lower()) or font.lower().endswith("ti")
                    spans_all.append((pno + 1, text, is_italic, font))
                    page_text.append(text)
        full_text_parts.append(" ".join(page_text))

    full_text = "\n".join(full_text_parts)

    # ---- 1. Marcadores ?? ----
    print("=" * 70)
    print("1. REFERÊNCIAS QUEBRADAS (??)")
    print("=" * 70)
    found = False
    for pno, part in enumerate(full_text_parts):
        for m in re.finditer(r"\?\?", part):
            found = True
            s = max(0, m.start() - 50)
            e = min(len(part), m.end() + 50)
            print(f"  P{pno+1}: ...{part[s:e]}...")
    if not found:
        print("  Nenhuma ocorrência de '??' encontrada.")
    print()

    # ---- 2. Referências a Figuras/Tabelas/Quadros ----
    print("=" * 70)
    print("2. NUMERAÇÃO DE FIGURAS / TABELAS / QUADROS (definições)")
    print("=" * 70)
    for kind in ["Figura", "Tabela", "Quadro"]:
        # legendas definidas: 'Figura N –' ou 'Figura N -'
        defs = sorted(set(int(m) for m in re.findall(rf"{kind}\s+(\d+)\s*[–\-]", full_text)))
        # citações no texto: 'Figura N' / 'Figuras N'
        cites = sorted(set(int(m) for m in re.findall(rf"{kind}s?~?\s+(\d+)", full_text)))
        print(f"  {kind}: definidas={defs}")
        missing_def = [c for c in cites if c not in defs]
        if missing_def:
            print(f"    !! citadas sem legenda correspondente: {missing_def}")
        # gaps
        if defs:
            gaps = [i for i in range(1, max(defs) + 1) if i not in defs]
            if gaps:
                print(f"    !! lacunas na sequência: {gaps}")
    print()

    # ---- 3. Seções citadas ----
    print("=" * 70)
    print("3. CITAÇÕES A SEÇÕES (amostra de padrões suspeitos)")
    print("=" * 70)
    sec_cites = re.findall(r"Se[çc][ãa]o\s+(\d+(?:\.\d+)*)", full_text)
    print(f"  Total de citações 'Seção X': {len(sec_cites)}")
    weird = [s for s in sec_cites if s.count(".") >= 3]
    if weird:
        print(f"  !! numeração com >=4 níveis (revisar): {sorted(set(weird))}")
    print()

    # ---- 4. Citações bibliográficas quebradas ----
    print("=" * 70)
    print("4. POSSÍVEIS CITAÇÕES QUEBRADAS")
    print("=" * 70)
    for pat, label in [
        (r"\[\?\]", "[?]"),
        (r"\bautor desconhecido\b", "autor desconhecido"),
        (r"\bCITEKEY\b", "CITEKEY"),
        (r"\(\s*,\s*\d{4}\)", "(, ANO) — autor vazio"),
        (r"\(\s*\?\s*\)", "(?)"),
    ]:
        hits = re.findall(pat, full_text)
        if hits:
            print(f"  {label}: {len(hits)} ocorrência(s)")
    print("  (checagem heurística — validar no BibTeX do Overleaf)")
    print()

    # ---- 5. Termos EN fora de itálico ----
    print("=" * 70)
    print("5. TERMOS EM INGLÊS — ITÁLICO vs. ROMANO (por span)")
    print("=" * 70)

    # Normaliza spans: agrupa por termo isolado (palavra) - abordagem por palavra única
    # Para termos compostos, faz busca no full_text por span concatenado é complexo;
    # aqui tratamos termo simples (uma palavra) via spans; compostos reportados à parte.
    simple_terms = {t.lower() for t in EN_TERMS if " " not in t and "-" not in t}
    roman_hits = defaultdict(list)
    italic_hits = defaultdict(list)

    for pno, text, is_italic, font in spans_all:
        # tokeniza palavras do span (o itálico vale para todo o span)
        for w in re.findall(r"[A-Za-zÀ-ÿ]+", text):
            wl = w.lower()
            if wl in simple_terms:
                if is_italic:
                    italic_hits[wl].append(pno)
                else:
                    roman_hits[wl].append(pno)

    print("\n  -- Palavras simples --")
    print(f"  {'termo':<16}{'itálico':<24}{'ROMANO (revisar)':<30}")
    for t in sorted(simple_terms):
        it = italic_hits.get(t, [])
        ro = roman_hits.get(t, [])
        if not it and not ro:
            continue
        it_pages = ",".join(str(x) for x in sorted(set(it))[:8])
        ro_pages = ",".join(str(x) for x in sorted(set(ro))[:12])
        flag = "  <<<" if ro else ""
        print(f"  {t:<16}{('p.'+it_pages if it else '-'):<24}{('p.'+ro_pages if ro else '-'):<30}{flag}")

    # Compostos: busca no full_text e verifica itálico do primeiro token
    print("\n  -- Termos compostos (checagem por 1º token) --")
    compound = [t for t in EN_TERMS if " " in t or "-" in t]
    first_token_italic = defaultdict(lambda: {"it": set(), "ro": set()})
    for pno, text, is_italic, font in spans_all:
        for c in compound:
            head = re.split(r"[ \-]", c)[0].lower()
            if re.search(rf"\b{re.escape(head)}\b", text.lower()):
                if is_italic:
                    first_token_italic[c]["it"].add(pno)
                else:
                    first_token_italic[c]["ro"].add(pno)
    for c in compound:
        data = first_token_italic[c]
        if not data["it"] and not data["ro"]:
            continue
        ro = ",".join(str(x) for x in sorted(data["ro"])[:12])
        it = ",".join(str(x) for x in sorted(data["it"])[:8])
        flag = "  <<< revisar" if data["ro"] else ""
        print(f"  {c:<28} it:[{it}]  roman:[{ro}]{flag}")

    print("\n  NOTA: 'ROMANO' lista páginas onde o termo aparece SEM itálico.")
    print("  Pode haver falsos positivos (nomes próprios, siglas, títulos, sumário).")
    print()

    # ---- 6. Nome no arquivo ----
    print("=" * 70)
    print("6. OUTRAS CHECAGENS")
    print("=" * 70)
    print(f"  'Macelo' (nome) ocorre no texto: {full_text.count('Macelo')}  (verificar Marcelo)")
    print(f"  'gpt-4o-mini' ocorrências: {len(re.findall(r'gpt-4o-mini', full_text))}")
    print(f"  Total de páginas: {n_pages}")


if __name__ == "__main__":
    main()
