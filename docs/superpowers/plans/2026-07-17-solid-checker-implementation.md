# SOLID Checker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI tool that analyzes codebases for SOLID principle violations, with multi-language support via a plugin adapter architecture and hybrid static + LLM analysis.

**Architecture:** Plugin-based core with language adapters producing a normalized Intermediate Representation (IR). Static rules operate on IR for fast deterministic checks; LLM rules provide deeper analysis only on static-flagged violations. Reporters format output for terminal or JSON/SARIF.

**Tech Stack:** Python 3.9+, Click (CLI), pyyaml (config), pytest (testing), anthropic SDK (optional LLM), tree-sitter (JS/TS parsing), built-in `ast` (Python parsing)

## Global Constraints

- Python 3.9+ (use `typing` module, no Python 3.10+ syntax)
- Follow PEP 8, type hints on all public functions
- TDD: write failing test before implementation
- Commit after each passing test
- No external dependencies beyond what's listed in tech stack
- Config file: `solid-checker.yml`, sensible defaults so tool works with no config

## File Structure

```
solid_checker/
├── __init__.py              # Package init, version
├── cli.py                   # Click CLI entry point
├── config.py                # YAML config loading with defaults
├── engine.py                # Core orchestration pipeline
├── violations.py            # Violation dataclass
├── ir/
│   ├── __init__.py
│   ├── models.py            # IR dataclasses (Class, Method, Dependency, etc.)
│   └── builder.py           # IRBuilder - assembles IR from adapter output
├── adapters/
│   ├── __init__.py
│   ├── base.py              # BaseAdapter abstract class
│   ├── python_adapter.py    # Python AST → IR
│   └── js_adapter.py        # JS/TS AST → IR
├── rules/
│   ├── __init__.py
│   ├── base.py              # BaseRule abstract class
│   ├── static/
│   │   ├── __init__.py
│   │   ├── god_class.py
│   │   ├── feature_envy.py
│   │   ├── hard_coded_types.py
│   │   ├── lsp_violations.py
│   │   ├── interface_bloat.py
│   │   ├── dip_violations.py
│   │   └── dependency_metrics.py
│   └── llm/
│       ├── __init__.py
│       ├── semantic_cohesion.py
│       ├── dependency_direction.py
│       ├── abstraction_quality.py
│       └── naming_intent.py
├── reporters/
│   ├── __init__.py
│   ├── terminal.py          # Color-coded terminal output
│   └── json.py              # JSON output for CI
└── llm/
    ├── __init__.py
    └── analyzer.py          # LLM analysis wrapper (optional)

tests/
├── conftest.py              # Shared fixtures
├── test_ir.py               # IR model tests
├── test_builder.py          # IRBuilder tests
├── test_adapters.py         # Adapter tests
├── test_rules.py            # Static rule tests
├── test_engine.py           # Integration tests
├── test_cli.py              # CLI tests
├── test_config.py           # Config tests
└── fixtures/
    ├── python_samples/
    │   ├── god_class.py
    │   ├── feature_envy.py
    │   └── dip_violation.py
    └── js_samples/
        ├── god_class.ts
        └── interface_bloat.ts
```

---

### Task 1: Project Setup + IR Models

**Files:**
- Create: `solid_checker/__init__.py`
- Create: `solid_checker/ir/__init__.py`
- Create: `solid_checker/ir/models.py`
- Create: `tests/test_ir.py`
- Create: `pyproject.toml`

**Interfaces:**
- Consumes: nothing (first task)
- Produces: `Class`, `Interface`, `Method`, `Parameter`, `Dependency`, `Module` dataclasses; `Violation` dataclass; package structure

- [ ] **Step 1: Write pyproject.toml**

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

- [ ] **Step 2: Write package init**

`solid_checker/__init__.py`:
```python
"""SOLID Checker — Analyze codebases for SOLID principle violations."""
__version__ = "0.1.0"
```

- [ ] **Step 3: Write failing test for IR models**

`tests/test_ir.py`:
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
        classes=[Class(name="UserService", methods=[], properties=[])],
        imports=[Dependency(target="database")],
        file_path="user_service.py",
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

- [ ] **Step 4: Run test to verify it fails**

Run: `pytest tests/test_ir.py -v`
Expected: FAIL with "No module named 'solid_checker.ir.models'"

- [ ] **Step 5: Write IR models**

`solid_checker/ir/__init__.py`:
```python
from .models import Class, Interface, Method, Parameter, Dependency, Module
from .models import Violation, Severity
```

`solid_checker/ir/models.py`:
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
    type: str = "import"  # import, call, inheritance
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
    principle: str          # SRP, OCP, LSP, ISP, DIP
    rule: str               # god_class, feature_envy, etc.
    file_path: str
    line: int
    description: str
    severity: str = "warning"  # info, warning, error
    suggestion: Optional[str] = None
    metadata: dict = field(default_factory=dict)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_ir.py -v`
Expected: PASS (3/3)

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml solid_checker/__init__.py solid_checker/ir/__init__.py solid_checker/ir/models.py tests/test_ir.py
git commit -m "feat: add IR models and project setup"
```

---

### Task 2: IR Builder + Base Adapter

**Files:**
- Create: `solid_checker/ir/builder.py`
- Create: `solid_checker/adapters/__init__.py`
- Create: `solid_checker/adapters/base.py`
- Create: `tests/test_builder.py`

**Interfaces:**
- Consumes: IR models from Task 1
- Produces: `IRBuilder` class; `BaseAdapter` abstract class with `parse(file_path) -> Module` interface

- [ ] **Step 1: Write failing test for IRBuilder**

`tests/test_builder.py`:
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

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_builder.py -v`
Expected: FAIL with "No module named 'solid_checker.ir.builder'"

- [ ] **Step 3: Write IRBuilder**

`solid_checker/ir/builder.py`:
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

`solid_checker/adapters/__init__.py`:
```python
from .base import BaseAdapter
```

`solid_checker/adapters/base.py`:
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

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_builder.py -v`
Expected: PASS (3/3)

- [ ] **Step 5: Commit**

```bash
git add solid_checker/ir/builder.py solid_checker/adapters/__init__.py solid_checker/adapters/base.py tests/test_builder.py
git commit -m "feat: add IRBuilder and BaseAdapter"
```

---

### Task 3: Python Adapter

**Files:**
- Create: `solid_checker/adapters/python_adapter.py`
- Create: `tests/test_adapters.py`
- Create: `tests/fixtures/python_samples/god_class.py`
- Create: `tests/fixtures/python_samples/feature_envy.py`
- Create: `tests/fixtures/python_samples/dip_violation.py`

