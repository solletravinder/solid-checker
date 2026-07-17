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
        except SyntaxError:
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
