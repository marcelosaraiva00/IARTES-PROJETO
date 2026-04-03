from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field

from src.engine.metrics import OptimizationMetrics, compute_metrics
from src.engine.pipeline import run_optimization_pipeline
from src.llm.base import LLMProvider
from src.llm.factory import create_llm_provider
from src.models.test_case import OptimizationResult, TestCase


@dataclass
class BenchmarkRun:
    provider_name: str
    result: OptimizationResult
    metrics: OptimizationMetrics
    elapsed_ms: float


@dataclass
class BenchmarkComparison:
    runs: list[BenchmarkRun] = field(default_factory=list)

    def to_dict(self) -> dict:
        comparison_table: dict[str, dict[str, object]] = {}

        labels = {
            "unique_normalized_ids": "Steps Únicos Detectados",
            "normalized_groups": "Grupos Normalizados",
            "verifications_detected": "Verificações Detectadas",
            "actions_detected": "Ações Detectadas",
            "destructive_steps": "Steps Destrutivos",
            "total_optimized_steps": "Steps Otimizados",
            "steps_eliminated": "Steps Eliminados",
            "reduction_percent": "Redução %",
            "resetup_count": "Re-setups",
            "context_switches": "Trocas de Contexto",
            "merge_depth_max": "Profundidade Merge (máx)",
            "merge_depth_avg": "Profundidade Merge (média)",
        }

        for key, label in labels.items():
            row: dict[str, object] = {"label": label}
            for run in self.runs:
                row[run.provider_name] = getattr(run.metrics, key)
            comparison_table[key] = row

        timing_row: dict[str, object] = {"label": "Tempo (ms)"}
        for run in self.runs:
            timing_row[run.provider_name] = round(run.elapsed_ms, 1)
        comparison_table["elapsed_ms"] = timing_row

        runs_data = []
        for run in self.runs:
            runs_data.append({
                "provider": run.provider_name,
                "elapsed_ms": round(run.elapsed_ms, 1),
                "metrics": run.metrics.to_dict(),
                "result": run.result.to_dict(),
            })

        return {
            "comparison_table": comparison_table,
            "runs": runs_data,
            "providers": [r.provider_name for r in self.runs],
        }


def run_benchmark(
    test_cases: list[TestCase],
    provider_names: list[str] | None = None,
) -> BenchmarkComparison:
    """Executa o pipeline com múltiplos providers e retorna comparação.

    Por padrão compara 'local' com todos os providers configurados com API key.
    """
    if provider_names is None:
        provider_names = _detect_available_providers()

    comparison = BenchmarkComparison()

    for name in provider_names:
        try:
            provider = create_llm_provider(name)
        except (ValueError, Exception):
            continue

        tc_copy = copy.deepcopy(test_cases)

        start = time.perf_counter()
        result = run_optimization_pipeline(tc_copy, provider, use_cache=False)
        elapsed = (time.perf_counter() - start) * 1000

        metrics = compute_metrics(result)

        comparison.runs.append(BenchmarkRun(
            provider_name=name,
            result=result,
            metrics=metrics,
            elapsed_ms=elapsed,
        ))

    return comparison


def _detect_available_providers() -> list[str]:
    import config
    providers = ["local"]
    if config.OPENAI_API_KEY:
        providers.append("openai")
    if config.GEMINI_API_KEY:
        providers.append("gemini")
    return providers
