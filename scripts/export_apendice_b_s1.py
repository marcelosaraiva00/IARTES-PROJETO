#!/usr/bin/env python3
"""Gera artefatos do Apêndice B (exemplo S1, provedor local)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.engine.pipeline import run_optimization_pipeline
from src.llm.factory import create_llm_provider
from src.parser.input_parser import parse_free_text

SUITE = ROOT / "test_suites" / "suite_1_portugues.txt"
OUT = ROOT / "docs" / "apendice_b"


def main() -> None:
    text = SUITE.read_text(encoding="utf-8")
    cases = parse_free_text(text)
    result = run_optimization_pipeline(cases, create_llm_provider("local"))
    data = result.to_dict()

    OUT.mkdir(parents=True, exist_ok=True)

    entrada: list[str] = []
    case_count = 0
    for line in text.splitlines():
        if line.startswith("TEST-"):
            case_count += 1
            if case_count > 3:
                break
        entrada.append(line)
    (OUT / "entrada_s1_trecho.txt").write_text("\n".join(entrada) + "\n", encoding="utf-8")

    seq_lines: list[str] = []
    for item in data["optimized_sequence"]:
        badges: list[str] = []
        if item["validates_tests"]:
            badges.append("PASSA " + ", ".join(item["validates_tests"]))
        if item["is_resetup"]:
            badges.append("RE-SETUP")
        if item["step_type"] == "verification":
            badges.append("VERIF")
        if item["is_destructive"]:
            badges.append("DESTRUTIVO")
        suffix = f" [{'; '.join(badges)}]" if badges else ""
        seq_lines.append(f"{item['position']:3d}. {item['step_text']}{suffix}")
    (OUT / "sequencia_s1_local.txt").write_text("\n".join(seq_lines) + "\n", encoding="utf-8")

    metrics = data.get("metrics", {})
    stats = data.get("stats", {})
    summary = {
        "suite": "S1 (suite_1_portugues.txt)",
        "provider": "local",
        "stats": stats,
        "metrics": metrics,
    }
    (OUT / "metricas_s1_local.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    rows = [
        ("test_count", metrics.get("test_count")),
        ("total_original_steps", metrics.get("total_original_steps", stats.get("original_step_count"))),
        ("total_optimized_steps", metrics.get("total_optimized_steps", stats.get("optimized_step_count"))),
        ("steps_eliminated", metrics.get("steps_eliminated", stats.get("steps_saved"))),
        ("reduction_percent", metrics.get("reduction_percent", stats.get("reduction_percent"))),
        ("resetup_count", metrics.get("resetup_count")),
        ("merge_depth_max", metrics.get("merge_depth_max")),
        ("context_switches", metrics.get("context_switches")),
        ("destructive_steps", metrics.get("destructive_steps")),
        ("unique_normalized_ids", metrics.get("unique_normalized_ids")),
    ]
    (OUT / "metricas_s1_local.txt").write_text(
        "\n".join(f"{k}: {v}" for k, v in rows if v is not None) + "\n",
        encoding="utf-8",
    )

    print(f"Artefatos em {OUT}")
    print("stats:", stats)


if __name__ == "__main__":
    main()
