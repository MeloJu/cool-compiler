import io
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main


class TestCli(unittest.TestCase):
    def test_modo_semantic_confirma_programa_valido(self):
        source = "class Main { main() : Object { self }; };"

        with (
            patch.object(sys, "argv", ["main.py", "semantic", "programa.cl"]),
            patch("main._read_source", return_value=source),
            patch("sys.stdout", new_callable=io.StringIO) as output,
        ):
            main.main()

        self.assertEqual(output.getvalue().strip(), "Analise semantica concluida com sucesso.")

    def test_modo_semantic_exibe_erros_e_retorna_falha(self):
        source = "class Main { main() : Int { true }; };"

        with (
            patch.object(sys, "argv", ["main.py", "semantic", "programa.cl"]),
            patch("main._read_source", return_value=source),
            patch("sys.stdout", new_callable=io.StringIO) as output,
            self.assertRaises(SystemExit) as exit_error,
        ):
            main.main()

        self.assertEqual(exit_error.exception.code, 1)
        self.assertIn("Erro semantico na linha 1:", output.getvalue())

    def test_modo_codegen_emite_programa_bril(self):
        source = "class Main { main() : Object { 1 + 2 }; };"

        with (
            patch.object(sys, "argv", ["main.py", "codegen", "programa.cl"]),
            patch("main._read_source", return_value=source),
            patch("sys.stdout", new_callable=io.StringIO) as output,
        ):
            main.main()

        self.assertIn('"name": "main"', output.getvalue())

    def test_modo_codegen_informa_recurso_ainda_nao_implementado(self):
        source = "class Main { main() : Object { new Object }; };"

        with (
            patch.object(sys, "argv", ["main.py", "codegen", "programa.cl"]),
            patch("main._read_source", return_value=source),
            patch("sys.stdout", new_callable=io.StringIO) as output,
            self.assertRaises(SystemExit) as exit_error,
        ):
            main.main()

        self.assertEqual(exit_error.exception.code, 1)
        self.assertIn("Erro na geracao de codigo:", output.getvalue())

    def test_modo_codegen_grava_arquivo_bril_json(self):
        source = "class Main { main() : Object { 1 + 2 }; };"
        output_path = "programa.bril.json"
        with (
            patch.object(sys, "argv", ["main.py", "codegen", "programa.cl", output_path]),
            patch("main._read_source", return_value=source),
            patch("main.Path.write_text") as write_text,
            patch("sys.stdout", new_callable=io.StringIO) as output,
        ):
            main.main()

        self.assertIn('"name": "main"', write_text.call_args.args[0])
        self.assertIn("Codigo Bril gerado em:", output.getvalue())
