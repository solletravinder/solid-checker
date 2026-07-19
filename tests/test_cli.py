from click.testing import CliRunner
from solid_checker.cli import main
from solid_checker.adapters.python_adapter import PythonAdapter
from solid_checker.rules.static.god_class import GodClassRule
from solid_checker.engine import SolidChecker
import tempfile
import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "python_samples"

def test_cli_check_command():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        for f in FIXTURES_DIR.glob("*.py"):
            Path(tmpdir, f.name).write_text(f.read_text())
        result = runner.invoke(main, ["check", tmpdir, "--language", "python"])
        assert result.exit_code in (0, 1)
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
        data = json.loads(result.output)
        assert isinstance(data, list)
