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
        file_path="user_service.py",
        classes=[Class(name="UserService", methods=[], properties=[])],
        imports=[Dependency(target="database")],
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
