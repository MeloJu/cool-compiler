# A integração entre o analisador léxico e o analisador sintático foi feita.
# O lexer agora expõe uma função que cria uma instância limpa para o parser consumir. 
# O parser foi criado com ply.yacc.

from dataclasses import dataclass

import ply.yacc as yacc

from lexer import build_lexer, tokens


@dataclass
class ClassNode:
    name: str


@dataclass
class ProgramNode:
    classes: list[ClassNode]


def p_program(p):
    """program : class_decl"""
    p[0] = ProgramNode(classes=[p[1]])


def p_class_decl(p):
    """class_decl : CLASS TYPEID '{' '}' ';'"""
    p[0] = ClassNode(name=p[2])


def p_error(p):
    if p is None:
        raise SyntaxError("Erro sintatico: fim de arquivo inesperado")
    if p.type == "ERROR":
        raise SyntaxError(f"Erro lexico na linha {p.lineno}: {p.value}")
    raise SyntaxError(
        f"Erro sintatico na linha {p.lineno}: token inesperado {p.type} ({p.value!r})"
    )


_parser = yacc.yacc(
    start="program",
    debug=False,
    write_tables=False,
    errorlog=yacc.NullLogger(),
)


def parse(source: str) -> ProgramNode:
    """Recebe codigo-fonte COOL e devolve a arvore sintatica inicial."""
    lexer = build_lexer(source)
    return _parser.parse(lexer=lexer)
