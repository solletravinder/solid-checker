# Task 3 Brief: Python Adapter

## Where This Fits
Third task. Builds on IR models (Task 1) and BaseAdapter (Task 2). The Python adapter parses Python source files into IR using the built-in `ast` module.

## Requirements (verbatim from plan)

### PythonAdapter (`solid_checker/adapters/python_adapter.py`)
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
                interfaces.append(base.func.id)

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

### Tests (`tests/test_adapters.py`)
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
    assert len(module.classes) >= 1
```

### Test Fixtures

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
        self.db = MySQLDatabase()

    def find_user(self, user_id):
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")
```

## Global Constraints
- Python 3.9+, no Python 3.10+ syntax
- Type hints on all public functions
- TDD: write failing test first, then implementation
- PEP 8 formatting
- Must use built-in `ast` module (no external parser)
- `ast.unparse` may not exist in all Python versions — guard with `hasattr(ast, "unparse")`

## Interfaces
- **Consumes:** `BaseAdapter` from Task 2, IR models from Task 1
- **Produces:** `PythonAdapter` class with `parse(file_path, source) -> Module`

## Report Contract
Write results to `.superpowers/sdd/reports/task-3-report.md` with:
1. Status: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
2. Commits made (SHA)
3. Test summary
4. Any concerns
