from itertools import product
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

frequency_assignment_source = """var bin x = ndarray(N, U)
var cont z = ndarray(1)
obj min z[0]
constr forall (i:=N) (sum (c:=U) x[i][c]) == r[i]
constr forall (i:=N) (j:=N, i != j) (c1:=U) (c2:=U, c1 <= c2, c2 < c1 + d[i][j]) (x[i][c1] + x[j][c2] <= 1)
constr forall (i:=N) (c1:=U) (c2:=U, c1 < c2, c2 < c1 + d[i][i]) (x[i][c1] + x[i][c2] <= 1)
constr forall (i:=N) (c:=U) (z[0] >= (c + 1) * x[i][c])"""

project_scheduling_source = """var bin x = ndarray (J, T)
obj min (sum (t:=T) t * x[n + 1][t])
constr forall (j:=J) (sum (t:=T) x[j][t]) == 1
constr forall (r:=R) (t:=T) (sum (j:=J) (t2:=0:t, t2 >= (t - p[j] + 1)) u[j][r] * x[j][t2]) <= c[r]
constr forall (j:=X, s:=Y) (sum (t:=T) t * x[s][t] - t * x[j][t]) >= p[j]"""

job_scheduling_source = """var cont c = ndarray (1)
var cont x = ndarray (n, m)
var bin y = ndarray (n, n, m)
obj min c[0]
constr forall (j:=n) (i:=m, i > 0) x[j][machines[j][i]] - x[j][machines[j][i-1]] >= times[j][machines[j][i-1]]
constr forall (j:=n) (k:=n, k != j) (i:=m) x[j][i] - x[k][i] + M*y[j][k][i] >= times[k][i]
constr forall (j:=n) (k:=n, k != j) (i:=m) x[k][i] - x[j][i] - M*y[j][k][i] >= times[j][i] - M
constr forall (j:=n) c[0] - x[j][machines[j][m - 1]] >= times[j][machines[j][m - 1]]"""

cutting_stock_source = """var int x = ndarray (m, n)
var bin y = ndarray (n)
obj min sum (i:=n) y[i]
constr forall (i:=m) (sum (j:=n) x[i][j]) >= b[i]
constr forall (j:=n) (sum (i:=m) w[i] * x[i][j]) <= L * y[j]
constr forall (j:=n, j > 0) y[j - 1] >= y[j]"""

