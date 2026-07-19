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
