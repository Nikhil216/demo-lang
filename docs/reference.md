## Preface

This language heavily relies on python to do a lot of the work. It used the python tokenizer, its parser generator and its function call stack as the evaluation stack. The the langauge compiles into python code for running [`python-mip`](https://www.python-mip.com/) which will solve a mixed integer programming problem. Thus it is assumed that user is familiar with python as well as python-mip package. If you are not familiar with any of the both then the user must get familiar with them first. Here are some links to learn [python](https://docs.python.org/3/tutorial/) and [python-mip](https://docs.python-mip.com/en/latest/quickstart.html).

## Introduction

There are three important parts to a mixed integer programing problem variables, objective and constraints. Thus there are three kinds of statements in this langauges. The following sections will describe each of these statements.

## Arithmetic Expression

The arthmetic expression acts much like python's but with far less operators. Here are the operators

```
+   add
-   subtract
*   multiply
/   divide
<   less than
<=  less than or equal
>   greater than
>=  greater thatn or equal
==  equal
!=  not equal
:   range
```

## Accessing arrays

Just like python, lists and arrays can be accessed by using the subscript syntax.

```python
x[i][j]
```

where `x` is the array, `i` is the first index and `j` is the second index.

## Variable Assignment

This statement starts with the keyword `var`. The statement will assign an array to an identifier which can be used in the following lines of the demo program.

```
var       bin    x            =                     ndarray    (n)
^keyword  ^type  ^identifier  ^assignment operator  ^function  ^function block
```

You can declare the identifier name and the type of the variable. There are three types: `bin`, `int` and `cont`. There correspond to the python-mip types.

```
cont -> mip.CONTINUOUS
bin  -> mip.BINARY
int  -> mip.INTEGER
```

The identifier will be assigned the expression on the right hand side of the assignment operator. The only valid expression can be the function `ndarray`.

## Functions

Functions are expressions which starts with a function name and returns a computed expression. A function will have a function block which is flanked by round paranthesis and it may be followed by an expression. There can be multiple function blocks. The function expression (body) is left associative thus the expression at the right most side of a chain of function names belongs to the right most function name. For example

```python
forall (i:=m) sum (j:=n) x[i][j]
```

Here, the expression `x[i][j]` will be the body for `sum`. Thus if we add paranthesis for disambiguation it will be as follows.

```python
forall (i:=m) (sum (j:=n) (x[i][j]))
```

There are three functions in the langauge explained in the following sections.

> Note: There is no provision to declare your own functions. Thus this language provides no way for writing abstractions.

### sum

Returns the sum of the expression iterated over the iterator block. For example, such expression will be converted into python expression like

```python
## demo
sum (i:=n) x[i]

## python
sum(x[i] for i in range(n))
```

It can have multiple iterators and it will nest these.

```python
## demo
sum (i:=m) (j:=n) x[i][j]

## python
sum(x[i][j] for i in range(m) for j in range(n))
```

### forall

Much like the mathematical notation, it iterates over the iterator block and create multiple copies of the same expression with varying subscript values. For example

```python
## demo
forall (i:=n) x[i] < c

## python
for i in range(n):
    x[i] < c
```

It is used in the constraint statement to declare multiple constraints at once.

### ndarray

This function is used solely to assign arrays to variables which can be used latter in the program. The value will be of nested python list acting like a tensor which can be accessed by subscripting it. Unlike python, there is no slice operation. This function takes the shape of the array in the function block. For example

```python
var bin x = ndarray (m, n)
constr forall (i:=m) (sum (j:=n) x[i][j]) == 1
```

## Iteration

Iterators in function blocks fulfill the basic need of iterating over an index. The iteration operator `:=` takes an identifier at the left hand side and can take one the following form at the right hand side.

```python
(i:=n)

(i:=0..n)
```

The first form has a variable at the right hand side. If this variable has a python value of an integer then the iterator will evaluate it as a range of values from `0` to `n - 1` which will be equivalent to the python expression

```python
range(n)
```

Thus it becomes a handy short hand for a verbose python expression like

```python
n = len(x)
for i in range(n):
```

If the python value is of a python iterator then the iterator will simple iterator over it assigning the value of the elements to the variable. For example

```python
## demo
(element:=array)

## python
for element in array
```

The second form has a range operator `:` on the right hand side. It iterates over the numbers on the either side of the range operator inclusively i.e.

```python
## demo
0..n

## python
range(0, n + 1)
```

The function blocks for sum and forall are interesting as they can nest iterators, zip iterators and filter them and thus are very useful. Each block can have multiple iterators and multiple conditions. There can be multiple blocks as well which will get nested. We will present a series of example to best explain its working.

### Conditions

Adding conditions to a block will filter out the ones which does not satisfy it. For example, this condition will skip `i = 0`

```python
## demo
sum (i:=n, i > 0) x[i]

## python
sum(x[i] for i in range(n) if i > 0)
```

You can add multiple conditions on the same block and the iterations will have to satisfy all of the conditions. For example, these conditions will skip both `i = 0` and `i = n`

```python
## demo
sum (i:=n, i > 0, i < n) x[i]

## python
sum(x[i] for i in range(n) if i > 0 and i < n)
```

It is important to note the scope of a block. A function can have multiple blocks, the variable in a block will be in scope for all the following blocks. For example, this program will evaluate

```python
## demo
forall (i:=n) (j:=n, i != j) x[i][j]
```

where as this will result in the error that the variable `j` is not in scope.

```python
## demo
forall (i:=n, i != j) (j:=n) x[i][j]
```

### Nested iterators

Multiple iterator blocks will be nested. It is the same effect that one gets by using the cartesian product. Here's a comparision for example

```python
## demo
sum (i:=m) (j:=n) x[i][j]

## python
sum(x[i][j] for i in range(m) for j in range(n))

## python
sum(x[i][j] for i, j in product(m, n))
```

### Zipped iterators

If the same function block contains more than one iterator then the iterators will be zipped together. The evaluated iterator will be same as the python `zip` function so all the rules applies here. The most important of which is the iteration stop with the shortest iterator.

```python
## demo
forall (x:=X, y:=Y) x * y

## python
for x, y in zip(X, Y):
    x * y
```

## Objective

To assign an objective you must first use the keyword `obj`. Then we can use `min` or `max` to declare if the objective should be minimized or maximized.

```
obj       min     c[0]
^keyword  ^sense  ^expression
```

## Constraint

To assign a constraint you must first use the keyword `constr` followed by the expression. The expression is usually going to be a conditional.

```
constr    x[i] * w[i] < c[0]
^keyword  ^expression
```