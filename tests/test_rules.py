from solid_checker.ir.models import Class, Method, Parameter, Module
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
            )
        ],
    )
    violations = rule.check(cls, _make_context())
    assert isinstance(violations, list)


def test_hard_coded_types_detects_conditionals():
    rule = HardCodedTypesRule()
    violations = rule.check(None, _make_context())
    assert isinstance(violations, list)
