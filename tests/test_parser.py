import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ast_nodes import (
    AssignNode,
    AttributeNode,
    BinaryOpNode,
    ClassNode,
    FormalNode,
    LiteralNode,
    MethodNode,
    ProgramNode,
    UnaryOpNode,
    VariableNode,
)
from parser import parse


class TestParserInicial(unittest.TestCase):
    def test_classe_vazia(self):
        ast = parse("class Main {\n};")
        self.assertEqual(ast, ProgramNode(classes=[ClassNode(name="Main", parent="Object")]))

    def test_classe_com_heranca(self):
        ast = parse("class Main inherits IO {\n};")
        self.assertEqual(ast, ProgramNode(classes=[ClassNode(name="Main", parent="IO")]))

    def test_varias_classes(self):
        source = """
        class A {
        };

        class B inherits A {
        };
        """
        ast = parse(source)
        self.assertEqual(
            ast,
            ProgramNode(
                classes=[
                    ClassNode(name="A", parent="Object"),
                    ClassNode(name="B", parent="A"),
                ]
            ),
        )

    def test_atributo_simples(self):
        ast = parse("class Main { x : Int; };")
        self.assertEqual(
            ast,
            ProgramNode(
                classes=[
                    ClassNode(
                        name="Main",
                        parent="Object",
                        features=[AttributeNode(name="x", type_name="Int")],
                    )
                ]
            ),
        )

    def test_atributo_com_inicializacao(self):
        ast = parse("class Main { msg : String <- \"oi\"; };")
        self.assertEqual(
            ast.classes[0].features[0],
            AttributeNode(
                name="msg",
                type_name="String",
                init=LiteralNode(value="oi", type_name="String"),
            ),
        )

    def test_metodo_sem_parametros(self):
        ast = parse("class Main { main() : Object { self }; };")
        self.assertEqual(
            ast.classes[0].features[0],
            MethodNode(
                name="main",
                params=[],
                return_type="Object",
                body=VariableNode(name="self"),
            ),
        )

    def test_metodo_com_parametros(self):
        ast = parse("class Main { soma(a : Int, b : Int) : Int { a }; };")
        self.assertEqual(
            ast.classes[0].features[0],
            MethodNode(
                name="soma",
                params=[
                    FormalNode(name="a", type_name="Int"),
                    FormalNode(name="b", type_name="Int"),
                ],
                return_type="Int",
                body=VariableNode(name="a"),
            ),
        )

    def test_precedencia_multiplicacao_antes_de_soma(self):
        ast = parse("class Main { calc() : Int { 1 + 2 * 3 }; };")
        self.assertEqual(
            ast.classes[0].features[0].body,
            BinaryOpNode(
                operator="+",
                left=LiteralNode(value=1, type_name="Int"),
                right=BinaryOpNode(
                    operator="*",
                    left=LiteralNode(value=2, type_name="Int"),
                    right=LiteralNode(value=3, type_name="Int"),
                ),
            ),
        )

    def test_parenteses_alteram_precedencia(self):
        ast = parse("class Main { calc() : Int { (1 + 2) * 3 }; };")
        self.assertEqual(
            ast.classes[0].features[0].body,
            BinaryOpNode(
                operator="*",
                left=BinaryOpNode(
                    operator="+",
                    left=LiteralNode(value=1, type_name="Int"),
                    right=LiteralNode(value=2, type_name="Int"),
                ),
                right=LiteralNode(value=3, type_name="Int"),
            ),
        )

    def test_comparacao(self):
        ast = parse("class Main { menor() : Bool { 1 <= 2 }; };")
        self.assertEqual(
            ast.classes[0].features[0].body,
            BinaryOpNode(
                operator="<=",
                left=LiteralNode(value=1, type_name="Int"),
                right=LiteralNode(value=2, type_name="Int"),
            ),
        )

    def test_atribuicao(self):
        ast = parse("class Main { set() : Int { x <- 1 + 2 }; };")
        self.assertEqual(
            ast.classes[0].features[0].body,
            AssignNode(
                name="x",
                value=BinaryOpNode(
                    operator="+",
                    left=LiteralNode(value=1, type_name="Int"),
                    right=LiteralNode(value=2, type_name="Int"),
                ),
            ),
        )

    def test_operadores_unarios(self):
        ast = parse("class Main { teste() : Bool { not isvoid ~x }; };")
        self.assertEqual(
            ast.classes[0].features[0].body,
            UnaryOpNode(
                operator="not",
                operand=UnaryOpNode(
                    operator="isvoid",
                    operand=UnaryOpNode(
                        operator="~",
                        operand=VariableNode(name="x"),
                    ),
                ),
            ),
        )

    def test_rejeita_ponto_virgula_faltando(self):
        with self.assertRaises(SyntaxError):
            parse("class Main {\n}")

    def test_rejeita_erro_lexico(self):
        with self.assertRaises(SyntaxError):
            parse("class Main { $ };")


if __name__ == "__main__":
    unittest.main()
