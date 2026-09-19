#!/usr/bin/env python3
"""
CLI dos analisadores de COOL.

Uso:
    python main.py lex caminho/arquivo.cl
    python main.py parse caminho/arquivo.cl
"""
import sys

from lexer import tokenize
from parser import parse


def _read_source(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _print_usage() -> None:
    print("uso: python main.py <lex|parse> <arquivo.cl>")


def main() -> None:
    if len(sys.argv) != 3:
        _print_usage()
        sys.exit(1)

    mode = sys.argv[1]
    path = sys.argv[2]
    source = _read_source(path)

    if mode == "lex":
        for token in tokenize(source):
            print(token)
    elif mode == "parse":
        try:
            parse(source)
        except SyntaxError as exc:
            print(exc)
            sys.exit(1)
        print("Analise sintatica concluida com sucesso.")
    else:
        _print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
