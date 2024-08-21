## Introduction

Demo lang has its own compiler albiet it is very small. Demo lang fills the particular niche of mixed integer programming[1] and hence the compiler is also peculiar. It derives a lot of power from python, that is, it delegates the heavy load of execution onto python itself. Thus in some sense, the compiler is a "transpiler" which convert the demo lang source into executed python code although the python code is never generated. Even though this is a small compiler, in my opinion it has some beautiful techniques which are worth discussing. The following sections attempts to do so.

## Component of the Demo lang compiler

In essence the demo lang compiler takes the demo lang source and executes it without generating any intermediate bytecode or any python code. Thus the compiler has two parts, parser and evaluator. The parser converts the source into a syntax tree and the evaluator takes the syntax tree and runs the code. The output of the evaluator is python object of class `mip.Model.Model`.

## Pegen and Directed Syntax Translation

The `demo_lang.compile.parse` function uses the parser generator [pegen](https://github.com/we-like-parsers/pegen) to create a parser from the specified grammar. As the parser uses the python's own tokenizer, the operators we use in demo lang are all restricted to ones used in python. The nice thing about pegen is one can write the translation of syntax into the data structure right in the grammar itself. For example, the rule

```
comp_op : '!='       { ('OP', 'NE') }
```

parses the string "!=" and returns the tuple "('OP', 'NE')" as a node in the syntax tree. The resulting tree will look like.

```python
('ROOT', None, [
    ('VAR', 'BIN', [
        ('IDEN', 'x', []),
        ('FUNC', 'NDARRAY', [
            ('IDEN', 'I', [])])])])
```

## Traversing the syntax tree

The evaluator uses a space efficient way of traversing through the syntax tree. It has two pointers named `curr_cursor` and `parent_cursor`. Whenever we need to move to a child node, we update the cursors and re-purpose the pointer to the child node, in to the pointer to the parent node. This helps in keeping track of the way back up to the root node.

## What runtime? It's python baby!

## The problem with scope

Demo lang has no way of declaring its own data structures other than ndarray of `mip.var`. For sake of writing useful programs, we should be able to use variables which contains data. Thus demo lang has all the variables available from the local python scope. Once the demo lang programs are run, we would like to have the declared variables in demo lang back into the python scope. But the requirements of scope goes further than this.

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

The evaluator will traverse depth first through the syntax tree, so we first arrive at the node `('OP', 'SLICE', [...])` which results from the expression `x[j]` now we could evaluate if only we knew what the value of `j`. To obtain the value of `j` we must traverse further in to the next node which is `('OP', 'ITER', [...])` which has the expression `j := 1..n`. This node can evaluate the value of `j` but has no idea where to use this. When we finally are done visiting all the nodes that we have the complete picture and we can finally carry out the computation we want. This translates into python code as 

```python
sum([x[j] for j in range(1, n + 1)])
```

For this to work we must be able to compose the two expressions, `for j in range(1, n + 1)` and `x[j]` while the value of `j` passes from one expression to another. Note that the value of `j` changes every iteration thus adding to the complexity.

This problem gets further aggravated when we have multiple iterators which behaves as zip and product further complicating the situation. For example

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

Now, not only we need to pass all the iterator variables to the scope of the expression, we also need pass the iterator defined in the previous block to be present in the scope of the next block.

Thus the goal at hand are
1. The return values of these node visit should be a computation which can be evaluated in the future. These 'can be evaluated' values will be named evaluators[4].
2. These evaluators should be composable.
3. When composed they should be able to share the scope with each other.

One saving grace we have is that demo lang has lexical scoping thus we can get away with use of mutable scope[3]. This means the constraint at hand is child nodes should not influence the parent scope. This lexical scoping rules will neatly arrange the nesting scopes into a stack similar to call stack of function execution. This results in an interesting property where, for a particular node in the syntax tree, the scope is provided by the node's parent and the scope for the each child is updated by the node. This suggests that all the scoping shenanigans need for a particular node is fulfilled by its parent as it has the visibility to the adjacent node which can influence its scope. This translates into the 'stack of scope' picture as the parent scope sitting right beneath the child scope and as the child nodes are visited, it updates the parent scope and the visit to the next child node will have the necessary variables in the scope provided by the previous child nodes.

Thus a strict fourth goal can be added to our evaluators which is

4. These evaluators should form a stack mimicking the scope stack.

Now it's clear that the similarity between call stack and scope stack is not a coincidence as the evaluator is acting like an execution frame.

## Thunks all the way down



## Notes

1. Mixed integer programming has nothing to do with computer programming and everything to do with optimization of problems.
2. Assuming that the value of `x` has been defined in some preceding statment in the program.
3. We do actually use mutable global scope because a demo lang program consists of var statements which sets the variables in the program scope. As only the var statement can mutate state and the rest of the language consists of expressions, we can say the mutation problem is highly contained.
4. In compiler parlance such a things is called a thunk.


```python
forall (i := 1..n) (sum (j := 1..n) x[i][j] == 1)
```

The syntax tree generated for this expression would be

```python
('FUNC', 'FORALL', [
    ('OP', 'EQ', [
        ('OP', 'PAREN', [
            ('FUNC', 'SUM', [
                ('OP', 'SLICE', [
                    ('IDEN', 'x', []),
                    ('IDEN', 'i', []),
                    ('IDEN', 'j', [])]),
                ('BLOCK', None, [
                    ('OP', 'ITER', [
                        ('RANGE', None, [
                            ('VALUE', 1, []),
                            ('IDEN', 'n', [])])])])])]),
        ('VALUE', 1, [])]),
    ('BLOCK', None, [
        ('OP', 'ITER', [
            ('IDEN', 'i', []),
            ('RANGE', None, [
                ('VALUE', 1, []),
                ('IDEN', 'n', [])])])])])
```