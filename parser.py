import ply.yacc as yacc

from ast_nodes import (
    AttributeNode,
    ClassNode,
    FormalNode,
    LiteralNode,
    MethodNode,
    ProgramNode,
    VariableNode,
)
from lexer import build_lexer, tokens


def p_program(p):
    """program : class_list"""
    p[0] = ProgramNode(classes=p[1])


def p_class_list_single(p):
    """class_list : class_decl"""
    p[0] = [p[1]]


def p_class_list_many(p):
    """class_list : class_list class_decl"""
    p[0] = p[1] + [p[2]]


def p_class_decl(p):
    """class_decl : CLASS TYPEID '{' feature_list '}' ';'"""
    p[0] = ClassNode(name=p[2], features=p[4])


def p_class_decl_inherits(p):
    """class_decl : CLASS TYPEID INHERITS TYPEID '{' feature_list '}' ';'"""
    p[0] = ClassNode(name=p[2], parent=p[4], features=p[6])


def p_feature_list_empty(p):
    """feature_list : empty"""
    p[0] = []


def p_feature_list_many(p):
    """feature_list : feature_list feature"""
    p[0] = p[1] + [p[2]]


def p_feature_attribute(p):
    """feature : OBJECTID ':' TYPEID ';'"""
    p[0] = AttributeNode(name=p[1], type_name=p[3])


def p_feature_attribute_init(p):
    """feature : OBJECTID ':' TYPEID ASSIGN expr ';'"""
    p[0] = AttributeNode(name=p[1], type_name=p[3], init=p[5])


def p_feature_method(p):
    """feature : OBJECTID '(' formal_list ')' ':' TYPEID '{' expr '}' ';'"""
    p[0] = MethodNode(name=p[1], params=p[3], return_type=p[6], body=p[8])


def p_formal_list_empty(p):
    """formal_list : empty"""
    p[0] = []


def p_formal_list_single(p):
    """formal_list : formal"""
    p[0] = [p[1]]


def p_formal_list_many(p):
    """formal_list : formal_list ',' formal"""
    p[0] = p[1] + [p[3]]


def p_formal(p):
    """formal : OBJECTID ':' TYPEID"""
    p[0] = FormalNode(name=p[1], type_name=p[3])


def p_expr_int(p):
    """expr : INT_CONST"""
    p[0] = LiteralNode(value=int(p[1]), type_name="Int")


def p_expr_string(p):
    """expr : STR_CONST"""
    p[0] = LiteralNode(value=p[1], type_name="String")


def p_expr_bool(p):
    """expr : BOOL_CONST"""
    p[0] = LiteralNode(value=p[1] == "true", type_name="Bool")


def p_expr_variable(p):
    """expr : OBJECTID"""
    p[0] = VariableNode(name=p[1])


def p_empty(p):
    """empty :"""
    p[0] = None


def p_error(p):
    if p is None:
        raise SyntaxError("Erro sintatico: fim de arquivo inesperado")
    if p.type == "ERROR":
        raise SyntaxError(f"Erro lexico na linha {p.lineno}: {p.value}")
    raise SyntaxError(
        f"Erro sintatico na linha {p.lineno}: token inesperado {p.type} ({p.value!r})"
    )


_parser = yacc.yacc(
    start="program",
    debug=False,
    write_tables=False,
    errorlog=yacc.NullLogger(),
)


def parse(source: str) -> ProgramNode:
    """Recebe codigo-fonte COOL e devolve a arvore sintatica inicial."""
    lexer = build_lexer(source)
    return _parser.parse(lexer=lexer)