level_packing_source = """var bin x = ndarray (n, n)
obj min sum (i:=n) h[i] * x[i][i]
constr forall (i:=n) (j:=n, h[j] > h[i]) x[i][j] == 0.0
constr forall (i:=n) (sum (j:=n, h[j] >= h[i]) x[j][i]) == 1
constr forall (i:=n) (sum (j:=n, j != i, h[j] <= h[i]) w[j] * x[i][j]) <= (W - w[i]) * x[i][i]"""

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

    def test_frequency_assignment_problem(self):
        filename = "src/demo_lang/assets/frequency_assignment_ast.pkl"
        parse_tree = compile.parse(frequency_assignment_source)
        with open(filename, "rb") as f:
            check_tree = pickle.load(f)
        self.assertEqual(check_tree, parse_tree)

    def test_project_scheduling_problem(self):
        filename = "src/demo_lang/assets/project_scheduling_ast.pkl"
        parse_tree = compile.parse(project_scheduling_source)
        with open(filename, "rb") as f:
            check_tree = pickle.load(f)
        self.assertEqual(check_tree, parse_tree)

    def test_job_scheduling_problem(self):
        filename = "src/demo_lang/assets/job_scheduling_ast.pkl"
        parse_tree = compile.parse(job_scheduling_source)
        with open(filename, "rb") as f:
            check_tree = pickle.load(f)
        self.assertEqual(check_tree, parse_tree)

    def test_cutting_stock_problem(self):
        filename = "src/demo_lang/assets/cutting_stock_ast.pkl"
        parse_tree = compile.parse(cutting_stock_source)
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
            "N-Queens Problem",
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
        self.assertEqual(solution, attempt)

    def test_frequency_assignment_problem(self):
        solution = [
            [6, 12, 32],
            [4, 10, 16, 22, 28],
            [2, 8, 14, 20, 26, 32, 37, 40],
            [7, 13, 19],
            [0, 4, 10, 16, 24, 37],
            [2, 8, 14, 20, 26],
            [0, 6, 12, 18, 24, 30, 35],
            [0, 16, 21],
        ]
        r = [3, 5, 8, 3, 6, 5, 7, 3]
        d = [
            [3, 2, 0, 0, 2, 2, 0, 0],
            [2, 3, 2, 0, 0, 2, 2, 0],
            [0, 2, 3, 0, 0, 0, 3, 0],
            [0, 0, 0, 3, 2, 0, 0, 2],
            [2, 0, 0, 2, 3, 2, 0, 0],
            [2, 2, 0, 0, 2, 3, 2, 0],
            [0, 2, 2, 0, 0, 2, 3, 0],
            [0, 0, 0, 2, 0, 0, 0, 3],
        ]
        N = len(r)
        U = sum(d[i][j] for (i, j) in product(range(N), range(N))) + sum(el for el in r)
        gen = compile.ModelGenerator(
            "Frequency Assignment Problem",
            frequency_assignment_source,
            {
                "r": r,
                "d": d,
                "N": N,
                "U": U,
            },
        )
        scope = gen.generate()
        gen.model.verbose = 0
        gen.model.optimize(max_nodes=30)
        attempt = []
        if gen.model.num_solutions:
            for i in range(N):
                attempt.append([c for c in range(U) if scope["x"][i][c].x >= 0.99])
        self.assertEqual(solution, attempt)

    def test_project_scheduling_problem(self):
        obj_val = 21.0
        solution = [0, 0, 0, 6, 3, 3, 11, 7, 14, 17, 11, 21]
        n = 10
        p = [0, 3, 2, 5, 4, 2, 3, 4, 2, 4, 6, 0]
        u = [
            [0, 0],
            [5, 1],
            [0, 4],
            [1, 4],
            [1, 3],
            [3, 2],
            [3, 1],
            [2, 4],
            [4, 0],
            [5, 2],
            [2, 5],
            [0, 0],
        ]
        c = [6, 8]
        X = [0, 0, 0, 1, 1, 2, 2, 3, 4, 4, 5, 5, 6, 6, 7, 8, 9, 10]
        Y = [1, 2, 3, 4, 5, 9, 10, 8, 6, 7, 9, 10, 8, 9, 8, 11, 11, 11]
        R = len(c)
        J = len(p)
        T = sum(p)
        gen = compile.ModelGenerator(
            "Resource Constrained Project Scheduling Problem",
            project_scheduling_source,
            {
                "n": n,
                "p": p,
                "u": u,
                "c": c,
                "X": X,
                "Y": Y,
                "R": R,
                "J": J,
                "T": T,
            },
        )
        scope = gen.generate()
        gen.model.verbose = 0
        gen.model.optimize()
        self.assertAlmostEqual(gen.model.objective_value, obj_val)
        attempt = []
        for j in range(J):
            for t in range(T):
                if scope["x"][j][t].x >= 0.99:
                    attempt.append(t)
        self.assertEqual(solution, attempt)

    def test_job_scheduling_problem(self):
        obj_val = 7.0
        solution = [2.0, 5.0, 0.0, 5.0, 0.0, 3.0, 6.0, 3.0, 2.0]
        n = m = 3
        times = [[2, 1, 2], [1, 2, 2], [1, 2, 1]]
        M = sum(times[i][j] for i in range(n) for j in range(m))
        machines = [[2, 0, 1], [1, 2, 0], [2, 1, 0]]
        gen = compile.ModelGenerator(
            "Job Shop Scheduling Problem",
            job_scheduling_source,
            {
                "n": n,
                "m": m,
                "times": times,
                "M": M,
                "machines": machines,
            },
        )
        scope = gen.generate()
        gen.model.verbose = 0
        gen.model.optimize()
        self.assertAlmostEqual(gen.model.objective_value, obj_val)
        attempt = []
        for j in range(n):
            for i in range(m):
                attempt.append(scope["x"][j][i].x)
        self.assertAlmostEqual(attempt, solution)
        
    def test_cutting_stock_problem(self):
        obj_val = 3.0
        solution_x = [[(0, 0, 1.0)], [(1, 2, 2.0)], [(2, 1, 2.0)], [(3, 1, 1.0)]]
        solution_y = [(0, 1.0), (1, 1.0), (2, 1.0)]
        n = 10  # maximum number of bars
        L = 250  # bar length
        m = 4  # number of requests
        w = [187, 119, 74, 90]  # size of each item
        b = [1, 2, 2, 1]  # demand for each item
        gen = compile.ModelGenerator(
            "Cutting Stock Problem",
            cutting_stock_source,
            {
                "n": n,
                "L": L,
                "m": m,
                "w": w,
                "b": b,
            }
        )
        scope = gen.generate()
        gen.model.verbose = 0
        gen.model.optimize()
        self.assertAlmostEqual(gen.model.objective_value, obj_val)
        attempt_x = [[(i, j, scope['x'][i][j].x) for j in range(n) if scope['x'][i][j].x > 1e-5] for i in range(m)]
        attempt_y = [(i, scope['y'][i].x) for i in range(n) if scope['y'][i].x > 1e-5]
        self.assertAlmostEqual(attempt_x, solution_x)
        self.assertAlmostEqual(attempt_y, solution_y)

    def test_level_packing_problem(self):
        solution = [[2], [5, 7], [3, 6]]
        w = [4, 3, 5, 2, 1, 4, 7, 3]  # widths
        h = [2, 4, 1, 5, 6, 3, 5, 4]  # heights
        n = len(w)
        W = 10
        gen = compile.ModelGenerator(
            "Level Packing Problem",
            level_packing_source,
            {
                "w": w,
                "h": h,
                "n": n,
                "W": W,
            }
        )
        scope = gen.generate()
        gen.model.verbose = 0
        gen.model.optimize()
        attempt = []
        for i in [j for j in range(n) if scope['x'][j][j].x >= 0.99]:
            attempt.append(
                    [j for j in range(n) if i != j and h[j] <= h[i] and scope['x'][i][j].x >= 0.99]
            )
        self.assertEqual(attempt, solution)
        

if __name__ == "__main__":
    unittest.main()