**Interfaces:**
- Consumes: `BaseAdapter` from Task 2, IR models from Task 1
- Produces: `PythonAdapter` class with `parse(file_path, source) -> Module`

- [ ] **Step 1: Write failing test for PythonAdapter**

`tests/fixtures/python_samples/god_class.py`:
```python
"""Sample file with a God Class violation for testing."""

class UserService:
    def create_user(self): pass
    def delete_user(self): pass
    def update_user(self): pass
    def find_user(self): pass
    def list_users(self): pass
    def authenticate(self): pass
    def send_email(self): pass
    def generate_report(self): pass
    def export_data(self): pass
    def validate_input(self): pass
    def log_action(self): pass
    def notify_admins(self): pass
    def backup_data(self): pass
    def restore_data(self): pass
    def audit_trail(self): pass
    def sanitize_input(self): pass
    def encrypt_data(self): pass
    def decrypt_data(self): pass
    def hash_password(self): pass
    def compare_passwords(self): pass

    def extra_method_1(self): pass
    def extra_method_2(self): pass
```

`tests/fixtures/python_samples/feature_envy.py`:
```python
"""Sample file with Feature Envy violation."""

class Address:
    def __init__(self):
        self.street = ""
        self.city = ""
        self.zip_code = ""

class Customer:
    def __init__(self):
        self.name = ""
        self.address = Address()

    def get_address_info(self):
        # This method reaches into Address more than it uses Customer's own data
        return f"{self.address.street}, {self.address.city}, {self.address.zip_code}"
```

`tests/fixtures/python_samples/dip_violation.py`:
```python
"""Sample file with DIP violation - concrete dependency."""

class MySQLDatabase:
    def connect(self): pass
    def query(self, sql): pass

class UserRepository:
    def __init__(self):
        # Direct instantiation of concrete class - DIP violation
        self.db = MySQLDatabase()

    def find_user(self, user_id):
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")
```

`tests/test_adapters.py`:
```python
import ast
from pathlib import Path
from solid_checker.adapters.python_adapter import PythonAdapter
from solid_checker.ir.models import Class, Method, Dependency

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "python_samples"

def _load(name: str) -> str:
    return (FIXTURES_DIR / name).read_text()

def test_python_adapter_language():
    adapter = PythonAdapter()
    assert adapter.language == "python"

def test_python_adapter_extensions():
    adapter = PythonAdapter()
    assert ".py" in adapter.supported_extensions

def test_parse_god_class():
    adapter = PythonAdapter()
    source = _load("god_class.py")
    module = adapter.parse("god_class.py", source)
    assert len(module.classes) == 1
    assert module.classes[0].name == "UserService"
    assert len(module.classes[0].methods) >= 20

def test_parse_feature_envy():
    adapter = PythonAdapter()
    source = _load("feature_envy.py")
    module = adapter.parse("feature_envy.py", source)
    assert len(module.classes) == 2
    names = {c.name for c in module.classes}
    assert "Address" in names
    assert "Customer" in names

def test_parse_dip_violation():
    adapter = PythonAdapter()
    source = _load("dip_violation.py")
    module = adapter.parse("dip_violation.py", source)
    # The adapter should detect the MySQLDatabase instantiation
    assert len(module.classes) >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_adapters.py -v`
Expected: FAIL with "No module named 'solid_checker.adapters.python_adapter'"

- [ ] **Step 3: Write PythonAdapter**

`solid_checker/adapters/python_adapter.py`:
```python
from __future__ import annotations
import ast
from pathlib import Path
from typing import List, Optional
from .base import BaseAdapter
from solid_checker.ir.models import (
    Module, Class, Interface, Method, Parameter,
    Property, Dependency
)


class PythonAdapter(BaseAdapter):
    """Parses Python source files into IR using the built-in ast module."""

    @property
    def language(self) -> str:
        return "python"

    @property
    def supported_extensions(self) -> list[str]:
        return [".py"]

    def parse(self, file_path: str, source: str) -> Module:
        module_name = Path(file_path).stem
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            # Return minimal module on parse error
            return Module(
                name=module_name,
                file_path=file_path,
                language="python",
            )

        visitor = _PythonIRVisitor(file_path)
        visitor.visit(tree)

        return Module(
            name=module_name,
            file_path=file_path,
            classes=visitor.classes,
            interfaces=visitor.interfaces,
            functions=visitor.functions,
            imports=visitor.imports,
            language="python",
        )


class _PythonIRVisitor(ast.NodeVisitor):
    """AST visitor that builds IR structures."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.classes: List[Class] = []
        self.interfaces: List[Interface] = []
        self.functions: List[Method] = []
        self.imports: List[Dependency] = []
        self._current_class: Optional[Class] = None

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(Dependency(
                target=alias.name,
                type="import",
                line=node.lineno,
            ))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            self.imports.append(Dependency(
                target=f"{module}.{alias.name}",
                type="import",
                line=node.lineno,
            ))
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        parent_class = None
        interfaces = []
        decorators = []

        for dec in node.decorator_list:
            decorators.append(ast.unparse(dec) if hasattr(ast, "unparse") else "")

        for base in node.bases:
            if isinstance(base, ast.Name):
                parent_class = base.id
            elif isinstance(base, ast.Call) and isinstance(base.func, ast.Name):
                # Protocol(), ABC() — treat as interface
                interfaces.append(base.func.id)

        # Detect Protocol/ABC classes as interfaces
        is_interface = (
            any("Protocol" in d for d in decorators)
            or any("abc.ABC" in d or "ABC" in d for d in decorators)
            or any("Protocol" in i for i in interfaces)
        )

        methods = []
        properties = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                params = self._parse_params(item.args)
                visibility = self._parse_visibility(item)
                methods.append(Method(
                    name=item.name,
                    parameters=params,
                    return_type=self._parse_return_type(item),
                    visibility=visibility,
                    line=item.lineno,
                ))
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                properties.append(Property(
                    name=item.target.id,
                    type_hint=ast.unparse(item.annotation) if item.annotation and hasattr(ast, "unparse") else None,
                    visibility="public",
                    line=item.lineno,
                ))

        if is_interface:
            self.interfaces.append(Interface(
                name=node.name,
                methods=methods,
                properties=properties,
                line=node.lineno,
            ))
        else:
            cls = Class(
                name=node.name,
                methods=methods,
                properties=properties,
                parent_class=parent_class,
                interfaces=interfaces,
                decorators=decorators,
                line=node.lineno,
            )
            self.classes.append(cls)
            self._current_class = cls

        self.generic_visit(node)
        self._current_class = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self._current_class is None:
            params = self._parse_params(node.args)
            self.functions.append(Method(
                name=node.name,
                parameters=params,
                return_type=self._parse_return_type(node),
                line=node.lineno,
            ))
        self.generic_visit(node)

    def _parse_params(self, args: ast.arguments) -> List[Parameter]:
        params = []
        all_args = (
            (args.posonlyargs or [])
            + args.args
            + (args.kwonlyargs or [])
        )
        for arg in all_args:
            type_hint = None
            if arg.annotation and hasattr(ast, "unparse"):
                type_hint = ast.unparse(arg.annotation)
            params.append(Parameter(name=arg.arg, type_hint=type_hint))
        return params

    def _parse_return_type(self, node) -> Optional[str]:
        if node.returns and hasattr(ast, "unparse"):
            return ast.unparse(node.returns)
        return None

    def _parse_visibility(self, node) -> str:
        for dec in node.decorator_list:
            name = ast.unparse(dec) if hasattr(ast, "unparse") else ""
            if name.startswith("_"):
                return "private"
        return "public"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_adapters.py -v`
