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
    var_statement: 'var' var_type lhs=iden '=' rhs=var_expr { ('VAR', var_type, [lhs, rhs])}
    var_type:
        | 'cont'                                            { 'CONT' }
        | 'int'                                             { 'INT' }
        | 'bin'                                             { 'BIN' }
    var_expr: 'ndarray' '(' ','.base_expr+ ')'              { 'FUNC', 'NDARRAY', []}
    constr_statement: 'constr' expr                         { 'CONSTR', None, [expr]}
    obj_statement: 'obj' obj_func expr                      { ('OBJ', obj_func, [expr])}
    obj_func:
        | 'min'                                             { 'MIN' }
        | 'max'                                             { 'MAX' }
    expr:
        | func_expr
        | comp_op_expr
    func_expr: func=func_iden b=block+ expr                 { (*func, [expr, *b])}
    block: '(' it=iter_expr re=rest* ')'                    { ('BLOCK', None, [it, *re]) }
    rest: ',' comp_op_expr                                  { comp_op_expr }
    func_iden:
        | 'sum'                                             { ('FUNC', 'SUM')}
        | 'forall'                                          { ('FUNC', 'FORALL')}
    iter_expr: lhs=iden ':' rhs=set_expr                    { ('OP', 'ITER', [lhs, rhs])}
    set_expr:
        | iden
    comp_op_expr:
        | lhs=add_sub_op_expr op=comp_op rhs=add_sub_op_expr { (*op, [lhs, rhs])}
        | add_sub_op_expr
    comp_op:
        | '!='                                              { ('OP', 'NE')}
        | '=='                                              { ('OP', 'EQ')}
        | '<='                                              { ('OP', 'LE')}
        | '>='                                              { ('OP', 'GE')}
        | '<'                                               { ('OP', 'LT')}
        | '>'                                               { ('OP', 'GT')}
    add_sub_op_expr:
        | lhs=mul_div_op_expr '+' rhs=add_sub_op_expr       { ('OP', 'ADD', [lhs, rhs])}
        | lhs=mul_div_op_expr '-' rhs=add_sub_op_expr       { ('OP', 'SUB', [lhs, rhs])}
        | mul_div_op_expr
    mul_div_op_expr:
        | lhs=paren_expr '*' rhs=mul_div_op_expr            { ('OP', 'MUL', [lhs, rhs])}
        | lhs=paren_expr '/' rhs=mul_div_op_expr            { ('OP', 'DIV', [lhs, rhs])}
        | paren_expr
    paren_expr:
        | '(' val=add_sub_op_expr ')'                       { ('OP', 'PAREN', [val])}
        | base_expr
    base_expr:
        | slice_expr
        | iden
        | value
    slice_expr: val=iden idx=sub_op+                        { ('OP', 'SLICE', [val, *idx])}
    sub_op: '[' iden']'                                     { iden }
    value: NUMBER                                           { ('VALUE', int(number.string), [])}
    iden: NAME                                              { ('IDEN', name.string, [])}
    """

    file = io.StringIO(source)
    parser_class = pegen.utils.make_parser(grammer)
    tokengen = tokenize.generate_tokens(file.readline)
    tokenizer = pegen.tokenizer.Tokenizer(tokengen, verbose=False)
    parser = parser_class(tokenizer, verbose=False)
    return parser.start()

nodeKeys = [
    'IDEN',
    'VALUE',
    'SLICE',
    'OP',
    'FUNC',
    'OBJ',
    'CONSTR',
    'VAR',
    'BLOCK',
]    

opKeys = [
    'SLICE',
    'PAREN',
    'MUL',
    'DIV',
    'ADD',
    'SUB',
    'NE',
    'EQ',
    'LT',
    'GT',
    'LE',
    'GE',
    'ITER',
]

funcKeys = [
    'FORALL',
    'SUM',
]

varKeys = [
    'CONT',
    'BIN',
    'INT'
]