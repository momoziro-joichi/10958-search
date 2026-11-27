import itertools
from fractions import Fraction
import unittest
from search import make_solver
from test_search import evaluate


class EdgeInversionTests(unittest.TestCase):
    def test_edge_paths_against_original(self):
        strings = ["".join(p) for p in itertools.product("0123", repeat=3)]
        strings += ["1234", "12345", "2300", "2331"]
        for digits in strings:
            forward, _ = make_solver(digits)
            targets = set(forward(0, len(digits)))
            targets |= {Fraction(n, 2) for n in range(-10, 11)}
            for split in sorted({1, len(digits) - 1}):
                old = make_solver(digits, root_split=split, lookup_digits=0,
                                  edge_inversion=False)[1]
                new = make_solver(digits, root_split=split, lookup_digits=0)[1]
                for target in targets:
                    before = old(0, len(digits), target)
                    after = new(0, len(digits), target)
                    self.assertEqual(before is not None, after is not None,
                                     (digits, split, target))
                    if after is not None:
                        self.assertEqual(evaluate(after), target)
                        self.assertEqual("".join(c for c in after if c.isdigit()), digits)
                old.cache_clear()
                new.cache_clear()
            forward.cache_clear()


if __name__ == "__main__":
    unittest.main()
