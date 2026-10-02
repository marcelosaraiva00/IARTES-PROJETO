#!/usr/bin/env python3
"""Gera captura PNG da tela Sequência Otimizada (provedor local) para o TCC."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.parser.input_parser import parse_free_text
from src.engine.pipeline import run_optimization_pipeline
from src.llm.factory import create_llm_provider

CSS = """
:root {
    --bg: #0f1117;
    --bg-card: #1a1d27;
    --border: #2e3140;
    --text: #e4e6ed;
    --text-muted: #8b8fa3;
    --accent: #6c63ff;
    --success: #22c55e;
    --radius: 8px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 24px;
    width: 900px;
}
h2 { font-size: 1.35rem; margin-bottom: 1rem; }
.stats-bar {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 0.75rem;
    margin-bottom: 1rem;
}
.stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.85rem 0.5rem;
    text-align: center;
}
.stat-value { font-size: 1.5rem; font-weight: 700; }
.stat-label { font-size: 0.72rem; color: var(--text-muted); margin-top: 0.2rem; }
.metrics-panel summary {
    cursor: pointer;
    color: var(--accent);
    margin-bottom: 0.75rem;
    font-weight: 600;
}
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.65rem;
}
.metric-item {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.75rem;
    text-align: center;
}
.metric-value { display: block; font-size: 1.25rem; font-weight: 700; }
.metric-label { display: block; font-size: 0.7rem; color: var(--text-muted); margin-top: 0.25rem; }
"""


def build_html(data: dict) -> str:
    stats = data["stats"]
    metrics = data["metrics"]
    metric_items = [
        ("Steps Únicos (norm. IDs)", metrics["unique_normalized_ids"]),
        ("Grupos Normalizados", metrics["normalized_groups"]),
        ("Verificações Detectadas", metrics["verifications_detected"]),
        ("Ações Detectadas", metrics["actions_detected"]),
        ("Steps Destrutivos", metrics["destructive_steps"]),
        ("Re-setups Inseridos", metrics["resetup_count"]),
        ("Trocas de Contexto", metrics["context_switches"]),
        ("Profundidade Merge (máx)", metrics["merge_depth_max"]),
        ("Profundidade Merge (média)", metrics["merge_depth_avg"]),
    ]
    metrics_html = "".join(
        f'<div class="metric-item"><span class="metric-value">{v}</span>'
        f'<span class="metric-label">{label}</span></div>'
        for label, v in metric_items
    )
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><style>{CSS}</style></head>
<body>
<h2>Sequência Otimizada</h2>
<div class="stats-bar">
  <div class="stat-card"><div class="stat-value">{stats['test_count']}</div><div class="stat-label">Testes</div></div>
  <div class="stat-card"><div class="stat-value">{stats['original_step_count']}</div><div class="stat-label">Steps Originais</div></div>
  <div class="stat-card"><div class="stat-value">{stats['optimized_step_count']}</div><div class="stat-label">Steps Otimizados</div></div>
  <div class="stat-card"><div class="stat-value" style="color:var(--success)">{stats['steps_saved']}</div><div class="stat-label">Steps Economizados</div></div>
  <div class="stat-card"><div class="stat-value" style="color:var(--success)">{stats['reduction_percent']}%</div><div class="stat-label">Redução</div></div>
</div>
<details class="metrics-panel" open>
  <summary>Métricas Detalhadas</summary>
  <div class="metrics-grid">{metrics_html}</div>
</details>
</body></html>"""


def screenshot_html(html: str, output: Path) -> None:
    from playwright.sync_api import sync_playwright

    tmp = output.with_suffix(".html")
    tmp.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 900, "height": 520})
        page.goto(tmp.as_uri())
        page.locator("body").screenshot(path=str(output))
        browser.close()
    tmp.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--suite",
        type=Path,
        default=ROOT / "test_suites" / "suite_4_portugues.txt",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "figures" / "corrigidas" / "local-suite4.png",
    )
    args = parser.parse_args()

    text = args.suite.read_text(encoding="utf-8")
    cases = parse_free_text(text)
    llm = create_llm_provider("local")
    result = run_optimization_pipeline(cases, llm)
    data = result.to_dict()
    html = build_html(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    screenshot_html(html, args.output)
    print(f"Gerado: {args.output}")


if __name__ == "__main__":
    main()
