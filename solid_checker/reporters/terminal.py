from typing import List
from solid_checker.ir.models import Violation


class TerminalReporter:
    """Formats violations for terminal display with color support."""

    def __init__(self, use_color: bool = True, verbose: bool = False):
        self.use_color = use_color
        self.verbose = verbose

    def render(self, violations: List[Violation]) -> str:
        if not violations:
            return "\033[32mNo SOLID violations found.\033[0m\n"

        lines = []
        by_file: dict = {}
        for v in violations:
            by_file.setdefault(v.file_path, []).append(v)

        for file_path, file_violations in by_file.items():
            lines.append(f"\033[1m{file_path}\033[0m")
            for v in file_violations:
                color = self._severity_color(v.severity)
                lines.append(
                    f"  {color}[{v.principle}]\033[0m "
                    f"\033[90m{v.rule}\033[0m "
                    f"L{v.line}: {v.description}"
                )
                if self.verbose and v.suggestion:
                    lines.append(f"    \033[36mSuggestion: {v.suggestion}\033[0m")
            lines.append("")

        summary = f"\033[1m{len(violations)} violation(s) found.\033[0m\n"
        return "\n".join(lines) + "\n" + summary

    def _severity_color(self, severity: str) -> str:
        if not self.use_color:
            return ""
        colors = {
            "error": "\033[31m",
            "warning": "\033[33m",
            "info": "\033[36m",
        }
        return colors.get(severity, "")
