import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ast_nodes import ProgramNode
from parser import parse
from semantic import (
    Scope,
    SemanticResult,
    analyze,
    builtin_class_table,
    conforms,
    least_upper_bound,
)


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

    def test_escopo_consulta_pai_quando_nome_nao_e_local(self):
        outer_scope = Scope(symbols={"x": "Int"})
        inner_scope = Scope(parent=outer_scope, symbols={"y": "String"})

        self.assertEqual(inner_scope.lookup("x"), "Int")
        self.assertEqual(inner_scope.lookup("y"), "String")
        self.assertIsNone(inner_scope.lookup("z"))

    def test_registra_atributos_e_metodos_da_classe(self):
        result = analyze(
            parse("class Main { valor : Int; dobro(x : Int) : Int { x + x }; };")
        )

        self.assertTrue(result.success)
        self.assertEqual(result.class_table["Main"].attributes["valor"].type_name, "Int")
        self.assertEqual(
            result.class_table["Main"].methods["dobro"].parameter_types,
            ("Int",),
        )

    def test_rejeita_tipo_de_atributo_inexistente(self):
        result = analyze(parse("class Main { valor : Ausente; };"))

        self.assertFalse(result.success)
        self.assertIn("tipo inexistente 'Ausente'", result.errors[0].message)

    def test_rejeita_atributo_com_nome_self(self):
        result = analyze(parse("class Main { self : Int; };"))

        self.assertFalse(result.success)
        self.assertIn("atributo nao pode receber o nome 'self'", result.errors[0].message)

    def test_rejeita_parametro_duplicado(self):
        result = analyze(parse("class Main { f(x : Int, x : Int) : Int { x }; };"))

        self.assertFalse(result.success)
        self.assertIn("parametro duplicado 'x'", result.errors[0].message)

    def test_rejeita_atributo_que_redefine_atributo_herdado(self):
        result = analyze(parse("class A { x : Int; }; class B inherits A { x : Int; };"))

        self.assertFalse(result.success)
        self.assertTrue(any("redefine um atributo herdado" in error.message for error in result.errors))

    def test_rejeita_sobrescrita_de_metodo_com_assinatura_diferente(self):
        source = """
        class A { f(x : Int) : Int { x }; };
        class B inherits A { f(x : String) : Int { 0 }; };
        """
        result = analyze(parse(source))

        self.assertFalse(result.success)
        self.assertTrue(
            any("assinatura diferente da versao herdada" in error.message for error in result.errors)
        )

    def test_conformidade_entre_classes_da_hierarquia(self):
        result = analyze(parse("class A { }; class B inherits A { };"))

        self.assertTrue(conforms("B", "A", "B", result.class_table))
        self.assertTrue(conforms("B", "Object", "B", result.class_table))
        self.assertFalse(conforms("A", "B", "A", result.class_table))

    def test_conformidade_com_self_type(self):
        result = analyze(parse("class Main { };"))

        self.assertTrue(conforms("SELF_TYPE", "SELF_TYPE", "Main", result.class_table))
        self.assertTrue(conforms("SELF_TYPE", "Object", "Main", result.class_table))
        self.assertFalse(conforms("Object", "SELF_TYPE", "Main", result.class_table))

    def test_uniao_de_tipos_irmaos(self):
        result = analyze(
            parse("class A { }; class B inherits A { }; class C inherits A { };")
        )

        self.assertEqual(least_upper_bound("B", "C", "B", result.class_table), "A")
        self.assertEqual(least_upper_bound("Int", "Bool", "B", result.class_table), "Object")

    def test_uniao_preserva_self_type_quando_ambos_sao_self_type(self):
        result = analyze(parse("class Main { };"))

        self.assertEqual(
            least_upper_bound("SELF_TYPE", "SELF_TYPE", "Main", result.class_table),
            "SELF_TYPE",
        )

    def test_infere_tipos_de_literais_e_operadores(self):
        program = parse("class Main { soma() : Int { 1 + 2 * 3 }; };")
        expression = program.classes[0].features[0].body

        result = analyze(program)

        self.assertTrue(result.success)
        self.assertEqual(result.expression_types[id(expression)], "Int")

    def test_rejeita_operacao_aritmetica_com_tipo_incorreto(self):
        result = analyze(parse("class Main { soma() : Int { true + 1 }; };"))

        self.assertFalse(result.success)
        self.assertTrue(any("exige dois operandos Int" in error.message for error in result.errors))

    def test_rejeita_identificador_nao_declarado(self):
        result = analyze(parse("class Main { f() : Object { ausente }; };"))

        self.assertFalse(result.success)
        self.assertIn("Identificador 'ausente' nao foi declarado", result.errors[0].message)

    def test_rejeita_atribuicao_com_tipo_incompativel(self):
        source = "class Main { valor : Int; define() : Bool { valor <- true }; };"
        result = analyze(parse(source))

        self.assertFalse(result.success)
        self.assertTrue(any("espera 'Int', mas recebeu 'Bool'" in error.message for error in result.errors))

    def test_rejeita_retorno_de_metodo_incompativel(self):
        result = analyze(parse("class Main { f() : Int { true }; };"))

        self.assertFalse(result.success)
        self.assertTrue(any("declara retorno 'Int'" in error.message for error in result.errors))


if __name__ == "__main__":
    unittest.main()
