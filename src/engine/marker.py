from __future__ import annotations

from src.models.test_case import OptimizationResult, OptimizedStep, TestCase


def build_optimization_result(
    optimized_sequence: list[OptimizedStep],
    original_test_cases: list[TestCase],
) -> OptimizationResult:
    """Constrói o resultado final de otimização com todas as estatísticas.

    Garante que todos os testes estejam marcados como validados em algum ponto
    da sequência. Se algum teste não foi marcado pela trie (caso raro), marca
    no último step que pertence ao seu caminho.
    """
    validated_ids = set()
    for opt_step in optimized_sequence:
        for tid in opt_step.validates_tests:
            validated_ids.add(tid)

    all_test_ids = {tc.id for tc in original_test_cases}
    missing = all_test_ids - validated_ids

    if missing and optimized_sequence:
        for tid in missing:
            tc = next((t for t in original_test_cases if t.id == tid), None)
            if tc is None:
                continue
            last_norm_ids = {
                s.normalized_id or s.original_text for s in tc.steps
            }
            for opt_step in reversed(optimized_sequence):
                step_nid = opt_step.step.normalized_id or opt_step.step.original_text
                if step_nid in last_norm_ids:
                    opt_step.validates_tests.append(tid)
                    break

    return OptimizationResult(
        optimized_sequence=optimized_sequence,
        original_test_cases=original_test_cases,
    )