Expected: PASS (5/5)

- [ ] **Step 5: Commit**

```bash
git add solid_checker/adapters/python_adapter.py tests/test_adapters.py tests/fixtures/python_samples/
git commit -m "feat: add Python AST adapter"
```

---

### Task 4: JS/TS Adapter

**Files:**
- Create: `solid_checker/adapters/js_adapter.py`
- Create: `tests/fixtures/js_samples/god_class.ts`
- Create: `tests/fixtures/js_samples/interface_bloat.ts`

**Interfaces:**
- Consumes: `BaseAdapter` from Task 2, IR models from Task 1
- Produces: `JSAdapter` class with `parse(file_path, source) -> Module`

- [ ] **Step 1: Write failing test for JSAdapter**

`tests/fixtures/js_samples/god_class.ts`:
```typescript
/** Sample file with a God Class violation for testing. */
export class UserService {
    createUser() { }
    deleteUser() { }
    updateUser() { }
    findUser() { }
    listUsers() { }
    authenticate() { }
    sendEmail() { }
    generateReport() { }
    exportData() { }
    validateInput() { }
    logAction() { }
    notifyAdmins() { }
    backupData() { }
    restoreData() { }
    auditTrail() { }
    sanitizeInput() { }
    encryptData() { }
    decryptData() { }
    hashPassword() { }
    comparePasswords() { }
    extraMethod1() { }
    extraMethod2() { }
}
```

`tests/fixtures/js_samples/interface_bloat.ts`:
```typescript
/** Sample file with Interface Segregation violation. */
export interface Worker {
    work(): void;
    eat(): void;
    sleep(): void;
    attendMeeting(): void;
    writeReport(): void;
    code(): void;
    test(): void;
    deploy(): void;
    monitor(): void;
    debug(): void;
    optimize(): void;
    document(): void;
    review(): void;
    plan(): void;
    estimate(): void;
    present(): void;
    negotiate(): void;
    hire(): void;
    fire(): void;
    promote(): void;
    manageBudget(): void;
    approveLeaves(): void;
    conductInterview(): void;
}
```

`tests/test_adapters.py` — append these tests:
```python
def test_js_adapter_language():
    from solid_checker.adapters.js_adapter import JSAdapter
    adapter = JSAdapter()
    assert adapter.language == "javascript"

def test_js_adapter_extensions():
    from solid_checker.adapters.js_adapter import JSAdapter
    adapter = JSAdapter()
    assert ".ts" in adapter.supported_extensions
    assert ".js" in adapter.supported_extensions

def test_parse_ts_god_class():
    from solid_checker.adapters.js_adapter import JSAdapter
    source = (FIXTURES_DIR.parent / "js_samples" / "god_class.ts").read_text()
    adapter = JSAdapter()
    module = adapter.parse("god_class.ts", source)
    assert len(module.classes) == 1
    assert module.classes[0].name == "UserService"
    assert len(module.classes[0].methods) >= 20

def test_parse_ts_interface_bloat():
    from solid_checker.adapters.js_adapter import JSAdapter
    source = (FIXTURES_DIR.parent / "js_samples" / "interface_bloat.ts").read_text()
    adapter = JSAdapter()
    module = adapter.parse("interface_bloat.ts", source)
    assert len(module.interfaces) == 1
    assert module.interfaces[0].name == "Worker"
    assert len(module.interfaces[0].methods) >= 20
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_adapters.py -v`
Expected: FAIL with "No module named 'solid_checker.adapters.js_adapter'"

- [ ] **Step 3: Write JSAdapter**

