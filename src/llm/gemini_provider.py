from __future__ import annotations

import json
import re

import google.generativeai as genai

import config
from src.llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str = "", model: str = ""):
        self.api_key = api_key or config.GEMINI_API_KEY
        self.model_name = model or config.GEMINI_MODEL
        self.timeout_s = config.LLM_TIMEOUT_S
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def complete(self, prompt: str, *, system_prompt: str = "") -> str:
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        response = self.model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.2),
            request_options={"timeout": self.timeout_s},
        )
        return response.text or ""

    def complete_json(self, prompt: str, *, system_prompt: str = "") -> dict | list:
        json_instruction = "Responda APENAS com JSON válido, sem markdown, sem texto adicional."
        full_system = f"{system_prompt}\n\n{json_instruction}" if system_prompt else json_instruction
        full_prompt = f"{full_system}\n\n{prompt}"

        response = self.model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
            request_options={"timeout": self.timeout_s},
        )
        raw = response.text or "{}"
        raw = _extract_json(raw)
        return json.loads(raw)


def _extract_json(text: str) -> str:
    """Remove blocos de código markdown se presentes."""
    match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()
