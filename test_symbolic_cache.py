from functools import lru_cache
import unittest
from unittest.mock import patch
import strategy_probe as probe
from benchmark_symbolic_cache import run


class CacheTests(unittest.TestCase):
    def test_classifications_and_parameter_keys(self):
        original=probe.evaluate
        cached=lru_cache(maxsize=64)(original)
        try:
            for tree in probe.all_trees('1234'):
                for bits,cap in ((2,None),(16,3),(4096,100)):
                    probe.evaluate=original
                    expected=[probe.matches_target(tree,t,bits,cap) for t in (0,1,8,10958)]
                    probe.evaluate=cached
                    self.assertEqual(expected,[probe.matches_target(tree,t,bits,cap) for t in (0,1,8,10958)])
            self.assertLessEqual(cached.cache_info().currsize,64)
        finally:
            probe.evaluate=original
            cached.cache_clear()

    def test_cleanup_on_failure(self):
        original=probe.evaluate
        with patch.object(probe,'all_trees',side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):
                run('123',64)
        self.assertIs(probe.evaluate,original)


if __name__=='__main__':
    unittest.main()
