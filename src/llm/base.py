from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Interface abstrata para provedores de LLM."""

    @property
    def provider_name(self) -> str:
        return self.__class__.__name__.lower().replace("provider", "")

    @abstractmethod
    def complete(self, prompt: str, *, system_prompt: str = "") -> str:
        """Envia um prompt e retorna a resposta da LLM como texto."""
        ...

    @abstractmethod
    def complete_json(self, prompt: str, *, system_prompt: str = "") -> dict | list:
        """Envia um prompt e retorna a resposta parseada como JSON."""
        ...
