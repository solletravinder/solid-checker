from pathlib import Path
from solid_checker.engine import SolidChecker
from solid_checker.adapters.python_adapter import PythonAdapter
from solid_checker.rules.static.god_class import GodClassRule

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "python_samples"

def test_engine_analyzes_directory(tmp_path):
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
    assert isinstance(violations, list)
