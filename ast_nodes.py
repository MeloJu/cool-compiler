"""Nos da arvore sintatica abstrata inicial de COOL."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProgramNode:
    classes: list["ClassNode"]


@dataclass
class ClassNode:
    name: str
    parent: str = "Object"
    features: list[Any] = field(default_factory=list)


@dataclass
class FormalNode:
    name: str
    type_name: str


@dataclass
class AttributeNode:
    name: str
    type_name: str
    init: Any = None


@dataclass
class MethodNode:
    name: str
    params: list[FormalNode]
    return_type: str
    body: Any


@dataclass
class LiteralNode:
    value: Any
    type_name: str


@dataclass
class VariableNode:
    name: str


@dataclass
class AssignNode:
    name: str
    value: Any


@dataclass
class BinaryOpNode:
    operator: str
    left: Any
    right: Any


@dataclass
class UnaryOpNode:
    operator: str
    operand: Any
