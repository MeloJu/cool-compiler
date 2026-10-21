"""Base do analisador semantico da linguagem COOL.

Esta etapa recebe a AST criada pelo parser. As validacoes de classes,
escopos e tipos serao adicionadas nos proximos commits.
"""

from dataclasses import dataclass, field

from ast_nodes import (
    AssignNode,
    AttributeNode,
    BinaryOpNode,
    ClassNode,
    LiteralNode,
    MethodNode,
    ProgramNode,
    UnaryOpNode,
    VariableNode,
)


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


def conforms(
    actual_type: str,
    expected_type: str,
    current_class: str,
    class_table: dict[str, ClassInfo],
) -> bool:
    """Informa se ``actual_type`` esta em conformidade com ``expected_type``.

    Em COOL, um tipo esta em conformidade com ele mesmo ou com qualquer um de
    seus ancestrais. ``SELF_TYPE`` representa a classe que esta sendo
    analisada e so se conforma diretamente com outro ``SELF_TYPE``.
    """
    if actual_type == "SELF_TYPE" and expected_type == "SELF_TYPE":
        return True
    if expected_type == "SELF_TYPE":
        return False

    resolved_actual = current_class if actual_type == "SELF_TYPE" else actual_type
    if resolved_actual not in class_table or expected_type not in class_table:
        return False

    current_type: str | None = resolved_actual
    visited: set[str] = set()
    while current_type is not None and current_type not in visited:
        if current_type == expected_type:
            return True
        visited.add(current_type)
        current_info = class_table.get(current_type)
        current_type = current_info.parent if current_info is not None else None
    return False


def least_upper_bound(
    left_type: str,
    right_type: str,
    current_class: str,
    class_table: dict[str, ClassInfo],
) -> str | None:
    """Devolve o ancestral comum mais especifico entre dois tipos.

    O resultado preserva ``SELF_TYPE`` apenas quando os dois operandos possuem
    esse tipo. Para os demais casos, ele e resolvido para a classe atual antes
    de percorrer a hierarquia.
    """
    if left_type == "SELF_TYPE" and right_type == "SELF_TYPE":
        return "SELF_TYPE"

    resolved_left = current_class if left_type == "SELF_TYPE" else left_type
    resolved_right = current_class if right_type == "SELF_TYPE" else right_type
    if resolved_left not in class_table or resolved_right not in class_table:
        return None

    left_ancestors: set[str] = set()
    current_type: str | None = resolved_left
    while current_type is not None and current_type not in left_ancestors:
        left_ancestors.add(current_type)
        current_type = class_table[current_type].parent

    visited: set[str] = set()
    current_type = resolved_right
    while current_type is not None and current_type not in visited:
        if current_type in left_ancestors:
            return current_type
        visited.add(current_type)
        current_type = class_table[current_type].parent
    return None


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


def _record_expression_type(
    expression: object, type_name: str, result: "SemanticResult"
) -> str:
    result.expression_types[id(expression)] = type_name
    return type_name


def _class_scope(class_name: str, result: "SemanticResult") -> Scope:
    """Cria o escopo de um metodo, com atributos herdados e ``self``."""
    attribute_sets: list[dict[str, AttributeInfo]] = []
    current_name: str | None = class_name
    visited: set[str] = set()
    while current_name is not None and current_name not in visited:
        visited.add(current_name)
        class_info = result.class_table.get(current_name)
        if class_info is None:
            break
        attribute_sets.append(class_info.attributes)
        current_name = class_info.parent

    scope = Scope(symbols={"self": "SELF_TYPE"})
    for attributes in reversed(attribute_sets):
        for attribute_name, attribute_info in attributes.items():
            scope.symbols[attribute_name] = attribute_info.type_name
    return scope


