from __future__ import annotations

from src.llm.base import LLMProvider
from src.models.test_case import TestCase

NORMALIZATION_PROMPT = """\
Você é um especialista em testes de software. Receberá uma lista de steps (passos) \
extraídos de diferentes casos de teste.

Sua tarefa: identificar steps que representam a MESMA ação (mesmo que escritos de \
formas diferentes) e agrupá-los sob um ID normalizado.

Regras:
- Steps que fazem exatamente a mesma coisa devem receber o MESMO normalized_id.
- O normalized_id deve ser descritivo, em UPPER_SNAKE_CASE (ex: CRIAR_CONTATO, INICIAR_CHAMADA_VOZ).
- O normalized_text deve ser uma versão limpa e padronizada do step em português.
- Preserve a semântica: "Verifique o ícone de HD" e "Cheque se o ícone HD aparece" são equivalentes, \
  mas "Verifique o ícone de HD" e "Verifique que o vídeo aparece" NÃO são.

Retorne um JSON com a seguinte estrutura:
{
  "mappings": {
    "<texto_original_exato>": {
      "normalized_id": "<ID_NORMALIZADO>",
      "normalized_text": "<Texto padronizado>"
    },
    ...
  }
}

STEPS PARA NORMALIZAR:
"""


def normalize_steps(test_cases: list[TestCase], llm: LLMProvider) -> list[TestCase]:
    """Usa a LLM para normalizar steps equivalentes entre test cases.

    Modifica os steps in-place, preenchendo normalized_id e normalized_text.
    Retorna os mesmos test_cases com steps atualizados.
    """
    unique_steps: dict[str, list[tuple[TestCase, int]]] = {}
    for tc in test_cases:
        for i, step in enumerate(tc.steps):
            text = step.original_text
            if text not in unique_steps:
                unique_steps[text] = []
            unique_steps[text].append((tc, i))

    if not unique_steps:
        return test_cases

    step_list = "\n".join(f"- {text}" for text in unique_steps)
    prompt = NORMALIZATION_PROMPT + step_list

    result = llm.complete_json(prompt)

    mappings = result.get("mappings", {}) if isinstance(result, dict) else {}

    for original_text, locations in unique_steps.items():
        mapping = mappings.get(original_text, {})
        norm_id = mapping.get("normalized_id", _fallback_id(original_text))
        norm_text = mapping.get("normalized_text", original_text)

        for tc, step_idx in locations:
            tc.steps[step_idx].normalized_id = norm_id
            tc.steps[step_idx].normalized_text = norm_text

    return test_cases


def _fallback_id(text: str) -> str:
    """Gera um ID normalizado simples se a LLM não retornar mapeamento."""
    import re
    clean = re.sub(r"[^\w\s]", "", text.upper())
    parts = clean.split()[:5]
    return "_".join(parts) if parts else "STEP_DESCONHECIDO"
