# 10958-search
Exact search for 10958 using 123456789

## Current status — Stage 9A validation

`search.py` implements concatenation, `+`, `-`, `*`, `/`, and integer
exponentiation using exact `Fraction` arithmetic. Negative exponents and
rational bases are supported. `^` in returned expressions means exponentiation;
Python itself uses `**`.

Both forward DP and reverse search restrict every exponent to
`abs(exponent) <= MAX_ABS_EXPONENT` (currently 100). This **limits the searched
expression space**; it is not a complete unrestricted search.
`0^0`, zero to a negative power, and division by zero are excluded.
The digit order is preserved and each input digit is used exactly once.

Reverse search checks both signs of an even root, all available nonzero bases
for exponent zero, and reciprocal targets for negative exponents.
Integer roots use an integer bit-length bound; no floating-point roots are used.

Run with Python 3 (standard library only):

```bash
python -m unittest -v
python search.py
```

The test suite checks exact expression values and digit order, the minimal
`23 -> (2^3) = 8` case, negative/zero exponents, rational roots, zero handling,
and forward/reverse agreement for all 64 three-digit strings over `0..3`,
plus `1234` and `12345`. It also checks a sample of absent targets.

The default validation passes for `123` (35 values), `1234` (261 values),
and `12345` (2,453 values). These are bounded validation results, not a proof
for longer inputs or unrestricted powers. In particular, `1234` now recovers
`(1-23)^4 = 234256` and `((1/2)-3)^4 = 625/16`.

**The current script does not run the `123456789 -> 10958` search.**
Its final `10958 search: NOT RUN YET` message is intentional.
Large-input time and memory usage remain unresolved; there is no complete
10958 result from this version.

The sections below record historical runs under different rules and are not
new results from the current implementation.

## Initial Result

### Basic Integer Interval DP

- Digits: `123456789`
- Target: `10958`
- Operations: `+`, `-`, `*`, `/`
- Concatenation: allowed
- Parentheses: allowed
- Intermediate values: integers only
- Distinct values: `132,993`
- Result: **NOT FOUND**

This is only the first-stage result.
It does not prove that 10958 cannot be represented.

## Search Results

### Stage 1 — Integer DP

- Digits: `123456789`
- Target: `10958`
- Operations: `+`, `-`, `*`, `/`
- Concatenation: allowed
- Parentheses: allowed
- Intermediate values: integers only
- Distinct final values: `132,993`
- Result: **NOT FOUND**

### Stage 2 — Exact Rational DP

- Digits: `123456789`
- Target: `10958`
- Operations: `+`, `-`, `*`, `/`
- Concatenation: allowed
- Parentheses: allowed
- Intermediate values: exact rational numbers
- Arithmetic: Python `Fraction`
- `1/2` representation: verified
- `1/3` representation: verified
- Result: **NOT FOUND**

### Stage 3 — Integer Exponentiation

- Operations: `+`, `-`, `*`, `/`, `^`
- Concatenation: allowed
- Intermediate values: exact rational numbers
- Exponentiation: integer base and non-negative integer exponent
- Temporary power limit: 100 decimal digits

Observed search-space growth:

- Length 7: 871,674 total values
- Length 8: 5,421,848 total values
- Length 9: terminated before completion

Conclusion:

A naive forward interval-DP becomes impractical when
integer exponentiation is introduced.

Therefore, the next stage will use
target-directed / reverse search rather than generating
the entire value space.

Stage 4 — Target-directed search
Result: terminated before completion
Reason: intermediate value generation remained too large

### Stage 5 — Structural Target Search

- Exact rational arithmetic
- Target-directed recursion
- Integer exponentiation
- Result: terminated before completion

The recursive state space remained too large.
Further optimization is required before claiming completeness.

Method:
Target-directed recursive search

Visited states:
20,450,000+

Result:
No solution found before stopping

Status:
Computationally expensive
These results do not prove that 10958 is impossible.
Exponentiation is implemented in the current Stage 9A code; see the current status above.
