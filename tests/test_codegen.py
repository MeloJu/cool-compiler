import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ast_nodes import ProgramNode
from codegen import BrilGenerator, generate_bril
from parser import parse


class TestCodegenBase(unittest.TestCase):
    def test_gera_programa_bril_com_funcao_main(self):
        program = parse("class Main { main() : Object { 1 + 2 }; };")

        bril = generate_bril(program)

        self.assertEqual(
            [function["name"] for function in bril["functions"]],
            [
                "__cool_string_length",
                "__cool_string_concat",
                "__cool_string_substr",
                "main",
            ],
        )
        self.assertEqual(bril["functions"][-1]["name"], "main")
        self.assertIn(
            "add", [instruction.get("op") for instruction in bril["functions"][-1]["instrs"]]
        )

    def test_runtime_de_string_usa_memoria_e_terminador_zero(self):
        program = parse("class Main { main() : Object { 0 }; };")

        bril = generate_bril(program)
        runtime = bril["functions"][:3]
        instructions = [instruction for function in runtime for instruction in function["instrs"]]

        self.assertTrue(any(instruction.get("op") == "alloc" for instruction in instructions))
        self.assertTrue(any(instruction.get("op") == "load" for instruction in instructions))
        self.assertTrue(any(instruction.get("op") == "store" for instruction in instructions))
        self.assertTrue(
            any(
                instruction.get("op") == "const" and instruction.get("value") == 0
                for instruction in instructions
            )
        )

    def test_gera_string_e_operadores_basicos(self):
        program = parse('class Main { main() : Object { not false }; };')

        bril = generate_bril(program)
        operations = [instruction.get("op") for instruction in bril["functions"][-1]["instrs"]]

        self.assertEqual(operations, ["const", "not"])

        string_program = parse('class Main { main() : Object { "oi" }; };')
        string_bril = generate_bril(string_program)
        string_operations = [
            instruction.get("op") for instruction in string_bril["functions"][-1]["instrs"]
        ]
        self.assertIn("alloc", string_operations)
        self.assertIn("store", string_operations)

    def test_gera_nomes_temporarios_unicos(self):
        generator = BrilGenerator()

        self.assertEqual(generator.new_temporary(), "tmp0")
        self.assertEqual(generator.new_temporary(), "tmp1")

    def test_gera_labels_unicos(self):
        generator = BrilGenerator()

        self.assertEqual(generator.new_label("if_then"), "if_then_0")
        self.assertEqual(generator.new_label("if_else"), "if_else_1")

    def test_rejeita_objeto_que_nao_e_ast_de_programa(self):
        with self.assertRaisesRegex(TypeError, "ProgramNode"):
            generate_bril(ProgramNode)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
