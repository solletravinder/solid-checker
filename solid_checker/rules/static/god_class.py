from __future__ import annotations
from typing import List
from solid_checker.ir.models import Class, Violation
from solid_checker.rules.base import BaseRule, RuleContext


class GodClassRule(BaseRule):
    """Detects classes with too many methods (SRP violation)."""

    target_kind: str = "class"

    def __init__(self, threshold: int = 20, config: dict = None):
        super().__init__(config)
        self.threshold = self.config.get("threshold", threshold)

    @property
    def name(self) -> str:
        return "God Class"

    @property
    def principle(self) -> str:
        return "SRP"

    def check(self, target: Class, context: RuleContext) -> List[Violation]:
        violations = []
        if not isinstance(target, Class):
            return violations

        method_count = len(target.methods)
        if method_count > self.threshold:
            violations.append(Violation(
                principle=self.principle,
                rule="god_class",
                file_path=context.module_path,
                line=target.line,
                description=(
                    f"Class '{target.name}' has {method_count} methods, "
                    f"exceeding threshold of {self.threshold}. "
                    f"It likely has too many responsibilities."
                ),
                severity="warning",
                suggestion=(
                    f"Consider splitting '{target.name}' into smaller, "
                    f"more focused classes."
                ),
            ))
        return violations
