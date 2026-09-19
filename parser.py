import ply.yacc as yacc

from ast_nodes import (
    AssignNode,
    AttributeNode,
    BinaryOpNode,
    BlockNode,
    CaseBranchNode,
    CaseNode,
    ClassNode,
    FormalNode,
    IfNode,
    LetBindingNode,
    LetNode,
    LiteralNode,
    MethodCallNode,
    MethodNode,
    NewNode,
    ProgramNode,
    UnaryOpNode,
    VariableNode,
    WhileNode,
)
from lexer import build_lexer, tokens


precedence = (
    ("right", "ASSIGN"),
    ("right", "NOT"),
    ("nonassoc", "<", "LE", "="),
    ("left", "+", "-"),
    ("left", "*", "/"),
    ("right", "ISVOID"),
    ("right", "UNARY_NEG"),
    ("left", "DISPATCH"),
)


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


def p_expr_assign(p):
    """expr : OBJECTID ASSIGN expr"""
    p[0] = AssignNode(name=p[1], value=p[3])


def p_expr_binary(p):
    """expr : expr '+' expr
            | expr '-' expr
            | expr '*' expr
            | expr '/' expr
            | expr '<' expr
            | expr LE expr
            | expr '=' expr"""
    p[0] = BinaryOpNode(operator=p[2], left=p[1], right=p[3])


def p_expr_not(p):
    """expr : NOT expr"""
    p[0] = UnaryOpNode(operator="not", operand=p[2])


def p_expr_isvoid(p):
    """expr : ISVOID expr"""
    p[0] = UnaryOpNode(operator="isvoid", operand=p[2])


def p_expr_unary_neg(p):
    """expr : '~' expr %prec UNARY_NEG"""
    p[0] = UnaryOpNode(operator="~", operand=p[2])


def p_expr_group(p):
    """expr : '(' expr ')'"""
    p[0] = p[2]


def p_expr_if(p):
    """expr : IF expr THEN expr ELSE expr FI"""
    p[0] = IfNode(condition=p[2], then_expr=p[4], else_expr=p[6])


def p_expr_while(p):
    """expr : WHILE expr LOOP expr POOL"""
    p[0] = WhileNode(condition=p[2], body=p[4])


def p_expr_case(p):
    """expr : CASE expr OF case_branch_list ESAC"""
    p[0] = CaseNode(expression=p[2], branches=p[4])


def p_case_branch_list_single(p):
    """case_branch_list : case_branch"""
    p[0] = [p[1]]


def p_case_branch_list_many(p):
    """case_branch_list : case_branch_list case_branch"""
    p[0] = p[1] + [p[2]]


def p_case_branch(p):
    """case_branch : OBJECTID ':' TYPEID DARROW expr ';'"""
    p[0] = CaseBranchNode(name=p[1], type_name=p[3], body=p[5])


def p_expr_block(p):
    """expr : '{' block_expr_list '}'"""
    p[0] = BlockNode(expressions=p[2])


def p_block_expr_list_single(p):
    """block_expr_list : expr ';'"""
    p[0] = [p[1]]


def p_block_expr_list_many(p):
    """block_expr_list : block_expr_list expr ';'"""
    p[0] = p[1] + [p[2]]


def p_expr_let(p):
    """expr : LET let_binding_list IN expr"""
    p[0] = LetNode(bindings=p[2], body=p[4])


def p_let_binding_list_single(p):
    """let_binding_list : let_binding"""
    p[0] = [p[1]]


def p_let_binding_list_many(p):
    """let_binding_list : let_binding_list ',' let_binding"""
    p[0] = p[1] + [p[3]]


def p_let_binding(p):
    """let_binding : OBJECTID ':' TYPEID"""
    p[0] = LetBindingNode(name=p[1], type_name=p[3])


def p_let_binding_init(p):
    """let_binding : OBJECTID ':' TYPEID ASSIGN expr"""
    p[0] = LetBindingNode(name=p[1], type_name=p[3], init=p[5])


def p_expr_new(p):
    """expr : NEW TYPEID"""
    p[0] = NewNode(type_name=p[2])


def p_expr_implicit_call(p):
    """expr : OBJECTID '(' arg_list ')' %prec DISPATCH"""
    p[0] = MethodCallNode(receiver=None, method=p[1], args=p[3])


def p_expr_dispatch(p):
    """expr : expr '.' OBJECTID '(' arg_list ')' %prec DISPATCH"""
    p[0] = MethodCallNode(receiver=p[1], method=p[3], args=p[5])


def p_expr_static_dispatch(p):
    """expr : expr '@' TYPEID '.' OBJECTID '(' arg_list ')' %prec DISPATCH"""
    p[0] = MethodCallNode(receiver=p[1], method=p[5], args=p[7], static_type=p[3])


def p_arg_list_empty(p):
    """arg_list : empty"""
    p[0] = []


def p_arg_list_values(p):
    """arg_list : arg_expr_list"""
    p[0] = p[1]


def p_arg_expr_list_single(p):
    """arg_expr_list : expr"""
    p[0] = [p[1]]


def p_arg_expr_list_many(p):
    """arg_expr_list : arg_expr_list ',' expr"""
    p[0] = p[1] + [p[3]]


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
