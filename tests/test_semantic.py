import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ast_nodes import ProgramNode
from parser import parse
from semantic import SemanticResult, analyze, builtin_class_table


class TestSemanticBase(unittest.TestCase):
    def test_analisa_programa_sintaticamente_valido(self):
        program = parse("class Main { main() : Object { self }; };")

        result = analyze(program)

        self.assertIsInstance(result, SemanticResult)
        self.assertTrue(result.success)
        self.assertEqual(result.errors, [])

    def test_rejeita_objeto_que_nao_e_ast_de_programa(self):
        with self.assertRaisesRegex(TypeError, "ProgramNode"):
            analyze(ProgramNode)  # type: ignore[arg-type]

    def test_tabela_contem_classes_nativas(self):
        table = builtin_class_table()

        self.assertEqual(set(table), {"Object", "IO", "Int", "Bool", "String"})
        self.assertIsNone(table["Object"].parent)
        self.assertEqual(table["String"].parent, "Object")

    def test_tabela_contem_assinaturas_dos_metodos_nativos(self):
        result = analyze(parse("class Main { };"))

        self.assertEqual(
            result.class_table["IO"].methods["out_int"].parameter_types,
            ("Int",),
        )
        self.assertEqual(
            result.class_table["String"].methods["length"].return_type,
            "Int",
        )

    def test_registra_classes_do_programa_na_tabela(self):
        result = analyze(parse("class A { }; class Main inherits A { };"))

        self.assertTrue(result.success)
        self.assertEqual(result.class_table["A"].parent, "Object")
        self.assertEqual(result.class_table["Main"].parent, "A")

    def test_rejeita_redefinicao_de_classe_nativa(self):
        result = analyze(parse("class Object { };"))

        self.assertFalse(result.success)
        self.assertIn("Classe 'Object' foi definida mais de uma vez", result.errors[0].message)

    def test_rejeita_classes_com_mesmo_nome(self):
        result = analyze(parse("class A { }; class A { };"))

        self.assertFalse(result.success)
        self.assertIn("Classe 'A' foi definida mais de uma vez", result.errors[0].message)

    def test_rejeita_classe_pai_inexistente(self):
        result = analyze(parse("class Main inherits Desconhecida { };"))

        self.assertFalse(result.success)
        self.assertIn("herda de classe inexistente 'Desconhecida'", result.errors[0].message)

    def test_rejeita_heranca_de_tipo_basico(self):
        result = analyze(parse("class Main inherits Int { };"))

        self.assertFalse(result.success)
        self.assertIn("nao pode herdar de 'Int'", result.errors[0].message)

    def test_rejeita_ciclo_de_heranca(self):
        result = analyze(parse("class A inherits B { }; class B inherits A { };"))

        self.assertFalse(result.success)
        self.assertTrue(any("Ciclo de heranca" in error.message for error in result.errors))


if __name__ == "__main__":
    unittest.main()