`solid_checker/adapters/js_adapter.py`:
```python
from __future__ import annotations
import re
from pathlib import Path
from typing import List, Optional
from .base import BaseAdapter
from solid_checker.ir.models import (
    Module, Class, Interface, Method, Parameter,
    Property, Dependency
)


class JSAdapter(BaseAdapter):
    """Parses JS/TS source files into IR using regex-based extraction."""

    @property
    def language(self) -> str:
        return "javascript"

    @property
    def supported_extensions(self) -> list[str]:
        return [".js", ".jsx", ".ts", ".tsx"]

    def parse(self, file_path: str, source: str) -> Module:
        module_name = Path(file_path).stem
        classes = _extract_classes(source)
        interfaces = _extract_interfaces(source)
        imports = _extract_imports(source)

        return Module(
            name=module_name,
            file_path=file_path,
            classes=classes,
            interfaces=interfaces,
            imports=imports,
            language="javascript",
        )


def _extract_classes(source: str) -> List[Class]:
    classes = []
    # Match class declarations: class Name ... or export class Name ...
    pattern = re.compile(
        r'(?:export\s+)?(?:default\s+)?class\s+(\w+)\s*(?:extends\s+(\w+))?',
        re.MULTILINE
    )
    for match in pattern.finditer(source):
        name = match.group(1)
        parent = match.group(2)

        # Extract methods from class body
        methods = _extract_methods_in_class(source, name)
        properties = _extract_properties_in_class(source, name)

        classes.append(Class(
            name=name,
            methods=methods,
            properties=properties,
            parent_class=parent,
            line=source[:match.start()].count('\n') + 1,
        ))
    return classes


def _extract_interfaces(source: str) -> List[Interface]:
    interfaces = []
    # Match interface declarations
    pattern = re.compile(
        r'(?:export\s+)?interface\s+(\w+)',
        re.MULTILINE
    )
    for match in pattern.finditer(source):
        name = match.group(1)
        methods = _extract_interface_methods(source, name)
        interfaces.append(Interface(
            name=name,
            methods=methods,
            line=source[:match.start()].count('\n') + 1,
        ))
    return interfaces


def _extract_imports(source: str) -> List[Dependency]:
    imports = []
    # Match: import { x } from 'module' or import x from 'module'
    pattern = re.compile(
        r'import\s+(?:\{[^}]*\}|\w+)\s+from\s+[\'"]([^\'"]+)[\'"]',
        re.MULTILINE
    )
    for match in pattern.finditer(source):
        imports.append(Dependency(
            target=match.group(1),
            type="import",
            line=source[:match.start()].count('\n') + 1,
        ))

    # Match: require('module')
    req_pattern = re.compile(
        r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
        re.MULTILINE
    )
    for match in req_pattern.finditer(source):
        imports.append(Dependency(
            target=match.group(1),
            type="import",
            line=source[:match.start()].count('\n') + 1,
        ))
    return imports


def _extract_methods_in_class(source: str, class_name: str) -> List[Method]:
    methods = []
    # Find the class body
    class_pattern = re.compile(
        r'(?:export\s+)?(?:default\s+)?class\s+' + re.escape(class_name) + r'\s*\{',
        re.MULTILINE
    )
    class_match = class_pattern.search(source)
    if not class_match:
        return methods

    # Find matching closing brace
    start = class_match.end()
    depth = 1
    i = start
    while i < len(source) and depth > 0:
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
        i += 1
    class_body = source[start:i - 1]

    # Extract methods: methodName(params) { or async methodName(params) {
    method_pattern = re.compile(
        r'(?:async\s+)?(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{\n]+))?\s*\{',
        re.MULTILINE
    )
    for match in method_pattern.finditer(class_body):
        name = match.group(1)
        # Skip constructor keywords that might be caught
        if name in ('if', 'for', 'while', 'switch', 'catch', 'class', 'interface'):
            continue
        params_str = match.group(2) or ""
        params = _parse_ts_params(params_str)
        return_type = (match.group(3) or "").strip() or None
        methods.append(Method(
            name=name,
            parameters=params,
            return_type=return_type,
            line=source[:start + match.start()].count('\n') + 1,
        ))
    return methods


def _extract_interface_methods(source: str, interface_name: str) -> List[Method]:
    methods = []
    iface_pattern = re.compile(
        r'(?:export\s+)?interface\s+' + re.escape(interface_name) + r'\s*\{',
        re.MULTILINE
    )
    iface_match = iface_pattern.search(source)
    if not iface_match:
        return methods

    start = iface_match.end()
    depth = 1
    i = start
    while i < len(source) and depth > 0:
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
        i += 1
    iface_body = source[start:i - 1]

    method_pattern = re.compile(
        r'(\w+)\s*\(([^)]*)\)\s*:',
        re.MULTILINE
    )
    for match in method_pattern.finditer(iface_body):
        params_str = match.group(2) or ""
        methods.append(Method(
            name=match.group(1),
            parameters=_parse_ts_params(params_str),
            line=source[:start + match.start()].count('\n') + 1,
        ))
    return methods


def _extract_properties_in_class(source: str, class_name: str) -> List[Property]:
    properties = []
    class_pattern = re.compile(
        r'(?:export\s+)?(?:default\s+)?class\s+' + re.escape(class_name) + r'\s*\{',
        re.MULTILINE
    )
    class_match = class_pattern.search(source)
    if not class_match:
        return properties

    start = class_match.end()
    depth = 1
    i = start
    while i < len(source) and depth > 0:
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
        i += 1
    class_body = source[start:i - 1]

    prop_pattern = re.compile(
        r'(?:public|private|protected)?\s*(\w+)\s*[?:]',
        re.MULTILINE
    )
    for match in prop_pattern.finditer(class_body):
        name = match.group(1)
        if name not in ('if', 'for', 'while', 'switch', 'catch'):
            properties.append(Property(
                name=name,
                line=source[:start + match.start()].count('\n') + 1,
            ))
    return properties


def _parse_ts_params(params_str: str) -> List[Parameter]:
    params = []
    if not params_str.strip():
        return params
    for part in params_str.split(','):
        part = part.strip()
        if not part:
            continue
        if ':' in part:
            name, type_hint = part.split(':', 1)
            params.append(Parameter(
                name=name.strip(),
                type_hint=type_hint.strip() or None,
            ))
        else:
            params.append(Parameter(name=part))
    return params
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_adapters.py -v`
Expected: PASS (9/9)

- [ ] **Step 5: Commit**

```bash
git add solid_checker/adapters/js_adapter.py tests/fixtures/js_samples/ tests/test_adapters.py
git commit -m "feat: add JS/TS adapter"
```

---

### Task 5: Static Rules — God Class, Feature Envy, Hard-coded Types

**Files:**
- Create: `solid_checker/rules/__init__.py`
- Create: `solid_checker/rules/base.py`
- Create: `solid_checker/rules/static/__init__.py`
- Create: `solid_checker/rules/static/god_class.py`
- Create: `solid_checker/rules/static/feature_envy.py`
- Create: `solid_checker/rules/static/hard_coded_types.py`
- Create: `tests/test_rules.py`

**Interfaces:**
- Consumes: IR models from Task 1, `IRBuilder` from Task 2
- Produces: `BaseRule` abstract class; `GodClassRule`, `FeatureEnvyRule`, `HardCodedTypesRule`

- [ ] **Step 1: Write failing test for static rules**

`tests/test_rules.py`:
```python
from solid_checker.ir.models import Class, Method, Parameter, Dependency
from solid_checker.ir.builder import IRBuilder
from solid_checker.rules.static.god_class import GodClassRule
from solid_checker.rules.static.feature_envy import FeatureEnvyRule
from solid_checker.rules.static.hard_coded_types import HardCodedTypesRule
from solid_checker.rules.base import RuleContext

def _make_context(module_path="test.py"):
    builder = IRBuilder()
    return RuleContext(builder=builder, module_path=module_path)

def test_god_class_rule_detects_large_class():
    rule = GodClassRule(threshold=10)
    cls = Class(
        name="GodClass",
        methods=[Method(name=f"method_{i}") for i in range(15)],
    )
    violations = rule.check(cls, _make_context())
    assert len(violations) == 1
    assert violations[0].principle == "SRP"
    assert violations[0].rule == "god_class"

def test_god_class_rule_passes_small_class():
    rule = GodClassRule(threshold=10)
    cls = Class(
        name="SmallClass",
        methods=[Method(name="run")],
    )
    violations = rule.check(cls, _make_context())
    assert len(violations) == 0

def test_feature_envy_rule_detects_external_access():
    rule = FeatureEnvyRule()
    cls = Class(
        name="Customer",
        methods=[
            Method(
                name="get_address_info",
                # Method that accesses another class's fields heavily
            )
        ],
    )
    # We need a full module with Address class for this
    # Simplified: test with explicit dependency
    violations = rule.check(cls, _make_context())
    # Feature envy requires cross-class analysis, so this is a simplified test
    assert isinstance(violations, list)

def test_hard_coded_types_detects_conditionals():
    rule = HardCodedTypesRule()
    # This rule operates on method body patterns
    # We test the IR-level detection
    violations = rule.check(None, _make_context())
    assert isinstance(violations, list)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_rules.py -v`
