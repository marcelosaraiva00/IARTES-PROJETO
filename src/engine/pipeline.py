from __future__ import annotations

from src.engine.cache import StepCache
from src.engine.classifier import classify_steps
from src.engine.graph_builder import build_prefix_trie, serialize_trie_for_visualization
from src.engine.marker import build_optimization_result
from src.engine.metrics import compute_metrics
from src.engine.normalizer import normalize_steps
from src.engine.optimizer import optimize_sequence
from src.engine.reorder import reorder_tests_for_merge
from src.llm.base import LLMProvider
from src.models.test_case import OptimizationResult, TestCase


def run_optimization_pipeline(
    test_cases: list[TestCase],
    llm: LLMProvider,
    *,
    use_cache: bool = True,
) -> OptimizationResult:
    """Executa o pipeline completo de otimização:

    1. Normaliza steps equivalentes via LLM (com cache)
    2. Classifica steps (verificação/ação, destrutivo/não) via LLM (com cache)
    3. Reordena testes para maximizar compartilhamento de prefixo
    4. Constrói trie/DAG com merge de sufixos compartilhados
    5. Gera sequência otimizada via DFS
    6. Marca pontos de validação de cada teste
    7. Calcula métricas de qualidade
    """
    cache = StepCache(llm.provider_name) if use_cache else None

    test_cases = normalize_steps(test_cases, llm, cache=cache)
    test_cases = classify_steps(test_cases, llm, cache=cache)
    test_cases = reorder_tests_for_merge(test_cases)
    trie_root = build_prefix_trie(test_cases)
    optimized = optimize_sequence(trie_root)
    result = build_optimization_result(optimized, test_cases)
    result.trie_tree = serialize_trie_for_visualization(trie_root)

    metrics = compute_metrics(result)
    result.metrics = metrics.to_dict()

    return result
