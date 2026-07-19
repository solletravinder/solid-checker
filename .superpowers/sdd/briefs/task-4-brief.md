# Task 4 Brief: JS/TS Adapter

## Where This Fits
Fourth task. Builds on BaseAdapter (Task 2) and IR models (Task 1). The JS adapter parses JS/TS source files into IR using regex-based extraction.

## Requirements (verbatim from plan)

### JSAdapter (`solid_checker/adapters/js_adapter.py`)
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
    pattern = re.compile(
        r'(?:export\s+)?(?:default\s+)?class\s+(\w+)\s*(?:extends\s+(\w+))?',
        re.MULTILINE
    )
    for match in pattern.finditer(source):
        name = match.group(1)
        parent = match.group(2)
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
    class_pattern = re.compile(
        r'(?:export\s+)?(?:default\s+)?class\s+' + re.escape(class_name) + r'\s*\{',
        re.MULTILINE
    )
    class_match = class_pattern.search(source)
    if not class_match:
        return methods
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
    method_pattern = re.compile(
        r'(?:async\s+)?(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{\n]+))?\s*\{',
        re.MULTILINE
    )
    for match in method_pattern.finditer(class_body):
        name = match.group(1)
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

### Tests (append to `tests/test_adapters.py`)
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
    source = (Path(__file__).parent / "fixtures" / "js_samples" / "god_class.ts").read_text()
    adapter = JSAdapter()
    module = adapter.parse("god_class.ts", source)
    assert len(module.classes) == 1
    assert module.classes[0].name == "UserService"
    assert len(module.classes[0].methods) >= 20

def test_parse_ts_interface_bloat():
    from solid_checker.adapters.js_adapter import JSAdapter
    source = (Path(__file__).parent / "fixtures" / "js_samples" / "interface_bloat.ts").read_text()
    adapter = JSAdapter()
    module = adapter.parse("interface_bloat.ts", source)
    assert len(module.interfaces) == 1
    assert module.interfaces[0].name == "Worker"
    assert len(module.interfaces[0].methods) >= 20
```

### Test Fixtures

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

## Global Constraints
- Python 3.9+, no Python 3.10+ syntax
- Type hints on all public functions
- TDD: write failing test first, then implementation
- PEP 8 formatting
- Regex-based parsing (no tree-sitter dependency)
- Must handle `.js`, `.jsx`, `.ts`, `.tsx` extensions

## Interfaces
- **Consumes:** `BaseAdapter` from Task 2, IR models from Task 1
- **Produces:** `JSAdapter` class with `parse(file_path, source) -> Module`

## Report Contract
Write results to `.superpowers/sdd/reports/task-4-report.md` with:
1. Status: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
2. Commits made (SHA)
3. Test summary
4. Any concerns
