import pickle
import unittest
from . import compile

knapsack_source = """var bin x = ndarray (I)
obj max sum (i:=I) p[i] * x[i]
constr (sum (i:=I) w[i] * x[i]) <= c"""

travelling_salesman_source = """var bin x = ndarray (n, n)
var cont y = ndarray (n)
obj min sum (i:=n) (j:=n) c[i][j] * x[i][j]
constr forall (i:=n) (sum (j:=n, i != j) x[i][j]) == 1
constr forall (i:=n) (sum (j:=n, i != j) x[j][i]) == 1
constr forall (i:=n, i != 0) (j:=n, j != 0, i != j) y[i] - (n + 1) * x[i][j] >= y[j] - n"""

n_queens_source = """var bin x = ndarray (n, n)
constr forall (i:=n) (sum (j:=n) x[i][j]) == 1
constr forall (j:=n) (sum (i:=n) x[i][j]) == 1
constr forall (k:=2-n:n-2) (sum (i:=n, 0 <= i - k, i - k < n) x[i][i - k]) <= 1
constr forall (k:=1:2*n-3) (sum (i:=n, 0 <= k - i, k - i < n) x[i][k - i]) <= 1"""


class TestParser(unittest.TestCase):

    def test_n_queens_problem(self):
        filename = "src/demo_lang/assets/n_queens_ast.pkl"
        parse_tree = compile.parse(n_queens_source)
        with open(filename, "rb") as f:
            check_tree = pickle.load(f)
        self.assertEqual(check_tree, parse_tree)

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

    def test_n_queens_problem(self):
        solution = [
            (0, 23),
            (1, 18),
            (2, 5),
            (3, 8),
            (4, 31),
            (5, 33),
            (6, 15),
            (7, 25),
            (8, 14),
            (9, 16),
            (10, 26),
            (11, 37),
            (12, 27),
            (13, 4),
            (14, 10),
            (15, 13),
            (16, 2),
            (17, 36),
            (18, 38),
            (19, 21),
            (20, 32),
            (21, 34),
            (22, 22),
            (23, 7),
            (24, 35),
            (25, 29),
            (26, 3),
            (27, 20),
            (28, 9),
            (29, 28),
            (30, 12),
            (31, 0),
            (32, 11),
            (33, 1),
            (34, 17),
            (35, 6),
            (36, 30),
            (37, 24),
            (38, 39),
            (39, 19),
        ]
        n = 40
        gen = compile.ModelGenerator(
            "N-Queens Proble",
            n_queens_source,
            {
                "n": n,
            },
        )
        scope = gen.generate()
        gen.model.verbose = 0
        gen.model.optimize()
        attempt = []
        for i, row in enumerate(scope["x"]):
            for j, square in enumerate(row):
                if square.x > 0.99:
                    attempt.append((i, j))
        assert solution == attempt


if __name__ == "__main__":
    unittest.main()
