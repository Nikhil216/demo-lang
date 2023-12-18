import io
import pegen.tokenizer
import pegen.utils
import tokenize


def parse(source):
    grammer = """
    start: NEWLINE.statement+
    statement:
        | var_statement
        | obj_statement
        | constr_statement
    var_statement: 'var' var_type iden '=' var_expr
    var_type:
        | 'cont'
        | 'int'
        | 'bin'
    var_expr: 'ndarray' '(' ','.base_expr+ ')'
    constr_statement: 'constr' expr
    obj_statement: 'obj' obj_func expr
    obj_func:
        | 'min'
        | 'max'
    expr:
        | func_expr
        | comp_op_expr
    func_expr: func_iden ('(' iter_expr (','comp_op_expr)* ')')+ expr
    func_iden:
        | 'sum'
        | 'forall'
    iter_expr: iden ':' set_expr
    set_expr:
        | iden
    comp_op_expr:
        | add_sub_op_expr comp_op add_sub_op_expr 
        | add_sub_op_expr
    comp_op:
        | '!='
        | '=='
        | '<='
        | '>='
    add_sub_op_expr:
        | mul_div_op_expr '+' add_sub_op_expr
        | mul_div_op_expr '-' add_sub_op_expr
        | mul_div_op_expr
    mul_div_op_expr:
        | paren_expr '*' mul_div_op_expr
        | paren_expr '/' mul_div_op_expr
        | paren_expr
    paren_expr:
        | '(' add_sub_op_expr ')'
        | base_expr
    base_expr:
        | slice_expr
        | iden
        | value
    slice_expr: iden ('[' iden ']')+
    value: NUMBER
    iden: NAME
    """

    file = io.StringIO(source)
    parser_class = pegen.utils.make_parser(grammer)
    tokengen = tokenize.generate_tokens(file.readline)
    tokenizer = pegen.tokenizer.Tokenizer(tokengen, verbose=False)
    parser = parser_class(tokenizer, verbose=False)
    return parser.start()
