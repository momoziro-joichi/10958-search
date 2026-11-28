import json
import subprocess
import unittest

class WorkerTests(unittest.TestCase):
    def test_negative_and_candidate(self):
        for target,status in [('8','candidate_unverified'),('9','complete_rejected')]:
            p=subprocess.run(['python','run_subpartition.py','--tokens','2','3','--split','1','--op','^','--target',target],capture_output=True,text=True,timeout=10)
            self.assertEqual(p.returncode,0,p.stderr)
            r=json.loads(p.stdout);self.assertEqual(r['status'],status)
            self.assertEqual(r['expected'],1)
    def test_bad_tokens(self):
        p=subprocess.run(['python','run_subpartition.py','--tokens','2','-3','--split','1','--op','+'],capture_output=True,text=True,timeout=10)
        self.assertNotEqual(p.returncode,0)
