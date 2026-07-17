from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional
from solid_checker.ir.models import Class, Violation, Module
from solid_checker.ir.builder import IRBuilder


class RuleContext:
    """Context passed to each rule during analysis."""
    def __init__(self, builder: IRBuilder, module_path: str):
        self.builder = builder
        self.module_path = module_path
        self.config: dict = {}


class BaseRule(ABC):
    """Abstract base class for all rules."""

    def __init__(self, config: dict = None):
        self.config = config or {}

    @abstractmethod
    def check(self, target, context: RuleContext) -> List[Violation]:
        """Analyze a target (Class, Module, or IRBuilder) and return violations."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable rule name."""
        ...

    @property
    @abstractmethod
    def principle(self) -> str:
        """Which SOLID principle this rule checks."""
        ...
