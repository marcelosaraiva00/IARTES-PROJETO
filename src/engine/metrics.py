from __future__ import annotations

from dataclasses import dataclass
from src.models.test_case import OptimizationResult, StepType


@dataclass
class OptimizationMetrics:
    """Métricas detalhadas da qualidade de uma otimização."""

    total_original_steps: int
    total_optimized_steps: int
    steps_eliminated: int
    reduction_percent: float

    unique_normalized_ids: int
    normalized_groups: int

    verifications_detected: int
    actions_detected: int
    destructive_steps: int

    resetup_count: int
    context_switches: int

    merge_depth_max: int
    merge_depth_avg: float

    test_count: int

    def to_dict(self) -> dict:
        return {
            "total_original_steps": self.total_original_steps,
            "total_optimized_steps": self.total_optimized_steps,
            "steps_eliminated": self.steps_eliminated,
            "reduction_percent": round(self.reduction_percent, 1),
            "unique_normalized_ids": self.unique_normalized_ids,
            "normalized_groups": self.normalized_groups,
            "verifications_detected": self.verifications_detected,
            "actions_detected": self.actions_detected,
            "destructive_steps": self.destructive_steps,
            "resetup_count": self.resetup_count,
            "context_switches": self.context_switches,
            "merge_depth_max": self.merge_depth_max,
            "merge_depth_avg": round(self.merge_depth_avg, 2),
            "test_count": self.test_count,
        }


def compute_metrics(result: OptimizationResult) -> OptimizationMetrics:
    """Calcula métricas detalhadas a partir de um OptimizationResult."""
    total_original = result.original_step_count
    total_optimized = result.optimized_step_count
    steps_eliminated = total_original - total_optimized
    reduction = (steps_eliminated / total_original * 100) if total_original > 0 else 0.0

    all_norm_ids: set[str] = set()
    norm_groups: dict[str, set[str]] = {}
    for tc in result.original_test_cases:
        for step in tc.steps:
            nid = step.normalized_id or step.original_text
            all_norm_ids.add(nid)
            if nid not in norm_groups:
                norm_groups[nid] = set()
            norm_groups[nid].add(step.original_text)

    verifications = 0
    actions = 0
    destructive = 0
    for nid in all_norm_ids:
        step = _find_step_by_nid(result, nid)
        if step is None:
            actions += 1
            continue
        if step.step_type == StepType.VERIFICATION:
            verifications += 1
        else:
            actions += 1
        if step.is_destructive:
            destructive += 1

    resetup_count = sum(1 for opt in result.optimized_sequence if opt.is_resetup)

    context_switches = 0
    for i, opt in enumerate(result.optimized_sequence):
        if i == 0:
            continue
        if opt.step.is_destructive and not opt.is_resetup:
            context_switches += 1

    merge_depths = _compute_merge_depths(result)
    merge_max = max(merge_depths) if merge_depths else 0
    merge_avg = sum(merge_depths) / len(merge_depths) if merge_depths else 0.0

    return OptimizationMetrics(
        total_original_steps=total_original,
        total_optimized_steps=total_optimized,
        steps_eliminated=steps_eliminated,
        reduction_percent=reduction,
        unique_normalized_ids=len(all_norm_ids),
        normalized_groups=len(norm_groups),
        verifications_detected=verifications,
        actions_detected=actions,
        destructive_steps=destructive,
        resetup_count=resetup_count,
        context_switches=context_switches,
        merge_depth_max=merge_max,
        merge_depth_avg=merge_avg,
        test_count=len(result.original_test_cases),
    )


def _find_step_by_nid(result: OptimizationResult, nid: str):
    for tc in result.original_test_cases:
        for step in tc.steps:
            if (step.normalized_id or step.original_text) == nid:
                return step
    return None


def _compute_merge_depths(result: OptimizationResult) -> list[int]:
    """Calcula a profundidade de merge para cada par de test cases.

    Profundidade de merge = quantos steps consecutivos desde o início
    dois test cases compartilham (o prefixo comum na trie).
    """
    test_cases = result.original_test_cases
    if len(test_cases) < 2:
        return [0]

    depths = []
    for i in range(len(test_cases)):
        for j in range(i + 1, len(test_cases)):
            tc_a = test_cases[i]
            tc_b = test_cases[j]
            depth = 0
            for step_a, step_b in zip(tc_a.steps, tc_b.steps):
                nid_a = step_a.normalized_id or step_a.original_text
                nid_b = step_b.normalized_id or step_b.original_text
                if nid_a == nid_b:
                    depth += 1
                else:
                    break
            depths.append(depth)

    return depths if depths else [0]
