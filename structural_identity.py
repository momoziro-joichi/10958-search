"""Build experimental checkpoint identity from explicitly required sources.

Callers must include every semantic dependency, including their runner.
This detects changes, not authenticity or mathematical correctness.
"""
from fractions import Fraction
from hashlib import sha256
from pathlib import Path


def build_identity(digits, target, sources, bits=4096):
    if not isinstance(digits,str) or not digits or any(c not in '0123456789' for c in digits):
        raise ValueError('invalid digits')
    if type(bits) is not int or bits <= 0:
        raise ValueError('bits must be a positive integer')
    if not sources:
        raise ValueError('explicit source manifest required')
    manifest={}
    for name,path in sorted(sources.items()):
        if not isinstance(name,str) or not name:
            raise ValueError('invalid source name')
        manifest[name]=sha256(Path(path).read_bytes()).hexdigest()
    return dict(digits=digits,target=str(Fraction(target)),bits=bits,
                exponent_cap=None,sources_sha256=manifest)
