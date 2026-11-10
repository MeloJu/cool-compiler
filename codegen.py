"""Infraestrutura para gerar programas Bril a partir da AST de COOL."""

from ast_nodes import ProgramNode


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
        return {"functions": self.functions}


def generate_bril(program: ProgramNode) -> dict:
    """Gera um programa Bril em seu formato JSON canonico."""
    return BrilGenerator().generate(program)
