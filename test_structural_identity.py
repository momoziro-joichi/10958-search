from pathlib import Path
import tempfile
import unittest
from structural_identity import build_identity
from structural_checkpoint import validate

class IdentityTests(unittest.TestCase):
    def test_changed_source_rejects_saved_completion(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'solver.py';p.write_text('version1')
            old=build_identity('123','2/2',{'solver':p})
            self.assertEqual(old['target'],'1')
            saved={'schema':1,'identity':old,'completed':{'0':{'rejected':1}}}
            self.assertEqual(validate(saved,old),saved)
            p.write_text('version2')
            with self.assertRaises(ValueError):validate(saved,build_identity('123',1,{'solver':p}))
    def test_missing_source_and_invalid_config(self):
        with self.assertRaises(FileNotFoundError):build_identity('123',1,{'missing':'/nonexistent/10958-source'})
        for digits,bits,sources in [('',4096,{}),('１２',4096,{}),('123',True,{}),('123',4096,{})]:
            with self.assertRaises(ValueError):build_identity(digits,1,sources,bits)

if __name__=='__main__':unittest.main()
