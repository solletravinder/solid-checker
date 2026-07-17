from __future__ import annotations
from typing import List, Dict, Optional, Set, Tuple
from .models import Module, Class, Dependency


class IRBuilder:
    """Accumulates IR modules and provides cross-module analysis."""

    def __init__(self):
        self._modules: List[Module] = []
        self._class_index: Dict[str, Class] = {}

    def add_module(self, module: Module) -> None:
        self._modules.append(module)
        for cls in module.classes:
            self._class_index[cls.name] = cls
        for iface in module.interfaces:
            self._class_index[iface.name] = iface

    def get_modules(self) -> List[Module]:
        return list(self._modules)

    def get_class_by_name(self, name: str) -> Optional[Class]:
        return self._class_index.get(name)

    def get_circular_dependencies(self) -> List[Tuple[str, ...]]:
        """Detect circular import chains using DFS."""
        graph: Dict[str, List[str]] = {}
        for mod in self._modules:
            graph[mod.name] = [dep.target for dep in mod.imports]

        cycles: List[Tuple[str, ...]] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycles.append(tuple(path[cycle_start:] + [neighbor]))
            path.pop()
            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                dfs(node)

        return cycles

    def get_all_classes(self) -> List[Class]:
        classes = []
        for mod in self._modules:
            classes.extend(mod.classes)
            classes.extend(mod.interfaces)
        return classes

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        graph: Dict[str, List[str]] = {}
        for mod in self._modules:
            graph[mod.name] = []
            for dep in mod.imports:
                graph[mod.name].append(dep.target)
        return graph
