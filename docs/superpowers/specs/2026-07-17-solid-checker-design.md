# SOLID Checker — Design Spec

**Date:** 2026-07-17
**Status:** Approved

## 1. Purpose

Build a tool that analyzes codebases and reports SOLID principle violations. It runs locally as a CLI tool and outputs structured data for CI/CD pipelines.

## 2. Supported Languages

Multi-language with a plugin-based adapter architecture. Initial adapters: **Python** and **JavaScript/TypeScript**. Adding a new language requires only a new adapter — zero changes to core or rules.

## 3. Interface

CLI commands:

```
solid-checker check <path>        # analyze a directory or single file
solid-checker check <path> --json # structured output for CI
solid-checker check <path> --language python  # override language detection
solid-checker init-config         # write default config file
```

**Flags:**
- `--json` — output results as JSON instead of terminal text
- `--language <lang>` — force a specific language adapter
- `--strict` — exit with code 1 if any violations are found
- `--verbose` — show full violation descriptions and suggested fixes
- `--config <path>` — path to a config file (YAML/TOML)

## 4. Architecture

Five layers, each with one clear responsibility:

### 4.1 CLI Interface
Entry point. Parses arguments, discovers files, calls the core engine, formats output. Contains no language-specific or rule-specific logic.

### 4.2 Core Engine
Orchestrates the analysis pipeline:
1. Walk the target directory, filter files by extension
2. Detect language per file (extension-based, overridable via `--language`)
3. Dispatch each file to the appropriate language adapter
4. Collect IR from all adapters
5. Run static rules on IR (fast, deterministic)
6. For violations flagged by static rules, optionally run LLM rules for deeper analysis
7. Aggregate and return results to the reporter

### 4.3 Language Adapters → Intermediate Representation (IR)
Each adapter knows one language. It:
1. Parses source files into an AST (using language-native parsers)
2. Normalizes the AST into a common IR

The IR captures only what SOLID rules need:
- `Class` / `Interface` / `Module` — name, visibility, methods, properties
- `Method` — name, parameters (count, types), visibility, return type
- `Import` / `Dependency` — what this module depends on
- `Inheritance` — parent classes, implemented interfaces
- `Coupling` — inbound/outbound dependency counts

Adding a new language: write one adapter that produces this IR. No other layer changes.

### 4.4 Rules
Two categories, both operating on the IR:

**Static Rules** (fast, deterministic):
- **SRP — God Class:** class with too many methods or responsibilities
- **SRP — Feature Envy:** method that uses another class's data more than its own
- **OCP — Hard-coded type checks:** switch/if chains on type instead of polymorphism
- **LSP — Inheritance misuse:** subclass that narrows parameter types or throws on override
- **ISP — Interface bloat:** interface with too many methods
- **DIP — Concrete dependencies:** module directly instantiates concrete classes instead of depending on abstractions
- **Dependency metrics:** circular imports, high coupling (too many outgoing dependencies)

**LLM Rules** (deeper analysis, optional):
- Semantic cohesion — does the class do one conceptual thing?
- Dependency direction — do high-level modules depend on low-level ones correctly?
- Appropriate abstraction — are interfaces well-designed?
- Naming and intent — do names reflect responsibilities?

LLM rules run only on violations already flagged by static rules (to limit API calls and cost).

### 4.5 Reporters
Two output modes:

**Terminal** (default): color-coded output grouped by file and principle. Each violation shows file, line, principle, description, and suggested fix.

**JSON** (`--json` flag): machine-readable array of violation objects with file, line, principle, severity, description. Suitable for CI tools, IDE integrations, or further processing.

**SARIF** (future): GitHub Actions / CodeQL compatible format.

## 5. Data Flow

```
Source Files
    ↓
Language Adapters (parse → IR)
    ↓
Static Rules (analyze IR → violations)
    ↓
LLM Rules (analyze IR + source snippets → deeper violations, only for flagged items)
    ↓
Result Aggregator
    ↓
Reporter (terminal or JSON/SARIF)
```

## 6. Configuration

A `solid-checker.yml` config file supports:
- Language-specific thresholds (e.g., max methods per class, max parameters)
- Rule enable/disable flags
- LLM provider and API key (optional, defaults to static-only if not set)
- Exclude paths/patterns
- Severity thresholds for CI exit codes

Defaults are sensible — the tool works out of the box with no config.

## 7. Error Handling

- **No language adapter found** → skip file, warn user
- **Parse error** → report file with error details, continue analysis of other files
- **LLM unavailable** → fall back to static-only results, note in output
- **No violations found** → print "No SOLID violations found." and exit 0

## 8. Testing Strategy

- **Unit tests** for each IR adapter (feed known source, assert correct IR output)
- **Unit tests** for each static rule (feed known IR, assert violations found)
- **Integration tests** for the full pipeline on small sample codebases
- **Golden file tests**: store expected output for known violations, compare on changes

## 9. Scope Boundaries (YAGNI)

**In scope for V1:**
- Python and JS/TS adapters
- Static rules listed in §4.4
- Terminal + JSON output
- Config file support
- LLM analysis as optional enhancement

**Out of scope (future iterations):**
- More language adapters (Java, Go, C#)
- SARIF output
- Fix suggestions with auto-generated patches
- Web dashboard / visualization
- Incremental analysis (only changed files)

## 10. Implementation Order

1. Core engine + IR model (language-agnostic)
2. Python adapter
3. JS/TS adapter
4. Static rules (all)
5. CLI + terminal reporter
6. JSON reporter
7. Config file support
8. LLM rules (optional)
