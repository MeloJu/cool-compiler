"""Base do analisador semantico da linguagem COOL.

Esta etapa recebe a AST criada pelo parser. As validacoes de classes,
escopos e tipos serao adicionadas nos proximos commits.
"""

from dataclasses import dataclass, field

from ast_nodes import AttributeNode, ClassNode, MethodNode, ProgramNode


@dataclass(frozen=True)
class SemanticError:
    """Representa um erro encontrado durante a analise semantica."""

    message: str


@dataclass(frozen=True)
class MethodSignature:
    """Assinatura de um metodo conhecida pela analise semantica."""

    parameter_types: tuple[str, ...]
    return_type: str


@dataclass(frozen=True)
class AttributeInfo:
    """Declaracao de um atributo conhecida pela analise semantica."""

    type_name: str


@dataclass
class ClassInfo:
    """Informacoes semanticas de uma classe da linguagem."""

    name: str
    parent: str | None
    attributes: dict[str, AttributeInfo] = field(default_factory=dict)
    methods: dict[str, MethodSignature] = field(default_factory=dict)


@dataclass
class Scope:
    """Escopo de identificadores, com acesso opcional a um escopo externo."""

    parent: "Scope | None" = None
    symbols: dict[str, str] = field(default_factory=dict)

    def define(self, name: str, type_name: str) -> bool:
        """Adiciona um nome ao escopo atual e informa se ele era inedito."""
        if name in self.symbols:
            return False
        self.symbols[name] = type_name
        return True

    def lookup(self, name: str) -> str | None:
        """Busca um nome neste escopo e, se preciso, nos escopos externos."""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent is None:
            return None
        return self.parent.lookup(name)


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


def _register_program_classes(
    program: ProgramNode, result: "SemanticResult"
) -> list[ClassNode]:
    """Inclui as classes da AST na tabela, sem substituir tipos nativos."""
    registered_classes: list[ClassNode] = []
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
        registered_classes.append(class_node)
    return registered_classes


def _validate_inheritance(
    classes: list[ClassNode], result: "SemanticResult"
) -> None:
    """Verifica a existencia, as restricoes e os ciclos da hierarquia."""
    forbidden_parents = {"Int", "Bool", "String"}
    class_names = {class_node.name for class_node in classes}

    for class_node in classes:
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


def _type_exists(type_name: str, result: "SemanticResult") -> bool:
    return type_name == "SELF_TYPE" or type_name in result.class_table


def _parent_member(
    class_info: ClassInfo, member_name: str, member_kind: str, result: "SemanticResult"
) -> AttributeInfo | MethodSignature | None:
    """Busca um atributo ou metodo apenas nos ancestrais de uma classe."""
    current_parent = class_info.parent
    visited: set[str] = set()
    while (
        current_parent is not None
        and current_parent in result.class_table
        and current_parent not in visited
    ):
        visited.add(current_parent)
        parent_info = result.class_table[current_parent]
        members = parent_info.attributes if member_kind == "attribute" else parent_info.methods
        if member_name in members:
            return members[member_name]
        current_parent = parent_info.parent
    return None


def _validate_feature_types(
    class_node: ClassNode, feature: AttributeNode | MethodNode, result: "SemanticResult"
) -> None:
    if isinstance(feature, AttributeNode):
        if not _type_exists(feature.type_name, result):
            result.errors.append(
                SemanticError(
                    f"Atributo '{feature.name}' da classe '{class_node.name}' "
                    f"usa tipo inexistente '{feature.type_name}'"
                )
            )
        return

    if not _type_exists(feature.return_type, result):
        result.errors.append(
            SemanticError(
                f"Metodo '{feature.name}' da classe '{class_node.name}' "
                f"usa tipo de retorno inexistente '{feature.return_type}'"
            )
        )

    formal_scope = Scope()
    for formal in feature.params:
        if formal.name == "self":
            result.errors.append(
                SemanticError(f"Metodo '{feature.name}' nao pode ter parametro chamado 'self'")
            )
        elif not formal_scope.define(formal.name, formal.type_name):
            result.errors.append(
                SemanticError(
                    f"Metodo '{feature.name}' possui parametro duplicado '{formal.name}'"
                )
            )
        if formal.type_name == "SELF_TYPE" or not _type_exists(formal.type_name, result):
            result.errors.append(
                SemanticError(
                    f"Parametro '{formal.name}' do metodo '{feature.name}' "
                    f"usa tipo invalido '{formal.type_name}'"
                )
            )


def _register_features(classes: list[ClassNode], result: "SemanticResult") -> None:
    """Registra as declaracoes locais de atributos e metodos das classes."""
    for class_node in classes:
        class_info = result.class_table[class_node.name]
        for feature in class_node.features:
            _validate_feature_types(class_node, feature, result)
            if isinstance(feature, AttributeNode):
                if feature.name == "self":
                    result.errors.append(
                        SemanticError("Um atributo nao pode receber o nome 'self'")
                    )
                elif feature.name in class_info.attributes:
                    result.errors.append(
                        SemanticError(
                            f"Atributo '{feature.name}' foi definido mais de uma vez "
                            f"na classe '{class_node.name}'"
                        )
                    )
                else:
                    class_info.attributes[feature.name] = AttributeInfo(feature.type_name)
            elif isinstance(feature, MethodNode):
                if feature.name in class_info.methods:
                    result.errors.append(
                        SemanticError(
                            f"Metodo '{feature.name}' foi definido mais de uma vez "
                            f"na classe '{class_node.name}'"
                        )
                    )
                else:
                    class_info.methods[feature.name] = MethodSignature(
                        tuple(formal.type_name for formal in feature.params),
                        feature.return_type,
                    )


def _validate_inherited_features(
    classes: list[ClassNode], result: "SemanticResult"
) -> None:
    """Garante que atributos e metodos respeitem as regras de heranca."""
    for class_node in classes:
        class_info = result.class_table[class_node.name]
        for attribute_name in class_info.attributes:
            if _parent_member(class_info, attribute_name, "attribute", result) is not None:
                result.errors.append(
                    SemanticError(
                        f"Atributo '{attribute_name}' da classe '{class_node.name}' "
                        "redefine um atributo herdado"
                    )
                )
        for method_name, signature in class_info.methods.items():
            inherited = _parent_member(class_info, method_name, "method", result)
            if inherited is not None and signature != inherited:
                result.errors.append(
                    SemanticError(
                        f"Metodo '{method_name}' da classe '{class_node.name}' "
                        "tem assinatura diferente da versao herdada"
                    )
                )


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
    classes = _register_program_classes(program, result)
    _validate_inheritance(classes, result)
    _register_features(classes, result)
    _validate_inherited_features(classes, result)
    return result