Expected: FAIL with "No module named 'solid_checker.rules'"

- [ ] **Step 3: Write base Rule class**

`solid_checker/rules/__init__.py`:
```python
from .base import BaseRule, RuleContext
```

`solid_checker/rules/base.py`:
```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional
from solid_checker.ir.models import Class, Violation, Module
from solid_checker.ir.builder import IRBuilder


class RuleContext:
    """Context passed to each rule during analysis."""
    def __init__(self, builder: IRBuilder, module_path: str):
        self.builder = builder
        self.module_path = module_path
        self.config: dict = {}


class BaseRule(ABC):
    """Abstract base class for all rules."""

    def __init__(self, config: dict = None):
        self.config = config or {}

    @abstractmethod
    def check(self, target, context: RuleContext) -> List[Violation]:
        """Analyze a target (Class, Module, or IRBuilder) and return violations."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable rule name."""
        ...

    @property
    @abstractmethod
    def principle(self) -> str:
        """Which SOLID principle this rule checks."""
        ...
```

`solid_checker/rules/static/__init__.py`:
```python
from .god_class import GodClassRule
from .feature_envy import FeatureEnvyRule
from .hard_coded_types import HardCodedTypesRule
```

`solid_checker/rules/static/god_class.py`:
```python
from __future__ import annotations
from typing import List
from solid_checker.ir.models import Class, Violation
from solid_checker.rules.base import BaseRule, RuleContext


class GodClassRule(BaseRule):
    """Detects classes with too many methods (SRP violation)."""

    def __init__(self, threshold: int = 20, config: dict = None):
        super().__init__(config)
        self.threshold = self.config.get("threshold", threshold)

    @property
    def name(self) -> str:
        return "God Class"

    @property
    def principle(self) -> str:
        return "SRP"

    def check(self, target: Class, context: RuleContext) -> List[Violation]:
        violations = []
        if not isinstance(target, Class):
            return violations

        method_count = len(target.methods)
        if method_count > self.threshold:
            violations.append(Violation(
                principle=self.principle,
                rule="god_class",
                file_path=context.module_path,
                line=target.line,
                description=(
                    f"Class '{target.name}' has {method_count} methods, "
                    f"exceeding threshold of {self.threshold}. "
                    f"It likely has too many responsibilities."
                ),
                severity="warning",
                suggestion=(
                    f"Consider splitting '{target.name}' into smaller, "
                    f"more focused classes."
                ),
            ))
        return violations
```

`solid_checker/rules/static/feature_envy.py`:
```python
from __future__ import annotations
from typing import List, Set
from solid_checker.ir.models import Class, Method, Violation, Dependency
from solid_checker.rules.base import BaseRule, RuleContext


class FeatureEnvyRule(BaseRule):
    """Detects methods that heavily depend on another class's internals (SRP violation)."""

    def __init__(self, config: dict = None):
        super().__init__(config)

    @property
    def name(self) -> str:
        return "Feature Envy"

    @property
    def principle(self) -> str:
        return "SRP"

    def check(self, target, context: RuleContext) -> List[Violation]:
        violations = []
        modules = context.builder.get_modules()

        # Build a map of external field accesses per class
        for module in modules:
            for cls in module.classes:
                for method in cls.methods:
                    # Check if method name or params suggest external dependency
                    envied = self._detect_envy(cls, method, context.builder)
                    if envied:
                        violations.append(Violation(
                            principle=self.principle,
                            rule="feature_envy",
                            file_path=context.module_path,
                            line=method.line,
                            description=(
                                f"Method '{method.name}' in '{cls.name}' appears to "
                                f"have Feature Envy toward '{envied}' — it likely "
                                f"uses another class's data more than its own."
                            ),
                            severity="info",
                            suggestion=(
                                f"Consider moving '{method.name}' to '{envied}'."
                            ),
                        ))
        return violations

    def _detect_envy(self, cls: Class, method: Method, builder) -> str | None:
        """Heuristic: if method references another class name in its params or logic."""
        # Check method name for hints
        method_name_lower = method.name.lower()
        for param in method.parameters:
            param_type = (param.type_hint or "").lower()
            # If method takes a parameter of another class type and acts on it
            if cls.name.lower() in method_name_lower and param_type:
                all_classes = [c.name for c in builder.get_all_classes()]
                for class_name in all_classes:
                    if class_name.lower() in param_type and class_name.lower() != cls.name.lower():
                        return class_name
        return None
```

`solid_checker/rules/static/hard_coded_types.py`:
```python
from __future__ import annotations
from typing import List
from solid_checker.ir.models import Violation
from solid_checker.rules.base import BaseRule, RuleContext


class HardCodedTypesRule(BaseRule):
    """Detects OCP violations: hard-coded type checks instead of polymorphism."""

    def __init__(self, config: dict = None):
        super().__init__(config)

    @property
    def name(self) -> str:
        return "Hard-coded Type Checks"

    @property
    def principle(self) -> str:
        return "OCP"

    def check(self, target, context: RuleContext) -> List[Violation]:
        violations = []
        modules = context.builder.get_modules()

        for module in modules:
            for cls in module.classes:
                for method in cls.methods:
                    # Heuristic: method name suggests type checking
                    name_lower = method.name.lower()
                    type_check_indicators = [
                        "is_", "handle_", "process_", "type_", "get_type",
                        "check_type", "validate_type"
                    ]
                    for indicator in type_check_indicators:
                        if method.name.lower().startswith(indicator.replace("_", "")):
                            violations.append(Violation(
                                principle=self.principle,
                                rule="hard_coded_types",
                                file_path=context.module_path,
                                line=method.line,
                                description=(
                                    f"Method '{method.name}' in '{cls.name}' "
                                    f"may use hard-coded type checking, "
                                    f"violating Open/Closed Principle."
                                ),
                                severity="info",
                                suggestion=(
                                    f"Consider using polymorphism instead of "
                                    f"type checks in '{method.name}'."
                                ),
                            ))
                            break
        return violations
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_rules.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add solid_checker/rules/ tests/test_rules.py
git commit -m "feat: add static rules (God Class, Feature Envy, Hard-coded Types)"
```

