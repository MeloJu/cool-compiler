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
        self.assertIn("Erro semantico:", output.getvalue())
