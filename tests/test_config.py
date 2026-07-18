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
    assert config["thresholds"]["max_parameters"] == 5

def test_default_config_has_all_keys():
    assert "rules" in DEFAULT_CONFIG
    assert "exclude" in DEFAULT_CONFIG
    assert "llm" in DEFAULT_CONFIG