def _infer_expression_type(
    expression: object,
    current_class: str,
    scope: Scope,
    result: "SemanticResult",
) -> str | None:
    """Infere o tipo das expressoes basicas suportadas nesta etapa."""
    if isinstance(expression, LiteralNode):
        return _record_expression_type(expression, expression.type_name, result)

    if isinstance(expression, VariableNode):
        variable_type = scope.lookup(expression.name)
        if variable_type is None:
            result.errors.append(
                SemanticError(f"Identificador '{expression.name}' nao foi declarado")
            )
            return None
        return _record_expression_type(expression, variable_type, result)

    if isinstance(expression, AssignNode):
        value_type = _infer_expression_type(
            expression.value, current_class, scope, result
        )
        if expression.name == "self":
            result.errors.append(SemanticError("Nao e permitido atribuir um valor a 'self'"))
            return value_type
        variable_type = scope.lookup(expression.name)
        if variable_type is None:
            result.errors.append(
                SemanticError(f"Identificador '{expression.name}' nao foi declarado")
            )
            return value_type
        if value_type is not None and not conforms(
            value_type, variable_type, current_class, result.class_table
        ):
            result.errors.append(
                SemanticError(
                    f"Atribuicao a '{expression.name}' espera '{variable_type}', "
                    f"mas recebeu '{value_type}'"
                )
            )
        if value_type is None:
            return None
        return _record_expression_type(expression, value_type, result)

    if isinstance(expression, BinaryOpNode):
        left_type = _infer_expression_type(expression.left, current_class, scope, result)
        right_type = _infer_expression_type(
            expression.right, current_class, scope, result
        )
        if left_type is None or right_type is None:
            return None
        if expression.operator in {"+", "-", "*", "/"}:
            if left_type != "Int" or right_type != "Int":
                result.errors.append(
                    SemanticError(
                        f"Operador '{expression.operator}' exige dois operandos Int"
                    )
                )
                return None
            return _record_expression_type(expression, "Int", result)
        if expression.operator in {"<", "<="}:
            if left_type != "Int" or right_type != "Int":
                result.errors.append(
                    SemanticError(
                        f"Operador '{expression.operator}' exige dois operandos Int"
                    )
                )
                return None
            return _record_expression_type(expression, "Bool", result)
        if expression.operator == "=":
            basic_types = {"Int", "Bool", "String"}
            if (left_type in basic_types or right_type in basic_types) and left_type != right_type:
                result.errors.append(
                    SemanticError("Comparacao '=' entre tipos basicos exige tipos iguais")
                )
                return None
            return _record_expression_type(expression, "Bool", result)

    if isinstance(expression, UnaryOpNode):
        operand_type = _infer_expression_type(
            expression.operand, current_class, scope, result
        )
        if operand_type is None:
            return None
        required_type = {"~": "Int", "not": "Bool"}.get(expression.operator)
        if required_type is not None and operand_type != required_type:
            result.errors.append(
                SemanticError(
                    f"Operador '{expression.operator}' exige operando do tipo "
                    f"'{required_type}'"
                )
            )
            return None
        if expression.operator == "isvoid":
            return _record_expression_type(expression, "Bool", result)
        if required_type is not None:
            return _record_expression_type(expression, required_type, result)

    return None


def _validate_basic_expression_types(
    classes: list[ClassNode], result: "SemanticResult"
) -> None:
    """Verifica inicializacoes e corpos de metodos com expressoes basicas."""
    for class_node in classes:
        for feature in class_node.features:
            class_scope = _class_scope(class_node.name, result)
            if isinstance(feature, AttributeNode) and feature.init is not None:
                init_type = _infer_expression_type(
                    feature.init, class_node.name, class_scope, result
                )
                if init_type is not None and not conforms(
                    init_type, feature.type_name, class_node.name, result.class_table
                ):
                    result.errors.append(
                        SemanticError(
                            f"Inicializacao do atributo '{feature.name}' espera "
                            f"'{feature.type_name}', mas recebeu '{init_type}'"
                        )
                    )
            elif isinstance(feature, MethodNode):
                method_scope = Scope(parent=class_scope)
                for formal in feature.params:
                    method_scope.define(formal.name, formal.type_name)
                body_type = _infer_expression_type(
                    feature.body, class_node.name, method_scope, result
                )
                if body_type is not None and not conforms(
                    body_type, feature.return_type, class_node.name, result.class_table
                ):
                    result.errors.append(
                        SemanticError(
                            f"Metodo '{feature.name}' declara retorno '{feature.return_type}', "
                            f"mas o corpo possui tipo '{body_type}'"
                        )
                    )


@dataclass
class SemanticResult:
    """Resultado da analise semantica de um programa."""

    errors: list[SemanticError] = field(default_factory=list)
    class_table: dict[str, ClassInfo] = field(default_factory=builtin_class_table)
    expression_types: dict[int, str] = field(default_factory=dict)

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
    _validate_basic_expression_types(classes, result)
    return result
