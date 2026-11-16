import json
from pathlib import Path
import tempfile
import unittest
from structural_checkpoint import save,load,validate

class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.identity={'digits':'123','target':'10958','source_sha256':'test-only','bits':4096}
        self.data={'schema':1,'identity':self.identity,'completed':{'1':{'rejected':5}}}
    def test_schema_and_top_level_types(self):
        for data in (None, [], True, 1, 'checkpoint', dict(self.data,schema=True), dict(self.data,schema=1.0)):
            with self.assertRaises(ValueError):validate(data,self.identity)

    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'checkpoint.json';save(p,self.data,self.identity)
            self.assertEqual(load(p,self.identity),self.data)
            altered=dict(self.identity,bits=8192)
            with self.assertRaises(ValueError):load(p,altered)
    def test_bad_counts_and_masks(self):
        for record in ({'01':{'rejected':5}},{'4':{'rejected':5}}, {'1':{'rejected':4}}, {'1':{'rejected':True}}, {'1':{'unresolved':5}}):
            with self.assertRaises(ValueError):validate(dict(self.data,completed=record),self.identity)
    def test_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'c.json';p.write_text('{"schema":1,"schema":1}')
            with self.assertRaises(ValueError):load(p,self.identity)

if __name__=='__main__':unittest.main()
