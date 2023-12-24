import io
import tokenize

import mip
import pegen.tokenizer
import pegen.utils


def parse(source):
    grammer = """
    start: root                                             { ('ROOT', None, root)}
    root: NEWLINE.statement+
    statement:
        | var_statement
        | obj_statement
        | constr_statement
    var_statement: tk='var' var_type lhs=iden '=' rhs=var_expr { ('VAR', var_type, [lhs, rhs], tk)}
    var_type:
        | 'cont'                                            { 'CONT' }
        | 'int'                                             { 'INT' }
        | 'bin'                                             { 'BIN' }
    var_expr:
        | 'ndarray' '(' shape ')'                           { ('FUNC', 'NDARRAY', shape) }
    shape: ','.base_expr+                                   
    constr_statement: 'constr' expr                         { ('CONSTR', None, [expr])}
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
    sub_op: '[' iden ']'                                    { iden }
    value: NUMBER                                           { ('VALUE', int(number.string), [], number) }
    iden: NAME                                              { ('IDEN', name.string, [], name) }
    """

    file = io.StringIO(source)
    parser_class = pegen.utils.make_parser(grammer)
    tokengen = tokenize.generate_tokens(file.readline)
    tokenizer = pegen.tokenizer.Tokenizer(tokengen, verbose=False)
    parser = parser_class(tokenizer, verbose=False)
    return parser.start()


NODES = [
    "IDEN",
    "VALUE",
    "SLICE",
    "OP",
    "FUNC",
    "OBJ",
    "CONSTR",
    "VAR",
    "BLOCK",
    "TREE",
]

OPS = [
    "SLICE",
    "PAREN",
    "MUL",
    "DIV",
    "ADD",
    "SUB",
    "NE",
    "EQ",
    "LT",
    "GT",
    "LE",
    "GE",
    "ITER",
]

FUNCS = [
    "FORALL",
    "SUM",
]

VARS = ["CONT", "BIN", "INT"]


class CompilerError(Exception):
    ...


class ModelGenerator:
    var_type_map = {
        "CONT": mip.CONTINUOUS,
        "BIN": mip.BINARY,
        "INT": mip.INTEGER,
    }

    def __init__(self, model_name, root, locals):
        self.model = mip.Model(model_name)
        self.iden_table = {}
        self.root = root
        self.locals = locals.copy()
        self.curr_cursor = root
        self.prev_cursor = None

    def enter(self, idx):
        print(f"enter: {self.curr_cursor[0]} {self.curr_cursor[1]} {idx}")
        children = self.curr_cursor[2]
        next_cursor = children[idx]
        children[idx] = self.prev_cursor
        self.prev_cursor = self.curr_cursor
        self.curr_cursor = next_cursor

    def exit(self, idx):
        print(f"exit: {self.curr_cursor[0]} {self.curr_cursor[1]} {idx}")
        next_cursor = self.curr_cursor
        self.curr_cursor = self.prev_cursor
        children = self.prev_cursor[2]
        self.prev_cursor = children[idx]
        children[idx] = next_cursor

    def ndarray(self, var_name, var_type, shape):
        match shape:
            case [x]:
                arr_x = []
                for i in range(x):
                    self.model.add_var(f"{var_name}_{i}", var_type=var_type)
                return arr_x
            case [x, y]:
                arr_x = []
                for i in range(x):
                    arr_y = []
                    for j in range(y):
                        arr_y.append(
                            self.model.add_var(f"{var_name}_{i}_{j}", var_type=var_type)
                        )
                    arr_x.append(arr_y)
                return arr_x
            case [x, y, z]:
                arr_x = []
                for i in range(x):
                    arr_y = []
                    for j in range(y):
                        arr_z = []
                        for k in range(z):
                            arr_z.append(
                                self.model.add_var(
                                    f"{var_name}_{i}_{j}_{k}", var_type=var_type
                                )
                            )
                        arr_y.append(arr_z)
                    arr_x.append(arr_y)
                return arr_x
            case [x, y, z, *rest]:
                raise CompilerError(f"Cannot create arrays with dimension {len(shape)}")
            case _:
                raise CompilerError(f"Undefiend array dimension {shape}")

    def generate(self):
        children = self.curr_cursor[2]
        for idx in range(len(children)):
            self.enter(idx)
            self.statement()
            self.exit(idx)

    def statement(self):
        match self.curr_cursor:
            case ("VAR", var_type, _, _):
                var_type_str = self.var_type_map[var_type]
                self.enter(0)
                var_name = self.var_lhs()
                self.exit(0)
                self.enter(1)
                self.iden_table[var_name] = self.var_expr(var_name, var_type_str)
                self.exit(1)

    def var_lhs(self):
        match self.curr_cursor:
            case ("IDEN", var_name, [], tk_info):
                return var_name
            case _:
                raise CompilerError(
                    f"Cannot assign lhs to {self.curr_cursor[0:2]} at {tk_info.start} on line {tk_info.line}"
                )

    def var_expr(self, var_name, var_type):
        match self.curr_cursor:
            case ("FUNC", "NDARRAY", shape):
                shape_arr = []
                for i in range(len(shape)):
                    self.enter(i)
                    shape_arr.append(self.value())
                    self.exit(i)
                return self.ndarray(var_name, var_type, shape_arr)
            case _:
                raise CompilerError(
                    f"Cannot assign variable {var_name} with {self.curr_cursor[0]} {self.curr_cursor[1]}"
                )

    def value(self):
        match self.curr_cursor:
            case ("VALUE", num, _, tk_info):
                return num
            case _:
                raise CompilerError(
                    f"Expected a value instead got the token {self.curr_cursor[0]} at {tk_info.start} on line {tk_info.line}"
                )
