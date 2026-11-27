from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from structural_lock import checkpoint_lock

class LockTests(unittest.TestCase):
    def test_competing_process_and_release(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'checkpoint.json'
            code='from structural_lock import checkpoint_lock\nimport sys\nwith checkpoint_lock(sys.argv[1]): pass'
            with checkpoint_lock(p):
                result=subprocess.run([sys.executable,'-c',code,str(p)],capture_output=True,timeout=5)
                self.assertNotEqual(result.returncode,0)
                self.assertIn(b'BlockingIOError',result.stderr)
            result=subprocess.run([sys.executable,'-c',code,str(p)],capture_output=True,timeout=5)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertTrue(Path(str(p)+'.lock').exists())
    def test_exception_releases(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'c.json'
            with self.assertRaises(RuntimeError):
                with checkpoint_lock(p):raise RuntimeError('test')
            with checkpoint_lock(p):pass

if __name__=='__main__':unittest.main()
