"""Atomic storage primitive for experimental structural partitions.

Only completed, fully rejected partitions can be reused. Not a search runner.
The caller must hold exclusive ownership of the checkpoint path.
"""
import json
import os
from pathlib import Path
import tempfile
from math import comb


def expected_count(mask):
    k=mask.bit_count()
    return comb(2*k,k)//(k+1)*5**k


def validate(data, identity):
    if data.get('schema') != 1 or data.get('identity') != identity:
        raise ValueError('checkpoint identity mismatch')
    records=data.get('completed')
    if not isinstance(records,dict):
        raise ValueError('invalid records')
    for key, record in records.items():
        if not isinstance(key,str) or not key.isascii() or not key.isdecimal():
            raise ValueError('invalid mask')
        mask=int(key)
        if str(mask)!=key or not 0<=mask<1<<(len(identity['digits'])-1):
            raise ValueError('mask outside input')
        if not isinstance(record,dict) or set(record)!={'rejected'}:
            raise ValueError('only completed rejection records supported')
        if type(record['rejected']) is not int or record['rejected']!=expected_count(mask):
            raise ValueError('incomplete partition')
    return data


def load(path, identity):
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key]=value
        return result
    return validate(json.loads(Path(path).read_text(),object_pairs_hook=unique),identity)


def save(path, data, identity):
    validate(data,identity)
    path=Path(path)
    fd,name=tempfile.mkstemp(dir=path.parent,prefix=path.name+'.')
    try:
        with os.fdopen(fd,'w') as f:
            json.dump(data,f,sort_keys=True);f.flush();os.fsync(f.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):
            os.unlink(name)
