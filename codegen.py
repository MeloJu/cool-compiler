"""Geracao de programas Bril a partir da AST de COOL."""

from ast_nodes import (
    AssignNode,
    BinaryOpNode,
    BlockNode,
    IfNode,
    LetNode,
    LiteralNode,
    MethodNode,
    ProgramNode,
    UnaryOpNode,
    VariableNode,
    WhileNode,
)
from semantic import SemanticResult, analyze


class CodeGenerationError(Exception):
    """Indica que uma construcao COOL ainda nao possui traducao para Bril."""


class BrilGenerator:
    """Monta um programa Bril e controla nomes temporarios e labels."""

    def __init__(self) -> None:
        self.functions: list[dict] = []
        self.instructions: list[dict] = []
        self._temporary_index = 0
        self._label_index = 0

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
        if cool_type not in basic_types:
            raise CodeGenerationError(
                f"A geracao de codigo para o tipo '{cool_type}' ainda nao foi implementada"
            )
        return basic_types[cool_type]

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
        environment: dict[str, str],
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
            return environment[expression.name]

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
        self._generate_string_runtime()
        self._generate_entry_point()
        analysis: SemanticResult = analyze(program)
        if not analysis.success:
            raise CodeGenerationError("Nao e possivel gerar Bril para um programa semanticamente invalido")
        self._generate_expression(self._main_method(program).body, analysis.expression_types, {})
        return {"functions": self.functions}


def generate_bril(program: ProgramNode) -> dict:
    """Gera um programa Bril em seu formato JSON canonico."""
    return BrilGenerator().generate(program)
