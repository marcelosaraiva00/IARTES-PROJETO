from __future__ import annotations

import csv
import io
import json
from typing import Any


def export_result_json(result_dict: dict) -> str:
    """Exporta resultado de otimização como JSON formatado."""
    return json.dumps(result_dict, ensure_ascii=False, indent=2)


def export_result_csv(result_dict: dict) -> str:
    """Exporta a sequência otimizada como CSV."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Posição",
        "Step",
        "Texto Original",
        "Tipo",
        "Destrutivo",
        "Re-setup",
        "Valida Testes",
    ])

    for item in result_dict.get("optimized_sequence", []):
        writer.writerow([
            item["position"],
            item["step_text"],
            item["original_text"],
            item["step_type"],
            "Sim" if item["is_destructive"] else "Não",
            "Sim" if item["is_resetup"] else "Não",
            ", ".join(item["validates_tests"]) if item["validates_tests"] else "",
        ])

    return output.getvalue()


def export_metrics_csv(metrics_dict: dict) -> str:
    """Exporta métricas como CSV (uma linha por métrica)."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Métrica", "Valor"])

    labels = {
        "total_original_steps": "Total Steps Originais",
        "total_optimized_steps": "Total Steps Otimizados",
        "steps_eliminated": "Steps Eliminados",
        "reduction_percent": "Redução (%)",
        "unique_normalized_ids": "Steps Únicos (norm. IDs)",
        "normalized_groups": "Grupos Normalizados",
        "verifications_detected": "Verificações Detectadas",
        "actions_detected": "Ações Detectadas",
        "destructive_steps": "Steps Destrutivos",
        "resetup_count": "Re-setups Inseridos",
        "context_switches": "Trocas de Contexto",
        "merge_depth_max": "Profundidade Merge (máx)",
        "merge_depth_avg": "Profundidade Merge (média)",
        "test_count": "Quantidade de Testes",
    }

    for key, label in labels.items():
        if key in metrics_dict:
            writer.writerow([label, metrics_dict[key]])

    return output.getvalue()


def export_benchmark_csv(benchmark_dict: dict) -> str:
    """Exporta tabela comparativa de benchmark como CSV."""
    output = io.StringIO()
    writer = csv.writer(output)

    providers = benchmark_dict.get("providers", [])
    header = ["Métrica"] + [p.capitalize() for p in providers]
    writer.writerow(header)

    for key, row in benchmark_dict.get("comparison_table", {}).items():
        csv_row = [row.get("label", key)]
        for p in providers:
            csv_row.append(row.get(p, ""))
        writer.writerow(csv_row)

    return output.getvalue()
