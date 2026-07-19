from typing import List, Optional
from solid_checker.ir.models import Class, Method, Violation, Dependency
from solid_checker.rules.base import BaseRule, RuleContext


class FeatureEnvyRule(BaseRule):
    """Detects methods that heavily depend on another class's internals (SRP violation)."""

    target_kind: str = "class"

    def __init__(self, config: dict = None):
        super().__init__(config)

    @property
    def name(self) -> str:
        return "Feature Envy"

    @property
    def principle(self) -> str:
        return "SRP"

    def check(self, target, context: RuleContext) -> List[Violation]:
        violations = []
        modules = context.builder.get_modules()

        for module in modules:
            for cls in module.classes:
                for method in cls.methods:
                    envied = self._detect_envy(cls, method, context.builder)
                    if envied:
                        violations.append(Violation(
                            principle=self.principle,
                            rule="feature_envy",
                            file_path=context.module_path,
                            line=method.line,
                            description=(
                                f"Method '{method.name}' in '{cls.name}' appears to "
                                f"have Feature Envy toward '{envied}' — it likely "
                                f"uses another class's data more than its own."
                            ),
                            severity="info",
                            suggestion=(
                                f"Consider moving '{method.name}' to '{envied}'."
                            ),
                        ))
        return violations

    def _detect_envy(self, cls: Class, method: Method, builder) -> Optional[str]:
        """Heuristic: if method references another class name in its params or logic."""
        method_name_lower = method.name.lower()
        for param in method.parameters:
            param_type = (param.type_hint or "").lower()
            if cls.name.lower() in method_name_lower and param_type:
                all_classes = [c.name for c in builder.get_all_classes()]
                for class_name in all_classes:
                    if class_name.lower() in param_type and class_name.lower() != cls.name.lower():
                        return class_name
        return None
