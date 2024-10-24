## Introduction

Demo lang has its own compiler albiet it is very small. Demo lang fills the particular niche of mixed integer programming[1] and hence the compiler is also peculiar. It derives a lot of power from python, that is, it delegates the heavy load of execution onto python itself. Thus in some sense, the compiler is a "transpiler" which convert the demo lang source into executed python code although the python code is never generated. Even though this is a small compiler, in my opinion it has some beautiful techniques which are worth discussing. The following sections attempt to do so.

## Components of the Demo lang compiler

In essence the demo lang compiler takes the demo lang source and executes it without generating any intermediate bytecode or any python code. Thus the compiler has two parts, parser and evaluator. The parser converts the source into a syntax tree and the evaluator takes the syntax tree and runs the code. The output of the evaluator is python object of class `mip.Model.Model`.

## Pegen and Directed Syntax Translation

The `demo_lang.compile.parse` function uses the parser generator [pegen](https://github.com/we-like-parsers/pegen) to create a parser from the specified grammar. As the parser uses the python's own tokenizer, the operators we use in demo lang are all restricted to ones used in python. The nice thing about pegen is that - one can write the translation of syntax into a data structure right in the grammar itself. For example, the rule

```
comp_op : '!='       { ('OP', 'NE') }
```

parses the string "!=" and returns the tuple "('OP', 'NE')" as a node in the syntax tree. For example, the following statement in demo-lang

```python
var bin x = ndarray (I)
```

will result in a syntax tree looking like.

```python
('ROOT', None, [
    ('VAR', 'BIN', [
        ('IDEN', 'x', []),
        ('FUNC', 'NDARRAY', [
            ('IDEN', 'I', [])])])])
```

## Traversing the syntax tree

The evaluator uses a space efficient way of traversing through the syntax tree. It has two pointers named `curr_cursor` and `parent_cursor`. Whenever we need to move to a child node, we update the cursors and re-purpose the pointer to the child node, in to the pointer to the parent node. This helps in keeping track of the way back up to the root node.

> TODO: Explaing the traversal

## The problem with scope

Demo lang has no way of declaring its own data structures other than ndarray of `mip.var`. For sake of writing useful programs, we should be able to use variables which contains other data structures. Thus demo lang has all the variables available from the local python scope. Once the demo lang programs are run, we would like to have the declared variables in demo lang back into the python scope. But the requirements of scope within a demo-lang program goes further than this.

Let's take for example the `sum` function. It sums an expression for all values enumerated. For example

$$
\sum_{j = 1}^{n} x_{ij}
$$

would be written in demo lang as 

```python
sum (j := 1..n) x[j]
```

The syntax tree generated for this expression would be

```python
('FUNC', 'SUM', [
    ('OP', 'SLICE', [
        ('IDEN', 'x', []),
        ('IDEN', 'j', [])]),
    ('BLOCK', None, [
        ('OP', 'ITER', [
            ('IDEN', 'j', []),
            ('RANGE', None, [
                ('VALUE', 1, []),
                ('IDEN', 'n', [])])])])])
```

The evaluator will traverse depth first through the syntax tree, so we first arrive at the node `('OP', 'SLICE', [...])` which results from the expression `x[j]` now we could evaluate if only we knew what the value of `j`. To obtain the value of `j` we must traverse further in to the next node which is `('OP', 'ITER', [...])` which has the expression `j := 1..n`. This node can evaluate the value of `j` but has no idea where to use this. When we are finally done visiting all the nodes, we can have the complete picture and we can finally carry out the computation we want. This translates into python code as 

```python
sum([x[j] for j in range(1, n + 1)])
```

For this to work we must be able to compose the two expressions, `for j in range(1, n + 1)` and `x[j]` while the value of `j` passes from one expression to another. Note that the value of `j` changes every iteration thus adding to the complexity.

This problem gets further aggravated when we have multiple iterators which behaves as zip and product, further complicating the situation. For example

```python
# ziping two iterators in demo lang
sum (i:=m, j:=n) x[i] + y[j]

# equivalant python code
sum([x[i] + y[j] for i, j in zip(range(m), range(n))])
```

```python
# product of two iterators in demo lang
sum (i:=m) (j:=n) x[i][j]

# equivalent python code
sum([x[i][j] for i, j in product(range(m), range(n))])
```

On top of all of this are conditions which filter out values from iterators

```python
# sum of upper triangle in a matrix
sum (i:=m) (j:=m, i < j) x[i][j]

# equivalent python code
sum([x[i][j] for i, j in product(range(m), range(n)) if i < j])
```

In this case - you'd notice - the second iterator block `(j:=m, i < j)` has the variable `i` which is in the first iterator block `(i:=m)`. Now, not only we need to pass all the iterator variables to the scope of the expression, we also need to pass the iterator defined in the previous block to be present in the scope of the next block.

Thus our goals at hand are

1. The return values of these node visit should be a computation which can be evaluated in the future. These 'can be evaluated' values will be named evaluators[4].
2. These evaluators should be composable.
3. When composed they should be able to share the scope with each other.

One saving grace we have is that demo lang has lexical scoping thus we can get away with use of mutable scope[3]. Here - mutable scope means - the constraint at hand is child nodes should not influence the parent scope. This lexical scoping rules will neatly arrange the nesting scopes into a stack similar to call stack of function execution. This results in an interesting property where, for a particular node in the syntax tree, the scope is provided by the node's parent and the scope for the each child is updated by the node. This suggests that all the scoping shenanigans needed for a particular node is fulfilled by its parent as it has the visibility to the adjacent node which can influence its scope. This translates well into the 'stack of scope' picture as the parent scope sitting right beneath the child scope and as the child nodes are visited, it updates the parent scope and the visit to the next child node will have the necessary variables in the scope provided by the previous child nodes.

Thus a strict fourth goal can be added to our evaluators which is

4. These evaluators should form a stack mimicking the scope stack.

Now it's clear that the similarity between call stack and scope stack is not a coincidence as the evaluator is acting like an execution frame.

## Thunks all the way down

The idea of an expression being stored in a value which can be evaluated later fits the description of a closure[5]. Indeed the visitor methods in `demo_lang.compile.ModelGenerator` return a closure named evaluator. When this closure is called, it evaluates a python expression and return a concrete (python) value. The argument passed to this closure is the current scope. Now we see how these evaluators are composed.

Let's pick the simplest example

```python
sum (j := n) x[j]
```

The expression body of `sum` will emit an evaluator, which in python can be written as

```python
def evaluator():
    return x[j]
```

Since both `x` and `j` are free variables, we must provide them through scope.

```python
def evaluator(scope):
    x = scope['x']
    j = scope['j']
    return x[j]
```

Similarly, the block will also emit an evaluator

```python
def evaluator(scope):
    n = scope['n']
    return ({'j': j} for j in range(n))
```

The return value of this evaluator is a python generator. This generator iterates over the `range(n)` and returns a scope!

```python
{ 'j' : j }
```

This is a neat trick as we'll come to see. Once the block and expression nodes are visited, the sum node will return its own evaluator. To disambiguate, we will name each evaluator separately.

```python
def evaluator_sum(scope):
    acc = 0
    for local_scope in evaluator_block(scope):
        acc += evaluator_expression({**scope, **local_scope})
    return acc
```

Since evaluators are just python functions we can compose them in any way we want, as long as it's valid python. The interesting point to notice is that the evaluators are nested, i.e. they call each other, thus acts like a call stack. To be fair the call stack we are describing is actually python's call stack. This is only possible because we choose our evaluators to be plain python functions. The added benefit we get is the scope also follows a stack due to python's lexical scoping. When we refer to closures, we mean lexical closure as the free variables are assigned by lexical scoping. Thus closures by their mere definition satisfy all four goal we set out to have for our evaluators.

## Composition of blocks

As we had seen in the [previous section](#the-problem-with-scope) blocks compose in many ways. There are three things to take care about:

1. blocks should form cartesian product with other blocks
2. blocks should form zips with other blocks
3. blocks should filter values on conditions

First we'll talk about compositions. The evaluators of a block takes in a scope and emits a generator which yields scope. Thus the question of composition of block evaluators reduces to the question of composition of generator of scopes and further - finally - to composition of scopes. Scopes are just key value pairs represented by python dictionaries. Thus we need to answer two questions

1. how to compose scopes as products
2. how to comose scopes as zips

The zips one is straight forward. If we have two iterators

```python
(i := m, j := n)
```

the scopes we get per iteration will be (where m < n)

```python
{ 'i': 0 },   { 'j': 0 }
{ 'i': 1 },   { 'j': 1 }
{ 'i': 2 },   { 'j': 2 }
  ...     ,     ...
{ 'i': m-1 }, { 'j': m-1 }
                ...
              { 'j': n-1 }
```

Zipping these two iterators will simply mean we should combine the scope at each iteration such that both `i` and `j` should be in scope when evaluated. This will result in the iterations

```python
{ 'i': 0, 'j': 0 }
{ 'i': 1, 'j': 1 }
{ 'i': 2, 'j': 2 }
  ...     ,   ...
{ 'i': m-1, 'j': m-1 }
```

The generated evaluator will look something like

```python
def eval_iter_1(scope):
    m = scope['m']
    return ({ 'i': i } for i in range(m))

def eval_iter_2(scope):
    n = scope['n']
    return ({ 'j': j } for j in range(n))

def eval_iter_zip(scope):
    return ({ **scope_1, **scope_2 } for scope_1, scope_2 in zip(eval_iter_1(scope), eval_iter_2(scope)))
```

Next, the product of two iterators will generate m x n iteration with every possible combination between i and j. It looks something like

```python
{ 'i': 0, 'j': 0}
{ 'i': 0, 'j': 1}
   ...  ,   ...
{ 'i': 0, 'j': n-1}
{ 'i': 1, 'j': 0}
{ 'i': 1, 'j': 1}
   ...  ,   ...
{ 'i': 1, 'j': n-1}
{ 'i': 2, 'j': 0}
   ...  ,   ...
   ...  ,   ...
{ 'i': m-1, 'j': n-1}
```

The neat trick about this composition is that we have to replace just the `zip` function with `product` function and the evaulator behaves just as we want.

```python
def eval_iter_1(scope):
    m = scope['m']
    return ({ 'i': i } for i in range(m))

def eval_iter_2(scope):
    n = scope['n']
    return ({ 'j': j } for j in range(n))

def eval_iter_product(scope):
    return ({ **scope_1, **scope_2 } for scope_1, scope_2 in product(eval_iter_1(scope), eval_iter_2(scope)))
#                                                            ^^^^^^^ replaced from zip
```

> Excersice: Readers are encouraged to verify whether these evaluators produce the appropriate generators.

As we have seen, composing two block/iterator evaluators is the same as composing two generators returning scope. The reason we can compose two evaluators is we can compose two scopes (and generator of scope) trivially. Composition of dictionary is just creating a new dictionary with all the key value pairs in both the dictionaries.

```python
{ **scope_1, **scope_2 }
```

Along with iterator, a block can also contain conditions. These condition filter out values which satisfy all the conditions in a given block. These conditions don't affect the composition of blocks.

> TODO: conditions in blocks

## What runtime? It's python baby!

The job of the execution engine is to emit a python object of `mip.model.Model` rather than some bytecode or native code. So the execution engine evaluates all the expression as python expressions and builds a `mip.model.Model`. This raises the question, does it really have a runtime?

Demo lang, as previously mentioned, relies heavily on python. Even though it generates no code, it still has to know what is being executed and how it would be evaluted in python. For example, a demo-lang expression represented as a python string

```python
"x[i]"
```

would be converted into python code

```python
x[j]
```

Moreover - as the evaluation is strict - to return the evaluated value of `x[j]` we must - first - evaluate the values of `x` and `j`. To do that we must know what expression will evalute into `x` or `j`. Thus each evaluation will depened on some previous evalutation to be complete.

> TODO: Complete the story

## Notes

1. Mixed integer programming has nothing to do with computer programming and everything to do with optimization of problems.
2. Assuming that the value of `x` has been defined in some preceding statment in the program. The same is true for `n`.
3. We do actually use mutable global scope because a demo lang program consists of `var` statements which sets the variables in the program scope. Only the var statement can mutate state and the rest of the language consists of expressions. Thus we can say the mutation problem is highly contained.
4. In compiler parlance such a thing is called a thunk.
5. It can also be an object given that you represent the expression into a data structure and have an eval method.