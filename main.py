#!/usr/bin/env python3
"""
CLI dos analisadores de COOL.

Uso:
    python main.py lex caminho/arquivo.cl
    python main.py parse caminho/arquivo.cl
    python main.py semantic caminho/arquivo.cl
    python main.py codegen caminho/arquivo.cl [saida.bril.json]
"""
import json
import sys
from pathlib import Path

from codegen import CodeGenerationError, generate_bril
from lexer import tokenize
from parser import parse
from semantic import analyze


def _read_source(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _print_usage() -> None:
    print("uso: python main.py <lex|parse|semantic|codegen> <arquivo.cl> [saida.bril.json]")


def main() -> None:
    if len(sys.argv) not in {3, 4}:
        _print_usage()
        sys.exit(1)

    mode = sys.argv[1]
    path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) == 4 else None
    if output_path is not None and mode != "codegen":
        _print_usage()
        sys.exit(1)
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
    elif mode == "semantic":
        try:
            program = parse(source)
        except SyntaxError as exc:
            print(exc)
            sys.exit(1)

        result = analyze(program)
        if not result.success:
            for error in result.errors:
                location = (
                    f" na linha {error.line}" if error.line is not None else ""
                )
                print(f"Erro semantico{location}: {error.message}")
            sys.exit(1)
        print("Analise semantica concluida com sucesso.")
    elif mode == "codegen":
        try:
            program = parse(source)
        except SyntaxError as exc:
            print(exc)
            sys.exit(1)

        result = analyze(program)
        if not result.success:
            for error in result.errors:
                location = (
                    f" na linha {error.line}" if error.line is not None else ""
                )
                print(f"Erro semantico{location}: {error.message}")
            sys.exit(1)

        try:
            bril_json = json.dumps(generate_bril(program), indent=2)
        except CodeGenerationError as exc:
            print(f"Erro na geracao de codigo: {exc}")
            sys.exit(1)
        if output_path is None:
            print(bril_json)
        else:
            Path(output_path).write_text(bril_json + "\n", encoding="utf-8")
            print(f"Codigo Bril gerado em: {output_path}")
    else:
        _print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
