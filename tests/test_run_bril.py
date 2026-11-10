import io
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import run_bril


class TestRunBril(unittest.TestCase):
    def test_informa_quando_o_interpretador_nao_esta_instalado(self):
        with (
            patch("run_bril.shutil.which", return_value=None),
            patch("sys.stderr", new_callable=io.StringIO) as error_output,
        ):
            result = run_bril.run_bril_file("programa.bril.json")

        self.assertEqual(result, 1)
        self.assertIn("brilirs", error_output.getvalue())

    def test_envia_json_para_o_interpretador(self):
        completed_process = type("Process", (), {"returncode": 0})()
        with (
            patch("run_bril.shutil.which", return_value="brilirs"),
            patch("run_bril.Path.is_file", return_value=True),
            patch(
                "run_bril.Path.read_text",
                return_value='{"functions": [{"name": "main", "instrs": []}]}',
            ),
            patch("run_bril.subprocess.run", return_value=completed_process) as run,
        ):
            result = run_bril.run_bril_file("programa.bril.json")

        self.assertEqual(result, 0)
        self.assertEqual(run.call_args.args[0], ["brilirs"])
        self.assertIn('"functions"', run.call_args.kwargs["input"])
