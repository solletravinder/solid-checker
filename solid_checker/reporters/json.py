from __future__ import annotations
from typing import List, Dict, Any
from solid_checker.ir.models import Violation
import json


class JSONReporter:
    """Formats violations as JSON for CI/CD consumption."""

    def render(self, violations: List[Violation]) -> str:
        data = [self._violation_to_dict(v) for v in violations]
        return json.dumps(data, indent=2)

    def _violation_to_dict(self, v: Violation) -> Dict[str, Any]:
        return {
            "principle": v.principle,
            "rule": v.rule,
            "file_path": v.file_path,
            "line": v.line,
            "description": v.description,
            "severity": v.severity,
            "suggestion": v.suggestion,
        }