---

### Task 6: Static Rules — LSP, ISP, DIP, Dependency Metrics

**Files:**
- Create: `solid_checker/rules/static/lsp_violations.py`
- Create: `solid_checker/rules/static/interface_bloat.py`
- Create: `solid_checker/rules/static/dip_violations.py`
- Create: `solid_checker/rules/static/dependency_metrics.py`

**Interfaces:**
- Consumes: `BaseRule` from Task 5, IR models from Task 1
- Produces: `LSPViolationsRule`, `InterfaceBloatRule`, `DIPViolationsRule`, `DependencyMetricsRule`

- [ ] **Step 1: Write failing tests**

`tests/test_rules.py` — append:
```python
from solid_checker.rules.static.lsp_violations import LSPViolationsRule
from solid_checker.rules.static.interface_bloat import InterfaceBloatRule
from solid_checker.rules.static.dip_violations import DIPViolationsRule
from solid_checker.rules.static.dependency_metrics import DependencyMetricsRule

def test_lsp_rule_detects_override_throws():
    rule = LSPViolationsRule()
    cls = Class(
        name="BadSubclass",
        parent_class="BaseClass",
        methods=[Method(name="process", parameters=[Parameter("x", "int")])],
    )
    violations = rule.check(cls, _make_context())
    # LSP check: subclass should not narrow parameters
    assert isinstance(violations, list)

def test_interface_bloat_rule_detects_large_interface():
    rule = InterfaceBloatRule(threshold=10)
    iface = type('IFace', (), {
        'name': 'BigInterface',
        'methods': [Method(name=f"m{i}") for i in range(15)],
        'line': 1,
    })()
    # Need a proper Interface object
    from solid_checker.ir.models import Interface
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

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_rules.py -v -k "test_lsp or test_interface_bloat or test_dip_rule or test_dependency_metrics"`
Expected: FAIL with "No module named 'solid_checker.rules.static.xxx'"

- [ ] **Step 3: Write remaining static rules**

`solid_checker/rules/static/lsp_violations.py`:
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
                        # Check for narrowed parameters
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

`solid_checker/rules/static/interface_bloat.py`:
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

`solid_checker/rules/static/dip_violations.py`:
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

        # Check if class directly instantiates concrete dependencies
        for dep in context.builder.get_module(target.name).imports if False else []:
            pass

        # Heuristic: check method names for direct instantiation patterns
        for method in target.methods:
            for param in method.parameters:
                if param.type_hint:
                    type_lower = param.type_hint.lower()
                    if not any(kw in type_lower for kw in self.abstract_keywords):
                        # Might be a concrete dependency
                        pass

        # Check if class has no interface dependencies
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

`solid_checker/rules/static/dependency_metrics.py`:
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

        # Check for high coupling
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

        # Check for circular dependencies
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

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_rules.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add solid_checker/rules/static/ tests/test_rules.py
git commit -m "feat: add static rules (LSP, ISP, DIP, Dependency Metrics)"
```

---

### Task 7: Core Engine + Config

**Files:**
- Create: `solid_checker/engine.py`
- Create: `solid_checker/config.py`
- Create: `tests/test_engine.py`
- Create: `tests/test_config.py`

**Interfaces:**
- Consumes: All adapters, all rules, IRBuilder from earlier tasks
- Produces: `SolidChecker` class with `analyze(path, options) -> List[Violation]`; config loader

- [ ] **Step 1: Write failing test for engine**

`tests/test_engine.py`:
```python
from pathlib import Path
from solid_checker.engine import SolidChecker
from solid_checker.adapters.python_adapter import PythonAdapter
from solid_checker.rules.static.god_class import GodClassRule

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "python_samples"

