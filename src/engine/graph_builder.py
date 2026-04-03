from __future__ import annotations

from dataclasses import dataclass, field

from src.models.test_case import Step, StepType, TestCase


@dataclass
class TrieNode:
    """Nó de uma árvore de prefixos (Trie/DAG) de steps normalizados."""

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

    merge_shared_suffixes(root)
    return root


def merge_shared_suffixes(root: TrieNode) -> None:
    """Merge de sufixos idênticos na trie, transformando-a em DAG.

    Se dois branches no mesmo nível pai têm subárvores estruturalmente
    idênticas (mesmos normalized_ids), eles são fundidos: os validates_tests
    são unificados e o branch duplicado é removido.
    """
    _merge_recursive(root)


def _subtree_signature(node: TrieNode) -> str:
    """Gera uma assinatura textual da subárvore para comparação de equivalência."""
    child_sigs = sorted(
        f"{nid}:{_subtree_signature(child)}"
        for nid, child in node.children.items()
    )
    validations = ",".join(sorted(node.validates_tests)) if node.validates_tests else ""
    return f"[{validations}]({';'.join(child_sigs)})"


def _merge_recursive(node: TrieNode) -> None:
    """Percorre a árvore bottom-up e merge nós com subárvores idênticas."""
    for child in list(node.children.values()):
        _merge_recursive(child)

    if len(node.children) < 2:
        return

    sig_to_nids: dict[str, list[str]] = {}
    for nid, child in node.children.items():
        sig = _subtree_signature(child)
        if sig not in sig_to_nids:
            sig_to_nids[sig] = []
        sig_to_nids[sig].append(nid)

    for sig, nids in sig_to_nids.items():
        if len(nids) < 2:
            continue
        canonical_nid = nids[0]
        canonical_node = node.children[canonical_nid]
        for dup_nid in nids[1:]:
            dup_node = node.children[dup_nid]
            _absorb_validations(canonical_node, dup_node)
            del node.children[dup_nid]


def _absorb_validations(target: TrieNode, source: TrieNode) -> None:
    """Transfere validates_tests de source para target recursivamente."""
    for tid in source.validates_tests:
        if tid not in target.validates_tests:
            target.validates_tests.append(tid)

    for nid, src_child in source.children.items():
        if nid in target.children:
            _absorb_validations(target.children[nid], src_child)
        else:
            target.children[nid] = src_child
