from __future__ import annotations

import json

from openai import OpenAI

import config
from src.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str = "", model: str = ""):
        self.api_key = api_key or config.OPENAI_API_KEY
        self.model = model or config.OPENAI_MODEL
        self.timeout_s = config.LLM_TIMEOUT_S
        self.client = OpenAI(api_key=self.api_key, timeout=self.timeout_s, max_retries=1)

    def complete(self, prompt: str, *, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            timeout=self.timeout_s,
        )
        return response.choices[0].message.content or ""

    def complete_json(self, prompt: str, *, system_prompt: str = "") -> dict | list:
        full_system = (system_prompt + "\n\n" if system_prompt else "")
        full_system += "Responda APENAS com JSON válido, sem markdown, sem texto adicional."

        messages = [
            {"role": "system", "content": full_system},
            {"role": "user", "content": prompt},
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
            timeout=self.timeout_s,
        )
        raw = response.choices[0].message.content or "{}"
        return json.loads(raw)
