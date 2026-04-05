from __future__ import annotations

from src.database.db import (
    kb_get_classification,
    kb_get_normalization,
    kb_save_classification,
    kb_save_classifications_batch,
    kb_save_normalization,
    kb_save_normalizations_batch,
)


class StepCache:
    """Cache persistente em SQLite para normalizações e classificações.

    Cada provider registra seus resultados. Na leitura, busca primeiro
    resultados do próprio provider, depois de qualquer provider (knowledge
    base cross-provider).
    """

    def __init__(self, provider_name: str):
        self._provider = provider_name
        self._pending_norms: list[tuple[str, str, str]] = []
        self._pending_classes: list[tuple[str, str, bool]] = []

    def get_normalization(self, original_text: str) -> dict | None:
        hit = kb_get_normalization(original_text, provider=self._provider)
        if hit:
            return {"normalized_id": hit["normalized_id"], "normalized_text": hit["normalized_text"]}
        hit = kb_get_normalization(original_text, provider=None)
        if hit:
            return {"normalized_id": hit["normalized_id"], "normalized_text": hit["normalized_text"]}
        return None

    def set_normalization(self, original_text: str, mapping: dict) -> None:
        nid = mapping.get("normalized_id", "")
        ntext = mapping.get("normalized_text", original_text)
        self._pending_norms.append((original_text, nid, ntext))

    def get_classification(self, normalized_id: str) -> dict | None:
        hit = kb_get_classification(normalized_id, provider=self._provider)
        if hit:
            return {"step_type": hit["step_type"], "is_destructive": hit["is_destructive"]}
        hit = kb_get_classification(normalized_id, provider=None)
        if hit:
            return {"step_type": hit["step_type"], "is_destructive": hit["is_destructive"]}
        return None

    def set_classification(self, normalized_id: str, info: dict) -> None:
        step_type = info.get("step_type", "action")
        is_destructive = bool(info.get("is_destructive", False))
        self._pending_classes.append((normalized_id, step_type, is_destructive))

    def save(self) -> None:
        if self._pending_norms:
            kb_save_normalizations_batch(self._provider, self._pending_norms)
            self._pending_norms.clear()
        if self._pending_classes:
            kb_save_classifications_batch(self._provider, self._pending_classes)
            self._pending_classes.clear()

    @property
    def norm_count(self) -> int:
        from src.database.db import kb_get_stats
        stats = kb_get_stats()
        return stats.get("normalizations_total", 0)

    @property
    def class_count(self) -> int:
        from src.database.db import kb_get_stats
        stats = kb_get_stats()
        return stats.get("classifications_total", 0)
