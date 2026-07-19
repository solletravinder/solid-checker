from typing import List
from solid_checker.ir.models import Class, Violation
from solid_checker.rules.base import BaseRule, RuleContext


class LSPViolationsRule(BaseRule):
    """Detects Liskov Substitution Principle violations."""

    target_kind: str = "class"

    def __init__(self, config: dict = None):
        super().__init__(config)

    @property
    def name(self) -> str:
        return "LSP Violations"

    @property
    def principle(self) -> str:
        return "LSP"

    def check(self, target, context: RuleContext) -> List[Violation]:
        violations = []
        modules = context.builder.get_modules()

        for module in modules:
            for cls in module.classes:
                if cls.parent_class:
                    parent = context.builder.get_class_by_name(cls.parent_class)
                    if parent:
                        for child_method in cls.methods:
                            parent_method = self._find_method(parent, child_method.name)
                            if parent_method:
                                if len(child_method.parameters) < len(parent_method.parameters):
                                    violations.append(Violation(
                                        principle=self.principle,
                                        rule="lsp_narrowed_params",
                                        file_path=context.module_path,
                                        line=child_method.line,
                                        description=(
                                            f"Method '{child_method.name}' in '{cls.name}' "
                                            f"has fewer parameters than parent "
                                            f"'{cls.parent_class}.{parent_method.name}', "
                                            f"violating LSP."
                                        ),
                                        severity="warning",
                                    ))
        return violations

    def _find_method(self, cls: Class, name: str):
        for m in cls.methods:
            if m.name == name:
                return m
        return None
