# SOLID Checker

Analyze codebases for SOLID principle violations. Supports Python and JavaScript/TypeScript.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Analyze a directory
python -m solid_checker check ./src/

# JSON output for CI
python -m solid_checker check ./src/ --json

# Force a language
python -m solid_checker check ./src/ --language python

# Strict mode — exit 1 on violations
python -m solid_checker check ./src/ --strict

# Initialize a config file
python -m solid_checker init-config
```

## Configuration

Create `solid-checker.yml` to customize thresholds, enable/disable rules, or configure LLM analysis:

```yaml
thresholds:
  max_methods_per_class: 20
  max_methods_per_interface: 10
  max_parameters: 5
  max_outgoing_deps: 5

rules:
  god_class: true
  feature_envy: true
  hard_coded_types: true
  lsp_violations: true
  interface_bloat: true
  dip_violations: true
  dependency_metrics: true

llm:
  enabled: false
  provider: anthropic
  api_key: null
```

## Architecture

- **Core Engine** — orchestrates file discovery, parsing, rule execution
- **Language Adapters** — parse source into normalized IR (Python, JS/TS)
- **Static Rules** — fast deterministic checks on IR (SRP, OCP, LSP, ISP, DIP)
- **LLM Rules** — optional deeper analysis via Anthropic API
- **Reporters** — terminal (color-coded) or JSON output

## SOLID Principles Checked

| Principle | Rules |
|-----------|-------|
| **S** — Single Responsibility | God Class, Feature Envy |
| **O** — Open/Closed | Hard-coded Type Checks |
| **L** — Liskov Substitution | LSP Violations |
| **I** — Interface Segregation | Interface Bloat |
| **D** — Dependency Inversion | DIP Violations, Dependency Metrics |
