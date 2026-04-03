from __future__ import annotations

from dataclasses import dataclass, field

from src.models.test_case import Step, StepType, TestCase


@dataclass
class TrieNode:
    """Nó de uma árvore de prefixos (Trie) de steps normalizados."""

    normalized_id: str
    step: Step | None = None
    children: dict[str, "TrieNode"] = field(default_factory=dict)
    validates_tests: list[str] = field(default_factory=list)

    @property
    def is_verification(self) -> bool:
        if self.step is None:
            return False
        return self.step.step_type == StepType.VERIFICATION

    @property
    def is_destructive(self) -> bool:
        if self.step is None:
            return False
        return self.step.is_destructive


def build_prefix_trie(test_cases: list[TestCase]) -> TrieNode:
    """Constrói uma árvore de prefixos a partir dos test cases normalizados.

    Cada caminho raiz→folha representa um test case.
    Nós compartilhados = steps que aparecem na mesma posição em múltiplos testes.
    """
    root = TrieNode(normalized_id="ROOT")

    for tc in test_cases:
        current = root
        for i, step in enumerate(tc.steps):
            nid = step.normalized_id or step.original_text

            if nid not in current.children:
                current.children[nid] = TrieNode(
                    normalized_id=nid,
                    step=step,
                )
            current = current.children[nid]

            is_last_step = (i == len(tc.steps) - 1)
            if is_last_step:
                current.validates_tests.append(tc.id)

    return root
