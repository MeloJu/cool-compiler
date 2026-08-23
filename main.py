#!/usr/bin/env python3
"""
CLI do analisador léxico de COOL.

Uso:
    python main.py caminho/arquivo.cl
"""
import sys

from lexer import tokenize


def main() -> None:
    if len(sys.argv) != 2:
        print("uso: python main.py <arquivo.cl>")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    for token in tokenize(source):
        print(token)


if __name__ == "__main__":
    main()
