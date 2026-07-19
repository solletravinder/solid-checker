# Task 7 Brief: Core Engine + Config

## Where This Fits
Seventh task. Builds on everything from Tasks 1-6. The core engine orchestrates the full analysis pipeline (file discovery → parsing → rule execution → result aggregation). The config loader provides YAML-based configuration with sensible defaults.

## Requirements (verbatim from plan)

### Config (`solid_checker/config.py`)
```python
from __future__ import annotations
from pathlib import Path
from typing import Optional
import yaml


DEFAULT_CONFIG = {
    "thresholds": {
        "max_methods_per_class": 20,
        "max_methods_per_interface": 10,
        "max_parameters": 5,
        "max_outgoing_deps": 5,
    },
    "rules": {
        "god_class": True,
        "feature_envy": True,
        "hard_coded_types": True,
        "lsp_violations": True,
        "interface_bloat": True,
        "dip_violations": True,
        "dependency_metrics": True,
    },
    "exclude": [
        "node_modules",
        "__pycache__",
        ".git",
        "venv",
        "vendor",
        "dist",
        "build",
    ],
}


def load_config(config_path: Optional[str] = None) -> dict:
    """Load config from file, falling back to defaults."""
    if config_path and Path(config_path).exists():
        with open(config_path, "r") as f:
            user_config = yaml.safe_load(f) or {}
        return _merge_configs(DEFAULT_CONFIG, user_config)
    return dict(DEFAULT_CONFIG)


def _merge_configs(base: dict, override: dict) -> dict:
    """Deep merge override into base."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value
    return result
```

### Engine (`solid_checker/engine.py`)
```python
from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Dict
from .adapters.base import BaseAdapter
from .rules.base import BaseRule, RuleContext
from .ir.builder import IRBuilder
from .ir.models import Module, Violation
from .config import load_config


class SolidChecker:
    """Core analysis engine — orchestrates the full pipeline."""

    def __init__(
        self,
        adapters: Optional[List[BaseAdapter]] = None,
        rules: Optional[List[BaseRule]] = None,
        config_path: Optional[str] = None,
    ):
        self.adapters = adapters or []
        self.rules = rules or []
        self.config = load_config(config_path)
        self._adapter_map: Dict[str, BaseAdapter] = {}
        for adapter in self.adapters:
            for ext in adapter.supported_extensions:
                self._adapter_map[ext] = adapter

    def analyze(self, target_path: str) -> List[Violation]:
        """Run full analysis on a file or directory. Returns all violations."""
        path = Path(target_path)
        files = self._discover_files(path)
        builder = IRBuilder()
        violations = []

        # Phase 1: Parse all files into IR
        modules = self._parse_files(files, builder)
        for module in modules:
            builder.add_module(module)

        # Phase 2: Run static rules
        for rule in self.rules:
            if not self._is_rule_enabled(rule):
                continue
            target_kind = getattr(rule, 'target_kind', 'class')
            for module in modules:
                context = RuleContext(builder=builder, module_path=module.file_path)
                context.config = self.config
                if target_kind == 'builder':
                    violations.extend(rule.check(builder, context))
                elif target_kind == 'interface':
                    for iface in module.interfaces:
                        violations.extend(rule.check(iface, context))
                elif target_kind == 'module':
                    violations.extend(rule.check(module, context))
                else:  # 'class' — default
                    for cls in module.classes:
                        violations.extend(rule.check(cls, context))

        # Phase 3: Aggregate and deduplicate
        violations = self._deduplicate(violations)
        return violations

    def _discover_files(self, path: Path) -> List[Path]:
        if path.is_file():
            return [path]
        files = []
        exclude = set(self.config.get("exclude", []))
        for ext, adapter in self._adapter_map.items():
            for f in path.rglob(f"*{ext}"):
                if not any(ex in str(f) for ex in exclude):
                    files.append(f)
        return sorted(set(files))

    def _parse_files(self, files: List[Path], builder: IRBuilder) -> List[Module]:
        modules = []
        for file_path in files:
            source = file_path.read_text(encoding="utf-8", errors="replace")
            ext = file_path.suffix
            adapter = self._adapter_map.get(ext)
            if not adapter:
                continue
            try:
                module = adapter.parse(str(file_path), source)
                modules.append(module)
            except Exception as e:
                modules.append(Module(
                    name=file_path.stem,
                    file_path=str(file_path),
                    language=adapter.language,
                ))
        return modules

    def _is_rule_enabled(self, rule: BaseRule) -> bool:
        rule_name = getattr(rule, 'name', None)
        if rule_name:
            return self.config.get("rules", {}).get(rule_name, True)
        return True

    def _deduplicate(self, violations: List[Violation]) -> List[Violation]:
        seen = set()
        unique = []
        for v in violations:
            key = (v.file_path, v.line, v.rule, v.description)
            if key not in seen:
                seen.add(key)
                unique.append(v)
        return unique
```

### Tests (`tests/test_engine.py`)
```python
from pathlib import Path
from solid_checker.engine import SolidChecker
from solid_checker.adapters.python_adapter import PythonAdapter
from solid_checker.rules.static.god_class import GodClassRule

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "python_samples"

def test_engine_analyzes_directory(tmp_path):
    src = FIXTURES_DIR
    for f in src.glob("*.py"):
        (tmp_path / f.name).write_text(f.read_text())

    checker = SolidChecker(
        adapters=[PythonAdapter()],
        rules=[GodClassRule(threshold=10)],
    )
    violations = checker.analyze(str(tmp_path))
    assert len(violations) >= 1
    god_class_violations = [v for v in violations if v.rule == "god_class"]
    assert len(god_class_violations) >= 1

def test_engine_skips_unparseable_file(tmp_path):
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("def invalid syntax here !!!")
    (tmp_path / "good.py").write_text("class Good:\n    def run(self): pass\n")

    checker = SolidChecker(adapters=[PythonAdapter()], rules=[])
    violations = checker.analyze(str(tmp_path))
    assert isinstance(violations, list)
```

### Tests (`tests/test_config.py`)
```python
from solid_checker.config import load_config, DEFAULT_CONFIG

def test_load_config_returns_defaults():
    config = load_config()
    assert "thresholds" in config
    assert config["thresholds"]["max_methods_per_class"] == 20

def test_load_config_from_file(tmp_path):
    config_file = tmp_path / "solid-checker.yml"
    config_file.write_text("thresholds:\n  max_methods_per_class: 30\n")
    config = load_config(str(config_file))
    assert config["thresholds"]["max_methods_per_class"] == 30
    assert config["thresholds"]["max_parameters"] == 5

def test_default_config_has_all_keys():
    assert "rules" in DEFAULT_CONFIG
    assert "exclude" in DEFAULT_CONFIG
    assert "thresholds" in DEFAULT_CONFIG
```

## Global Constraints
- Python 3.9+, no Python 3.10+ syntax
- Type hints on all public functions
- TDD: write failing test first, then implementation
- PEP 8 formatting
- Must use `tmp_path` pytest fixture for file-based tests
- Must import from all previous tasks

## Interfaces
- **Consumes:** All adapters (Task 3, 4), all rules (Task 5, 6), IRBuilder (Task 2), IR models (Task 1)
- **Produces:** `SolidChecker` class with `analyze(path) -> List[Violation]`; `load_config()` function

## Report Contract
Write results to `.superpowers/sdd/reports/task-7-report.md` with:
1. Status: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
2. Commits made (SHA)
3. Test summary
4. Any concerns
