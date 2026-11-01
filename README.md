# 10958-search
Exact search for 10958 using 123456789

## Current status — bounded search completed

On 2026-11-01, all eight top-level partitions of `123456789 -> 10958`
completed with **no expression found under the integer-exponent bound -5000..5000**.
The sum of partition worker wall times was 6.604807 seconds; the largest
observed worker RSS was 24,496 KiB. These are single-run measurements.
This does **not** establish impossibility with unrestricted exponents.
The latest checkpoint is `checkpoint_10958_cap5000.json` (cap 5000).
Resume it with `python resume_search.py --max-abs-exponent 5000 --seconds 240
--per-split-seconds 45 --memory-mib 768 --checkpoint checkpoint_10958_cap5000.json`
(on one line). The historical `checkpoint_10958.json` retains cap 2000 unchanged but uses an older source fingerprint. The pre-optimization cap-2000 checkpoint is archived unchanged
in `checkpoint_10958_cap2000_before_digit_inverse.json`. The previous cap-1000 result is archived unchanged in
`checkpoint_10958_cap1000_before_verifier.json`. The previous schema-2 cap-1000 result is archived in
`checkpoint_10958_cap1000_schema2.json`. Historical cap-200 results are in `checkpoint_10958_cap200.json`; earlier
schema-1 cap-100 checkpoints are retained as historical evidence only.
Long exponent operands now use target-directed bounded-integer queries after exact
root/base checks, avoiding a full exponent-operand table. No intermediate-value
size pruning is used. The preceding checkpoint is preserved unchanged in
`checkpoint_10958_cap2000_before_exponent_queries.json`.
See `PROGRESS.md` for test results, exact limits, and measurements.

For a right operand of at most two digits shorter than the left operand,
reverse search now enumerates the right values and solves for the left. This
avoids building large left tables without pruning any intermediate values.
The prior checkpoint is archived as
`checkpoint_10958_cap2000_before_right_inverse.json`.

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
python resume_search.py --max-abs-exponent 2000 --seconds 240 --per-split-seconds 60 --memory-mib 768 --checkpoint checkpoint_10958.json
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
both runners and the independent witness verifier. If any of those change, use a new checkpoint path and revalidate;
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

When the left base is a single digit 2..9, repeated exact integer division
finds the unique possible exponent (or proves none matches the target).
Negative exponents require a reciprocal integer target. Bases 0 and 1 retain
all permitted matching exponents because their powers are not one-to-one.
The solver then asks whether the exponent can be formed on the right. This avoids building an eight-digit exponent table.
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

Schema-3 checkpoints record the cap explicitly, as well as input and source
fingerprints. A different cap or source version is rejected before any completed
partition can be reused. Schema-1 and schema-2 checkpoints are historical records and cannot
be resumed by this version. Use a fresh path when expanding the cap:

```bash
python resume_search.py --max-abs-exponent 200 --seconds 400 --per-split-seconds 45 --memory-mib 768 --checkpoint checkpoint_cap200.json
```

Increasing the cap expands the expression space and can sharply increase time
and memory use. A completed negative result applies only to the recorded cap.


### High-cap independent validation

`python -m unittest -v test_large_limits` checks caps 200, 1000 and 2000 against
independent syntax-tree enumeration on `2200`, `2999`, `1234`, and `0000`.
Both reverse implementations (with and without single-digit edge inversion)
are compared with the oracle, with short-interval lookup disabled. The tests
cover 6,381 syntax trees and 3,838 reverse queries, including absent targets.

Separate boundary cases check positive powers, negative powers, and rational
bases at exponents 200 and 1000, as well as rejection immediately below each
bound. Every witness is evaluated with Fraction and checked for digit order.
The independent AST evaluator now accepts an explicit cap and checks every
power node, even when the final value is small. These are correctness tests,
not an extension of the completed nine-digit search domain.


### Checkpoint content validation

Schema 3 validates each partition's input, exponent cap, split number, attempt
count, status, timing and memory fields before it can be skipped. Unknown or
noncanonical split keys, duplicate JSON keys, missing fields, inconsistent
aggregate completion, and contradictory expression/status records are rejected.
An interruption after the last completed partition but before final aggregation
is accepted and finalized without rerunning those partitions.

Fresh worker output is checked before saving; malformed JSON or a status/exit
code mismatch becomes a retryable worker_error, never a completed absence.
The runner passes a canonical Fraction target string to prevent equivalent
spellings such as 14/2 and 7 from being treated as different record targets.

These checks detect malformed records, not forged mathematical evidence. A
structurally valid negative record is still trusted. Do not edit checkpoint
contents by hand.

### Independent production witness verification

