"""
Analisador léxico para a linguagem COOL (Classroom Object Oriented Language),
construído com PLY (Python Lex-Yacc) — a versão em Python das ferramentas
clássicas lex/yacc citadas no enunciado.

Em vez de escrever o loop de leitura na mão, aqui só *declaramos* os tokens
(cada um como uma expressão regular) e o PLY monta o tokenizer sozinho.
Comentários de bloco aninhados e strings usam "estados exclusivos" do PLY
(`states`), que são o equivalente aos "start conditions" do flex.

Tokens reconhecidos:
    - Palavras-chave: class, else, fi, if, in, inherits, isvoid, let, loop,
      pool, then, while, case, esac, new, of, not (case-insensitive)
    - Booleanos: true, false (a primeira letra deve ser minúscula)
    - TYPEID: identificador iniciado com letra maiúscula
    - OBJECTID: identificador iniciado com letra minúscula
    - INT_CONST: sequência de dígitos
    - STR_CONST: string entre aspas, com escapes (\\n \\t \\b \\f \\" \\\\ etc.)
    - Símbolos literais: { } ( ) : ; , . @ ~ * / + - < =
    - Símbolos de 2 caracteres: <- <= =>
    - Comentários: linha (--) e bloco aninhado ((* *)), ambos descartados

Erros léxicos detectados (viram token ERROR em vez de exceção):
    - Caractere desconhecido
    - String não terminada (fim de linha ou fim de arquivo dentro da string)
    - String contendo caractere nulo
    - String maior que 1024 caracteres
    - Comentário de bloco não fechado (EOF dentro do comentário)
    - "*)" sem "(*" correspondente
"""

from dataclasses import dataclass
from typing import List, Optional

import ply.lex as lex

MAX_STR_LEN = 1024

# palavra reservada (minúscula) -> nome do token
reserved = {
    "class": "CLASS",
    "else": "ELSE",
    "fi": "FI",
    "if": "IF",
    "in": "IN",
    "inherits": "INHERITS",
    "isvoid": "ISVOID",
    "let": "LET",
    "loop": "LOOP",
    "pool": "POOL",
    "then": "THEN",
    "while": "WHILE",
    "case": "CASE",
    "esac": "ESAC",
    "new": "NEW",
    "of": "OF",
    "not": "NOT",
}

# tokens que não carregam valor (o tipo já diz tudo) ao imprimir
_NO_VALUE = set(reserved.values()) | {"ASSIGN", "LE", "DARROW"}

# --- vocabulário exigido pelo PLY -----------------------------------------
tokens = [
    "ASSIGN", "LE", "DARROW",
    "TYPEID", "OBJECTID", "INT_CONST", "STR_CONST", "BOOL_CONST",
    "ERROR",
] + list(reserved.values())

# símbolos de 1 caractere: o PLY cria o token sozinho, com type == o caractere
literals = ["{", "}", "(", ")", ":", ";", ",", ".", "@", "~", "*", "/", "+", "-", "<", "="]

# estados exclusivos: enquanto ativos, só as regras "t_<estado>_*" valem
states = (
    ("comment", "exclusive"),
    ("string", "exclusive"),
)


# ---------------------------------------------------------------------------
# Estado INITIAL
# ---------------------------------------------------------------------------

t_ignore = " \t\r\f\v"          # espaços em branco são simplesmente pulados
t_ASSIGN = r"<-"
t_LE = r"<="
t_DARROW = r"=>"


def t_TYPEID(t):
    r"[A-Z][A-Za-z0-9_]*"
    low = t.value.lower()
    if low in reserved:
        t.type = reserved[low]
    return t


def t_OBJECTID(t):
    r"[a-z][A-Za-z0-9_]*"
    low = t.value.lower()
    if low == "true" and t.value[0] == "t":
        t.type = "BOOL_CONST"
        t.value = "true"
    elif low == "false" and t.value[0] == "f":
        t.type = "BOOL_CONST"
        t.value = "false"
    elif low in reserved:
        t.type = reserved[low]
    return t


def t_INT_CONST(t):
    r"\d+"
    return t


def t_line_comment(t):
    r"--[^\n]*"
    pass  # descartado, não vira token


def t_open_comment(t):
    r"\(\*"
    t.lexer.comment_start_line = t.lexer.lineno
    t.lexer.comment_depth = 1
    t.lexer.begin("comment")


def t_unmatched_close_comment(t):
    r"\*\)"
    t.type = "ERROR"
    t.value = "Unmatched *)"
    return t


def t_open_string(t):
    r'"'
    t.lexer.string_start_line = t.lexer.lineno
    t.lexer.string_buffer = ""
    t.lexer.string_has_null = False
    t.lexer.begin("string")


def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)


