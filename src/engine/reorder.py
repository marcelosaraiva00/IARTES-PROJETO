from __future__ import annotations

from src.models.test_case import TestCase


def reorder_tests_for_merge(test_cases: list[TestCase]) -> list[TestCase]:
    """Reordena test cases para maximizar compartilhamento de prefixo na trie.

    Usa algoritmo greedy nearest-neighbor: começa pelo teste com mais steps,
    e a cada passo escolhe o teste não selecionado com o prefixo mais longo
    em comum com o último selecionado.
    """
    if len(test_cases) <= 2:
        return test_cases

    nid_sequences = {
        tc.id: [s.normalized_id or s.original_text for s in tc.steps]
        for tc in test_cases
    }
    tc_map = {tc.id: tc for tc in test_cases}

    remaining = set(tc.id for tc in test_cases)
    first_id = max(remaining, key=lambda tid: len(nid_sequences[tid]))
    remaining.remove(first_id)
    ordered = [first_id]

    while remaining:
        last_seq = nid_sequences[ordered[-1]]
        best_id = None
        best_prefix_len = -1

        for tid in remaining:
            plen = _common_prefix_length(last_seq, nid_sequences[tid])
            if plen > best_prefix_len or (
                plen == best_prefix_len and len(nid_sequences[tid]) > len(nid_sequences.get(best_id, []))
            ):
                best_prefix_len = plen
                best_id = tid

        remaining.remove(best_id)
        ordered.append(best_id)

    return [tc_map[tid] for tid in ordered]


def _common_prefix_length(seq_a: list[str], seq_b: list[str]) -> int:
    length = 0
    for a, b in zip(seq_a, seq_b):
        if a == b:
            length += 1
        else:
            break
    return length
