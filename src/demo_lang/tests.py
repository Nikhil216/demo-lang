import unittest
from . import compile

class TestParser(unittest.TestCase):
    
    def test_travelling_salesman_problem(self):
        source = """var bin x = ndarray (V, V)
var cont y = ndarray (V)
obj min sum (i:V) (j:V) c[i][j] * x[i][j]
constr forall (i:V) sum (j:V, j != i) x[i][j] == 1
constr forall (i:V, i != 0) (j:V, j != 0, j != i) y[i] - (n + 1)*x[i][j] >= y[j] - n"""
        source_lines = len(source.split('\n'))
        tree = compile.parse(source)
        parsed_lines = len(tree)
        self.assertEqual(parsed_lines, source_lines)

if __name__ == '__main__':
    unittest.main()