from __future__ import annotations
from typing import List
from solid_checker.ir.models import Interface, Violation
from solid_checker.rules.base import BaseRule, RuleContext


class InterfaceBloatRule(BaseRule):
    """Detects interfaces with too many methods (ISP violation)."""

    def __init__(self, threshold: int = 10, config: dict = None):
        super().__init__(config)
        self.threshold = self.config.get("threshold", threshold)

    @property
    def name(self) -> str:
        return "Interface Bloat"

    @property
    def principle(self) -> str:
        return "ISP"

    def check(self, target: Interface, context: RuleContext) -> List[Violation]:
        violations = []
        if not isinstance(target, Interface):
            return violations

        method_count = len(target.methods)
        if method_count > self.threshold:
            violations.append(Violation(
                principle=self.principle,
                rule="interface_bloat",
                file_path=context.module_path,
                line=target.line,
                description=(
                    f"Interface '{target.name}' has {method_count} methods, "
                    f"exceeding threshold of {self.threshold}. "
                    f"Clients are forced to depend on methods they don't use."
                ),
                severity="warning",
                suggestion=(
                    f"Split '{target.name}' into smaller, role-specific interfaces."
                ),
            ))
        return violations
