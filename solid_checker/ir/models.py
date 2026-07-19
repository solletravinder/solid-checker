from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Parameter:
    name: str
    type_hint: Optional[str] = None


@dataclass
class Method:
    name: str
    parameters: List[Parameter] = field(default_factory=list)
    return_type: Optional[str] = None
    visibility: str = "public"
    line: int = 0


@dataclass
class Property:
    name: str
    type_hint: Optional[str] = None
    visibility: str = "public"
    line: int = 0


@dataclass
class Class:
    name: str
    methods: List[Method] = field(default_factory=list)
    properties: List[Property] = field(default_factory=list)
    parent_class: Optional[str] = None
    interfaces: List[str] = field(default_factory=list)
    visibility: str = "public"
    line: int = 0
    decorators: List[str] = field(default_factory=list)


@dataclass
class Interface:
    name: str
    methods: List[Method] = field(default_factory=list)
    properties: List[Property] = field(default_factory=list)
    visibility: str = "public"
    line: int = 0


@dataclass
class Dependency:
    target: str
    type: str = "import"
    line: int = 0


@dataclass
class Module:
    name: str
    file_path: str
    classes: List[Class] = field(default_factory=list)
    interfaces: List[Interface] = field(default_factory=list)
    functions: List[Method] = field(default_factory=list)
    imports: List[Dependency] = field(default_factory=list)
    language: str = "unknown"


@dataclass
class Violation:
    principle: str
    rule: str
    file_path: str
    line: int
    description: str
    severity: str = "warning"
    suggestion: Optional[str] = None
    metadata: dict = field(default_factory=dict)
