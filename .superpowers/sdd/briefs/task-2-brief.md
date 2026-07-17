# Task 2 Brief: IR Builder + Base Adapter

## Where This Fits
Second task. Builds on IR models from Task 1. Provides the cross-module analysis infrastructure (`IRBuilder`) and the abstract base class (`BaseAdapter`) that all language adapters inherit from.

## Requirements (verbatim from plan)

### IRBuilder (`solid_checker/ir/builder.py`)
```python
from __future__ import annotations
from typing import List, Dict, Optional, Set, Tuple
from .models import Module, Class, Dependency


class IRBuilder:
    """Accumulates IR modules and provides cross-module analysis."""

    def __init__(self):
        self._modules: List[Module] = []
        self._class_index: Dict[str, Class] = {}

    def add_module(self, module: Module) -> None:
        self._modules.append(module)
        for cls in module.classes:
            self._class_index[cls.name] = cls
        for iface in module.interfaces:
            self._class_index[iface.name] = iface

    def get_modules(self) -> List[Module]:
        return list(self._modules)

    def get_class_by_name(self, name: str) -> Optional[Class]:
        return self._class_index.get(name)

    def get_circular_dependencies(self) -> List[Tuple[str, ...]]:
        """Detect circular import chains using DFS."""
        graph: Dict[str, List[str]] = {}
        for mod in self._modules:
            graph[mod.name] = [dep.target for dep in mod.imports]

        cycles: List[Tuple[str, ...]] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycles.append(tuple(path[cycle_start:] + [neighbor]))
            path.pop()
            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                dfs(node)

        return cycles

    def get_all_classes(self) -> List[Class]:
        classes = []
        for mod in self._modules:
            classes.extend(mod.classes)
            classes.extend(mod.interfaces)
        return classes

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        graph: Dict[str, List[str]] = {}
        for mod in self._modules:
            graph[mod.name] = []
            for dep in mod.imports:
                graph[mod.name].append(dep.target)
        return graph
```

### BaseAdapter (`solid_checker/adapters/base.py`)
```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
from solid_checker.ir.models import Module


class BaseAdapter(ABC):
    """Abstract base class for language adapters."""

    @abstractmethod
    def parse(self, file_path: str, source: str) -> Module:
        """Parse source code into a normalized IR Module."""
        ...

    @property
    @abstractmethod
    def language(self) -> str:
        """Return the language name this adapter handles."""
        ...

    @property
    def supported_extensions(self) -> list[str]:
        """Return file extensions this adapter handles."""
        return []
```

### Tests (`tests/test_builder.py`)
```python
from solid_checker.ir.builder import IRBuilder
from solid_checker.ir.models import Class, Method, Module, Dependency

def test_builder_accumulates_modules():
    builder = IRBuilder()
    builder.add_module(Module(name="a", file_path="a.py", classes=[
        Class(name="A", methods=[Method(name="run")])
    ]))
    builder.add_module(Module(name="b", file_path="b.py", classes=[
        Class(name="B", methods=[Method(name="run")])
    ]))
    modules = builder.get_modules()
    assert len(modules) == 2

def test_builder_detects_circular_deps():
    builder = IRBuilder()
    builder.add_module(Module(name="a", file_path="a.py", imports=[
        Dependency(target="b")
    ]))
    builder.add_module(Module(name="b", file_path="b.py", imports=[
        Dependency(target="a")
    ]))
    cycles = builder.get_circular_dependencies()
    assert len(cycles) == 1

def test_builder_get_class_by_name():
    builder = IRBuilder()
    builder.add_module(Module(name="a", file_path="a.py", classes=[
        Class(name="UserService", methods=[])
    ]))
    cls = builder.get_class_by_name("UserService")
    assert cls is not None
    assert cls.name == "UserService"
```

### Package inits
`solid_checker/ir/__init__.py` — add `IRBuilder`:
```python
from .models import Class, Interface, Method, Parameter, Dependency, Module
from .models import Violation, Severity
from .builder import IRBuilder
```

`solid_checker/adapters/__init__.py`:
```python
from .base import BaseAdapter
```

## Global Constraints
- Python 3.9+, no Python 3.10+ syntax
- Type hints on all public functions
- TDD: write failing test first, then implementation
- PEP 8 formatting
- Must import correctly from Task 1's IR models

## Interfaces
- **Consumes:** IR models from Task 1 (`Class`, `Module`, `Dependency`, etc.)
- **Produces:** `IRBuilder` class; `BaseAdapter` abstract class with `parse(file_path) -> Module` interface

## Report Contract
Write results to `.superpowers/sdd/reports/task-2-report.md` with:
1. Status: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
2. Commits made (SHA)
3. Test summary
4. Any concerns
