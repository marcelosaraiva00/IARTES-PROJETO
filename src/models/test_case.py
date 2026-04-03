from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class StepType(str, Enum):
    VERIFICATION = "verification"
    ACTION = "action"


@dataclass
class Step:
    """Um passo individual dentro de um caso de teste."""

    original_text: str
    normalized_id: Optional[str] = None
    normalized_text: Optional[str] = None
    step_type: StepType = StepType.ACTION
    is_destructive: bool = False

    def display_text(self) -> str:
        return self.normalized_text or self.original_text


@dataclass
class TestCase:
    """Um caso de teste composto por uma sequência ordenada de steps."""

    id: str
    name: str
    steps: list[Step] = field(default_factory=list)

    @property
    def step_count(self) -> int:
        return len(self.steps)


@dataclass
class OptimizedStep:
    """Um step na sequência otimizada, com marcações de quais testes valida."""

    step: Step
    validates_tests: list[str] = field(default_factory=list)
    is_resetup: bool = False


@dataclass
class OptimizationResult:
    """Resultado completo da otimização."""

    optimized_sequence: list[OptimizedStep] = field(default_factory=list)
    original_test_cases: list[TestCase] = field(default_factory=list)

    @property
    def original_step_count(self) -> int:
        return sum(tc.step_count for tc in self.original_test_cases)

    @property
    def optimized_step_count(self) -> int:
        return len(self.optimized_sequence)

    @property
    def steps_saved(self) -> int:
        return self.original_step_count - self.optimized_step_count

    @property
    def reduction_percent(self) -> float:
        if self.original_step_count == 0:
            return 0.0
        return (self.steps_saved / self.original_step_count) * 100

    def to_dict(self) -> dict:
        sequence = []
        for i, opt_step in enumerate(self.optimized_sequence, 1):
            entry = {
                "position": i,
                "step_text": opt_step.step.display_text(),
                "original_text": opt_step.step.original_text,
                "step_type": opt_step.step.step_type.value,
                "is_destructive": opt_step.step.is_destructive,
                "is_resetup": opt_step.is_resetup,
                "validates_tests": opt_step.validates_tests,
            }
            sequence.append(entry)

        return {
            "optimized_sequence": sequence,
            "stats": {
                "original_step_count": self.original_step_count,
                "optimized_step_count": self.optimized_step_count,
                "steps_saved": self.steps_saved,
                "reduction_percent": round(self.reduction_percent, 1),
                "test_count": len(self.original_test_cases),
            },
            "original_tests": [
                {"id": tc.id, "name": tc.name, "step_count": tc.step_count}
                for tc in self.original_test_cases
            ],
        }
