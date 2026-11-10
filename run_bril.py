"""Executa um programa Bril JSON usando o interpretador brilirs instalado."""

import shutil
import subprocess
import sys
from pathlib import Path


def run_bril_file(path: str) -> int:
    """Envia um arquivo ``.bril.json`` para o brilirs e devolve seu codigo final."""
    interpreter = shutil.which("brilirs")
    if interpreter is None:
        print(
            "Nao foi encontrado o comando 'brilirs'. "
            "Instale o interpretador Bril e tente novamente.",
            file=sys.stderr,
        )
        return 1

    program_path = Path(path)
    if not program_path.is_file():
        print(f"Arquivo Bril nao encontrado: {path}", file=sys.stderr)
        return 1

    result = subprocess.run(
        [interpreter],
        input=program_path.read_text(encoding="utf-8"),
        text=True,
        check=False,
    )
    return result.returncode


def main() -> None:
    if len(sys.argv) != 2:
        print("uso: python run_bril.py <programa.bril.json>")
        sys.exit(1)
    sys.exit(run_bril_file(sys.argv[1]))


if __name__ == "__main__":
    main()
