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
        self.instructions = []
        self.functions.append({"name": "main", "instrs": self.instructions})

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
        self._generate_entry_point()
        return {"functions": self.functions}


def generate_bril(program: ProgramNode) -> dict:
    """Gera um programa Bril em seu formato JSON canonico."""
    return BrilGenerator().generate(program)
