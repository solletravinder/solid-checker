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
        rule_name = getattr(rule, 'rule_name', None)
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
