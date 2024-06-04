import io
import itertools
import tokenize

import mip
import pegen.tokenizer
import pegen.utils


def parse(source):
    grammer = """
    start: root                                             { ('ROOT', None, root) }
    root: NEWLINE.statement+
    statement:
        | var_statement
        | obj_statement
        | constr_statement
    var_statement: tk='var' var_type lhs=iden '=' rhs=var_expr { ('VAR', var_type, [lhs, rhs], tk) }
    var_type:
        | 'cont'                                            { 'CONT' }
        | 'int'                                             { 'INT' }
        | 'bin'                                             { 'BIN' }
    var_expr:
        | tk='ndarray' '(' shape ')'                        { ('FUNC', 'NDARRAY', shape, tk) }
    shape: ','.base_expr+                                   
    constr_statement: tk='constr' expr                      { ('CONSTR', None, [expr], tk) }
    obj_statement: tk='obj' obj_func expr                   { ('OBJ', obj_func, [expr], tk) }
    obj_func:
        | 'min'                                             { 'MIN' }
        | 'max'                                             { 'MAX' }
    expr:
        | func_expr
        | comp_op_expr
    func_expr: func=func_iden b=block+ expr                 { (func[0], func[1], [expr, *b], func[2]) }
    block: tk='(' it=iter_expr re=rest* ')'                 { ('BLOCK', None, [it, *re], tk) }
    rest: ',' comp_op_expr                                  { comp_op_expr }
    func_iden:
        | tk='sum'                                          { ('FUNC', 'SUM', tk) }
        | tk='forall'                                       { ('FUNC', 'FORALL', tk) }
    iter_expr: lhs=iden tk=':' rhs=set_expr                 { ('OP', 'ITER', [lhs, rhs], tk) }
    set_expr:
        | iden
    comp_op_expr:
        | lhs=add_sub_op_expr comp_op rhs=add_sub_op_expr   { (comp_op[0], comp_op[1], [lhs, rhs], comp_op[2]) }
        | add_sub_op_expr
    comp_op:
        | tk='!='                                           { ('OP', 'NE', tk) }
        | tk='=='                                           { ('OP', 'EQ', tk) }
        | tk='<='                                           { ('OP', 'LE', tk) }
        | tk='>='                                           { ('OP', 'GE', tk) }
        | tk='<'                                            { ('OP', 'LT', tk) }
        | tk='>'                                            { ('OP', 'GT', tk) }
    add_sub_op_expr:
        | lhs=mul_div_op_expr op='+' rhs=add_sub_op_expr    { ('OP', 'ADD', [lhs, rhs], op) }
        | lhs=mul_div_op_expr op='-' rhs=add_sub_op_expr    { ('OP', 'SUB', [lhs, rhs], op) }
        | mul_div_op_expr
    mul_div_op_expr:
        | lhs=paren_expr op='*' rhs=mul_div_op_expr         { ('OP', 'MUL', [lhs, rhs], op) }
        | lhs=paren_expr op='/' rhs=mul_div_op_expr         { ('OP', 'DIV', [lhs, rhs], op) }
        | paren_expr
    paren_expr:
        | tk='(' val=add_sub_op_expr ')'                    { ('OP', 'PAREN', [val], tk) }
        | base_expr
    base_expr:
        | slice_expr
        | iden
        | value
    slice_expr: val=iden idx=sub_op+                        { ('OP', 'SLICE', [val, *idx], val[3]) }
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


class CompilerError(Exception): ...


class ModelGenerator:
    var_type_map = {
        "CONT": mip.CONTINUOUS,
        "BIN": mip.BINARY,
        "INT": mip.INTEGER,
    }

    obj_func_map = {
        "max": mip.maximize,
        "min": mip.minimize,
    }

    def __init__(self, model_name, root, locals):
        self.model = mip.Model(model_name)
        self.scope = {}
        self.root = root
        self.locals = locals.copy()
        self.curr_cursor = root
        self.prev_cursor = None

    def enter(self, idx):
        print(
            f"enter: {self.curr_cursor[0]} {self.curr_cursor[1]} {idx}"
            f" -> {self.curr_cursor[2][idx][0]} {self.curr_cursor[2][idx][1]}"
        )
        children = self.curr_cursor[2]
        next_cursor = children[idx]
        children[idx] = self.prev_cursor
        self.prev_cursor = self.curr_cursor
        self.curr_cursor = next_cursor

    def exit(self, idx):
        # print(
        #     f"exit: {self.curr_cursor[0]} {self.curr_cursor[1]} {idx}"
        #     f" -> {self.prev_cursor[0]} {self.prev_cursor[1]}"
        # )
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
                    arr_x.append(
                        self.model.add_var(f"{var_name}_{i}", var_type=var_type)
                    )
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
            case [x, y, z, *_]:
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
                expr_eval = self.var_expr(var_name, var_type_str)
                self.exit(1)
                self.scope[var_name] = expr_eval(self.scope)
            case ("OBJ", obj_func, _, _):
                self.enter(0)
                expr_eval = self.expr()
                self.exit(0)
                self.model.objective = self.obj_func_map[obj_func](expr_eval(self.scope))
            case _:
                raise CompilerError(
                    f"Expected a statement at the start of the program instead found: {self.curr_cursor[0:2]}"
                    f" at {self.curr_cursor[3].start} on line '{self.curr_cursor[3].line}'"
                )

    def var_lhs(self):
        return self.iden_lhs()

    def var_expr(self, var_name, var_type) -> function:
        match self.curr_cursor:
            case ("FUNC", "NDARRAY", shape, _):
                shape_arr = []
                for i in range(len(shape)):
                    self.enter(i)
                    shape_arr.append(self.base_expr())
                    self.exit(i)
                return lambda scope: self.ndarray(var_name, var_type, shape_arr)
            case _:
                raise CompilerError(
                    f"Cannot assign variable {var_name} with {self.curr_cursor[0]} {self.curr_cursor[1]}"
                    f" at {self.curr_cursor[3].start} on line '{self.curr_cursor[3].line}'"
                )

    def value(self):
        match self.curr_cursor:
            case ("VALUE", num, _, _):
                return lambda scope: num
            case _:
                raise CompilerError(
                    f"Expected a value instead found the token {self.curr_cursor[0]} at {self.curr_cursor[3].start} on line '{self.curr_cursor[3].line}'"
                )

    def iden_lhs(self):
        match self.curr_cursor:
            case ("IDEN", var_name, [], _):
                return var_name
            case _:
                raise CompilerError(
                    f"Cannot assign to variable {self.curr_cursor[0:2]} at {self.curr_cursor[3].start} on line '{self.curr_cursor[3].line}'"
                )

    def iden_rhs(self) -> function:
        match self.curr_cursor:
            case ("IDEN", var_name, [], tk_info):
                if var_name in self.locals:
                    return lambda scope: self.locals[var_name]
                else:
                    def evaluator(scope):
                        if var_name not in scope:
                            raise CompilerError(
                                f"Undefiend variable {self.curr_cursor[0:2]} at {tk_info.start} on line '{tk_info.line}'"
                            )
                        return scope[var_name]
                    return evaluator
            case _:
                raise CompilerError(
                    f"Unexpected token {self.curr_cursor[0:2]} at {self.curr_cursor[3].start} on line '{self.curr_cursor[3].line}'"
                )

    def base_expr(self) -> function:
        match self.curr_cursor:
            case ("OP", "SLICE"):
                return self.op_expr()
            case ("IDEN", *_):
                return self.iden_rhs()
            case ("VALUE", *_):
                return self.value()
            case _:
                raise CompilerError(
                    f"Unexpected token {self.curr_cursor[0:2]} at {self.curr_cursor[3].start} on line '{self.curr_cursor[3].line}'"
                )

    def expr(self) -> function:
        match self.curr_cursor:
            case ("FUNC", *_):
                return self.func()
            case ("OP", *_):
                return self.op_expr()
            case _:
                raise CompilerError(
                    f"Expected an expression instead found: {self.curr_cursor[0:2]}"
                    f" at {self.curr_cursor[3].start} on line '{self.curr_cursor[3].line}'"
                )

    def func(self) -> function:
        match self.curr_cursor:
            case ("FUNC", "SUM", children, _):
                blocks = []
                for idx in range(1, len(children)):
                    self.enter(idx)
                    blocks.append(self.block())
                    self.exit(idx)
                self.enter(0)
                expr_eval = self.expr()
                self.exit(0)
                block_eval = self.compose_blocks(blocks, expr_eval)
                return lambda scope: mip.xsum(block_eval(scope))
            case ("FUNC", "FORALL", _, _):
                raise NotImplemented
            case ("FUNC", *_):
                raise CompilerError(
                    f"Unknow function {self.curr_cursor[1]} encountered"
                    f" at {self.curr_cursor[3].start} on line '{self.curr_cursor[3].line}'"
                )
                
    def compose_blocks(self, blocks) -> function:
        # TODO: Deal with comparision as well
        return lambda scope: itertools.product(b(scope) for b in blocks)

    def block(self) -> function:
        match self.curr_cursor:
            case ("BLOCK", None, _, _):
                self.enter(0)
                expr_eval = self.op_expr()
                self.exit(0)
                return 
            case _:
                raise CompilerError(
                    f"Expected function block instead found: {self.curr_cursor[0:2]}"
                    f" at {self.curr_cursor[3].start} on line '{self.curr_cursor[3].line}'"
                )

    def set_expr(self):
        return self.iden_rhs()

    def op_expr(self):
        match self.curr_cursor:
            case ("OP", "ITER", children, _):
                self.enter(0)
                var_name = self.iden_lhs()
                self.exit(0)
                self.enter(1)
                expr = self.set_expr()
                self.exit(1)
                return [var_name, expr]
            case ("OP", "NE", _, _):
                self.enter(0)
                lhs = self.op_expr()
                self.exit(0)
                self.enter(1)
                rhs = self.op_expr()
                self.exit(1)
                return ["!=", lhs, rhs]
            case ("OP", "EQ", _, _):
                self.enter(0)
                lhs = self.op_expr()
                self.exit(0)
                self.enter(1)
                rhs = self.op_expr()
                self.exit(1)
                return ["==", lhs, rhs]
            case ("OP", "LE", _, _):
                self.enter(0)
                lhs = self.op_expr()
                self.exit(0)
                self.enter(1)
                rhs = self.op_expr()
                self.exit(1)
                return ["<=", lhs, rhs]
            case ("OP", "GE", _, _):
                self.enter(0)
                lhs = self.op_expr()
                self.exit(0)
                self.enter(1)
                rhs = self.op_expr()
                self.exit(1)
                return [">=", lhs, rhs]
            case ("OP", "LT", _, _):
                self.enter(0)
                lhs = self.op_expr()
                self.exit(0)
                self.enter(1)
                rhs = self.op_expr()
                self.exit(1)
                return ["<", lhs, rhs]
            case ("OP", "GT", _, _):
                self.enter(0)
                lhs = self.op_expr()
                self.exit(0)
                self.enter(1)
                rhs = self.op_expr()
                self.exit(1)
                return [">", lhs, rhs]
            case ("OP", "ADD", _, _):
                self.enter(0)
                lhs = self.op_expr()
                self.exit(0)
                self.enter(1)
                rhs = self.op_expr()
                self.exit(1)
                return ["+", lhs, rhs]
            case ("OP", "SUB", _, _):
                self.enter(0)
                lhs = self.op_expr()
                self.exit(0)
                self.enter(1)
                rhs = self.op_expr()
                self.exit(1)
                return ["-", lhs, rhs]
            case ("OP", "MUL", _, _):
                self.enter(0)
                lhs = self.op_expr()
                self.exit(0)
                self.enter(1)
                rhs = self.op_expr()
                self.exit(1)
                return ["*", lhs, rhs]
            case ("OP", "DIV", _, _):
                self.enter(0)
                lhs = self.op_expr()
                self.exit(0)
                self.enter(1)
                rhs = self.op_expr()
                self.exit(1)
                return ["/", lhs, rhs]
            case ("OP", "PAREN", _, _):
                self.enter(0)
                expr = self.op_expr()
                self.exit(0)
                return [expr]
            case ("OP", "SLICE", children, _):
                vs = []
                for idx in range(len(children)):
                    self.enter(idx)
                    vs.append(self.iden_rhs())
                    self.exit(idx)
                return [vs[0], vs[1:]]
            case _:
                return self.base_expr()