def t_error(t):
    t.type = "ERROR"
    t.value = t.value[0]
    t.lexer.skip(1)
    return t


# ---------------------------------------------------------------------------
# Estado "comment": corpo de um comentário de bloco (* ... *), com aninhamento
# ---------------------------------------------------------------------------

t_comment_ignore = ""


def t_comment_open(t):
    r"\(\*"
    t.lexer.comment_depth += 1


def t_comment_close(t):
    r"\*\)"
    t.lexer.comment_depth -= 1
    if t.lexer.comment_depth == 0:
        t.lexer.begin("INITIAL")


def t_comment_newline(t):
    r"\n"
    t.lexer.lineno += 1


def t_comment_body(t):
    r"."
    pass  # qualquer outro caractere dentro do comentário é ignorado


def t_comment_eof(t):
    line = t.lexer.comment_start_line
    t.lexer.begin("INITIAL")
    t.type = "ERROR"
    t.value = "EOF in comment"
    t.lineno = line
    return t


def t_comment_error(t):
    t.lexer.skip(1)


# ---------------------------------------------------------------------------
# Estado "string": corpo de uma string "...", com escapes e validações
# ---------------------------------------------------------------------------

t_string_ignore = ""


def t_string_escape(t):
    r"\\(.|\n)"
    esc = t.value[1]
    if esc == "n":
        t.lexer.string_buffer += "\n"
    elif esc == "t":
        t.lexer.string_buffer += "\t"
    elif esc == "b":
        t.lexer.string_buffer += "\b"
    elif esc == "f":
        t.lexer.string_buffer += "\f"
    elif esc == "\0":
        t.lexer.string_has_null = True
    else:
        # "\c" para qualquer outro c vira apenas c (cobre \" \\ e a
        # continuação de linha "\<newline>")
        t.lexer.string_buffer += esc
    if esc == "\n":
        t.lexer.lineno += 1


def t_string_null(t):
    r"\x00"
    t.lexer.string_has_null = True


def t_string_close(t):
    r'"'
    line = t.lexer.string_start_line
    t.lexer.begin("INITIAL")
    t.lineno = line
    if t.lexer.string_has_null:
        t.type = "ERROR"
        t.value = "String contains null character."
    elif len(t.lexer.string_buffer) > MAX_STR_LEN:
        t.type = "ERROR"
        t.value = "String constant too long"
    else:
        t.type = "STR_CONST"
        t.value = _escape_for_display(t.lexer.string_buffer)
    return t


def t_string_newline(t):
    r"\n"
    line = t.lexer.string_start_line
    t.lexer.lineno += 1
    t.lexer.begin("INITIAL")
    t.type = "ERROR"
    t.value = "Unterminated string constant"
    t.lineno = line
    return t


def t_string_body(t):
    r'[^\\\n"\x00]+'
    t.lexer.string_buffer += t.value


def t_string_eof(t):
    line = t.lexer.string_start_line
    t.lexer.begin("INITIAL")
    t.type = "ERROR"
    t.value = "EOF in string constant"
    t.lineno = line
    return t


def t_string_error(t):
    t.lexer.skip(1)


# ---------------------------------------------------------------------------
# Camada fina por cima do PLY: Token com o mesmo formato de antes e a função
# tokenize(source) usada pelo resto do projeto (main.py, testes).
# ---------------------------------------------------------------------------

@dataclass
class Token:
    type: str
    value: Optional[str]
    line: int

    def __str__(self) -> str:
        if len(self.type) == 1:  # símbolo literal: { } ( ) : ; , . @ ~ * / + - < =
            return f"#{self.line} '{self.type}'"
        if self.value is None:
            return f"#{self.line} {self.type}"
        if self.type == "STR_CONST":
            return f'#{self.line} STR_CONST "{self.value}"'
        if self.type == "ERROR":
            return f'#{self.line} ERROR "{self.value}"'
        return f"#{self.line} {self.type} {self.value}"


def _escape_for_display(s: str) -> str:
    """Reescreve caracteres de controle como escapes visíveis (\\n, \\t, ...)."""
    out = []
    for ch in s:
        if ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\b":
            out.append("\\b")
        elif ch == "\f":
            out.append("\\f")
        elif ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        else:
            out.append(ch)
    return "".join(out)


_lexer = lex.lex()


def tokenize(source: str) -> List[Token]:
    """Recebe o código-fonte COOL e devolve a lista de tokens (inclui ERROR)."""
    lexer = _lexer.clone()
    lexer.begin("INITIAL")
    lexer.lineno = 1
    lexer.input(source)

    result: List[Token] = []
    while True:
        tok = lexer.token()
        if tok is None:
            break
        value = None if tok.type in _NO_VALUE or len(tok.type) == 1 else tok.value
        result.append(Token(tok.type, value, tok.lineno))
    return result
