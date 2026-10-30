# 10958-search
Exact search for 10958 using 123456789

## Current status — bounded search completed

On 2026-10-30, all eight top-level partitions of `123456789 -> 10958`
completed with **no expression found under the integer-exponent bound -1000..1000**.
The sum of partition worker wall times was 55.789549 seconds; the largest
observed worker RSS was 171,380 KiB. These are single-run measurements.
This does **not** establish impossibility with unrestricted exponents.
The active `checkpoint_10958.json` records cap 1000 and requires that CLI option
when resuming. Cap-200 results are in `checkpoint_10958_cap200.json`; earlier
schema-1 cap-100 checkpoints are retained as historical evidence only.
See `PROGRESS.md` for test results, exact limits, and measurements.

### Arithmetic and validation

`search.py` implements concatenation, `+`, `-`, `*`, `/`, and integer
exponentiation using exact `Fraction` arithmetic. Negative exponents and
rational bases are supported. `^` in returned expressions means exponentiation;
Python itself uses `**`.

Both forward DP and reverse search restrict every exponent to
`abs(exponent) <= max_abs_exponent` (default 100). This **limits the searched
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

### Budgeted target search (Linux)

```bash
python run_search.py --digits 123456789 --target 10958 --seconds 60 --memory-mib 768
```

`run_search.py` runs the solver in a separate process. The parent enforces a
wall-clock timeout and kills/waits for the worker on expiry. The Linux worker
uses `RLIMIT_AS` to limit virtual address space (not just resident memory).
Other platforms are rejected rather than silently running without memory limits.
The default budget is 30 seconds and 512 MiB. JSON output distinguishes `found`,
`not_found_bounded`, `timeout`, `memory_limit`, and `worker_error`.
Incomplete/error runs exit with status 2; completed searches exit with status 0.
A timeout does not prove absence of a solution. Rerunning this single-job command starts over. Use the partitioned runner below
to retain completed top-level splits.

The first budgeted `123456789 -> 10958` attempt ended in **timeout** at
20.026 seconds with a 512 MiB address-space budget. No expression was returned;
the search was not completed. See `PROGRESS.md` for measurements and next work.

`python search.py` still runs only the validation suite, so its final
`10958 search: NOT RUN YET` message refers to that invocation.

Reverse-search memoization now retains at most 50,000 non-leaf states.
Single-digit queries are answered without caching, and power-base candidates
are looked up in the already-built left DP table. Cache eviction affects runtime,
not the allowed expressions; full DP tables are still unbounded within the
worker's process memory budget.

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

## Resumable partitioned search

```bash
python resume_search.py --max-abs-exponent 1000 --seconds 180 --per-split-seconds 60 --memory-mib 768 --checkpoint checkpoint_10958.json
```

The top-level operator splits `123456789` at one of eight positions. Each
partition searches all permitted operators at that split; concatenation is
checked separately. A checkpoint saves each finished partition using an atomic
file replacement, and a file lock prevents concurrent writers. On resume,
completed negative partitions are skipped, while timeouts and memory-limited
partitions are retried. **Progress inside an unfinished partition is not saved.**
The total time budget controls worker allocation; process startup and cleanup
can add a small amount of overhead. No work is started after that deadline.

Checkpoints bind the digit string, exact target and SHA-256 of the solver and
both runners. If any of those change, use a new checkpoint path and revalidate;
a mismatch is rejected. Do not manually change completion statuses or hashes.

Short intervals (up to four digits) now use exact precomputed table lookup.
Other intervals still use reverse search, trying balanced splits first. Tests
explicitly use `lookup_digits=0` to exercise the original reverse algorithm,
and independently compare hybrid results and partition unions on small spaces.
This changes execution order and reuse, not the operation rules or exponent cap.


### Single-digit edge inversion

When the right operand is a single digit, the solver now inverts each operator
and solves only the required left targets. It no longer builds the entire large
left value table for that split. Zero multiplication, zero exponent, and both
signs of even roots are handled explicitly.

When the left base is a single digit, exponentiation checks the complete existing
configured integer exponent range -N through N, then asks whether a matching exponent
can be formed on the right. This avoids building an eight-digit exponent table.
This is exact within the same exponent cap; floating-point logarithms are not
used. `edge_inversion=False` retains the preceding implementation for differential
tests. Source changes invalidate old checkpoints; archived checkpoints are
historical evidence and are not silently reused.


### Independent small-space enumeration

```bash
python -m unittest -v test_oracle
```

`test_oracle.py` first enumerates every digit tokenization, then every binary
expression tree and permitted operator, without using the production DP,
reverse/root routines, memoization or intermediate value deduplication.
For all 256 four-digit strings over 0..3, it enumerates 168,288 valid expression
trees and obtains 21,359 distinct values summed across inputs. It compares these
sets with forward DP, then checks 24,147 target queries against reverse search
with short-interval lookup disabled. Returned expressions are independently
re-evaluated and checked for digit order. Hand-calculated examples and +/-100
versus +/-101 exponent boundaries also test the oracle itself.

This adds independent small-space evidence, not a separate nine-digit
impossibility proof. These small-space tests do not establish the result for unrestricted powers.


### Configurable exponent cap

Both runners accept `--max-abs-exponent N` (nonnegative integer, default 100).
The solver API accepts `make_solver(digits, max_abs_exponent=N)` and applies
that cap to every exponent node, in forward DP and all reverse-search paths.
A cap of zero still permits nonzero bases raised to zero; it does not disable
exponentiation. Negative powers are permitted down to -N when the base is nonzero.

Schema-2 checkpoints record the cap explicitly, as well as input and source
fingerprints. A different cap or source version is rejected before any completed
partition can be reused. Schema-1 checkpoints are historical records and cannot
be resumed by this version. Use a fresh path when expanding the cap:

```bash
python resume_search.py --max-abs-exponent 200 --seconds 400 --per-split-seconds 45 --memory-mib 768 --checkpoint checkpoint_cap200.json
```

Increasing the cap expands the expression space and can sharply increase time
and memory use. A completed negative result applies only to the recorded cap.
