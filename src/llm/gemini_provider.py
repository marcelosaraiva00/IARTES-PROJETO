from __future__ import annotations

import json
import re

from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types

import config
from src.llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str = "", model: str = ""):
        self.api_key = api_key or config.GEMINI_API_KEY
        self.model_name = model or config.GEMINI_MODEL
        self.timeout_s = config.LLM_TIMEOUT_S
        self.max_retries = max(0, config.GEMINI_MAX_RETRIES)
        self.base_delay_s = max(0.2, config.GEMINI_RETRY_BASE_DELAY_S)
        self.fallback_models = [
            m for m in config.GEMINI_FALLBACK_MODELS if m and m != self.model_name
        ]
        self.models_to_try = [self.model_name, *self.fallback_models]

        # Mantém o estilo "simples e direto" do provider OpenAI:
        # timeout + retry padronizados no cliente, e chamadas lineares.
        self.client = genai.Client(
            api_key=self.api_key,
            http_options=genai_types.HttpOptions(
                timeout=int(self.timeout_s),
                retryOptions=genai_types.HttpRetryOptions(
                    attempts=self.max_retries + 1,
                    initialDelay=self.base_delay_s,
                    maxDelay=6.0,
                    expBase=2.0,
                    jitter=0.2,
                    httpStatusCodes=[429, 500, 502, 503, 504],
                ),
            ),
        )

    def complete(self, prompt: str, *, system_prompt: str = "") -> str:
        cfg = genai_types.GenerateContentConfig(
            temperature=0.2,
            systemInstruction=system_prompt or None,
        )
        response = self._generate_with_fallback(prompt, config=cfg)
        return response.text or ""

    def complete_json(self, prompt: str, *, system_prompt: str = "") -> dict | list:
        json_instruction = "Responda APENAS com JSON válido, sem markdown, sem texto adicional."
        full_system = (system_prompt + "\n\n" if system_prompt else "") + json_instruction

        cfg = genai_types.GenerateContentConfig(
            systemInstruction=full_system,
            temperature=0.1,
            responseMimeType="application/json",
        )
        response = self._generate_with_fallback(
            prompt,
            config=cfg,
        )
        raw = response.text or "{}"
        raw = _extract_json(raw)
        return json.loads(raw)

    def _generate_with_fallback(
        self,
        prompt: str,
        *,
        config: genai_types.GenerateContentConfig,
    ):
        last_error: Exception | None = None
        for model_name in self.models_to_try:
            try:
                return self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
            except Exception as exc:
                last_error = exc
                if not _is_retryable_error(exc):
                    raise
                continue

        if last_error:
            raise last_error
        raise RuntimeError("Falha inesperada ao chamar Gemini.")


def _extract_json(text: str) -> str:
    """Remove blocos de código markdown se presentes."""
    match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def _is_retryable_error(exc: Exception) -> bool:
    if isinstance(exc, genai_errors.APIError):
        code = getattr(exc, "code", None)
        if isinstance(code, int) and code in (429, 500, 502, 503, 504):
            return True
        status = str(getattr(exc, "status", "")).lower()
        if "unavailable" in status or "deadline" in status:
            return True

    text = str(exc).lower()
    return (
        "503" in text
        or "429" in text
        or "service unavailable" in text
        or "high demand" in text
        or "deadline exceeded" in text
    )