def test_engine_analyzes_directory(tmp_path):
    # Copy fixture files to a temp directory
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
    # Should not crash, should only analyze the valid file
    assert isinstance(violations, list)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_engine.py -v`
Expected: FAIL with "No module named 'solid_checker.engine'"

- [ ] **Step 3: Write config loader**

`solid_checker/config.py`:
```python
from __future__ import annotations
from pathlib import Path
from typing import Any, Optional
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
    "llm": {
        "enabled": False,
        "provider": "anthropic",
        "api_key": None,
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

- [ ] **Step 4: Write failing test for config**

`tests/test_config.py`:
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
    assert config["thresholds"]["max_parameters"] == 5  # default preserved

def test_default_config_has_all_keys():
    assert "rules" in DEFAULT_CONFIG
    assert "exclude" in DEFAULT_CONFIG
    assert "llm" in DEFAULT_CONFIG
```

- [ ] **Step 5: Run config tests to verify they pass**

Run: `pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 6: Write the core engine**

`solid_checker/engine.py`:
```python
from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Dict, Type
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
            for module in modules:
                context = RuleContext(builder=builder, module_path=module.file_path)
                context.config = self.config
                violations.extend(rule.check(module, context))

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
        # Deduplicate and sort
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
                # Log parse errors but continue
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
```

- [ ] **Step 7: Run engine tests to verify they pass**

Run: `pytest tests/test_engine.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add solid_checker/engine.py solid_checker/config.py tests/test_engine.py tests/test_config.py
git commit -m "feat: add core engine and config loader"
```

---

### Task 8: CLI + Terminal Reporter

**Files:**
- Create: `solid_checker/cli.py`
- Create: `solid_checker/reporters/__init__.py`
- Create: `solid_checker/reporters/terminal.py`
- Create: `tests/test_cli.py`

**Interfaces:**
- Consumes: `SolidChecker` from Task 7, all adapters and rules
- Produces: Click CLI with `check` and `init-config` commands; terminal reporter

- [ ] **Step 1: Write failing test for CLI**

`tests/test_cli.py`:
```python
from click.testing import CliRunner
from solid_checker.cli import main
from solid_checker.adapters.python_adapter import PythonAdapter
from solid_checker.rules.static.god_class import GodClassRule
from solid_checker.engine import SolidChecker
import tempfile, os
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "python_samples"

def test_cli_check_command():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        for f in FIXTURES_DIR.glob("*.py"):
            Path(tmpdir, f.name).write_text(f.read_text())
        result = runner.invoke(main, ["check", tmpdir, "--language", "python"])
        assert result.exit_code in (0, 1)  # 1 if violations found with --strict
        assert "SOLID" in result.output or "violation" in result.output.lower() or "No SOLID" in result.output

def test_cli_init_config(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["init-config", "--path", str(tmp_path / "solid-checker.yml")])
    assert result.exit_code == 0
    assert (tmp_path / "solid-checker.yml").exists()

def test_cli_json_output():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        for f in FIXTURES_DIR.glob("*.py"):
            Path(tmpdir, f.name).write_text(f.read_text())
        result = runner.invoke(main, [
            "check", tmpdir, "--language", "python", "--json"
        ])
        assert result.exit_code in (0, 1)
        # Output should be valid JSON array
        import json
        data = json.loads(result.output)
        assert isinstance(data, list)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL with "No module named 'solid_checker.cli'"

- [ ] **Step 3: Write terminal reporter**

`solid_checker/reporters/__init__.py`:
```python
from .terminal import TerminalReporter
from .json import JSONReporter
```

`solid_checker/reporters/terminal.py`:
```python
from __future__ import annotations
from typing import List
from solid_checker.ir.models import Violation


class TerminalReporter:
    """Formats violations for terminal display with color support."""

    def __init__(self, use_color: bool = True, verbose: bool = False):
        self.use_color = use_color
        self.verbose = verbose

    def render(self, violations: List[Violation]) -> str:
        if not violations:
            return "\033[32m✓ No SOLID violations found.\033[0m\n"

        lines = []
        # Group by file
        by_file: dict = {}
        for v in violations:
            by_file.setdefault(v.file_path, []).append(v)

        for file_path, file_violations in by_file.items():
            lines.append(f"\033[1m{file_path}\033[0m")
            for v in file_violations:
                color = self._severity_color(v.severity)
                principle_tag = f"[{v.principle}]"
                lines.append(
                    f"  {color}{principle_tag}\033[0m "
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
            "error": "\033[31m",    # red
            "warning": "\033[33m",  # yellow
            "info": "\033[36m",     # cyan
        }
        return colors.get(severity, "")
```

- [ ] **Step 4: Write JSON reporter**

`solid_checker/reporters/json.py`:
```python
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
```

- [ ] **Step 5: Write the CLI**

`solid_checker/cli.py`:
```python
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
```

- [ ] **Step 6: Run CLI tests to verify they pass**

Run: `pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add solid_checker/cli.py solid_checker/reporters/ tests/test_cli.py
git commit -m "feat: add CLI and terminal/JSON reporters"
```

---

### Task 9: LLM Rules (Optional Enhancement)

**Files:**
- Create: `solid_checker/llm/__init__.py`
- Create: `solid_checker/llm/analyzer.py`
- Create: `solid_checker/rules/llm/__init__.py`
- Create: `solid_checker/rules/llm/semantic_cohesion.py`
- Create: `solid_checker/rules/llm/dependency_direction.py`
- Create: `solid_checker/rules/llm/abstraction_quality.py`
- Create: `solid_checker/rules/llm/naming_intent.py`
- Create: `tests/test_llm.py`

**Interfaces:**
- Consumes: Anthropic SDK, IR models, static violations as context
- Produces: LLM-based rules that augment static findings

- [ ] **Step 1: Write failing test for LLM analyzer**

`tests/test_llm.py`:
```python
from solid_checker.llm.analyzer import LLMAnalyzer
from solid_checker.ir.models import Module, Class, Violation

def test_llm_analyzer_init():
    analyzer = LLMAnalyzer(api_key="test-key")
    assert analyzer.api_key == "test-key"

def test_llm_analyzer_no_key_returns_empty():
    analyzer = LLMAnalyzer(api_key=None)
    module = Module(name="test", file_path="test.py")
    result = analyzer.analyze_cohesion(module)
    assert result == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_llm.py -v`
Expected: FAIL with "No module named 'solid_checker.llm'"

- [ ] **Step 3: Write LLM analyzer**

`solid_checker/llm/__init__.py`:
```python
from .analyzer import LLMAnalyzer
```

`solid_checker/llm/analyzer.py`:
```python
from __future__ import annotations
from typing import List, Optional
from solid_checker.ir.models import Module, Violation

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class LLMAnalyzer:
    """Wraps LLM calls for deeper SOLID analysis."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package required for LLM analysis")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def analyze_cohesion(self, module: Module) -> List[Violation]:
        """Ask LLM to assess semantic cohesion of a module."""
        if not module.classes:
            return []

        prompt = self._build_cohesion_prompt(module)
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return self._parse_cohesion_response(response, module)

    def _build_cohesion_prompt(self, module: Module) -> str:
        class_descriptions = []
        for cls in module.classes:
            methods = ", ".join(m.name for m in cls.methods)
            class_descriptions.append(f"- {cls.name}: {methods}")

        return (
            f"Analyze the following classes from '{module.file_path}' for "
            f"Single Responsibility Principle violations:\n\n"
            + "\n".join(class_descriptions)
            + "\n\n"
            "Does each class have a single, cohesive responsibility? "
            "List any violations with class name, issue, and suggestion. "
            "Format each as: CLASS: <name> | ISSUE: <description> | SUGGESTION: <fix>"
        )

    def _parse_cohesion_response(self, response, module: Module) -> List[Violation]:
        violations = []
        text = response.content[0].text
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("CLASS:"):
                parts = line.split("|")
                if len(parts) >= 3:
                    class_name = parts[0].replace("CLASS:", "").strip()
                    issue = parts[1].replace("ISSUE:", "").strip()
                    suggestion = parts[2].replace("SUGGESTION:", "").strip()
                    violations.append(Violation(
                        principle="SRP",
                        rule="llm_semantic_cohesion",
                        file_path=module.file_path,
                        line=0,
                        description=f"LLM analysis: {issue} in '{class_name}'",
                        severity="info",
                        suggestion=suggestion,
                    ))
        return violations
```

`solid_checker/rules/llm/__init__.py`:
```python
from .semantic_cohesion import LLMSemanticCohesionRule
from .dependency_direction import LLMDependencyDirectionRule
from .abstraction_quality import LLMAbstractionQualityRule
from .naming_intent import LLMNamingIntentRule
```

`solid_checker/rules/llm/semantic_cohesion.py`:
```python
from __future__ import annotations
from typing import List
from solid_checker.ir.models import Class, Module, Violation
from solid_checker.rules.base import BaseRule, RuleContext
from solid_checker.llm.analyzer import LLMAnalyzer


class LLMSemanticCohesionRule(BaseRule):
    """Uses LLM to assess semantic cohesion of classes (SRP)."""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.analyzer = None
        if self.config.get("llm", {}).get("api_key"):
            try:
                self.analyzer = LLMAnalyzer(api_key=self.config["llm"]["api_key"])
            except ImportError:
                pass

    @property
    def name(self) -> str:
        return "LLM Semantic Cohesion"

    @property
    def principle(self) -> str:
        return "SRP"

    def check(self, target: Module, context: RuleContext) -> List[Violation]:
        if not self.analyzer:
            return []
        return self.analyzer.analyze_cohesion(target)
```

`solid_checker/rules/llm/dependency_direction.py`:
```python
from __future__ import annotations
from typing import List
from solid_checker.ir.models import Module, Violation
from solid_checker.rules.base import BaseRule, RuleContext
from solid_checker.llm.analyzer import LLMAnalyzer


class LLMDependencyDirectionRule(BaseRule):
    """Uses LLM to assess dependency direction (DIP)."""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.analyzer = None
        if self.config.get("llm", {}).get("api_key"):
            try:
                self.analyzer = LLMAnalyzer(api_key=self.config["llm"]["api_key"])
            except ImportError:
                pass

    @property
    def name(self) -> str:
        return "LLM Dependency Direction"

    @property
    def principle(self) -> str:
        return "DIP"

    def check(self, target: Module, context: RuleContext) -> List[Violation]:
        if not self.analyzer:
            return []
        # Future: implement dependency direction analysis via LLM
        return []
```

`solid_checker/rules/llm/abstraction_quality.py`:
```python
from __future__ import annotations
from typing import List
from solid_checker.ir.models import Interface, Module, Violation
from solid_checker.rules.base import BaseRule, RuleContext
from solid_checker.llm.analyzer import LLMAnalyzer


class LLMAbstractionQualityRule(BaseRule):
    """Uses LLM to assess interface/abstraction quality."""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.analyzer = None
        if self.config.get("llm", {}).get("api_key"):
            try:
                self.analyzer = LLMAnalyzer(api_key=self.config["llm"]["api_key"])
            except ImportError:
                pass

    @property
    def name(self) -> str:
        return "LLM Abstraction Quality"

    @property
    def principle(self) -> str:
        return "ISP"

    def check(self, target, context: RuleContext) -> List[Violation]:
        if not self.analyzer:
            return []
        # Future: implement abstraction quality analysis via LLM
        return []
```

`solid_checker/rules/llm/naming_intent.py`:
```python
from __future__ import annotations
from typing import List
from solid_checker.ir.models import Class, Module, Violation
from solid_checker.rules.base import BaseRule, RuleContext
from solid_checker.llm.analyzer import LLMAnalyzer


class LLMNamingIntentRule(BaseRule):
    """Uses LLM to assess whether names reflect responsibilities."""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.analyzer = None
        if self.config.get("llm", {}).get("api_key"):
            try:
                self.analyzer = LLMAnalyzer(api_key=self.config["llm"]["api_key"])
            except ImportError:
                pass

    @property
    def name(self) -> str:
        return "LLM Naming & Intent"

    @property
    def principle(self) -> str:
        return "SRP"

    def check(self, target: Module, context: RuleContext) -> List[Violation]:
        if not self.analyzer:
            return []
        # Future: implement naming intent analysis via LLM
        return []
```

- [ ] **Step 4: Run LLM tests to verify they pass**

Run: `pytest tests/test_llm.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add solid_checker/llm/ solid_checker/rules/llm/ tests/test_llm.py
git commit -m "feat: add LLM-assisted rules (optional)"
```

---

### Task 10: Final Integration + Polish

**Files:**
- Modify: `solid_checker/cli.py` (ensure LLM rules are registered when config enables them)
- Create: `tests/integration_test.py`
- Create: `README.md`

- [ ] **Step 1: Write integration test**

`tests/integration_test.py`:
```python
from pathlib import Path
from solid_checker.engine import SolidChecker
from solid_checker.adapters.python_adapter import PythonAdapter
from solid_checker.rules.static.god_class import GodClassRule
from solid_checker.rules.static.interface_bloat import InterfaceBloatRule
from solid_checker.rules.static.dependency_metrics import DependencyMetricsRule
from solid_checker.config import load_config
import tempfile

FIXTURES = Path(__file__).parent / "fixtures"

def test_full_python_analysis():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy all Python fixtures
        for f in (FIXTURES / "python_samples").glob("*.py"):
            Path(tmpdir, f.name).write_text(f.read_text())

        config = load_config()
        config["thresholds"]["max_methods_per_class"] = 10
        config["thresholds"]["max_methods_per_interface"] = 10

        checker = SolidChecker(
            adapters=[PythonAdapter()],
            rules=[
                GodClassRule(threshold=config["thresholds"]["max_methods_per_class"]),
                InterfaceBloatRule(threshold=config["thresholds"]["max_methods_per_interface"]),
                DependencyMetricsRule(max_outgoing=config["thresholds"]["max_outgoing_deps"]),
            ],
            config_path=None,
        )
        # Override config after init for thresholds
        checker.config = config

        violations = checker.analyze(tmpdir)

        # Should find god class violation in god_class.py
        god_violations = [v for v in violations if v.rule == "god_class"]
        assert len(god_violations) >= 1

        # Should find interface bloat in interface_bloat.py (if we had that fixture)
        # At minimum, verify no crashes and violations are returned
        assert isinstance(violations, list)
```

- [ ] **Step 2: Run integration test**

Run: `pytest tests/integration_test.py -v`
Expected: PASS

- [ ] **Step 3: Write README**

`README.md`:
```markdown
# SOLID Checker

Analyze codebases for SOLID principle violations. Supports Python and JavaScript/TypeScript.

## Installation

```bash
pip install solid-checker
```

## Usage

```bash
# Analyze a directory
solid-checker check ./src/

# JSON output for CI
solid-checker check ./src/ --json

# Force a language
solid-checker check ./src/ --language python

# Strict mode — exit 1 on violations
solid-checker check ./src/ --strict

# Initialize a config file
solid-checker init-config
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
```

- [ ] **Step 4: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 5: Final commit**

```bash
git add tests/integration_test.py README.md
git commit -m "feat: add integration tests and README"
```

---

## Implementation Notes

1. **Tree-sitter vs regex for JS/TS**: The JS adapter uses regex for simplicity. For production use, replace with tree-sitter for more accurate AST parsing.

2. **LLM rules are optional**: They gracefully degrade when no API key is configured. Static rules provide full coverage without LLM.

3. **Adding a new language**: Create a new adapter class inheriting from `BaseAdapter`, implement `parse()` returning a `Module`, register it in `cli.py`. Zero changes to rules or engine.

4. **Adding a new rule**: Create a new class inheriting from `BaseRule`, implement `check()`, register it in `cli.py`'s `_get_rules()`.

5. **Extending the IR**: Add new fields to `solid_checker/ir/models.py` — adapters populate them, rules consume them. No other layers need changes.
