from __future__ import annotations

from src.llm.base import LLMProvider
from src.models.test_case import StepType, TestCase

CLASSIFICATION_PROMPT = """\
Você é um especialista em testes de software. Receberá uma lista de steps (passos) \
normalizados de casos de teste.

Sua tarefa: classificar cada step em duas dimensões:

1. **step_type**: o step é uma VERIFICAÇÃO (apenas observa/checa algo, não muda o estado \
do sistema) ou uma AÇÃO (realiza algo que pode mudar o estado)?
   - "verification" = verificação (ex: "Verifique o ícone de HD", "Confira que o vídeo aparece")
   - "action" = ação (ex: "Crie um contato", "Faça upgrade para vídeo")

2. **is_destructive**: se for uma ação, ela DESTRÓI ou ALTERA o contexto/estado atual?
   - true = muda o estado de forma significativa (ex: "Encerre a ligação", "Faça upgrade para vídeo", "Delete o contato")
   - false = não destrói contexto (ex: "Crie um contato" quando é setup inicial, verificações)
   - Verificações são SEMPRE is_destructive = false

Dica: ações que MUDAM o modo atual (voz → vídeo, ligado → desligado, etc.) são destrutivas. \
Ações de SETUP inicial (criar contato, iniciar chamada) não são destrutivas pois constroem contexto.

Retorne um JSON:
{
  "classifications": {
    "<normalized_id>": {
      "step_type": "verification" | "action",
      "is_destructive": true | false,
      "reasoning": "<breve justificativa>"
    },
    ...
  }
}

STEPS PARA CLASSIFICAR:
"""


def classify_steps(test_cases: list[TestCase], llm: LLMProvider) -> list[TestCase]:
    """Usa a LLM para classificar cada step normalizado.

    Modifica os steps in-place, preenchendo step_type e is_destructive.
    Retorna os mesmos test_cases com steps atualizados.
    """
    unique_normalized: dict[str, str] = {}
    for tc in test_cases:
        for step in tc.steps:
            nid = step.normalized_id
            if nid and nid not in unique_normalized:
                unique_normalized[nid] = step.display_text()

    if not unique_normalized:
        return test_cases

    step_list = "\n".join(
        f"- {nid}: \"{text}\"" for nid, text in unique_normalized.items()
    )
    prompt = CLASSIFICATION_PROMPT + step_list

    result = llm.complete_json(prompt)

    classifications = result.get("classifications", {}) if isinstance(result, dict) else {}

    for tc in test_cases:
        for step in tc.steps:
            nid = step.normalized_id
            if nid and nid in classifications:
                info = classifications[nid]
                raw_type = info.get("step_type", "action")
                step.step_type = (
                    StepType.VERIFICATION if raw_type == "verification" else StepType.ACTION
                )
                step.is_destructive = bool(info.get("is_destructive", False))

    return test_cases
