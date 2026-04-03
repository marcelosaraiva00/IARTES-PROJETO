from __future__ import annotations

import config
from src.llm.base import LLMProvider


def create_llm_provider(provider: str = "") -> LLMProvider:
    """Factory que retorna o provider de LLM configurado."""
    provider = (provider or config.LLM_PROVIDER).lower().strip()

    if provider == "local":
        from src.llm.local_provider import LocalProvider
        return LocalProvider()

    if provider == "openai":
        from src.llm.openai_provider import OpenAIProvider
        return OpenAIProvider()

    if provider in ("gemini", "google"):
        from src.llm.gemini_provider import GeminiProvider
        return GeminiProvider()

    raise ValueError(
        f"Provider '{provider}' não suportado. Use 'local', 'openai' ou 'gemini'."
    )
