from __future__ import annotations

import re
import unicodedata

from src.engine.graph_builder import TrieNode
from src.models.test_case import OptimizedStep, StepType

# Verbos que indicam destruição TOTAL do contexto (encerram/removem o que os
# ancestrais construíram). Após um branch com esses verbos, é necessário
# re-executar os steps ancestrais para restaurar o contexto.
_CONTEXT_BREAKING_VERBS = {
    # BB8 Group 13: End, Finish, Complete, Exit, Close
    "end", "finish", "complete", "exit", "close", "stop", "quit",
    "encerre", "encerrar", "finalize", "finalizar",
    "feche", "fechar", "saia", "sair", "pare", "parar",
    "termine", "terminar",
    # BB8 Group 18: Remove, Delete
    "remove", "delete", "clear", "erase", "wipe",
    "remova", "remover", "deletar", "apague", "apagar",
    "exclua", "excluir", "limpe", "limpar",
    # BB8 Group 11: Disconnect
    "disconnect", "desconecte", "desconectar",
    # BB8 Group 20: System reset/reboot
    "reboot", "restart", "reset", "factory",
    "reinicie", "reiniciar", "resete", "resetar",
    "restaure", "restaurar", "formate", "formatar",
}


def optimize_sequence(root: TrieNode) -> list[OptimizedStep]:
    """Percorre a trie via DFS gerando a sequência otimizada de steps.

    Regras:
      1. Verificações primeiro, depois ações não-destrutivas, depois destrutivas
      2. Entre destrutivas: as que preservam contexto antes, as que quebram contexto por último
      3. Após um branch que quebra contexto, re-emite os steps ancestrais (re-setup)
    """
    result: list[OptimizedStep] = []
    _dfs(root, result, ancestor_path=[])
    return result


def _child_sort_key(node: TrieNode) -> tuple[int, int, int, str]:
    """Chave de ordenação dos filhos de um nó.

    Branches cujo subtree quebra contexto vão SEMPRE por último, independente
    de o nó raiz do branch ser verificação ou não. Isso garante que ações como
    "Encerre a chamada" só aconteçam quando todos os outros branches já
    foram executados.
    """
    breaks = _subtree_breaks_context(node)

    if breaks:
        priority = 3
    elif node.is_verification:
        priority = 0
    elif not node.is_destructive:
        priority = 1
    else:
        priority = 2

    has_verifications_below = _has_verification_descendants(node)
    sub_priority = 0 if has_verifications_below else 1

    subtree_size = _subtree_size(node)

    return (priority, sub_priority, subtree_size, node.normalized_id)


def _has_verification_descendants(node: TrieNode) -> bool:
    for child in node.children.values():
        if child.is_verification:
            return True
        if _has_verification_descendants(child):
            return True
    return False


def _subtree_size(node: TrieNode) -> int:
    """Conta nós na subárvore (branches menores primeiro para otimizar)."""
    count = 1
    for child in node.children.values():
        count += _subtree_size(child)
    return count


def _subtree_breaks_context(node: TrieNode) -> bool:
    """Verifica se a subárvore contém steps que quebram o contexto dos ancestrais."""
    if node.step is not None and _step_breaks_context(node.step):
        return True
    for child in node.children.values():
        if _subtree_breaks_context(child):
            return True
    return False


def _step_breaks_context(step) -> bool:
    """Verifica se um step individual quebra o contexto (usando verbos BB8)."""
    text = step.display_text() if hasattr(step, "display_text") else str(step)
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    words = re.findall(r"[a-zA-Z]+", normalized.lower())
    for word in words:
        if word in _CONTEXT_BREAKING_VERBS:
            return True
    return False


def _dfs(
    node: TrieNode,
    result: list[OptimizedStep],
    ancestor_path: list[TrieNode],
) -> None:
    """DFS que gera sequência otimizada com re-setup quando contexto é quebrado."""
    if node.step is not None:
        opt_step = OptimizedStep(
            step=node.step,
            validates_tests=list(node.validates_tests),
        )
        result.append(opt_step)

    current_path = ancestor_path + ([node] if node.step is not None else [])
    sorted_children = sorted(node.children.values(), key=_child_sort_key)

    needs_resetup = False
    for i, child in enumerate(sorted_children):
        if needs_resetup and current_path:
            _emit_resetup(current_path, result)
            needs_resetup = False

        _dfs(child, result, current_path)

        is_last = (i == len(sorted_children) - 1)
        if not is_last and _subtree_breaks_context(child):
            needs_resetup = True


def _emit_resetup(ancestor_path: list[TrieNode], result: list[OptimizedStep]) -> None:
    """Re-emite os steps ancestrais para restaurar o contexto."""
    for ancestor in ancestor_path:
        if ancestor.step is not None:
            opt_step = OptimizedStep(
                step=ancestor.step,
                validates_tests=[],
                is_resetup=True,
            )
            result.append(opt_step)
