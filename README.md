# 10958-search
Exact search for 10958 using 123456789
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
These results do not prove that 10958 is impossible.
Exponentiation has not yet been implemented.
