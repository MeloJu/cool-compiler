"""Geracao de programas Bril a partir da AST de COOL."""

from dataclasses import dataclass

from ast_nodes import (
    AssignNode,
    AttributeNode,
    BinaryOpNode,
    BlockNode,
    IfNode,
    LetNode,
    LiteralNode,
    MethodNode,
    MethodCallNode,
    NewNode,
    ProgramNode,
    UnaryOpNode,
    VariableNode,
    WhileNode,
)
from semantic import SemanticResult, analyze


class CodeGenerationError(Exception):
    """Indica que uma construcao COOL ainda nao possui traducao para Bril."""


@dataclass(frozen=True)
class AttributeAccess:
    """Localizacao de um atributo dentro de um objeto COOL em memoria."""

    object_register: str
    slot: int
    type_name: str


class BrilGenerator:
    """Monta um programa Bril e controla nomes temporarios e labels."""

    def __init__(self) -> None:
        self.functions: list[dict] = []
        self.instructions: list[dict] = []
        self._temporary_index = 0
        self._label_index = 0
        self.class_layouts: dict[str, dict[str, tuple[int, str, AttributeNode]]] = {}
        self.class_tags: dict[str, int] = {}
        self.class_parents: dict[str, str] = {}
        self.current_class = "Main"

    def new_temporary(self) -> str:
        """Devolve um nome unico para um valor intermediario em Bril."""
        name = f"tmp{self._temporary_index}"
        self._temporary_index += 1
        return name

    def new_label(self, prefix: str) -> str:
        """Devolve um label unico para desvios e estruturas de controle."""
        label = f"{prefix}_{self._label_index}"
        self._label_index += 1
        return label

    def emit(self, instruction: dict) -> None:
        """Adiciona uma instrucao a funcao Bril que esta sendo gerada."""
        self.instructions.append(instruction)

    def _generate_entry_point(self) -> None:
        """Cria a funcao principal exigida por um programa Bril executavel."""
        self._start_function("main")

    def _start_function(
        self,
        name: str,
        args: list[dict] | None = None,
        return_type: object | None = None,
    ) -> None:
        """Inicia uma funcao Bril e torna sua lista de instrucoes corrente."""
        self.instructions = []
        function = {"name": name, "instrs": self.instructions}
        if args:
            function["args"] = args
        if return_type is not None:
            function["type"] = return_type
        self.functions.append(function)

    def _string_pointer_type(self) -> dict:
        """Tipo Bril de uma string COOL: ponteiro para caracteres inteiros."""
        return {"ptr": "int"}

    def _generate_string_length(self) -> None:
        """Gera __cool_string_length, que encontra o terminador zero."""
        string_type = self._string_pointer_type()
        self._start_function(
            "__cool_string_length",
            [{"name": "text", "type": string_type}],
            "int",
        )
        loop = self.new_label("string_length_loop")
        end = self.new_label("string_length_end")
        char_type = "int"
        self.emit({"op": "const", "dest": "index", "type": "int", "value": 0})
        self.emit({"label": loop})
        self.emit(
            {
                "op": "ptradd",
                "dest": "character_address",
                "type": string_type,
                "args": ["text", "index"],
            }
        )
        self.emit(
            {
                "op": "load",
                "dest": "character",
                "type": char_type,
                "args": ["character_address"],
            }
        )
        self.emit({"op": "const", "dest": "zero", "type": "int", "value": 0})
        self.emit(
            {
                "op": "eq",
                "dest": "finished",
                "type": "bool",
                "args": ["character", "zero"],
            }
        )
        self.emit({"op": "br", "args": ["finished"], "labels": [end, loop + "_next"]})
        self.emit({"label": loop + "_next"})
        self.emit({"op": "const", "dest": "one", "type": "int", "value": 1})
        self.emit(
            {"op": "add", "dest": "index", "type": "int", "args": ["index", "one"]}
        )
        self.emit({"op": "jmp", "labels": [loop]})
        self.emit({"label": end})
        self.emit({"op": "ret", "args": ["index"]})

    def _generate_string_concat(self) -> None:
        """Gera __cool_string_concat, com uma nova area para o resultado."""
        string_type = self._string_pointer_type()
        self._start_function(
            "__cool_string_concat",
            [
                {"name": "left", "type": string_type},
                {"name": "right", "type": string_type},
            ],
            string_type,
        )
        left_loop = self.new_label("string_concat_left")
        right_loop = self.new_label("string_concat_right")
        finish = self.new_label("string_concat_end")
        self.emit(
            {
                "op": "call",
                "dest": "left_length",
                "type": "int",
                "funcs": ["__cool_string_length"],
                "args": ["left"],
            }
        )
        self.emit(
            {
                "op": "call",
                "dest": "right_length",
                "type": "int",
                "funcs": ["__cool_string_length"],
                "args": ["right"],
            }
        )
        self.emit(
            {"op": "add", "dest": "combined_length", "type": "int", "args": ["left_length", "right_length"]}
        )
        self.emit({"op": "const", "dest": "one", "type": "int", "value": 1})
        self.emit(
            {"op": "add", "dest": "size", "type": "int", "args": ["combined_length", "one"]}
        )
        self.emit({"op": "alloc", "dest": "result", "type": string_type, "args": ["size"]})
        self.emit({"op": "const", "dest": "left_index", "type": "int", "value": 0})
        self.emit({"op": "const", "dest": "result_index", "type": "int", "value": 0})
        self.emit({"label": left_loop})
        left_body = self.new_label("string_concat_left_body")
        self.emit(
            {"op": "eq", "dest": "left_finished", "type": "bool", "args": ["left_index", "left_length"]}
        )
        self.emit({"op": "br", "args": ["left_finished"], "labels": [right_loop, left_body]})
        self.emit({"label": left_body})
        self.emit(
            {"op": "ptradd", "dest": "left_address", "type": string_type, "args": ["left", "left_index"]}
        )
        self.emit({"op": "load", "dest": "character", "type": "int", "args": ["left_address"]})
        self.emit(
            {"op": "ptradd", "dest": "result_address", "type": string_type, "args": ["result", "result_index"]}
        )
        self.emit({"op": "store", "args": ["result_address", "character"]})
        self.emit({"op": "add", "dest": "left_index", "type": "int", "args": ["left_index", "one"]})
        self.emit({"op": "add", "dest": "result_index", "type": "int", "args": ["result_index", "one"]})
        self.emit({"op": "jmp", "labels": [left_loop]})
        self.emit({"label": right_loop})
        self.emit({"op": "const", "dest": "right_index", "type": "int", "value": 0})
        right_body = self.new_label("string_concat_right_body")
        self.emit(
            {"op": "eq", "dest": "right_finished", "type": "bool", "args": ["right_index", "right_length"]}
        )
        self.emit({"op": "br", "args": ["right_finished"], "labels": [finish, right_body]})
        self.emit({"label": right_body})
        self.emit(
            {"op": "ptradd", "dest": "right_address", "type": string_type, "args": ["right", "right_index"]}
        )
        self.emit({"op": "load", "dest": "character", "type": "int", "args": ["right_address"]})
        self.emit(
            {"op": "ptradd", "dest": "result_address", "type": string_type, "args": ["result", "result_index"]}
        )
        self.emit({"op": "store", "args": ["result_address", "character"]})
        self.emit({"op": "add", "dest": "right_index", "type": "int", "args": ["right_index", "one"]})
        self.emit({"op": "add", "dest": "result_index", "type": "int", "args": ["result_index", "one"]})
        self.emit({"op": "jmp", "labels": [right_loop]})
        self.emit({"label": finish})
        self.emit(
            {"op": "ptradd", "dest": "end_address", "type": string_type, "args": ["result", "result_index"]}
        )
        self.emit({"op": "const", "dest": "zero", "type": "int", "value": 0})
        self.emit({"op": "store", "args": ["end_address", "zero"]})
        self.emit({"op": "ret", "args": ["result"]})

    def _generate_string_substr(self) -> None:
        """Gera __cool_string_substr para copiar uma faixa da string."""
        string_type = self._string_pointer_type()
        self._start_function(
            "__cool_string_substr",
            [
                {"name": "text", "type": string_type},
                {"name": "start", "type": "int"},
                {"name": "length", "type": "int"},
            ],
            string_type,
        )
        loop = self.new_label("string_substr_loop")
        body = self.new_label("string_substr_body")
        end = self.new_label("string_substr_end")
        self.emit({"op": "const", "dest": "one", "type": "int", "value": 1})
        self.emit({"op": "add", "dest": "size", "type": "int", "args": ["length", "one"]})
        self.emit({"op": "alloc", "dest": "result", "type": string_type, "args": ["size"]})
        self.emit({"op": "const", "dest": "index", "type": "int", "value": 0})
        self.emit({"label": loop})
        self.emit({"op": "eq", "dest": "finished", "type": "bool", "args": ["index", "length"]})
        self.emit({"op": "br", "args": ["finished"], "labels": [end, body]})
        self.emit({"label": body})
        self.emit({"op": "add", "dest": "source_index", "type": "int", "args": ["start", "index"]})
        self.emit({"op": "ptradd", "dest": "source_address", "type": string_type, "args": ["text", "source_index"]})
        self.emit({"op": "load", "dest": "character", "type": "int", "args": ["source_address"]})
        self.emit({"op": "ptradd", "dest": "destination_address", "type": string_type, "args": ["result", "index"]})
        self.emit({"op": "store", "args": ["destination_address", "character"]})
        self.emit({"op": "add", "dest": "index", "type": "int", "args": ["index", "one"]})
        self.emit({"op": "jmp", "labels": [loop]})
        self.emit({"label": end})
        self.emit({"op": "ptradd", "dest": "end_address", "type": string_type, "args": ["result", "length"]})
        self.emit({"op": "const", "dest": "zero", "type": "int", "value": 0})
        self.emit({"op": "store", "args": ["end_address", "zero"]})
        self.emit({"op": "ret", "args": ["result"]})

    def _generate_string_runtime(self) -> None:
        """Inclui as rotinas Bril usadas pela classe nativa String de COOL."""
        self._generate_string_length()
        self._generate_string_concat()
        self._generate_string_substr()

    @staticmethod
    def _bril_type(cool_type: str) -> object:
        """Converte os tipos basicos de COOL para os tipos do Bril."""
        basic_types = {"Int": "int", "Bool": "bool", "String": {"ptr": "int"}}
        return basic_types.get(cool_type, {"ptr": "int"})

    def _build_class_layouts(self, program: ProgramNode) -> None:
        """Define o slot de cada atributo, preservando a ordem da heranca."""
        classes = {class_node.name: class_node for class_node in program.classes}
        self.class_parents = {
            class_node.name: class_node.parent for class_node in program.classes
        }
        built: set[str] = set()

        def build(class_name: str) -> None:
            if class_name in built or class_name not in classes:
                return
            class_node = classes[class_name]
            if class_node.parent in classes:
                build(class_node.parent)
            parent_layout = self.class_layouts.get(class_node.parent, {})
            layout = parent_layout.copy()
            for feature in class_node.features:
                if isinstance(feature, AttributeNode):
                    layout[feature.name] = (len(layout) + 1, feature.type_name, feature)
            self.class_layouts[class_name] = layout
            self.class_tags[class_name] = len(self.class_tags) + 1
            built.add(class_name)

        for class_node in program.classes:
            build(class_node.name)

    def _conforms_to_class(self, class_name: str, expected_parent: str) -> bool:
        """Informa se uma classe do programa herda de outra classe dada."""
        current: str | None = class_name
        while current is not None:
            if current == expected_parent:
                return True
            current = self.class_parents.get(current)
        return False

    def _method_implementation(self, class_name: str, method_name: str) -> str | None:
        """Encontra a classe que define a implementacao herdada de um metodo."""
        current: str | None = class_name
        while current in self.class_parents:
            class_layout = self._program_methods.get(current, set())
            if method_name in class_layout:
                return current
            current = self.class_parents.get(current)
        return None

    def _object_tag(self, object_register: str) -> str:
        """Carrega a tag dinamica guardada no primeiro slot do objeto."""
        position = self.new_temporary()
        address = self.new_temporary()
        tag = self.new_temporary()
        self.emit({"op": "const", "dest": position, "type": "int", "value": 0})
        self.emit(
            {
                "op": "ptradd",
                "dest": address,
                "type": {"ptr": "int"},
                "args": [object_register, position],
            }
        )
        self.emit({"op": "load", "dest": tag, "type": "int", "args": [address]})
        return tag

    def _generate_method_call(
        self,
        expression: MethodCallNode,
        expression_types: dict[int, str],
        environment: dict[str, str | AttributeAccess],
    ) -> str:
        """Gera um despacho estatico ou dinamico para metodos de classes COOL."""
        if expression.receiver is None:
            receiver = environment.get("self")
            if not isinstance(receiver, str):
                raise CodeGenerationError("Chamada implicita sem objeto self")
            receiver_type = self.current_class
        else:
            receiver = self._generate_expression(
                expression.receiver, expression_types, environment
            )
            if receiver is None:
                raise CodeGenerationError("Receptor de chamada sem valor")
            receiver_type = expression_types.get(id(expression.receiver))
            if receiver_type == "SELF_TYPE":
                receiver_type = self.current_class
        if receiver_type is None:
            raise CodeGenerationError("Tipo ausente para o receptor de uma chamada")

        dispatch_type = expression.static_type or receiver_type
        if dispatch_type not in self.class_parents:
            raise CodeGenerationError(
                f"Chamada de metodo nativo '{dispatch_type}.{expression.method}' ainda nao foi implementada"
            )
        arguments: list[str] = [receiver]
        for argument in expression.args:
            value = self._generate_expression(argument, expression_types, environment)
            if value is None:
                raise CodeGenerationError("Argumento de chamada sem valor")
            arguments.append(value)

        return_type = expression_types.get(id(expression))
        if return_type is None:
            raise CodeGenerationError("Tipo ausente para o retorno de uma chamada")
        result = self.new_temporary()
        result_bril_type = self._bril_type(
            self.current_class if return_type == "SELF_TYPE" else return_type
        )

        if expression.static_type is not None:
            implementation = self._method_implementation(dispatch_type, expression.method)
            if implementation is None:
                raise CodeGenerationError(
                    f"Metodo '{expression.method}' ainda nao possui implementacao Bril"
                )
            self.emit(
                {
                    "op": "call",
                    "dest": result,
                    "type": result_bril_type,
                    "funcs": [self._method_name(implementation, expression.method)],
                    "args": arguments,
                }
            )
            return result

        tag = self._object_tag(receiver)
        end_label = self.new_label("dispatch_end")
        candidates = [
            class_name
            for class_name in self.class_tags
            if self._conforms_to_class(class_name, dispatch_type)
        ]
        if not candidates:
            raise CodeGenerationError(
                f"Nenhuma classe encontrada para o despacho de '{expression.method}'"
            )
        for index, candidate in enumerate(candidates):
            call_label = self.new_label("dispatch_call")
            next_label = end_label if index == len(candidates) - 1 else self.new_label("dispatch_next")
            expected_tag = self.new_temporary()
            matches = self.new_temporary()
            self.emit(
                {"op": "const", "dest": expected_tag, "type": "int", "value": self.class_tags[candidate]}
            )
            self.emit({"op": "eq", "dest": matches, "type": "bool", "args": [tag, expected_tag]})
            self.emit({"op": "br", "args": [matches], "labels": [call_label, next_label]})
            self.emit({"label": call_label})
            implementation = self._method_implementation(candidate, expression.method)
            if implementation is None:
                raise CodeGenerationError(
                    f"Metodo '{expression.method}' ainda nao possui implementacao Bril"
                )
            self.emit(
                {
                    "op": "call",
                    "dest": result,
                    "type": result_bril_type,
                    "funcs": [self._method_name(implementation, expression.method)],
                    "args": arguments,
                }
            )
            self.emit({"op": "jmp", "labels": [end_label]})
            if next_label != end_label:
                self.emit({"label": next_label})
        self.emit({"label": end_label})
        return result

    def _attribute_address(self, attribute: AttributeAccess) -> str:
        """Produz o endereco Bril de um slot de atributo."""
        position = self.new_temporary()
        address = self.new_temporary()
        self.emit({"op": "const", "dest": position, "type": "int", "value": attribute.slot})
        self.emit(
            {
                "op": "ptradd",
                "dest": address,
                "type": {"ptr": "int"},
                "args": [attribute.object_register, position],
            }
        )
        return address

    def _read_attribute(self, attribute: AttributeAccess) -> str:
        """Carrega um atributo basico do objeto atual."""
        if attribute.type_name not in {"Int", "Bool"}:
            raise CodeGenerationError(
                f"Atributos do tipo '{attribute.type_name}' serao suportados no runtime completo"
            )
        address = self._attribute_address(attribute)
        result = self.new_temporary()
        self.emit(
            {
                "op": "load",
                "dest": result,
                "type": self._bril_type(attribute.type_name),
                "args": [address],
            }
        )
        return result

    def _write_attribute(self, attribute: AttributeAccess, value: str) -> None:
        """Armazena um valor basico em um atributo do objeto atual."""
        if attribute.type_name not in {"Int", "Bool"}:
            raise CodeGenerationError(
                f"Atributos do tipo '{attribute.type_name}' serao suportados no runtime completo"
            )
        self.emit({"op": "store", "args": [self._attribute_address(attribute), value]})

    def _new_object(self, type_name: str, expression_types: dict[int, str]) -> str:
        """Aloca uma instancia e executa as inicializacoes de seus atributos."""
        if type_name not in self.class_layouts:
            raise CodeGenerationError(f"Instanciacao de '{type_name}' ainda nao foi implementada")
        layout = self.class_layouts[type_name]
        object_register = self.new_temporary()
        size = self.new_temporary()
        self.emit({"op": "const", "dest": size, "type": "int", "value": len(layout) + 1})
        self.emit({"op": "alloc", "dest": object_register, "type": {"ptr": "int"}, "args": [size]})
        tag_position = self.new_temporary()
        tag_address = self.new_temporary()
        tag_value = self.new_temporary()
        self.emit({"op": "const", "dest": tag_position, "type": "int", "value": 0})
        self.emit({"op": "ptradd", "dest": tag_address, "type": {"ptr": "int"}, "args": [object_register, tag_position]})
        self.emit({"op": "const", "dest": tag_value, "type": "int", "value": self.class_tags[type_name]})
        self.emit({"op": "store", "args": [tag_address, tag_value]})

        environment: dict[str, str | AttributeAccess] = {"self": object_register}
        for name, (slot, attribute_type, _) in layout.items():
            environment[name] = AttributeAccess(object_register, slot, attribute_type)
        for _, (_, attribute_type, attribute) in layout.items():
            access = environment[attribute.name]
            assert isinstance(access, AttributeAccess)
            if attribute_type == "Int":
                default = self.new_temporary()
                self.emit({"op": "const", "dest": default, "type": "int", "value": 0})
                self._write_attribute(access, default)
            elif attribute_type == "Bool":
                default = self.new_temporary()
                self.emit({"op": "const", "dest": default, "type": "bool", "value": False})
                self._write_attribute(access, default)
            else:
                raise CodeGenerationError(
                    f"Atributos do tipo '{attribute_type}' serao suportados no runtime completo"
                )
            if attribute.init is not None:
                value = self._generate_expression(attribute.init, expression_types, environment)
                if value is None:
                    raise CodeGenerationError("Inicializacao de atributo sem valor")
                self._write_attribute(access, value)
        return object_register

    def _generate_string_literal(self, value: str) -> str:
        """Aloca os caracteres UTF-8 basicos de uma string e seu terminador."""
        result = self.new_temporary()
        size = self.new_temporary()
        self.emit({"op": "const", "dest": size, "type": "int", "value": len(value) + 1})
        self.emit({"op": "alloc", "dest": result, "type": self._string_pointer_type(), "args": [size]})
        for index, character in enumerate(value):
            position = self.new_temporary()
            address = self.new_temporary()
            code = self.new_temporary()
            self.emit({"op": "const", "dest": position, "type": "int", "value": index})
            self.emit({"op": "ptradd", "dest": address, "type": self._string_pointer_type(), "args": [result, position]})
            self.emit({"op": "const", "dest": code, "type": "int", "value": ord(character)})
            self.emit({"op": "store", "args": [address, code]})
        terminator_position = self.new_temporary()
        terminator_address = self.new_temporary()
        zero = self.new_temporary()
        self.emit({"op": "const", "dest": terminator_position, "type": "int", "value": len(value)})
        self.emit({"op": "ptradd", "dest": terminator_address, "type": self._string_pointer_type(), "args": [result, terminator_position]})
        self.emit({"op": "const", "dest": zero, "type": "int", "value": 0})
        self.emit({"op": "store", "args": [terminator_address, zero]})
        return result

    def _generate_expression(
        self,
        expression: object,
        expression_types: dict[int, str],
        environment: dict[str, str | AttributeAccess],
    ) -> str | None:
        """Traduz uma expressao basica e devolve o registrador com seu valor."""
        if isinstance(expression, LiteralNode):
            if expression.type_name == "String":
                return self._generate_string_literal(expression.value)
            result = self.new_temporary()
            self.emit(
                {
                    "op": "const",
                    "dest": result,
                    "type": self._bril_type(expression.type_name),
                    "value": expression.value,
                }
            )
            return result

        if isinstance(expression, VariableNode):
            if expression.name not in environment:
                raise CodeGenerationError(
                    f"A variavel '{expression.name}' ainda nao pode ser usada na geracao Bril"
                )
            value = environment[expression.name]
            if isinstance(value, AttributeAccess):
                return self._read_attribute(value)
            return value

        if isinstance(expression, AssignNode):
            value = self._generate_expression(expression.value, expression_types, environment)
            target = environment.get(expression.name)
            if target is None:
                raise CodeGenerationError(
                    f"A atribuicao a '{expression.name}' ainda nao pode ser gerada"
                )
            value_type = expression_types.get(id(expression.value))
            if value_type is None:
                raise CodeGenerationError("Tipo ausente para uma atribuicao COOL")
            if isinstance(target, AttributeAccess):
                self._write_attribute(target, value)
                return value
            self.emit({"op": "id", "dest": target, "type": self._bril_type(value_type), "args": [value]})
            return target

        if isinstance(expression, BinaryOpNode):
            left = self._generate_expression(expression.left, expression_types, environment)
            right = self._generate_expression(expression.right, expression_types, environment)
            operation = {"+": "add", "-": "sub", "*": "mul", "/": "div", "<": "lt", "<=": "le", "=": "eq"}.get(expression.operator)
            if operation is None:
                raise CodeGenerationError(f"Operador '{expression.operator}' nao suportado")
            result_type = expression_types.get(id(expression))
            if result_type is None:
                raise CodeGenerationError("Tipo ausente para uma operacao COOL")
            result = self.new_temporary()
            self.emit({"op": operation, "dest": result, "type": self._bril_type(result_type), "args": [left, right]})
            return result

        if isinstance(expression, UnaryOpNode):
            operand = self._generate_expression(expression.operand, expression_types, environment)
            if operand is None:
                raise CodeGenerationError("Operando sem valor em uma operacao unaria")
            result = self.new_temporary()
            if expression.operator == "not":
                self.emit({"op": "not", "dest": result, "type": "bool", "args": [operand]})
                return result
            if expression.operator == "~":
                zero = self.new_temporary()
                self.emit({"op": "const", "dest": zero, "type": "int", "value": 0})
                self.emit({"op": "sub", "dest": result, "type": "int", "args": [zero, operand]})
                return result
            if expression.operator == "isvoid":
                self.emit({"op": "const", "dest": result, "type": "bool", "value": False})
                return result
            raise CodeGenerationError(f"Operador '{expression.operator}' nao suportado")

        if isinstance(expression, BlockNode):
            value: str | None = None
            for item in expression.expressions:
                value = self._generate_expression(item, expression_types, environment)
            return value

        if isinstance(expression, LetNode):
            local_environment = environment.copy()
            for binding in expression.bindings:
                variable = self.new_temporary()
                local_environment[binding.name] = variable
                if binding.init is not None:
                    initial_value = self._generate_expression(
                        binding.init, expression_types, local_environment
                    )
                    if initial_value is None:
                        raise CodeGenerationError("Inicializacao de let sem valor")
                    self.emit(
                        {
                            "op": "id",
                            "dest": variable,
                            "type": self._bril_type(binding.type_name),
                            "args": [initial_value],
                        }
                    )
                    continue

                if binding.type_name == "Int":
                    default_value: object = 0
                elif binding.type_name == "Bool":
                    default_value = False
                elif binding.type_name == "String":
                    default_string = self._generate_string_literal("")
                    self.emit(
                        {
                            "op": "id",
                            "dest": variable,
                            "type": self._string_pointer_type(),
                            "args": [default_string],
                        }
                    )
                    continue
                else:
                    raise CodeGenerationError(
                        f"Valor padrao de let para '{binding.type_name}' ainda nao foi implementado"
                    )
                self.emit(
                    {
                        "op": "const",
                        "dest": variable,
                        "type": self._bril_type(binding.type_name),
                        "value": default_value,
                    }
                )
            return self._generate_expression(
                expression.body, expression_types, local_environment
            )

        if isinstance(expression, IfNode):
            condition = self._generate_expression(
                expression.condition, expression_types, environment
            )
            if condition is None:
                raise CodeGenerationError("Condicao de if sem valor")
            then_label = self.new_label("if_then")
            else_label = self.new_label("if_else")
            end_label = self.new_label("if_end")
            result_type = expression_types.get(id(expression))
            if result_type is None:
                raise CodeGenerationError("Tipo ausente para um if COOL")
            result = self.new_temporary()
            bril_type = self._bril_type(result_type)
            self.emit({"op": "br", "args": [condition], "labels": [then_label, else_label]})
            self.emit({"label": then_label})
            then_value = self._generate_expression(
                expression.then_expr, expression_types, environment.copy()
            )
            if then_value is None:
                raise CodeGenerationError("Ramo then sem valor")
            self.emit({"op": "id", "dest": result, "type": bril_type, "args": [then_value]})
            self.emit({"op": "jmp", "labels": [end_label]})
            self.emit({"label": else_label})
            else_value = self._generate_expression(
                expression.else_expr, expression_types, environment.copy()
            )
            if else_value is None:
                raise CodeGenerationError("Ramo else sem valor")
            self.emit({"op": "id", "dest": result, "type": bril_type, "args": [else_value]})
            self.emit({"label": end_label})
            return result

        if isinstance(expression, WhileNode):
            condition_label = self.new_label("while_condition")
            body_label = self.new_label("while_body")
            end_label = self.new_label("while_end")
            self.emit({"label": condition_label})
            condition = self._generate_expression(
                expression.condition, expression_types, environment
            )
            if condition is None:
                raise CodeGenerationError("Condicao de while sem valor")
            self.emit({"op": "br", "args": [condition], "labels": [body_label, end_label]})
            self.emit({"label": body_label})
            self._generate_expression(expression.body, expression_types, environment.copy())
            self.emit({"op": "jmp", "labels": [condition_label]})
            self.emit({"label": end_label})
            return None

        if isinstance(expression, NewNode):
            return self._new_object(expression.type_name, expression_types)

        if isinstance(expression, MethodCallNode):
            return self._generate_method_call(expression, expression_types, environment)

        raise CodeGenerationError(
            f"Geracao Bril para '{type(expression).__name__}' ainda nao foi implementada"
        )

    @staticmethod
    def _main_method(program: ProgramNode) -> MethodNode:
        """Localiza o corpo de Main.main, ponto inicial desta primeira traducao."""
        for class_node in program.classes:
            if class_node.name == "Main":
                for feature in class_node.features:
                    if isinstance(feature, MethodNode) and feature.name == "main":
                        return feature
        raise CodeGenerationError("Metodo Main.main nao encontrado")

    @staticmethod
    def _method_name(class_name: str, method_name: str) -> str:
        """Cria um nome Bril sem ambiguidades para um metodo COOL."""
        return f"{class_name}__{method_name}"

    def _generate_method(
        self,
        class_name: str,
        method: MethodNode,
        expression_types: dict[int, str],
    ) -> None:
        """Traduz um metodo COOL basico para uma funcao Bril com retorno."""
        arguments: list[dict] = []
        environment: dict[str, str | AttributeAccess] = {}
        self_register = self.new_temporary()
        arguments.append({"name": self_register, "type": {"ptr": "int"}})
        environment["self"] = self_register
        for attribute_name, (slot, type_name, _) in self.class_layouts.get(
            class_name, {}
        ).items():
            environment[attribute_name] = AttributeAccess(self_register, slot, type_name)
        for parameter in method.params:
            argument_name = self.new_temporary()
            arguments.append(
                {"name": argument_name, "type": self._bril_type(parameter.type_name)}
            )
            environment[parameter.name] = argument_name

        body_type = expression_types.get(id(method.body))
        if body_type is None:
            raise CodeGenerationError(
                f"Tipo ausente para o corpo de {class_name}.{method.name}"
            )
        self._start_function(
            self._method_name(class_name, method.name), arguments, self._bril_type(body_type)
        )
        previous_class = self.current_class
        self.current_class = class_name
        result = self._generate_expression(method.body, expression_types, environment)
        self.current_class = previous_class
        if result is None:
            raise CodeGenerationError(
                f"O metodo {class_name}.{method.name} nao produz um valor Bril"
            )
        self.emit({"op": "ret", "args": [result]})

    def _generate_methods(
        self, program: ProgramNode, expression_types: dict[int, str]
    ) -> None:
        """Gera as funcoes dos metodos definidos pelo usuario."""
        for class_node in program.classes:
            for feature in class_node.features:
                if not isinstance(feature, MethodNode):
                    continue
                if class_node.name == "Main" and feature.name == "main":
                    continue
                self._generate_method(class_node.name, feature, expression_types)

    def generate(self, program: ProgramNode) -> dict:
        """Gera a estrutura JSON inicial de um programa Bril.

        A traducao de expressoes, metodos e objetos sera incluida nos proximos
        commits. Nesta etapa, o objetivo e produzir uma base Bril valida.
        """
        if not isinstance(program, ProgramNode):
            raise TypeError("A geracao de codigo espera um ProgramNode")

        self.functions = []
        self._temporary_index = 0
        self._label_index = 0
        self.class_layouts = {}
        self.class_tags = {}
        self.class_parents = {}
        self._program_methods: dict[str, set[str]] = {}
        analysis: SemanticResult = analyze(program)
        if not analysis.success:
            raise CodeGenerationError("Nao e possivel gerar Bril para um programa semanticamente invalido")
        self._generate_string_runtime()
        self._build_class_layouts(program)
        self._program_methods = {
            class_node.name: {
                feature.name
                for feature in class_node.features
                if isinstance(feature, MethodNode)
            }
            for class_node in program.classes
        }
        self._generate_methods(program, analysis.expression_types)
        self._generate_entry_point()
        self.current_class = "Main"
        self._generate_expression(self._main_method(program).body, analysis.expression_types, {})
        return {"functions": self.functions}


def generate_bril(program: ProgramNode) -> dict:
    """Gera um programa Bril em seu formato JSON canonico."""
    return BrilGenerator().generate(program)
