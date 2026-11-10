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
                "__cool_out_string",
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

        self.assertIn("not", operations)

        string_program = parse('class Main { main() : Object { "oi" }; };')
        string_bril = generate_bril(string_program)
        string_operations = [
            instruction.get("op") for instruction in string_bril["functions"][-1]["instrs"]
        ]
        self.assertIn("alloc", string_operations)
        self.assertIn("store", string_operations)

    def test_gera_if_com_desvio_e_resultado(self):
        program = parse(
            "class Main { main() : Object { if true then 1 else 2 fi }; };"
        )

        bril = generate_bril(program)
        instructions = bril["functions"][-1]["instrs"]

        self.assertIn("br", [instruction.get("op") for instruction in instructions])
        self.assertIn("jmp", [instruction.get("op") for instruction in instructions])
        self.assertTrue(any(instruction.get("label", "").startswith("if_then") for instruction in instructions))

    def test_gera_let_bloco_atribuicao_e_while(self):
        program = parse(
            "class Main { main() : Object { let x : Int <- 1 in { "
            "x <- x + 2; while false loop 0 pool; x; } }; };"
        )

        bril = generate_bril(program)
        instructions = bril["functions"][-1]["instrs"]
        operations = [instruction.get("op") for instruction in instructions]

        self.assertIn("add", operations)
        self.assertIn("id", operations)
        self.assertIn("br", operations)
        self.assertTrue(
            any(
                instruction.get("label", "").startswith("while_condition")
                for instruction in instructions
            )
        )

    def test_gera_metodo_com_parametro_como_funcao_bril(self):
        program = parse(
            "class Main { dobro(x : Int) : Int { x + x }; "
            "main() : Object { 0 }; };"
        )

        bril = generate_bril(program)
        method = next(function for function in bril["functions"] if function["name"] == "Main__dobro")

        self.assertEqual(method["args"][0]["type"], {"ptr": "int"})
        self.assertEqual(method["args"][1]["type"], "int")
        self.assertEqual(method["type"], "int")
        self.assertIn("add", [instruction.get("op") for instruction in method["instrs"]])
        self.assertEqual(method["instrs"][-1]["op"], "ret")

    def test_gera_objeto_com_tag_e_atributos_na_memoria(self):
        program = parse(
            "class Point { x : Int <- 1; ativo : Bool; "
            "valor() : Int { x }; }; "
            "class Main { main() : Object { new Point }; };"
        )

        bril = generate_bril(program)
        main = bril["functions"][-1]
        method = next(function for function in bril["functions"] if function["name"] == "Point__valor")

        self.assertIn("alloc", [instruction.get("op") for instruction in main["instrs"]])
        self.assertIn("store", [instruction.get("op") for instruction in main["instrs"]])
        self.assertIn("load", [instruction.get("op") for instruction in method["instrs"]])

    def test_gera_despacho_dinamico_para_metodo_sobrescrito(self):
        program = parse(
            "class A { valor() : Int { 1 }; }; "
            "class B inherits A { valor() : Int { 2 }; }; "
            "class Main { main() : Object { let item : A <- new B in item.valor() }; };"
        )

        bril = generate_bril(program)
        main = bril["functions"][-1]
        calls = [instruction for instruction in main["instrs"] if instruction.get("op") == "call"]

        self.assertTrue(any(call["funcs"] == ["A__valor"] for call in calls))
        self.assertTrue(any(call["funcs"] == ["B__valor"] for call in calls))

    def test_gera_despacho_estatico_para_classe_indicada(self):
        program = parse(
            "class A { valor() : Int { 1 }; }; "
            "class B inherits A { valor() : Int { 2 }; }; "
            "class Main { main() : Object { (new B)@A.valor() }; };"
        )

        bril = generate_bril(program)
        main = bril["functions"][-1]
        calls = [instruction for instruction in main["instrs"] if instruction.get("op") == "call"]

        self.assertEqual(calls[-1]["funcs"], ["A__valor"])

    def test_conecta_chamadas_de_string_e_io_ao_runtime(self):
        program = parse(
            'class Main inherits IO { main() : Object { out_string("oi".concat("!")) }; };'
        )

        bril = generate_bril(program)
        main = bril["functions"][-1]
        calls = [instruction for instruction in main["instrs"] if instruction.get("op") == "call"]

        self.assertTrue(any(call["funcs"] == ["__cool_string_concat"] for call in calls))
        self.assertTrue(any(call["funcs"] == ["__cool_out_string"] for call in calls))
        self.assertIn("__cool_out_string", [function["name"] for function in bril["functions"]])

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