`verify_expression.py` parses the fully parenthesized solver grammar directly,
without importing search/DP/root logic, using Python eval, or floating-point
arithmetic. It checks digit order/count, syntax, all integer exponent bounds,
undefined arithmetic, the requested outer split, and exact Fraction equality.
Leading-zero concatenations are supported. It shares Fraction arithmetic with
the solver, so it is not an independent rational-number implementation.

The worker validates every found expression before reporting success, within
its existing wall-time and virtual-memory budget. Invalid witnesses return
worker_error, never a bounded absence. A validation timeout or memory limit is
an incomplete result. Saved found witnesses are re-evaluated in a budgeted
worker before resume can return found; failure leaves the checkpoint unchanged.
The verifier is included in the source fingerprint, invalidating earlier files.

Verify a supplied expression without running the search (Linux):

```bash
python run_search.py --digits 23 --target 8 --verify-expression '(2^3)' --seconds 5 --memory-mib 128
```

Expected: found. Replacing the expression with `(2+3)` returns worker_error and
exit status 2. On the original unverified path that wrong witness could have
been accepted as found. Returned expressions use `^`, not Python's `**` syntax.


### Reproducible profiling without changing checkpoints

```bash
python profile_search.py --split 2 --max-abs-exponent 2000 --seconds 60 --memory-mib 768 > profile_local.json
python -m unittest -v test_profile
```

The profiler launches an isolated Linux worker and enforces wall time and
virtual memory. JSON output includes the exact input, source SHA-256 values,
Python/platform versions, cache statistics, RSS, and every profiled function's
call counts, own time and cumulative time. It does not read or write a search
checkpoint. On timeout it emits timeout and exits 2; a failed worker emits
worker_error. Neither means bounded absence. Completed found witnesses are
independently checked before success.

Profiling adds overhead, so compare ordinary search runtimes separately.
Cumulative times overlap and must not be summed. The saved
profile_split2_cap2000.json is one completed observation of the optimized
solver: 28.694s profiled search / 29.073s including startup and report generation,
peak RSS 206080KiB. Forward DP accounts for 21.137s cumulative; Fraction power
accounts for 13.595s own time across 104101 calls. Remaining optimization should
target forward powers and hashing, not the removed single-digit power scan.

A bounded power-cache experiment is reproducible with
`python measure_power_cache.py --size 128` (Linux, 60s/768MiB).
The raw results in `power_cache_measurements.jsonl` show less than 0.1% reuse
at sizes 128/1024. The cache was not adopted in production; one timing sample
per size does not establish a speedup. See PROGRESS.md for conditions.

`python measure_power_sizes.py` and `python measure_hash_sizes.py` measure
operation cost by numerator/denominator bit length (each 60s/768MiB, Linux).
The committed JSON measurements identify a few huge powers as the main remaining
cost. These scripts do not prune large values or alter the production solver.

`python trace_large_powers.py` identifies the expressions behind the largest
powers under the same 60s/768MiB budget. The saved trace locates all twelve
large events in the right-operand table for `3456789`; see PROGRESS.md for the
planned exact exponent-target search alternative. No pruning was introduced.

### Root-cache experiment (2026-11-01)

`measure_root_cache.py` compares an unwrapped baseline with 1024/16384-entry
LRU caches of exact rational roots, admitting only inputs whose combined
numerator/denominator bit length is at most256. Each isolated run has a30s
alarm and768MiB virtual-memory ceiling. Example:

```bash
python measure_root_cache.py --split 1 --size 1024
python -m unittest -v test_root_cache
```

All18 measurements are in `root_cache_measurements.jsonl` (cap5000, splits1/8,
three runs per size). Caches were not adopted: both cache sizes had slower
median times on both splits. Solver and completed checkpoints remain unchanged.
See PROGRESS.md for numerical results and measurement limitations.


### Exact target-based exponent bound

For a reduced rational target other than0,1,-1, each nonunit absolute numerator
or denominator component c must itself be an integer |e|-th power. Therefore
c >= 2**|e| and |e| <= c.bit_length()-1. Negative exponents swap numerator and
denominator, so the same bound applies. Long exponent-operand queries now use
the minimum of these component bounds and the configured exponent cap. Targets
0,1,-1 keep the full configured range. No intermediate-value pruning is used.
For target10958 at cap5000, this reduces candidate integers from10001 to27
(including zero, subsequently rejected). The exact-root check is still required.

The preceding cap5000 checkpoint is preserved unchanged as
`checkpoint_10958_cap5000_before_exponent_bound.json`; the latest checkpoint
was recomputed with the new source fingerprint. Three paired timing samples per
split were noisy and did not demonstrate a consistent speedup on both splits;
see `exponent_bound_measurements.jsonl` and PROGRESS.md. Reproduce a comparison:

```bash
python measure_exponent_bound.py --split 1 --unbounded-candidates
python measure_exponent_bound.py --split 1
```

Both commands retain the per-node exponent cap5000; the first disables only
the mathematical target-based candidate bound, not the configured search limit.
