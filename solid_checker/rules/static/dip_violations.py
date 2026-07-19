from typing import List
from solid_checker.ir.models import Class, Dependency, Violation
from solid_checker.rules.base import BaseRule, RuleContext


class DIPViolationsRule(BaseRule):
    """Detects Dependency Inversion Principle violations."""

    target_kind: str = "class"

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.abstract_keywords = self.config.get(
            "abstract_keywords",
            ["interface", "abstract", "protocol", "abc", "base"]
        )

    @property
    def name(self) -> str:
        return "DIP Violations"

    @property
    def principle(self) -> str:
        return "DIP"

    def check(self, target: Class, context: RuleContext) -> List[Violation]:
        violations = []
        if not isinstance(target, Class):
            return violations

        all_classes = context.builder.get_all_classes()
        class_deps = self._get_class_dependencies(target, context.builder)
        concrete_deps = [d for d in class_deps if not self._is_abstract(d, context.builder)]

        if concrete_deps:
            violations.append(Violation(
                principle=self.principle,
                rule="dip_concrete_dependency",
                file_path=context.module_path,
                line=target.line,
                description=(
                    f"Class '{target.name}' depends on concrete classes: "
                    f"{', '.join(concrete_deps)}. "
                    f"It should depend on abstractions."
                ),
                severity="warning",
                suggestion=(
                    f"Consider injecting dependencies via interfaces/abstractions."
                ),
            ))
        return violations

    def _get_class_dependencies(self, cls: Class, builder) -> List[str]:
        deps = []
        for mod in builder.get_modules():
            for c in mod.classes:
                if c.name == cls.name:
                    for imp in mod.imports:
                        deps.append(imp.target)
        return deps

    def _is_abstract(self, dep_name: str, builder) -> bool:
        for cls in builder.get_all_classes():
            if cls.name == dep_name:
                from solid_checker.ir.models import Interface
                if isinstance(cls, Interface):
                    return True
                if cls.parent_class and "interface" in cls.parent_class.lower():
                    return True
        return any(
            kw in dep_name.lower()
            for kw in self.abstract_keywords
        )
