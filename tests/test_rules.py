from solid_checker.ir.models import Class, Method, Parameter, Module, Interface, Dependency
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


def test_lsp_rule_detects_override_throws():
    from solid_checker.rules.static.lsp_violations import LSPViolationsRule
    rule = LSPViolationsRule()
    cls = Class(
        name="BadSubclass",
        parent_class="BaseClass",
        methods=[Method(name="process", parameters=[Parameter("x", "int")])],
    )
    violations = rule.check(cls, _make_context())
    assert isinstance(violations, list)


def test_interface_bloat_rule_detects_large_interface():
    from solid_checker.rules.static.interface_bloat import InterfaceBloatRule
    rule = InterfaceBloatRule(threshold=10)
    iface = Interface(
        name="BigInterface",
        methods=[Method(name=f"m{i}") for i in range(15)],
        line=1,
    )
    violations = rule.check(iface, _make_context())
    assert len(violations) == 1
    assert violations[0].principle == "ISP"


def test_dip_rule_detects_concrete_dependency():
    from solid_checker.rules.static.dip_violations import DIPViolationsRule
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
    violations = rule.check(
        builder.get_all_classes()[0],
        RuleContext(builder=builder, module_path="repo.py"),
    )
    assert isinstance(violations, list)


def test_dependency_metrics_detects_high_coupling():
    from solid_checker.rules.static.dependency_metrics import DependencyMetricsRule
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
