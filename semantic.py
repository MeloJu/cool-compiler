"""Base do analisador semantico da linguagem COOL.

Esta etapa recebe a AST criada pelo parser. As validacoes de classes,
escopos e tipos serao adicionadas nos proximos commits.
"""

from dataclasses import dataclass, field

from ast_nodes import ProgramNode


@dataclass(frozen=True)
class SemanticError:
    """Representa um erro encontrado durante a analise semantica."""

    message: str


@dataclass(frozen=True)
class MethodSignature:
    """Assinatura de um metodo conhecida pela analise semantica."""

    parameter_types: tuple[str, ...]
    return_type: str


@dataclass
class ClassInfo:
    """Informacoes semanticas de uma classe da linguagem."""

    name: str
    parent: str | None
    methods: dict[str, MethodSignature] = field(default_factory=dict)


def builtin_class_table() -> dict[str, ClassInfo]:
    """Cria a tabela das classes predefinidas pela especificacao de COOL."""
    return {
        "Object": ClassInfo(
            name="Object",
            parent=None,
            methods={
                "abort": MethodSignature((), "Object"),
                "type_name": MethodSignature((), "String"),
                "copy": MethodSignature((), "SELF_TYPE"),
            },
        ),
        "IO": ClassInfo(
            name="IO",
            parent="Object",
            methods={
                "out_string": MethodSignature(("String",), "SELF_TYPE"),
                "out_int": MethodSignature(("Int",), "SELF_TYPE"),
                "in_string": MethodSignature((), "String"),
                "in_int": MethodSignature((), "Int"),
            },
        ),
        "Int": ClassInfo(name="Int", parent="Object"),
        "Bool": ClassInfo(name="Bool", parent="Object"),
        "String": ClassInfo(
            name="String",
            parent="Object",
            methods={
                "length": MethodSignature((), "Int"),
                "concat": MethodSignature(("String",), "String"),
                "substr": MethodSignature(("Int", "Int"), "String"),
            },
        ),
    }


def _register_program_classes(program: ProgramNode, result: "SemanticResult") -> None:
    """Inclui as classes da AST na tabela, sem substituir tipos nativos."""
    for class_node in program.classes:
        if class_node.name in result.class_table:
            result.errors.append(
                SemanticError(f"Classe '{class_node.name}' foi definida mais de uma vez")
            )
            continue

        result.class_table[class_node.name] = ClassInfo(
            name=class_node.name,
            parent=class_node.parent,
        )


def _validate_inheritance(program: ProgramNode, result: "SemanticResult") -> None:
    """Verifica a existencia, as restricoes e os ciclos da hierarquia."""
    forbidden_parents = {"Int", "Bool", "String"}
    class_names = {class_node.name for class_node in program.classes}

    for class_node in program.classes:
        if class_node.name not in result.class_table:
            continue

        parent = class_node.parent
        if parent not in result.class_table:
            result.errors.append(
                SemanticError(
                    f"Classe '{class_node.name}' herda de classe inexistente '{parent}'"
                )
            )
        elif parent in forbidden_parents:
            result.errors.append(
                SemanticError(
                    f"Classe '{class_node.name}' nao pode herdar de '{parent}'"
                )
            )

    for class_name in class_names:
        visited: set[str] = set()
        current = class_name
        while current in class_names:
            if current in visited:
                result.errors.append(
                    SemanticError(f"Ciclo de heranca detectado na classe '{class_name}'")
                )
                break
            visited.add(current)
            parent = result.class_table[current].parent
            if parent not in result.class_table:
                break
            current = parent


@dataclass
class SemanticResult:
    """Resultado da analise semantica de um programa."""

    errors: list[SemanticError] = field(default_factory=list)
    class_table: dict[str, ClassInfo] = field(default_factory=builtin_class_table)

    @property
    def success(self) -> bool:
        """Indica se nenhuma regra semantica foi violada."""
        return not self.errors


def analyze(program: ProgramNode) -> SemanticResult:
    """Analisa uma AST de COOL e devolve os erros encontrados.

    A funcao ja define a interface da etapa semantica. Por enquanto, ela
    apenas cria um resultado vazio; as proximas etapas incluirao as regras
    de validacao da linguagem.
    """
    if not isinstance(program, ProgramNode):
        raise TypeError("A analise semantica espera um ProgramNode")

    result = SemanticResult()
    _register_program_classes(program, result)
    _validate_inheritance(program, result)
    return result
