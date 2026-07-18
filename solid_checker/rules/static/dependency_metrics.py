from __future__ import annotations
from typing import List
from solid_checker.ir.builder import IRBuilder
from solid_checker.ir.models import Violation
from solid_checker.rules.base import BaseRule, RuleContext


class DependencyMetricsRule(BaseRule):
    """Detects high coupling and circular dependencies."""

    def __init__(self, max_outgoing: int = 5, config: dict = None):
        super().__init__(config)
        self.max_outgoing = self.config.get("max_outgoing", max_outgoing)

    @property
    def name(self) -> str:
        return "Dependency Metrics"

    @property
    def principle(self) -> str:
        return "DIP"

    def check(self, target: IRBuilder, context: RuleContext) -> List[Violation]:
        violations = []

        for module in target.get_modules():
            outgoing = len(module.imports)
            if outgoing > self.max_outgoing:
                violations.append(Violation(
                    principle=self.principle,
                    rule="high_coupling",
                    file_path=module.file_path,
                    line=0,
                    description=(
                        f"Module '{module.name}' has {outgoing} outgoing dependencies, "
                        f"exceeding threshold of {self.max_outgoing}."
                    ),
                    severity="warning",
                ))

        cycles = target.get_circular_dependencies()
        for cycle in cycles:
            violations.append(Violation(
                principle=self.principle,
                rule="circular_dependency",
                file_path=context.module_path,
                line=0,
                description=(
                    f"Circular dependency detected: {' -> '.join(cycle)}"
                ),
                severity="error",
                suggestion=(
                    f"Break the cycle by introducing an abstraction or "
                    f"reorganizing module dependencies."
                ),
            ))
        return violations
