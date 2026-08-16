from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

__all__ = ["InputField", "CalcResult", "CalculatorPlugin"]

VALID_FIELD_TYPES = ("number", "select", "text")


@dataclass(frozen=True)
class InputField:
    name: str
    label: str
    type: str
    default: Any = None
    options: tuple = ()
    min_val: float | None = None
    max_val: float | None = None
    help_text: str = ""

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("InputField.name must be a non-empty string.")
        if not self.label or not self.label.strip():
            raise ValueError("InputField.label must be a non-empty string.")
        if self.type not in VALID_FIELD_TYPES:
            raise ValueError(
                f"InputField.type must be one of {VALID_FIELD_TYPES}, got '{self.type}'."
            )
        if self.min_val is not None and self.max_val is not None:
            if self.min_val > self.max_val:
                raise ValueError(
                    f"InputField.min_val ({self.min_val}) must be <= max_val ({self.max_val})."
                )


@dataclass(frozen=True)
class CalcResult:
    total: float
    unit: str
    contributors: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


class CalculatorPlugin(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @property
    @abstractmethod
    def category(self) -> str:
        ...

    @abstractmethod
    def get_input_fields(self) -> list[InputField]:
        ...

    @abstractmethod
    def calculate(self, inputs: dict) -> CalcResult:
        ...

    def get_recommendations(self, result: CalcResult) -> list[str]:
        return []
