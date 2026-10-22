"""Nos da arvore sintatica abstrata inicial de COOL."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProgramNode:
    classes: list["ClassNode"]
    line: int | None = field(default=None, kw_only=True, compare=False)


@dataclass
class ClassNode:
    name: str
    parent: str = "Object"
    features: list[Any] = field(default_factory=list)
    line: int | None = field(default=None, kw_only=True, compare=False)


@dataclass
class FormalNode:
    name: str
    type_name: str
    line: int | None = field(default=None, kw_only=True, compare=False)


@dataclass
class AttributeNode:
    name: str
    type_name: str
    init: Any = None
    line: int | None = field(default=None, kw_only=True, compare=False)


@dataclass
class MethodNode:
    name: str
    params: list[FormalNode]
    return_type: str
    body: Any
    line: int | None = field(default=None, kw_only=True, compare=False)


@dataclass
class LiteralNode:
    value: Any
    type_name: str
    line: int | None = field(default=None, kw_only=True, compare=False)


@dataclass
class VariableNode:
    name: str
    line: int | None = field(default=None, kw_only=True, compare=False)


@dataclass
class AssignNode:
    name: str
    value: Any
    line: int | None = field(default=None, kw_only=True, compare=False)


@dataclass
class BinaryOpNode:
    operator: str
    left: Any
    right: Any
    line: int | None = field(default=None, kw_only=True, compare=False)


@dataclass
class UnaryOpNode:
    operator: str
    operand: Any
    line: int | None = field(default=None, kw_only=True, compare=False)


@dataclass
class IfNode:
    condition: Any
    then_expr: Any
    else_expr: Any
    line: int | None = field(default=None, kw_only=True, compare=False)


@dataclass
class WhileNode:
    condition: Any
    body: Any
    line: int | None = field(default=None, kw_only=True, compare=False)


@dataclass
class BlockNode:
    expressions: list[Any]
    line: int | None = field(default=None, kw_only=True, compare=False)


@dataclass
class LetBindingNode:
    name: str
    type_name: str
    init: Any = None
    line: int | None = field(default=None, kw_only=True, compare=False)


@dataclass
class LetNode:
    bindings: list[LetBindingNode]
    body: Any
    line: int | None = field(default=None, kw_only=True, compare=False)


@dataclass
class NewNode:
    type_name: str
    line: int | None = field(default=None, kw_only=True, compare=False)


@dataclass
class MethodCallNode:
    receiver: Any
    method: str
    args: list[Any] = field(default_factory=list)
    static_type: str | None = None
    line: int | None = field(default=None, kw_only=True, compare=False)


@dataclass
class CaseBranchNode:
    name: str
    type_name: str
    body: Any
    line: int | None = field(default=None, kw_only=True, compare=False)


@dataclass
class CaseNode:
    expression: Any
    branches: list[CaseBranchNode]
    line: int | None = field(default=None, kw_only=True, compare=False)
