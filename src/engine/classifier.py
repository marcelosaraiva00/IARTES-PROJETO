from __future__ import annotations

from src.engine.cache import StepCache
from src.llm.base import LLMProvider
from src.models.test_case import StepType, TestCase

CLASSIFICATION_PROMPT = """\
You are a software testing expert specialized in mobile device testing. \
You will receive a list of normalized test steps.

Classify each step on two dimensions:

1. **step_type**: Does this step only OBSERVE/CHECK something, or does it PERFORM an action?
   - "verification" = only observes, checks, or validates something WITHOUT changing system state.
     Examples: "Check the HD icon", "Verify video appears", "The mute icon should be visible",
     "Audio must be working normally", "The call should be connected", "Observe if it returned to voice"
   - "action" = performs something that may change the system state.
     Examples: "Create a contact", "Start a voice call", "Upgrade to video", "Tap the mute button"

2. **is_destructive**: If it's an action, does it CHANGE or DESTROY the current context/state?
   - true = significantly changes the current state. Examples:
     "Upgrade to video call" (changes call mode from voice to video)
     "End the call" (destroys the call entirely)
     "Tap the mute button" (changes audio state)
     "Downgrade to voice" (changes call mode)
     "Disconnect Bluetooth" (breaks connection)
     "Delete the contact" (removes data)
   - false = builds or maintains context without destroying existing state. Examples:
     "Create a contact" (initial setup, creates new context)
     "Start a voice call" (initial setup)
     "Open settings" (navigation, doesn't change state)
   - Verifications are ALWAYS is_destructive = false

KEY INSIGHT: The question is "does this step change what was already established?"
Setup steps (create, start, open) BUILD context = not destructive.
Steps that ALTER existing state (upgrade, mute, end, delete, switch) = destructive.

Return JSON:
{
  "classifications": {
    "<normalized_id>": {
      "step_type": "verification" | "action",
      "is_destructive": true | false,
      "reasoning": "<brief justification>"
    }
  }
}

IMPORTANT: Every single step below MUST appear in the classifications. Do not skip any.

STEPS TO CLASSIFY:
"""

BATCH_SIZE = 40


def _normalize_classification(info: dict) -> dict:
    """Garante regra do domínio: verificação nunca é destrutiva (corrige LLM/KB antiga)."""
    out = dict(info)
    if out.get("step_type") == "verification":
        out["is_destructive"] = False
    return out


def classify_steps(
    test_cases: list[TestCase],
    llm: LLMProvider,
    cache: StepCache | None = None,
) -> list[TestCase]:
    """Classifica cada step normalizado (verificação/ação, destrutivo/não).

    Usa cache para evitar re-processar steps já classificados.
    Processa steps novos em batches.
    """
    unique_normalized: dict[str, str] = {}
    for tc in test_cases:
        for step in tc.steps:
            nid = step.normalized_id
            if nid and nid not in unique_normalized:
                unique_normalized[nid] = step.display_text()

    if not unique_normalized:
        return test_cases

    cached: dict[str, dict] = {}
    uncached: dict[str, str] = {}

    for nid, text in unique_normalized.items():
        if cache:
            hit = cache.get_classification(nid)
            if hit:
                cached[nid] = _normalize_classification(hit)
                continue
        uncached[nid] = text

    all_classifications: dict[str, dict] = dict(cached)

    uncached_items = list(uncached.items())
    for i in range(0, len(uncached_items), BATCH_SIZE):
        batch = uncached_items[i : i + BATCH_SIZE]
        step_list = "\n".join(f'- {nid}: "{text}"' for nid, text in batch)
        prompt = CLASSIFICATION_PROMPT + step_list
        result = llm.complete_json(prompt)
        classifications = result.get("classifications", {}) if isinstance(result, dict) else {}

        for nid, _text in batch:
            info = _normalize_classification(
                classifications.get(nid, {"step_type": "action", "is_destructive": False})
            )
            all_classifications[nid] = info
            if cache:
                cache.set_classification(nid, info)

    for tc in test_cases:
        for step in tc.steps:
            nid = step.normalized_id
            if nid and nid in all_classifications:
                info = _normalize_classification(all_classifications[nid])
                raw_type = info.get("step_type", "action")
                step.step_type = (
                    StepType.VERIFICATION if raw_type == "verification" else StepType.ACTION
                )
                step.is_destructive = bool(info.get("is_destructive", False))

    if cache:
        cache.save()

    return test_cases
