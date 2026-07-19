# Task 6 Brief: Static Rules — LSP, ISP, DIP, Dependency Metrics

## Where This Fits
Sixth task. Completes the static rules set started in Task 5. Adds LSP violations, interface bloat (ISP), DIP violations, and dependency metrics (circular deps, high coupling).

## Requirements (verbatim from plan)

### Static rules init — update `solid_checker/rules/static/__init__.py`
```python
from .god_class import GodClassRule
from .feature_envy import FeatureEnvyRule
from .hard_coded_types import HardCodedTypesRule
from .lsp_violations import LSPViolationsRule
from .interface_bloat import InterfaceBloatRule
from .dip_violations import DIPViolationsRule
from .dependency_metrics import DependencyMetricsRule
```

### LSPViolationsRule (`solid_checker/rules/static/lsp_violations.py`)
```python
from __future__ import annotations
from typing import List
from solid_checker.ir.models import Class, Violation
from solid_checker.rules.base import BaseRule, RuleContext


class LSPViolationsRule(BaseRule):
    """Detects Liskov Substitution Principle violations."""

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
```

### InterfaceBloatRule (`solid_checker/rules/static/interface_bloat.py`)
```python
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
```

### DIPViolationsRule (`solid_checker/rules/static/dip_violations.py`)
```python
from __future__ import annotations
from typing import List
from solid_checker.ir.models import Class, Dependency, Violation
from solid_checker.rules.base import BaseRule, RuleContext


class DIPViolationsRule(BaseRule):
    """Detects Dependency Inversion Principle violations."""

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

        for method in target.methods:
            for param in method.parameters:
                if param.type_hint:
                    type_lower = param.type_hint.lower()
                    if not any(kw in type_lower for kw in self.abstract_keywords):
                        pass

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
```

### DependencyMetricsRule (`solid_checker/rules/static/dependency_metrics.py`)
```python
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
```

### Tests (append to `tests/test_rules.py`)
```python
from solid_checker.rules.static.lsp_violations import LSPViolationsRule
from solid_checker.rules.static.interface_bloat import InterfaceBloatRule
from solid_checker.rules.static.dip_violations import DIPViolationsRule
from solid_checker.rules.static.dependency_metrics import DependencyMetricsRule
from solid_checker.ir.models import Interface

def test_lsp_rule_detects_override_throws():
    rule = LSPViolationsRule()
    cls = Class(
        name="BadSubclass",
        parent_class="BaseClass",
        methods=[Method(name="process", parameters=[Parameter("x", "int")])],
    )
    violations = rule.check(cls, _make_context())
    assert isinstance(violations, list)

def test_interface_bloat_rule_detects_large_interface():
    rule = InterfaceBloatRule(threshold=10)
    iface = Interface(
        name="BigInterface",
        methods=[Method(name=f"m{i}") for i in range(15)],
        line=1,
    )
    violations = rule.check(iface, _make_context())
    assert len(violations) == 1
    assert violations[0].principle == "ISP"

def test_dip_rule_detects_concrete_dependency():
    rule = DIPViolationsRule()
    builder = IRBuilder()
    builder.add_module(Module(
        name="repo",
        file_path="repo.py",
        classes=[
            Class(
                name="UserRepository",
                methods=[Method(name="find_user")],
            )
        ],
        imports=[Dependency(target="mysql_database", type="import")],
    ))
    violations = rule.check(builder.get_classes()[0], RuleContext(builder=builder, module_path="repo.py"))
    assert isinstance(violations, list)

def test_dependency_metrics_detects_high_coupling():
    rule = DependencyMetricsRule(max_outgoing=3)
    builder = IRBuilder()
    builder.add_module(Module(
        name="main",
        file_path="main.py",
        classes=[Class(name="MainApp", methods=[], properties=[])],
        imports=[
            Dependency(target="a"), Dependency(target="b"),
            Dependency(target="c"), Dependency(target="d"),
        ],
    ))
    violations = rule.check(builder, _make_context("main.py"))
    assert len(violations) >= 1
    assert violations[0].principle == "DIP"
```

## Global Constraints
- Python 3.9+, no Python 3.10+ syntax
- Type hints on all public functions
- TDD: write failing test first, then implementation
- PEP 8 formatting
- Must import from Task 1 IR models, Task 2 IRBuilder, Task 5 BaseRule/RuleContext
- Must update `solid_checker/rules/static/__init__.py` to export new rules

## Interfaces
- **Consumes:** IR models from Task 1, IRBuilder from Task 2, BaseRule/RuleContext from Task 5
- **Produces:** `LSPViolationsRule`, `InterfaceBloatRule`, `DIPViolationsRule`, `DependencyMetricsRule`

## Report Contract
Write results to `.superpowers/sdd/reports/task-6-report.md` with:
1. Status: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
2. Commits made (SHA)
3. Test summary
4. Any concerns
