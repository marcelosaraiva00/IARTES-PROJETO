from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / ".cache"


class StepCache:
    """Cache em disco para normalizações e classificações de steps.

    Evita chamadas repetidas à LLM para steps já processados.
    Cada provider tem seu próprio namespace de cache.
    """

    def __init__(self, provider_name: str):
        self._provider = provider_name
        self._norm_cache: dict[str, dict] = {}
        self._class_cache: dict[str, dict] = {}
        self._dir = CACHE_DIR / provider_name
        self._dir.mkdir(parents=True, exist_ok=True)
        self._load()

    def _cache_file(self) -> Path:
        return self._dir / "step_cache.json"

    def _load(self) -> None:
        path = self._cache_file()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self._norm_cache = data.get("normalizations", {})
                self._class_cache = data.get("classifications", {})
            except (json.JSONDecodeError, OSError):
                self._norm_cache = {}
                self._class_cache = {}

    def _save(self) -> None:
        data = {
            "normalizations": self._norm_cache,
            "classifications": self._class_cache,
        }
        self._cache_file().write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @staticmethod
    def _key(text: str) -> str:
        return hashlib.md5(text.strip().lower().encode()).hexdigest()

    def get_normalization(self, original_text: str) -> dict | None:
        return self._norm_cache.get(self._key(original_text))

    def set_normalization(self, original_text: str, mapping: dict) -> None:
        self._norm_cache[self._key(original_text)] = mapping

    def get_classification(self, normalized_id: str) -> dict | None:
        return self._class_cache.get(normalized_id)

    def set_classification(self, normalized_id: str, info: dict) -> None:
        self._class_cache[normalized_id] = info

    def save(self) -> None:
        self._save()

    @property
    def norm_count(self) -> int:
        return len(self._norm_cache)

    @property
    def class_count(self) -> int:
        return len(self._class_cache)
