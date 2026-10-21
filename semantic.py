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


@dataclass
class SemanticResult:
    """Resultado da analise semantica de um programa."""

    errors: list[SemanticError] = field(default_factory=list)

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

    return SemanticResult()
