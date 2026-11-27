import unittest
from unittest.mock import patch
from diagnose_structural import sample

class DiagnosticTests(unittest.TestCase):
    def test_complete_small(self):
        r=sample('23','10958',1)
        self.assertEqual(r,dict(visited=5,samples=[],status='enumerated'))

    def test_unknown_is_retained(self):
        with patch('diagnose_structural.matches_target',return_value=None):
            r=sample('23','10958',1,2)
        self.assertEqual(r['status'],'sample_limit')
        self.assertEqual(len(r['samples']),2)
        self.assertEqual(r['visited'],2)

    def test_limits(self):
        for limit in (0,101,True):
            with self.assertRaises(ValueError): sample('23','8',1,limit)
