import pickle
import unittest
from . import compile

class TestParser(unittest.TestCase):
    
    def test_travelling_salesman_problem(self):
        source = """var bin x = ndarray (V, V)
var cont y = ndarray (V)
obj min sum (i:V) (j:V) c[i][j] * x[i][j]
constr forall (i:V) sum (j:V, j != i) x[i][j] == 1
constr forall (i:V, i != 0) (j:V, j != 0, j != i) y[i] - (n + 1)*x[i][j] >= y[j] - n"""
        filename = 'src/demo_lang/assets/travelling_salesman_ast.pkl'
        parse_tree = compile.parse(source)
        with open(filename, 'rb') as f:
            check_tree = pickle.load(f)
        self.assertEqual(check_tree, parse_tree)

if __name__ == '__main__':
    unittest.main()