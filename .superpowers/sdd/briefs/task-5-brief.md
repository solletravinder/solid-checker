# Task 5 Brief: Static Rules — God Class, Feature Envy, Hard-coded Types

## Where This Fits
Fifth task. Builds on IR models (Task 1), IRBuilder (Task 2), and BaseRule pattern. Implements the first three static SOLID violation detectors.

## Requirements (verbatim from plan)

### Base Rule (`solid_checker/rules/base.py`)
```python
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
```

### Rules init (`solid_checker/rules/__init__.py`)
```python
from .base import BaseRule, RuleContext
```

### Static rules init (`solid_checker/rules/static/__init__.py`)
```python
from .god_class import GodClassRule
from .feature_envy import FeatureEnvyRule
from .hard_coded_types import HardCodedTypesRule
```

### GodClassRule (`solid_checker/rules/static/god_class.py`)
```python
from __future__ import annotations
from typing import List
from solid_checker.ir.models import Class, Violation
from solid_checker.rules.base import BaseRule, RuleContext


class GodClassRule(BaseRule):
    """Detects classes with too many methods (SRP violation)."""

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
```

### FeatureEnvyRule (`solid_checker/rules/static/feature_envy.py`)
```python
from __future__ import annotations
from typing import List, Set
from solid_checker.ir.models import Class, Method, Violation, Dependency
from solid_checker.rules.base import BaseRule, RuleContext


class FeatureEnvyRule(BaseRule):
    """Detects methods that heavily depend on another class's internals (SRP violation)."""

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

    def _detect_envy(self, cls: Class, method: Method, builder) -> str | None:
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
```

### HardCodedTypesRule (`solid_checker/rules/static/hard_coded_types.py`)
```python
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
```

### Tests (`tests/test_rules.py`)
```python
from solid_checker.ir.models import Class, Method, Parameter, Dependency
from solid_checker.ir.builder import IRBuilder
from solid_checker.rules.static.god_class import GodClassRule
from solid_checker.rules.static.feature_envy import FeatureEnvyRule
from solid_checker.rules.static.hard_coded_types import HardCodedTypesRule
from solid_checker.rules.base import RuleContext


def _make_context(module_path="test.py"):
    builder = IRBuilder()
    return RuleContext(builder=builder, module_path=module_path)


def test_god_class_rule_detects_large_class():
    rule = GodClassRule(threshold=10)
    cls = Class(
        name="GodClass",
        methods=[Method(name=f"method_{i}") for i in range(15)],
    )
    violations = rule.check(cls, _make_context())
    assert len(violations) == 1
    assert violations[0].principle == "SRP"
    assert violations[0].rule == "god_class"

def test_god_class_rule_passes_small_class():
    rule = GodClassRule(threshold=10)
    cls = Class(
        name="SmallClass",
        methods=[Method(name="run")],
    )
    violations = rule.check(cls, _make_context())
    assert len(violations) == 0

def test_feature_envy_rule_detects_external_access():
    rule = FeatureEnvyRule()
    cls = Class(
        name="Customer",
        methods=[
            Method(
                name="get_address_info",
            )
        ],
    )
    violations = rule.check(cls, _make_context())
    assert isinstance(violations, list)

def test_hard_coded_types_detects_conditionals():
    rule = HardCodedTypesRule()
    violations = rule.check(None, _make_context())
    assert isinstance(violations, list)
```

## Global Constraints
- Python 3.9+, no Python 3.10+ syntax (use `str | None` not `Optional[str]` in type hints where possible, but `from __future__ import annotations` handles this)
- Type hints on all public functions
- TDD: write failing test first, then implementation
- PEP 8 formatting
- Must import from Task 1 IR models and Task 2 IRBuilder

## Interfaces
- **Consumes:** IR models from Task 1, `IRBuilder` from Task 2
- **Produces:** `BaseRule`, `RuleContext` base classes; `GodClassRule`, `FeatureEnvyRule`, `HardCodedTypesRule`

## Report Contract
Write results to `.superpowers/sdd/reports/task-5-report.md` with:
1. Status: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
2. Commits made (SHA)
3. Test summary
4. Any concerns
