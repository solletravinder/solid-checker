# Task 1 Brief: Project Setup + IR Models

## Where This Fits
First task in the SOLID Checker implementation. Establishes the foundational data types (IR models) and project structure that every subsequent task depends on.

## Requirements (verbatim from plan)

### pyproject.toml
```toml
[project]
name = "solid-checker"
version = "0.1.0"
description = "SOLID principle checker for codebases"
requires-python = ">=3.9"
dependencies = [
    "click>=8.0",
    "pyyaml>=6.0",
    "anthropic>=0.39",
    "tree-sitter>=0.20",
    "tree-sitter-python>=0.20",
    "tree-sitter-javascript>=0.20",
]

[project.scripts]
solid-checker = "solid_checker.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

### Package init (`solid_checker/__init__.py`)
```python
"""SOLID Checker — Analyze codebases for SOLID principle violations."""
__version__ = "0.1.0"
```

### IR Models (`solid_checker/ir/models.py`)
```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Parameter:
    name: str
    type_hint: Optional[str] = None


@dataclass
class Method:
    name: str
    parameters: List[Parameter] = field(default_factory=list)
    return_type: Optional[str] = None
    visibility: str = "public"
    line: int = 0


@dataclass
class Property:
    name: str
    type_hint: Optional[str] = None
    visibility: str = "public"
    line: int = 0


@dataclass
class Class:
    name: str
    methods: List[Method] = field(default_factory=list)
    properties: List[Property] = field(default_factory=list)
    parent_class: Optional[str] = None
    interfaces: List[str] = field(default_factory=list)
    visibility: str = "public"
    line: int = 0
    decorators: List[str] = field(default_factory=list)


@dataclass
class Interface:
    name: str
    methods: List[Method] = field(default_factory=list)
    properties: List[Property] = field(default_factory=list)
    visibility: str = "public"
    line: int = 0


@dataclass
class Dependency:
    target: str
    type: str = "import"
    line: int = 0


@dataclass
class Module:
    name: str
    file_path: str
    classes: List[Class] = field(default_factory=list)
    interfaces: List[Interface] = field(default_factory=list)
    functions: List[Method] = field(default_factory=list)
    imports: List[Dependency] = field(default_factory=list)
    language: str = "unknown"


@dataclass
class Violation:
    principle: str
    rule: str
    file_path: str
    line: int
    description: str
    severity: str = "warning"
    suggestion: Optional[str] = None
    metadata: dict = field(default_factory=dict)
```

### IR init (`solid_checker/ir/__init__.py`)
```python
from .models import Class, Interface, Method, Parameter, Dependency, Module
from .models import Violation, Severity
```

### Tests (`tests/test_ir.py`)
```python
from solid_checker.ir.models import (
    Class, Interface, Method, Parameter,
    Dependency, Module, Violation
)

def test_class_creation():
    cls = Class(
        name="UserService",
        methods=[Method(name="save", parameters=[Parameter("user", "User")])],
        properties=[],
    )
    assert cls.name == "UserService"
    assert len(cls.methods) == 1

def test_module_creation():
    mod = Module(
        name="user_service",
        file_path="user_service.py",
        classes=[Class(name="UserService", methods=[], properties=[])],
        imports=[Dependency(target="database")],
    )
    assert mod.name == "user_service"
    assert len(mod.imports) == 1

def test_violation_creation():
    v = Violation(
        principle="SRP",
        rule="god_class",
        file_path="user_service.py",
        line=10,
        description="Class has 42 methods, exceeding threshold of 20",
        severity="warning",
    )
    assert v.principle == "SRP"
    assert v.severity == "warning"
```

## Global Constraints
- Python 3.9+, no Python 3.10+ syntax
- Type hints on all public functions
- TDD: write failing test first, then implementation
- PEP 8 formatting
- Dependencies: click, pyyaml, anthropic, tree-sitter

## Report Contract
Write results to `.superpowers/sdd/reports/task-1-report.md` with:
1. Status: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
2. Commits made (SHA)
3. Test summary (pass/fail counts)
4. Any concerns
