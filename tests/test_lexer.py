import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lexer import tokenize


def types(source):
    return [t.type for t in tokenize(source)]


class TestPalavrasChaveEIdentificadores(unittest.TestCase):
    def test_palavras_chave(self):
        self.assertEqual(
            types("class else fi if in inherits isvoid let loop pool then while case esac new of not"),
            [
                "CLASS", "ELSE", "FI", "IF", "IN", "INHERITS", "ISVOID", "LET",
                "LOOP", "POOL", "THEN", "WHILE", "CASE", "ESAC", "NEW", "OF", "NOT",
            ],
        )

    def test_palavras_chave_case_insensitive(self):
        self.assertEqual(types("Class WHILE If"), ["CLASS", "WHILE", "IF"])

    def test_typeid_e_objectid(self):
        toks = tokenize("Main io_out x2")
        self.assertEqual([(t.type, t.value) for t in toks],
                          [("TYPEID", "Main"), ("OBJECTID", "io_out"), ("OBJECTID", "x2")])

    def test_booleanos(self):
        toks = tokenize("true false")
        self.assertEqual([(t.type, t.value) for t in toks],
                          [("BOOL_CONST", "true"), ("BOOL_CONST", "false")])

    def test_booleano_com_maiuscula_nao_conta_como_bool(self):
        # primeira letra maiúscula -> não é BOOL_CONST, vira TYPEID
        toks = tokenize("True False")
        self.assertEqual([t.type for t in toks], ["TYPEID", "TYPEID"])


class TestNumerosEStrings(unittest.TestCase):
    def test_inteiro(self):
        toks = tokenize("42")
        self.assertEqual((toks[0].type, toks[0].value), ("INT_CONST", "42"))

    def test_string_simples(self):
        toks = tokenize('"ola mundo"')
        self.assertEqual((toks[0].type, toks[0].value), ("STR_CONST", "ola mundo"))

    def test_string_com_escapes(self):
        toks = tokenize(r'"linha1\nlinha2\ttab"')
        self.assertEqual(toks[0].value, "linha1\\nlinha2\\ttab")

    def test_string_nao_terminada(self):
        toks = tokenize('"abc\n')
        self.assertEqual(toks[0].type, "ERROR")
        self.assertIn("Unterminated string", toks[0].value)

    def test_string_com_null(self):
        toks = tokenize('"a\0b"')
        self.assertEqual(toks[0].type, "ERROR")
        self.assertIn("null character", toks[0].value)

    def test_string_muito_longa(self):
        toks = tokenize('"' + ("a" * 1030) + '"')
        self.assertEqual(toks[0].type, "ERROR")
        self.assertIn("too long", toks[0].value)


class TestComentarios(unittest.TestCase):
    def test_comentario_de_linha_ignorado(self):
        self.assertEqual(types("class -- isso eh comentario\nMain"), ["CLASS", "TYPEID"])

    def test_comentario_de_bloco_ignorado(self):
        self.assertEqual(types("class (* bloco *) Main"), ["CLASS", "TYPEID"])

    def test_comentario_de_bloco_aninhado(self):
        self.assertEqual(types("class (* fora (* dentro *) ainda fora *) Main"), ["CLASS", "TYPEID"])

    def test_comentario_nao_fechado(self):
        toks = tokenize("class (* nunca fecha")
        self.assertEqual(toks[-1].type, "ERROR")
        self.assertIn("EOF in comment", toks[-1].value)

    def test_fechamento_sem_abertura(self):
        toks = tokenize("*)")
        self.assertEqual(toks[0].type, "ERROR")


class TestSimbolos(unittest.TestCase):
    def test_operadores_um_e_dois_caracteres(self):
        self.assertEqual(
            types("<- <= => { } ( ) : ; , . @ ~ * / + - <"),
            [
                "ASSIGN", "LE", "DARROW", "'{'", "'}'", "'('", "')'", "':'",
                "';'", "','", "'.'", "'@'", "'~'", "'*'", "'/'", "'+'", "'-'", "'<'",
            ],
        )

    def test_contagem_de_linhas(self):
        toks = tokenize("class\nMain")
        self.assertEqual(toks[0].line, 1)
        self.assertEqual(toks[1].line, 2)


class TestErros(unittest.TestCase):
    def test_caractere_desconhecido(self):
        toks = tokenize("a $ b")
        self.assertEqual([t.type for t in toks], ["OBJECTID", "ERROR", "OBJECTID"])
        self.assertEqual(toks[1].value, "$")


if __name__ == "__main__":
    unittest.main()
