import pickle
import unittest
from . import compile

knapsack_source = """var bin x = ndarray(I)
obj max sum (i:=I) p[i] * x[i]
constr (sum (i:=I) w[i] * x[i]) <= c"""

travelling_salesman_source = """var bin x = ndarray (n, n)
var cont y = ndarray (n)
obj min sum (i:=n) (j:=n) c[i][j] * x[i][j]
constr forall (i:=n) (sum (j:=n, i != j) x[i][j]) == 1
constr forall (i:=n) (sum (j:=n, i != j) x[j][i]) == 1
constr forall (i:=n, i != 0) (j:=n, j != 0, i != j) y[i] - (n + 1) * x[i][j] >= y[j] - n"""


class TestParser(unittest.TestCase):

    def test_travelling_salesman_problem(self):
        filename = "src/demo_lang/assets/travelling_salesman_ast.pkl"
        parse_tree = compile.parse(travelling_salesman_source)
        with open(filename, "rb") as f:
            check_tree = pickle.load(f)
        self.assertEqual(check_tree, parse_tree)

    def test_knapsack_problem(self):
        filename = "src/demo_lang/assets/knapsack_ast.pkl"
        parse_tree = compile.parse(knapsack_source)
        with open(filename, "rb") as f:
            check_tree = pickle.load(f)
        self.assertEqual(check_tree, parse_tree)


class TestEvaluator(unittest.TestCase):

    def test_knapsack_problem(self):
        gen = compile.ModelGenerator(
            "knapsack",
            knapsack_source,
            {
                "p": [10, 13, 18, 31, 7, 15],
                "w": [11, 15, 20, 35, 10, 33],
                "c": 47,
                "I": 6,
            },
        )
        scope = gen.generate()
        gen.model.verbose = 0
        gen.model.optimize()
        selected = [i for i in range(scope["I"]) if scope["x"][i].x >= 0.99]
        self.assertEqual(selected, [0, 3])

    def test_travelling_salesman_problem(self):
        dists = [
            [83, 81, 113, 52, 42, 73, 44, 23, 91, 105, 90, 124, 57],
            [161, 160, 39, 89, 151, 110, 90, 99, 177, 143, 193, 100],
            [90, 125, 82, 13, 57, 71, 123, 38, 72, 59, 82],
            [123, 77, 81, 71, 91, 72, 64, 24, 62, 63],
            [51, 114, 72, 54, 69, 139, 105, 155, 62],
            [70, 25, 22, 52, 90, 56, 105, 16],
            [45, 61, 111, 36, 61, 57, 70],
            [23, 71, 67, 48, 85, 29],
            [74, 89, 69, 107, 36],
            [117, 65, 125, 43],
            [54, 22, 84],
            [60, 44],
            [97],
            [],
        ]
        n = len(dists)
        c = [
            [
                0 if i == j else dists[i][j - i - 1] if j > i else dists[j][i - j - 1]
                for j in range(n)
            ]
            for i in range(n)
        ]
        gen = compile.ModelGenerator(
            "Travelling Salesman Problem",
            travelling_salesman_source,
            {
                "n": n,
                "c": c,
            },
        )
        scope = gen.generate()
        gen.model.verbose = 0
        gen.model.optimize()
        if gen.model.num_solutions:
            nc = 0
            path = [nc]
            while True:
                nc = [i for i in range(n) if scope["x"][nc][i].x >= 0.99][0]
                path.append(nc)
                if nc == 0:
                    break
            self.assertEqual(path, [0, 8, 7, 6, 2, 10, 12, 3, 11, 9, 13, 5, 4, 1, 0])


if __name__ == "__main__":
    unittest.main()
