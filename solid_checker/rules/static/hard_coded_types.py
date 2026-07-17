from __future__ import annotations
from typing import List
from solid_checker.ir.models import Violation
from solid_checker.rules.base import BaseRule, RuleContext


class HardCodedTypesRule(BaseRule):
    """Detects OCP violations: hard-coded type checks instead of polymorphism."""

    def __init__(self, config: dict = None):
        super().__init__(config)

    @property
    def name(self) -> str:
        return "Hard-coded Type Checks"

    @property
    def principle(self) -> str:
        return "OCP"

    def check(self, target, context: RuleContext) -> List[Violation]:
        violations = []
        modules = context.builder.get_modules()

        for module in modules:
            for cls in module.classes:
                for method in cls.methods:
                    name_lower = method.name.lower()
                    type_check_indicators = [
                        "is_", "handle_", "process_", "type_", "get_type",
                        "check_type", "validate_type"
                    ]
                    for indicator in type_check_indicators:
                        if method.name.lower().startswith(indicator.replace("_", "")):
                            violations.append(Violation(
                                principle=self.principle,
                                rule="hard_coded_types",
                                file_path=context.module_path,
                                line=method.line,
                                description=(
                                    f"Method '{method.name}' in '{cls.name}' "
                                    f"may use hard-coded type checking, "
                                    f"violating Open/Closed Principle."
                                ),
                                severity="info",
                                suggestion=(
                                    f"Consider using polymorphism instead of "
                                    f"type checks in '{method.name}'."
                                ),
                            ))
                            break
        return violations
