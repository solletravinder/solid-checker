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
