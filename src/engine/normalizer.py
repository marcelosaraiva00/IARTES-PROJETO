from __future__ import annotations

from src.engine.cache import StepCache
from src.llm.base import LLMProvider
from src.models.test_case import TestCase

NORMALIZATION_PROMPT = """\
You are a software testing expert. You will receive a list of test steps extracted \
from different test cases, possibly written by different people in different styles.

Your task: identify steps that represent the SAME action (even if written differently) \
and group them under a single normalized ID.

CRITICAL RULES:
- Steps that do the same thing MUST receive the SAME normalized_id, even if worded very differently.
- Synonymous verbs for the same action = SAME step. Examples:
  "Create a contact" = "Add a contact" = "Register a new contact" (all create a contact)
  "Start a voice call" = "Initiate a call" = "Place a call" = "Begin a call" = "Make a call"
  "Upgrade to video" = "Switch to video call" (both change call to video mode)
  "Check the HD icon" = "Verify the HD icon" = "Confirm the HD icon is visible"
- The normalized_id must be descriptive, in UPPER_SNAKE_CASE (e.g.: CREATE_CONTACT, START_VOICE_CALL).
- The normalized_text must be a clean, standardized version of the step IN THE SAME LANGUAGE as the original steps.
- DO NOT translate steps. Keep the same language as the input.
- Assertions like "The mute icon should be visible" or "Audio must be working normally" are ALSO steps \
  and should be normalized (they are verification/observation steps).

Return a JSON with this structure:
{
  "mappings": {
    "<exact_original_text>": {
      "normalized_id": "<NORMALIZED_ID>",
      "normalized_text": "<Standardized text>"
    }
  }
}

IMPORTANT: Every single step in the list below MUST appear as a key in the mappings. Do not skip any.

STEPS TO NORMALIZE:
"""

BATCH_SIZE = 40


def normalize_steps(
    test_cases: list[TestCase],
    llm: LLMProvider,
    cache: StepCache | None = None,
) -> list[TestCase]:
    """Normaliza steps equivalentes entre test cases.

    Usa cache para evitar re-processar steps já conhecidos.
    Processa steps novos em batches para não estourar contexto da LLM.
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

    cached: dict[str, dict] = {}
    uncached: list[str] = []

    for text in unique_steps:
        if cache:
            hit = cache.get_normalization(text)
            if hit:
                cached[text] = hit
                continue
        uncached.append(text)

    all_mappings: dict[str, dict] = dict(cached)

    for batch in _batches(uncached, BATCH_SIZE):
        step_list = "\n".join(f"- {text}" for text in batch)
        prompt = NORMALIZATION_PROMPT + step_list
        result = llm.complete_json(prompt)
        mappings = result.get("mappings", {}) if isinstance(result, dict) else {}

        for text in batch:
            mapping = mappings.get(text, {})
            if not mapping.get("normalized_id"):
                mapping = {
                    "normalized_id": _fallback_id(text),
                    "normalized_text": text,
                }
            all_mappings[text] = mapping
            if cache:
                cache.set_normalization(text, mapping)

    for original_text, locations in unique_steps.items():
        mapping = all_mappings.get(original_text, {})
        norm_id = mapping.get("normalized_id", _fallback_id(original_text))
        norm_text = mapping.get("normalized_text", original_text)

        for tc, step_idx in locations:
            tc.steps[step_idx].normalized_id = norm_id
            tc.steps[step_idx].normalized_text = norm_text

    if cache:
        cache.save()

    return test_cases


def _batches(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _fallback_id(text: str) -> str:
    import re
    clean = re.sub(r"[^\w\s]", "", text.upper())
    parts = clean.split()[:5]
    return "_".join(parts) if parts else "STEP_UNKNOWN"
