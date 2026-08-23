"""
Analisador léxico para a linguagem COOL (Classroom Object Oriented Language).

Implementação manual (sem geradores de lexer): percorre o código-fonte
caractere a caractere reconhecendo os tokens da linguagem.

Tokens reconhecidos:
    - Palavras-chave: class, else, fi, if, in, inherits, isvoid, let, loop,
      pool, then, while, case, esac, new, of, not (case-insensitive)
    - Booleanos: true, false (a primeira letra deve ser minúscula)
    - TYPEID: identificador iniciado com letra maiúscula
    - OBJECTID: identificador iniciado com letra minúscula
    - INT_CONST: sequência de dígitos
    - STR_CONST: string entre aspas, com escapes (\\n \\t \\b \\f \\" \\\\ etc.)
    - Símbolos: { } ( ) : ; , . @ ~ * / + - < = <- <= =>
    - Comentários: linha (--) e bloco aninhado ((* *)), ambos descartados

Erros léxicos detectados:
    - Caractere desconhecido
    - String não terminada (fim de linha ou fim de arquivo dentro da string)
    - String contendo caractere nulo
    - String maior que 1024 caracteres
    - Comentário de bloco não fechado (EOF dentro do comentário)
    - "*)" sem "(*" correspondente
"""

from dataclasses import dataclass
from typing import List, Optional

MAX_STR_LEN = 1024

KEYWORDS = {
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

# Símbolos de 1 caractere (os de 2 caracteres são tratados à parte)
SYMBOLS = {
    "{": "'{'",
    "}": "'}'",
    "(": "'('",
    ")": "')'",
    ":": "':'",
    ";": "';'",
    ",": "','",
    ".": "'.'",
    "@": "'@'",
    "~": "'~'",
    "*": "'*'",
    "/": "'/'",
    "+": "'+'",
    "-": "'-'",
    "<": "'<'",
    "=": "'='",
}

TWO_CHAR_SYMBOLS = {
    "<-": "ASSIGN",
    "<=": "LE",
    "=>": "DARROW",
}


@dataclass
class Token:
    type: str
    value: Optional[str]
    line: int

    def __str__(self) -> str:
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


class Lexer:
    def __init__(self, source: str):
        self.src = source
        self.pos = 0
        self.line = 1
        self.length = len(source)
        self.tokens: List[Token] = []

    # -- utilitários de leitura -------------------------------------------
    def _peek(self, offset: int = 0) -> str:
        p = self.pos + offset
        return self.src[p] if p < self.length else ""

    def _advance(self) -> str:
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
        return ch

    def _add(self, type_: str, value: Optional[str], line: int) -> None:
        self.tokens.append(Token(type_, value, line))

    # -- laço principal -----------------------------------------------------
    def tokenize(self) -> List[Token]:
        while self.pos < self.length:
            ch = self._peek()

            if ch in " \t\r\f\v\n":
                self._advance()
                continue

            if ch == "-" and self._peek(1) == "-":
                self._skip_line_comment()
                continue

            if ch == "(" and self._peek(1) == "*":
                self._skip_block_comment()
                continue

            if ch == "*" and self._peek(1) == ")":
                start_line = self.line
                self._advance()
                self._advance()
                self._add("ERROR", "Unmatched *)", start_line)
                continue

            if ch == '"':
                self._read_string()
                continue

            if ch.isdigit():
                self._read_integer()
                continue

            if ch.isalpha():
                self._read_identifier()
                continue

            if self._read_symbol():
                continue

            start_line = self.line
            bad = self._advance()
            self._add("ERROR", bad, start_line)

        return self.tokens

    # -- comentários -----------------------------------------------------
    def _skip_line_comment(self) -> None:
        while self.pos < self.length and self._peek() != "\n":
            self._advance()

    def _skip_block_comment(self) -> None:
        start_line = self.line
        self._advance()
        self._advance()  # consome "(*"
        depth = 1
        while depth > 0:
            if self.pos >= self.length:
                self._add("ERROR", "EOF in comment", start_line)
                return
            if self._peek() == "(" and self._peek(1) == "*":
                self._advance()
                self._advance()
                depth += 1
            elif self._peek() == "*" and self._peek(1) == ")":
                self._advance()
                self._advance()
                depth -= 1
            else:
                self._advance()

    # -- strings -----------------------------------------------------
    def _read_string(self) -> None:
        start_line = self.line
        self._advance()  # consome a aspas de abertura

        chars: List[str] = []
        contains_null = False
        error: Optional[str] = None

        while True:
            if self.pos >= self.length:
                error = "EOF in string constant"
                break

            ch = self._peek()

            if ch == '"':
                self._advance()
                break

            if ch == "\n":
                self._advance()
                error = "Unterminated string constant"
                break

            if ch == "\0":
                contains_null = True
                self._advance()
                continue

            if ch == "\\":
                self._advance()
                if self.pos >= self.length:
                    error = "EOF in string constant"
                    break
                esc = self._advance()
                if esc == "n":
                    chars.append("\n")
                elif esc == "t":
                    chars.append("\t")
                elif esc == "b":
                    chars.append("\b")
                elif esc == "f":
                    chars.append("\f")
                elif esc == "\0":
                    contains_null = True
                else:
                    # "\c" para qualquer outro c vira apenas c (inclui \n literal
                    # de continuação de linha, \" e \\)
                    chars.append(esc)
                continue

            chars.append(ch)
            self._advance()

        if contains_null:
            self._add("ERROR", "String contains null character.", start_line)
        elif error:
            self._add("ERROR", error, start_line)
        elif len(chars) > MAX_STR_LEN:
            self._add("ERROR", "String constant too long", start_line)
        else:
            self._add("STR_CONST", _escape_for_display("".join(chars)), start_line)

    # -- números -----------------------------------------------------
    def _read_integer(self) -> None:
        start_line = self.line
        start = self.pos
        while self.pos < self.length and self._peek().isdigit():
            self._advance()
        self._add("INT_CONST", self.src[start:self.pos], start_line)

    # -- identificadores e palavras-chave --------------------------------
    def _read_identifier(self) -> None:
        start_line = self.line
        start = self.pos
        while self.pos < self.length and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()
        value = self.src[start:self.pos]
        lower = value.lower()

        if lower == "true" and value[0] == "t":
            self._add("BOOL_CONST", "true", start_line)
        elif lower == "false" and value[0] == "f":
            self._add("BOOL_CONST", "false", start_line)
        elif lower in KEYWORDS:
            self._add(KEYWORDS[lower], None, start_line)
        elif value[0].isupper():
            self._add("TYPEID", value, start_line)
        else:
            self._add("OBJECTID", value, start_line)

    # -- símbolos -----------------------------------------------------
    def _read_symbol(self) -> bool:
        two = self._peek() + self._peek(1)
        if two in TWO_CHAR_SYMBOLS:
            start_line = self.line
            self._advance()
            self._advance()
            self._add(TWO_CHAR_SYMBOLS[two], None, start_line)
            return True

        one = self._peek()
        if one in SYMBOLS:
            start_line = self.line
            self._advance()
            self._add(SYMBOLS[one], None, start_line)
            return True

        return False


def tokenize(source: str) -> List[Token]:
    """Função de conveniência: recebe o código-fonte e devolve a lista de tokens."""
    return Lexer(source).tokenize()
