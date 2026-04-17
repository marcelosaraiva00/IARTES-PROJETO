#!/usr/bin/env python3
"""
Gera tabelas Markdown e LaTeX a partir do JSON de uma execução do IARTES.

Uso:
  python scripts/generate_result_tables.py --json resultado.json
  python scripts/generate_result_tables.py --json benchmark.json --label "S1"
  python scripts/generate_result_tables.py --demo --suite test_suites/suite_grande_portugues.txt

O JSON pode ser:
  - Resposta de /api/optimize (objeto com stats, metrics, optimized_sequence)
  - Resposta de /api/benchmark (objeto com runs, providers, comparison_table)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


METRIC_KEYS = [
    "test_count",
    "total_original_steps",
    "total_optimized_steps",
    "reduction_percent",
    "steps_eliminated",
    "resetup_count",
    "context_switches",
    "destructive_steps",
    "unique_normalized_ids",
    "normalized_groups",
    "verifications_detected",
    "actions_detected",
    "merge_depth_max",
    "merge_depth_avg",
]

METRIC_LABELS_PT = {
    "test_count": "Nº casos de teste",
    "total_original_steps": "Passos originais",
    "total_optimized_steps": "Passos otimizados",
    "reduction_percent": "Redução (%)",
    "steps_eliminated": "Passos eliminados",
    "resetup_count": "Re-setups",
    "context_switches": "Trocas de contexto",
    "destructive_steps": "Passos destrutivos",
    "unique_normalized_ids": "IDs normalizados únicos",
    "normalized_groups": "Grupos normalizados",
    "verifications_detected": "Verificações (contagem)",
    "actions_detected": "Ações (contagem)",
    "merge_depth_max": "Prof. merge (máx)",
    "merge_depth_avg": "Prof. merge (média)",
}


def _load_json(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return json.loads(text)


def _is_benchmark(data: dict) -> bool:
    return isinstance(data.get("runs"), list) and len(data["runs"]) > 0


def _escape_latex(s: str) -> str:
    return (
        s.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("_", "\\_")
        .replace("#", "\\#")
    )


def table_single_run_markdown(
    data: dict,
    suite_label: str,
    elapsed_ms: float | None,
) -> str:
    stats = data.get("stats") or {}
    metrics = data.get("metrics") or {}
    lines = [
        f"### Tabela gerada automaticamente — suíte `{suite_label}`",
        "",
        "| Métrica | Valor |",
        "|---------|-------|",
    ]
    tc = stats.get("test_count", metrics.get("test_count", "—"))
    lines.append(f"| Suíte (rótulo) | {suite_label} |")
    lines.append(f"| `test_count` | {tc} |")
    lines.append(f"| `total_original_steps` | {stats.get('original_step_count', metrics.get('total_original_steps', '—'))} |")
    lines.append(f"| `total_optimized_steps` | {stats.get('optimized_step_count', metrics.get('total_optimized_steps', '—'))} |")
    lines.append(f"| `steps_eliminated` | {stats.get('steps_saved', metrics.get('steps_eliminated', '—'))} |")
    lines.append(f"| `reduction_percent` | {stats.get('reduction_percent', metrics.get('reduction_percent', '—'))} |")
    for key in METRIC_KEYS:
        if key == "test_count":
            continue
        if key in ("total_original_steps", "total_optimized_steps", "reduction_percent", "steps_eliminated"):
            continue
        val = metrics.get(key, "—")
        label = METRIC_LABELS_PT.get(key, key)
        lines.append(f"| `{key}` ({label}) | {val} |")
    if elapsed_ms is not None:
        lines.append(f"| Tempo pipeline (ms) | {round(elapsed_ms, 1)} |")
    lines.append("")
    return "\n".join(lines)


def table_single_run_latex(
    data: dict,
    suite_label: str,
    elapsed_ms: float | None,
    caption: str,
    label: str,
) -> str:
    stats = data.get("stats") or {}
    metrics = data.get("metrics") or {}
    rows = []
    rows.append((r"Suíte (rótulo)", _escape_latex(suite_label)))
    rows.append((r"\texttt{test\_count}", str(metrics.get("test_count", stats.get("test_count", "—")))))
    rows.append((r"\texttt{total\_original\_steps}", str(stats.get("original_step_count", metrics.get("total_original_steps", "—")))))
    rows.append((r"\texttt{total\_optimized\_steps}", str(stats.get("optimized_step_count", metrics.get("total_optimized_steps", "—")))))
    rows.append((r"\texttt{steps\_eliminated}", str(stats.get("steps_saved", metrics.get("steps_eliminated", "—")))))
    rows.append((r"\texttt{reduction\_percent}", str(stats.get("reduction_percent", metrics.get("reduction_percent", "—")))))
    for key in METRIC_KEYS:
        if key in ("test_count", "total_original_steps", "total_optimized_steps", "reduction_percent", "steps_eliminated"):
            continue
        val = metrics.get(key, "—")
        safe_key = key.replace("_", r"\_")
        rows.append((rf"\texttt{{{safe_key}}}", str(val)))
    if elapsed_ms is not None:
        rows.append(("Tempo pipeline (ms)", str(round(elapsed_ms, 1))))

    body = "\n".join(f"{a} & {b} \\\\" for a, b in rows)
    return "\n".join(
        [
            r"\begin{table}[ht]",
            r"\centering",
            r"\caption{" + _escape_latex(caption) + "}",
            r"\label{" + label + "}",
            r"\begin{tabular}{l r}",
            r"\hline",
            r"\textbf{Métrica} & \textbf{Valor} \\",
            r"\hline",
            body,
            r"\hline",
            r"\end{tabular}",
            r"\end{table}",
            "",
        ]
    )


def table_benchmark_markdown(data: dict, suite_label: str) -> str:
    runs = data["runs"]
    providers = [r["provider"] for r in runs]
    header = "| Métrica | " + " | ".join(providers) + " |"
    sep = "|" + "|".join(["---"] * (len(providers) + 1)) + "|"
    lines = [
        f"### Benchmark — suíte `{suite_label}`",
        "",
        header,
        sep,
    ]
    keys_order = [
        "reduction_percent",
        "total_optimized_steps",
        "total_original_steps",
        "steps_eliminated",
        "resetup_count",
        "context_switches",
        "destructive_steps",
        "merge_depth_max",
        "merge_depth_avg",
        "unique_normalized_ids",
        "normalized_groups",
        "verifications_detected",
        "actions_detected",
        "test_count",
    ]
    for key in keys_order:
        row = [f"`{key}`"]
        for r in runs:
            m = r.get("metrics") or {}
            row.append(str(m.get(key, "—")))
        lines.append("| " + " | ".join(row) + " |")
    lines.append("| `elapsed_ms` (tempo) | " + " | ".join(str(r.get("elapsed_ms", "—")) for r in runs) + " |")
    lines.append("")
    return "\n".join(lines)


def table_benchmark_latex(data: dict, suite_label: str, caption: str, label: str) -> str:
    runs = data["runs"]
    providers = [r["provider"] for r in runs]
    n = len(providers)
    colspec = "l" + "r" * n
    header = "Métrica & " + " & ".join(_escape_latex(p) for p in providers) + r" \\"

    keys_order = [
        "reduction_percent",
        "total_optimized_steps",
        "total_original_steps",
        "steps_eliminated",
        "resetup_count",
        "context_switches",
        "destructive_steps",
        "merge_depth_max",
        "merge_depth_avg",
    ]
    body_rows = [r"\hline", header, r"\hline"]
    for key in keys_order:
        cells = [f"\\texttt{{{key.replace('_', '\\_')}}}"]
        for r in runs:
            m = r.get("metrics") or {}
            cells.append(str(m.get(key, "—")))
        body_rows.append(" & ".join(cells) + r" \\")

    body_rows.append(
        "Tempo (ms) & " + " & ".join(str(r.get("elapsed_ms", "—")) for r in runs) + r" \\"
    )
    body_rows.append(r"\hline")
    tabular = "\n".join(body_rows)
    return "\n".join(
        [
            r"\begin{table}[ht]",
            r"\centering",
            r"\small",
            r"\caption{" + _escape_latex(caption) + "}",
            r"\label{" + label + "}",
            rf"\begin{{tabular}}{{{colspec}}}",
            tabular,
            r"\end{tabular}",
            r"\end{table}",
            "",
        ]
    )


def run_demo(suite_path: Path, fmt: str) -> None:
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root))
    from src.parser.input_parser import parse_free_text
    from src.engine.pipeline import run_optimization_pipeline
    from src.llm.factory import create_llm_provider

    text = suite_path.read_text(encoding="utf-8")
    test_cases = parse_free_text(text)
    llm = create_llm_provider("local")
    result = run_optimization_pipeline(test_cases, llm)
    data = result.to_dict()
    label = suite_path.stem
    md = table_single_run_markdown(data, label, elapsed_ms=None)
    if fmt in ("markdown", "both"):
        print(md)
    if fmt in ("latex", "both"):
        print(
            table_single_run_latex(
                data,
                label,
                elapsed_ms=None,
                caption=f"Resultados com provedor local na suíte {label}.",
                label="tab:resultados-demo",
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera tabelas Markdown/LaTeX a partir de JSON do IARTES.")
    parser.add_argument("--json", type=Path, help="Ficheiro JSON (optimize ou benchmark).")
    parser.add_argument("--label", default="", help="Rótulo da suíte (ex.: S1). Por omissão: nome do ficheiro JSON.")
    parser.add_argument("--elapsed-ms", type=float, default=None, help="Tempo da execução (se não estiver no JSON).")
    parser.add_argument("--format", choices=("markdown", "latex", "both"), default="both")
    parser.add_argument("--latex-caption", default="", help="Legenda LaTeX (tabela única).")
    parser.add_argument("--latex-label", default="tab:resultados", help="Label LaTeX \\ref{...}.")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Executa pipeline local sobre uma suíte em texto e imprime as tabelas.",
    )
    parser.add_argument(
        "--suite",
        type=Path,
        default=None,
        help="Com --demo: caminho para ficheiro .txt (padrão: test_suites/suite_grande_portugues.txt).",
    )
    parser.add_argument("-o", "--output", type=Path, default=None, help="Escrever saída neste ficheiro em vez de stdout.")
    args = parser.parse_args()

    if args.demo:
        root = Path(__file__).resolve().parent.parent
        suite = args.suite or (root / "test_suites" / "suite_grande_portugues.txt")
        if not suite.is_file():
            print(f"Suíte não encontrada: {suite}", file=sys.stderr)
            sys.exit(1)
        import io

        buf = io.StringIO()
        old_out = sys.stdout
        sys.stdout = buf
        try:
            run_demo(suite, args.format)
        finally:
            sys.stdout = old_out
        out = buf.getvalue()
        if args.output:
            args.output.write_text(out, encoding="utf-8")
        else:
            sys.stdout.write(out)
        return

    if not args.json:
        parser.error("Indique --json FICHEIRO.json ou use --demo.")

    data = _load_json(args.json)
    label = args.label or args.json.stem
    caption = args.latex_caption or f"Resultados da execução ({label})."
    latex_label = args.latex_label

    chunks: list[str] = []
    if _is_benchmark(data):
        if args.format in ("markdown", "both"):
            chunks.append(table_benchmark_markdown(data, label))
        if args.format in ("latex", "both"):
            chunks.append(
                table_benchmark_latex(
                    data,
                    label,
                    caption=caption or f"Benchmark na suíte {label}.",
                    label=latex_label,
                )
            )
    else:
        if args.format in ("markdown", "both"):
            chunks.append(table_single_run_markdown(data, label, args.elapsed_ms))
        if args.format in ("latex", "both"):
            chunks.append(
                table_single_run_latex(
                    data,
                    label,
                    caption=caption,
                    label=latex_label,
                )
            )

    out = "\n".join(chunks)
    if args.output:
        args.output.write_text(out, encoding="utf-8")
    else:
        print(out, end="")


if __name__ == "__main__":
    main()
