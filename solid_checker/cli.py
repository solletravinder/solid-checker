from __future__ import annotations
import click
from pathlib import Path
from typing import Optional
from .engine import SolidChecker
from .adapters.python_adapter import PythonAdapter
from .adapters.js_adapter import JSAdapter
from .rules.static.god_class import GodClassRule
from .rules.static.feature_envy import FeatureEnvyRule
from .rules.static.hard_coded_types import HardCodedTypesRule
from .rules.static.lsp_violations import LSPViolationsRule
from .rules.static.interface_bloat import InterfaceBloatRule
from .rules.static.dip_violations import DIPViolationsRule
from .rules.static.dependency_metrics import DependencyMetricsRule
from .reporters.terminal import TerminalReporter
from .reporters.json import JSONReporter
from .config import load_config


@click.group()
@click.version_option()
def main():
    """SOLID Checker — Analyze codebases for SOLID principle violations."""
    pass


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--language", type=click.Choice(["python", "javascript"]), help="Force language")
@click.option("--strict", is_flag=True, help="Exit with code 1 if violations found")
@click.option("--verbose", is_flag=True, help="Show full descriptions and suggestions")
@click.option("--config", type=click.Path(), help="Path to config file")
def check(path, json_output, language, strict, verbose, config):
    """Analyze a file or directory for SOLID violations."""
    adapters = _get_adapters(language)
    rules = _get_rules(load_config(config))

    checker = SolidChecker(
        adapters=adapters,
        rules=rules,
        config_path=config,
    )
    violations = checker.analyze(path)

    if json_output:
        reporter = JSONReporter()
        click.echo(reporter.render(violations))
    else:
        reporter = TerminalReporter(verbose=verbose)
        click.echo(reporter.render(violations))

    if strict and violations:
        raise click.exceptions.Exit(1)


@main.command()
@click.option("--path", type=click.Path(), default="solid-checker.yml", help="Output path")
def init_config(path):
    """Write a default config file."""
    import yaml
    default = load_config()
    with open(path, "w") as f:
        yaml.dump(default, f, default_flow_style=False)
    click.echo(f"Config written to {path}")


def _get_adapters(language: Optional[str]) -> list:
    if language == "python":
        return [PythonAdapter()]
    elif language == "javascript":
        return [JSAdapter()]
    return [PythonAdapter(), JSAdapter()]


def _get_rules(config: dict) -> list:
    rules = []
    rule_map = {
        "god_class": lambda: GodClassRule(threshold=config["thresholds"]["max_methods_per_class"]),
        "feature_envy": lambda: FeatureEnvyRule(),
        "hard_coded_types": lambda: HardCodedTypesRule(),
        "lsp_violations": lambda: LSPViolationsRule(),
        "interface_bloat": lambda: InterfaceBloatRule(threshold=config["thresholds"]["max_methods_per_interface"]),
        "dip_violations": lambda: DIPViolationsRule(),
        "dependency_metrics": lambda: DependencyMetricsRule(max_outgoing=config["thresholds"]["max_outgoing_deps"]),
    }
    for rule_name, enabled in config.get("rules", {}).items():
        if enabled and rule_name in rule_map:
            rules.append(rule_map[rule_name]())
    return rules
