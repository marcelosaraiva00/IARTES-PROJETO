from __future__ import annotations

from src.engine.classifier import classify_steps
from src.engine.graph_builder import build_prefix_trie
from src.engine.marker import build_optimization_result
from src.engine.normalizer import normalize_steps
from src.engine.optimizer import optimize_sequence
from src.llm.base import LLMProvider
from src.models.test_case import OptimizationResult, TestCase


def run_optimization_pipeline(
    test_cases: list[TestCase],
    llm: LLMProvider,
) -> OptimizationResult:
    """Executa o pipeline completo de otimização:

    1. Normaliza steps equivalentes via LLM
    2. Classifica steps (verificação/ação, destrutivo/não) via LLM
    3. Constrói árvore de prefixos (trie)
    4. Gera sequência otimizada via DFS
    5. Marca pontos de validação de cada teste
    """
    test_cases = normalize_steps(test_cases, llm)
    test_cases = classify_steps(test_cases, llm)
    trie_root = build_prefix_trie(test_cases)
    optimized = optimize_sequence(trie_root)
    result = build_optimization_result(optimized, test_cases)
    return result
