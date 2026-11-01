# Search improvement log

## 2026-10-30 — bounded execution and memoization

Starting point: PR #1, commit `37416f7688c1d0af1ad5fdfa35a4b11009017f45`.
At inspection, PR #1 was open and main was still
`c036d134e49d582619fe08761165f3f9b550d828`.

### Changes

- Answer single-digit targets before memoization; these mostly unsuccessful
  queries previously occupied an unbounded cache.
- Limit other reverse-search cache entries to 50,000. This evicts saved results,
  not mathematical candidates.
- Look up power bases in the already-generated left DP table instead of
  recursively solving that same interval again.
- Add a Linux subprocess runner with wall-time and address-space budgets and
  explicit JSON statuses. No new exponent or value pruning was added.
- Add tests for cache behavior, runner success, bounded absence, timeout, and
  invalid arguments. Existing exact witness checks remain in place.

### Measurements

Environment: Linux x86_64, CPython 3.12.14. One fresh process per measurement,
768 MiB `RLIMIT_AS`, 60-second subprocess timeout. Same original four tests
before and after the solver changes, without the new runner/cache tests:

| Revision | Wall time (s) | Peak child RSS (KiB) |
| --- | ---: | ---: |
| Starting commit | 12.454 | 364332 |
| Optimized solver | 7.487 | 39080 |

Both passed. These are single-run observations, not a statistical benchmark.
Time includes process startup; RSS comes from `RUSAGE_CHILDREN.ru_maxrss`.
The complete expanded suite passed: 9 tests in 7.791 seconds.

Reproduce the current measurement from the repository root:

```python
import resource
import subprocess
import sys
import time

resource.setrlimit(resource.RLIMIT_AS, (768 * 1024**2, 768 * 1024**2))
started = time.perf_counter()
result = subprocess.run([sys.executable, '-m', 'unittest', '-q'], timeout=60)
print(result.returncode, time.perf_counter() - started,
      resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
```

The command now includes the five additional tests, so its runtime is not
directly comparable with the four-test table without selecting the same tests.

### 10958 attempt

```bash
python run_search.py --digits 123456789 --target 10958 --seconds 20 --memory-mib 512
```

Actual output:

```json
{"digits":"123456789","elapsed_seconds":20.025787,"expression":null,"max_abs_exponent":100,"memory_budget_mib":512,"status":"timeout","target":"10958","time_budget_seconds":20.0}
```

Exit status 2. No witness was returned, and the search did not finish.
This is neither a completed bounded negative result nor an impossibility proof.

Additional memory-limit check: `python run_search.py --seconds 10 --memory-mib 64`
returned `memory_limit` (exit 2) in 1.043795 seconds, with peak worker RSS
35,492 KiB. The budget is virtual address space, so RSS can be below 64 MiB
when the limit is reached. Default validation also passed for 123 (35 values),
1234 (261), and 12345 (2,453).

### Next work

1. Profile which interval tables dominate the budgeted nine-digit search;
   avoid increasing runtime budgets without measuring the bottleneck.
2. Add deterministic work partitioning and atomic, versioned checkpoints so
   interrupted searches can resume without repeating completed partitions.
3. Extend independent small-space oracle coverage (current DP/reverse comparison
   shares the same operation rules, while witness evaluation is independent).

Remaining limits: exponent absolute value <= 100; no checkpoint/resume yet;
full DP tables can still exhaust the process memory budget. The runner's memory
enforcement is Linux-only. No paid compute was used.


## 2026-10-30 — partition checkpoints and hybrid lookup

Starting commit: `ccfaab098bd90ba6270c092a4e7f1909365f599b`.

- Added `root_split` to constrain only the top-level split; recursive intervals
  retain all permitted splits. The union of all partitions plus concatenation
  covers the same bounded expression space.
- Added short-interval DP lookup (default <=4 digits) and balanced split order.
  Existing witness tests explicitly disable lookup to keep exercising reverse
  search, rather than silently comparing DP to itself.
- Added `resume_search.py`: atomic JSON replacement, exclusive process lock,
  input/code fingerprint validation, completed-partition skipping, and retry of
  unfinished partitions. No inside-partition continuation is claimed.
- 14 tests passed in 11.788s. New tests cover partition unions, independent exact
  witness values and digit order, checkpoint round trips, version mismatch,
  retry/skip semantics, and a real subprocess resume. This timing is not directly
  comparable with the historical four-test benchmark above.

### First partition pass

180-second total allocation, at most 20s per split, 512 MiB virtual-memory cap.
Completed splits 3,4,5,6,7 without a witness. Splits 1 and 2 timed out; split 8
hit the memory cap. A second pass used 180s total / 60s per split / 768 MiB,
reusing the checkpoint and skipping the five completed splits.

### Profiling observation

A separate 10-second cProfile sample of split 2 (512 MiB, interrupted by a
signal timer) recorded about 22.17 million calls. Fraction arithmetic wrappers
accounted for 3.476s cumulative, equality 1.882s, and full_dp 1.609s. Cumulative
times overlap and must not be summed. The profiler and one search worker ran
concurrently, so these are bottleneck observations, not clean speed benchmarks.

### Next priority

Avoid constructing an eight-digit forward table when one side of a top-level
split is only one digit. Explore reversing from the smaller side and exact
integer-exponent inversion; verify the new path against the existing reverse
solver on small inputs before using any prior negative results. Source changes
invalidate the checkpoint fingerprint and require a fresh checkpoint.

Reproduction:

```bash
python -m unittest -v
python resume_search.py --seconds 180 --per-split-seconds 60 --memory-mib 768 --checkpoint checkpoint_10958.json
```

The checkpoint is committed with the code so a later worker can resume it.
Only `not_found_bounded` partitions are skipped; an interrupted partition restarts.

### Saved second-pass result

| Split | Status | Attempts | Latest seconds |
| ---: | --- | ---: | ---: |
| 1 | timeout | 2 | 60.098 |
| 2 | not_found_bounded | 2 | 21.700 |
| 3 | not_found_bounded | 1 | 9.113 |
| 4 | not_found_bounded | 1 | 4.687 |
| 5 | not_found_bounded | 1 | 0.126 |
| 6 | not_found_bounded | 1 | 0.626 |
| 7 | not_found_bounded | 1 | 8.135 |
| 8 | memory_limit | 2 | 38.969 |

Overall: **incomplete**, no witness. Six splits (2 through 7) completed under the exponent bound; split 1 timed out and split 8 exceeded memory. This is not an impossibility proof.


## 2026-10-30 — invert single-digit edge operands

Starting commit: `f9100f21d8e041238195a947d61465279e8b536d`.
The remote head and local tracked file blob hashes were checked before editing;
PR #1 remained open and main unchanged.

### Changes and completeness within the cap

- For a single right digit b, solve the left targets T-b, T+b, T/b and T*b
  for +,-,*,/ respectively. Handle b=0 separately. For exponentiation, use
  exact roots and both signs for even b; zero exponent requires a nonzero base.
  No large left DP table is built for this split.
- For a single left digit a, check each integer exponent in the complete
  existing [-100,100] range and recursively construct only exponents for which
  a**b equals the exact target. Exclude zero to nonpositive powers. This avoids
  generating the entire right exponent table.
- Both paths recurse on strictly shorter intervals; other splits retain the
  existing algorithm. `edge_inversion=False` preserves the prior path for tests.
- The all-zero-base special case is exact under these rules: an all-zero string
  cannot produce a nonzero value when 0^0, negative powers of zero and division
  by zero are excluded; a string with any nonzero digit has a nonzero concat.

### Tests and checkpoint handling

15 tests passed in 55.833 seconds, under a 120s timeout and 768 MiB address-space
budget. The new differential test compares both edge splits, with short-table
lookup disabled, against the prior reverse implementation for all 64 strings
of length 3 over 0..3 and 1234,12345,2300,2331. It tests every forward value plus
sample negative targets, and independently evaluates returned expressions and
checks digit order. Existing tests continue to exercise the old reverse path.

The old checkpoint correctly failed the changed-source fingerprint check. It
is archived as `checkpoint_10958_before_edges.json`; the new checkpoint is
computed from scratch, without copying completed statuses from the old solver.

Search command (maximum 300s allocated, 45s per partition, 768 MiB per child):

```bash
python resume_search.py --seconds 300 --per-split-seconds 45 --memory-mib 768 --checkpoint checkpoint_10958.json
```

### Completed partition result

| Split | Status | Seconds | Peak RSS (KiB) |
| ---: | --- | ---: | ---: |
| 1 | not_found_bounded | 7.743 | 41888 |
| 2 | not_found_bounded | 8.442 | 163356 |
| 3 | not_found_bounded | 1.930 | 31692 |
| 4 | not_found_bounded | 1.011 | 17716 |
| 5 | not_found_bounded | 0.070 | 14444 |
| 6 | not_found_bounded | 0.609 | 23164 |
| 7 | not_found_bounded | 6.072 | 93100 |
| 8 | not_found_bounded | 5.666 | 36972 |

All eight partitions completed, with no expression found in the current bounded search. The sum of recorded worker wall times was 31.543464s; highest child RSS was 163,356 KiB. These are single-run observations. The completed checkpoint was resumed with subprocess launching mocked, confirming all eight partitions were skipped.

This is a completed negative result for the implemented integer-exponent domain [-100,100], not a proof for unrestricted powers. Next: strengthen independent small-space oracle coverage, then expose and validate configurable exponent limits before expanding the domain.

Cross-check: the unpartitioned runner also completed with `not_found_bounded` in 25.253217s, peak RSS 247,324 KiB, using a 60s/768MiB budget. Raw output is in `result_10958_unpartitioned.json`. It uses the same solver, so it checks partition orchestration but is not an independent proof of the solver.


## 2026-10-30 — independent syntax-tree oracle

Starting commit: `25c389a0ed16c9db9b33972219c65aa694c15ff0`.
PR #1 was open and unchanged. Local source, README, progress log and checkpoint
blob hashes matched the remote tree before editing.

Added `test_oracle.py`. Unlike the production interval DP, this oracle first
chooses all token boundaries, then all binary expression trees and operators.
It does not use production arithmetic-selection/root functions, memoization or
intermediate value deduplication. It still shares Python Fraction arithmetic;
that dependency is not an independent rational-arithmetic implementation.

Measured exhaustive validation (Linux, 120s timeout / 768MiB address-space cap):

- 256 inputs: every four-digit string over 0,1,2,3.
- 168,288 valid expression trees before final value deduplication.
- 21,359 distinct values summed separately for each input.
- 24,147 reverse queries, including absent half-integer targets.
- Forward value sets matched exactly; reverse membership matched the oracle;
  all returned witnesses evaluated exactly and preserved the input digit order.
- The exhaustive test passed in 16.824 seconds.

A second test checked hand-calculated 23/00/20 value sets and inclusion/exclusion
at positive and negative exponent limits 100/101; it passed in 0.001 seconds.
The earlier 15 tests were not rerun because their code and all solver/runner
files were unchanged. There are now 17 discoverable test methods.

The existing nine-digit checkpoint fingerprint was verified and is compatible.
Its eight completed partitions were retained; the completed search was not
repeated. Result remains **not_found_bounded** for integer exponents -100..100.
No claim is made for unrestricted exponents.

Next: make the exponent cap an explicit solver/CLI/checkpoint parameter, test
nondefault caps (especially 0 and boundaries), then budget an expanded search.
Do not modify the constant in place and silently reuse a completed checkpoint.


## 2026-10-30 — explicit exponent limits and checkpoint schema 2

Starting commit: `217ff9aa046205e8c0196a059cb21cd49b7fcb20`.
PR #1 remained open, with the previous head unchanged.

- Added nonnegative integer `max_abs_exponent` to make_solver, retaining default
  100. Every forward/reverse path captures the per-solver value, including both
  single-digit edge optimizations. Booleans, nonintegers and negative API caps
  are rejected; both CLIs reject negative caps.
- Added `--max-abs-exponent` to both runners, propagated it to worker processes,
  and report the actual selected cap in result JSON.
- Schema 2 checkpoint identity now includes the cap explicitly, together with
  the source fingerprint. Mismatched caps cannot reuse completed partitions.
- Kept cap zero meaningful: nonzero A^0 is allowed, rather than disabling powers.

Validation: all 21 tests passed in 69.015s with a 180s timeout and 768MiB
address-space budget. New tests compare caps 0,1,2,3 with the independent oracle
for 64 three-digit strings each (256 input/cap pairs), positive 100/101 and
negative 1/2 boundaries, cap-zero behavior, API validation, checkpoint mismatch,
and propagation through both CLIs. An extra assertion of the exact `(2^101)`
witness was subsequently added; the affected boundary test passed in 0.001s.

The old completed cap-100 checkpoint was rejected by the new source/schema
check and archived as `checkpoint_10958_cap100_schema1.json`. No completion
flags were copied forward. The expanded domains were freshly enumerated.

First expanded run:

```bash
python resume_search.py --max-abs-exponent 200 --seconds 400 --per-split-seconds 45 --memory-mib 768 --checkpoint checkpoint_10958.json
```

All eight partitions completed with `not_found_bounded`. That complete result
was retained as `checkpoint_10958_cap200.json` before starting the next domain:

```bash
python resume_search.py --max-abs-exponent 1000 --seconds 180 --per-split-seconds 20 --memory-mib 768 --checkpoint checkpoint_10958.json
```

The two total search allocations sum to 580 seconds, below the 600-second run
budget, and each child is capped at 768MiB of virtual address space. Actual
worker wall times and final statuses follow below. These are single observations,
not statistically controlled performance comparisons.

### Expanded-domain results

| Cap | Completed partitions | Sum of worker seconds | Peak RSS (KiB) |
| ---: | ---: | ---: | ---: |
| 200 | 8/8 | 28.843495 | 163916 |
| 1000 | 8/8 | 55.789549 | 171380 |

Both domains completed with **not_found_bounded**; no witness was returned. The cap-1000 checkpoint rejects the default cap 100 and skips all completed partitions when resumed with cap 1000 (verified without launching workers). There is still no claim about unrestricted integer powers or rational exponents.

Next: add independent cap-200/1000 small-space tests and strengthen checkpoint record validation; then assess further expansion with measured budgets instead of assuming completeness beyond the cap.


## 2026-10-30 — independent high-cap validation

Starting commit: `d4d23fe72f0d21dae465bb758494eed6b00a5d2a`. PR #1 remained
open and unmerged; main remained `c036d134e49d582619fe08761165f3f9b550d828`.
All local tracked source, test, documentation and checkpoint files matched
remote blob hashes before editing.

Added `test_large_limits.py` and parameterized the independent AST witness
evaluator's exponent limit (default unchanged). At caps 200 and 1000, the
independent tokenization/tree oracle enumerates 4,251 valid expressions across
eight input/cap pairs, then checks 2,558 reverse queries against both edge
inversion implementations with short-interval lookup disabled. Inputs are
2200, 2999, 1234 and 0000; 2999 exercises an exponent above 200. Exact value
and digit order are checked for oracle expressions and returned witnesses.

Additional cases exercise 2^N, 2^(0-N), and (1/2)^N at N=200 and N=1000,
with a restricted outer split; both reverse paths succeed at N and reject
the target at cap N-1. Evaluator tests check every power node even when
large powers cancel to zero, and reject 0^0, zero negative powers and
fractional exponents. No production search rules were changed.

Focused measurement: Linux/CPython 3.12, one process, 180s timeout and 768MiB
RLIMIT_AS. Three new tests passed in 7.795s (7.885562s including startup);
peak child RSS was 19,024KiB. Single-run measurements only.

Reproduce the new tests with `python -m unittest -v test_large_limits`;
run the entire suite with `python -m unittest -q`. Apply the resource/timeout
wrapper from the first log entry, changing timeout to 180 seconds.

The cap-1000 checkpoint's identity remains compatible. A mocked subprocess
that raises on any launch confirmed all eight partitions are skipped; the
checkpoint remained byte-identical. No nine-digit search was rerun, and no
new nine-digit timing or expanded absence claim is made. The result remains
**not_found_bounded for integer exponents -1000..1000**, not unrestricted
impossibility. No paid resources were used.

### Reproduced follow-up: checkpoint record validation

A temporary synthetic checkpoint with correct identity and partition
`{"1": {"status": "not_found_bounded"}}` was accepted by `load`, despite
missing digits, target, cap, root_split and attempts. This was a temporary
fixture, not an edit to the real checkpoint. Source fingerprints guard
version mismatch but do not validate each record's content or authenticate
a negative result. Existing real records contain those fields.

Next priority: reject malformed/contradictory checkpoint records and verify
found witnesses independently, with corruption tests. Changes to resume_search
will invalidate the source fingerprint: archive the current checkpoint and
perform a fresh budgeted run, rather than rewriting hashes or copying statuses.
Then profile larger exponent caps before choosing another bounded expansion.

Full-suite verification after the evaluator change: **24 tests passed in
78.795s**, 78.899774s including startup, peak child RSS 62,908KiB, with a
180s timeout and 768MiB RLIMIT_AS. This includes all earlier regressions,
CLI/timeout/resume tests, exhaustive small-space oracle and new high-cap tests.


## 2026-10-30 — validate checkpoint records before reuse

Starting commit: cf9871357c3867f91ce87d2a95af94001186eb37; PR #1 remained
open and main unchanged. Continued the locally staged work after an interrupted
session; its full-suite process result was unavailable, so it is not counted
as a successful run and the final suite was started again.

Fixed the reproduced acceptance of a completion-only partition record. Schema
3 validates required input/cap/split/attempt/timing/memory/status fields, rejects
duplicate JSON keys and noncanonical split keys, and checks aggregate completion
against all partitions. An incomplete aggregate with all partitions done is
allowed for crash recovery and finalized without worker launches. Worker JSON
is checked before persistence, including status/exit-code consistency; invalid
output becomes retryable worker_error. Equivalent rational target strings are
canonicalized before passing them to the subprocess.

Added five corruption/recovery test methods, and updated the existing mocked
retry test to use realistic worker metadata/exit codes. Coverage includes missing
fields, wrong types/inputs, non-finite timings, unknown statuses, duplicate keys,
contradictory completion, found record presence/digit checks, malformed worker
output, exit-code mismatch, and canonical rational targets.

The old cap-1000 checkpoint correctly failed the new source/schema identity
check and was archived unchanged as checkpoint_10958_cap1000_schema2.json.
No status or hash was copied to the new checkpoint. Previous cap-200 and
cap-100 files also remain historical records.

Remaining limitation: structural validation does not independently prove a
negative result or evaluate a found witness's value. Tests evaluate witnesses
exactly; production witness verification in a budgeted subprocess is next.
Then profile larger exponent caps and assess expansion within fixed budgets.

Final verification: 29 tests passed in 83.470 seconds (83.591125 seconds
including startup), peak child RSS 62,784KiB. Linux, Python 3.12, single
measurement, 180s timeout / 768MiB RLIMIT_AS. Reproduce with
`python -m unittest -q` under the resource wrapper documented above.

Fresh schema-3 search command (180s total, 30s per split, 768MiB per worker):

```bash
python resume_search.py --max-abs-exponent 1000 --seconds 180 --per-split-seconds 30 --memory-mib 768 --checkpoint checkpoint_10958.json
```

Fresh result: all eight partitions completed with not_found_bounded at
cap 1000. Sum of worker wall times: 62.662792s; peak child RSS: 171,492KiB.
Single observation, no simultaneous full-suite run. All attempts=1. A mocked
subprocess launch guard confirmed subsequent resume skips all eight partitions;
the checkpoint stayed byte-identical. This is bounded absence only, not proof
for unrestricted integer exponents. Total nine-digit allocation was 180s, below
the 600s run limit; no paid compute used.


## 2026-10-31 — independent production witness verification

Starting commit: 641e1c3f40a893b0c1a8bda85054aebe05fabfaf. PR #1 is still
open; main remains c036d134e49d582619fe08761165f3f9b550d828.

Added verify_expression.py: a direct parser for digit literals and fully
parenthesized binary operations, with exact Fraction evaluation. It shares
no search/root/DP routines and uses neither eval nor floating-point arithmetic.
It checks digit order/count, syntax, each exponent's integer/cap constraints,
division/zero-power exclusions, the requested root split and final target.

Every newly found expression is verified inside the existing bounded worker;
verification errors are worker_error, not not_found_bounded. Verification-only
CLI mode reuses the same timeout and RLIMIT_AS enforcement. Saved found results
are re-evaluated using that mode before resume returns success. Failed resume
verification preserves the saved file. The source fingerprint now also covers
the verifier module, so previous source versions are explicitly incompatible.

New tests inject a wrong solver witness, alter a structurally valid saved
witness's value, check independent evaluation against small forward witness
sets, rational/negative bases, high exponent 2000, digit/syntax/cap violations,
undefined arithmetic, and a real verification timeout. Focused 19-test run
passed in 1.313s. Reproduce: python -m unittest -v test_verifier.

Remaining limits: negative checkpoint flags are structurally checked rather
than mathematically certified; Fraction is shared by both evaluators; unfinished
partitions still restart. No unrestricted-exponent impossibility claim is made.

Full verification: 34 tests passed in 93.932s (94.097123s including startup),
peak child RSS 61,208KiB. Linux/CPython 3.12, one run, 180s timeout and
768MiB RLIMIT_AS. Tests finished before the performance measurement.

The cap-1000 checkpoint was rejected for source mismatch and archived unchanged
as checkpoint_10958_cap1000_before_verifier.json. Expanded search uses a fresh
checkpoint at cap 2000; no completion flags or source hashes were reused.

```bash
python resume_search.py --max-abs-exponent 2000 --seconds 240 --per-split-seconds 45 --memory-mib 768 --checkpoint checkpoint_10958.json
```

Total nine-digit search allocation is 240s, within the 600s limit. Each child
has a 768MiB virtual-memory cap. No paid resources are used.

Cap-2000 result: **all 8/8 partitions completed, not_found_bounded**.
Sum of worker wall times 146.637999s; maximum child RSS 202,888KiB.
All partitions required one attempt. Split 2 was the slowest at 42.440850s,
close to the 45s per-partition allowance; split 1 took 38.486115s.
This is one measurement, not a controlled benchmark against the prior run.
Subsequent resume was checked with worker launching forbidden; all partitions
were skipped and checkpoint bytes remained unchanged. No expression was found
under integer exponents -2000..2000; unrestricted powers remain unresolved.

Next: profile split 2 and the single-digit exponent path at cap 2000 before
increasing the cap again. Avoid assuming that the same 45s partition budget
will suffice for a larger domain. Retain the new completed checkpoint unless
source changes invalidate it; never rewrite fingerprints to reuse old results.


## 2026-10-31: cap-2000 regression and split-2 profile

Extended all three LargeExponentTests to caps 200, 1000, and 2000, retaining the earlier caps. Run: python -m unittest -q test_large_limits. All 3 tests passed in 23.740 seconds; 6,381 independently enumerated trees and 3,838 reverse queries. Includes positive/negative exponent and rational-base boundaries and internal-node evaluator bounds. The full suite was not rerun for this test-only extension.

Profiled source c03a84b7b60ba690ba957ec78d9529367bdbb599 using cProfile, digits 123456789, target Fraction(10958), root_split=2, max_abs_exponent=2000, default lookup and edge inversion. Linux address-space limit 768 MiB and external timeout 180 seconds. Result None (bounded absence), 59.222 seconds including profiler overhead. Single measurement; regression tests ran concurrently during part of the profile, so this is not a standalone wall-time benchmark.

127,471,503 calls: Fraction.__pow__ 7,565,966 calls, 27.249 seconds own time / 33.592 cumulative; cached_can_make 5.008 own / 59.221 cumulative; Fraction.__eq__ 17,032,868 calls, 4.080 own; full_dp 20.582 cumulative. Cumulative times overlap and must not be added. Fraction power own time is about 46% of total profile time. This supports investigating repeated exponent evaluation first; it does not establish a speedup or prove all calls originate in the single-digit scan. No production solver change or checkpoint change was made.

Reproduction (repository root, Linux):

```bash
timeout 180 python - <<'PY'
import cProfile, pstats, resource
from fractions import Fraction
from search import make_solver
resource.setrlimit(resource.RLIMIT_AS, (805306368, 805306368))
p = cProfile.Profile()
p.enable()
f, r = make_solver('123456789', root_split=2, max_abs_exponent=2000)
result = r(0, 9, Fraction(10958))
p.disable()
print('result', result)
pstats.Stats(p).strip_dirs().sort_stats('tottime').print_stats(15)
PY
```


## 2026-10-31 — invert digit powers without a linear power scan

Started from c7522897817a0be8ccccf4c70d4037ac9d24eb2a. Incorporated the
new remote test_large_limits.py and PROGRESS.md before editing; all other
local tracked files matched the remote tree. The cap-2000 regression/profile
work above is retained, not overwritten.

A 10s isolated cProfile sample (768MiB) confirmed Fraction.__pow__ as the
largest own-time entry: 1,816,144 calls, 3.571s own / 5.201s cumulative.
The sample was deliberately interrupted and is not a complete search result.
The existing full profile above independently supports the same bottleneck.

For a digit base 2..9, positive integer powers are strictly increasing and
negative powers are their reciprocals. A positive rational target must therefore
be an integer or reciprocal integer. Repeated divmod by the base yields the
unique exponent or rejects a nonpower, stopping at the existing exponent cap.
No logarithms, approximate roots, new pruning bounds or excluded expressions
are introduced. Base 0 retains every positive exponent for target 0; base 1
retains the entire bounded exponent range for target 1.

Added exhaustive direct-power comparison for all ten digit bases, caps
0/1/2/7/20 and rational/nonpositive targets, plus exact powers and neighboring
nonpowers at exponents 100/1000/2000 with reciprocal and cap-boundary cases.
The existing independent oracle and both reverse implementations remain tested.

Before-change split-2 standalone measurement: 39.076633s, peak RSS 203028KiB,
not_found_bounded. Command: python run_search.py --split 2
--max-abs-exponent 2000 --seconds 60 --memory-mib 768.
One process per measurement, Linux/Python 3.12, no concurrent test/search load.

The old cap-2000 checkpoint was rejected by the changed source fingerprint and
archived unchanged as checkpoint_10958_cap2000_before_digit_inverse.json.
No completion flag or fingerprint was reused. Fresh full-domain search follows
tests, with cap 2000 / total 240s / per-split 45s / 768MiB.

Validation: all 36 tests passed in 37.364s (37.470502s including startup),
peak child RSS 62,896KiB; 180s timeout and 768MiB RLIMIT_AS.
The retained cap-2000 oracle checked 6,381 trees and 3,838 reverse queries.

Fresh cap-2000 search: all 8/8 partitions not_found_bounded, one attempt each.
Sum of worker wall times 42.278727s, peak child RSS 202,908KiB.
The earlier full search took 146.637999s; these are single-run observations,
not a repeated statistical benchmark. For split 2 in this session, standalone
before-change time was 39.076633s versus 20.940156s in the new partition run
(about 46% lower). Both use the same input/cap/768MiB and no profiler; timeout
allowances differ (60s before, 45s after) and neither expired. RSS stayed near
203,000KiB. The change targets CPU work, not DP-table memory.

Completed-checkpoint resume skipped all workers and retained identical bytes.
Search allocations: 10s profile + 60s baseline + 240s new full search = 310s,
below 600s; tests additionally used a 180s timeout. No paid resources.
Result remains bounded absence for integer exponents -2000..2000; there is no
claim for unrestricted exponents. Reproduce the full run using a fresh path:

```bash
python resume_search.py --max-abs-exponent 2000 --seconds 240 --per-split-seconds 45 --memory-mib 768 --checkpoint checkpoint_fresh.json
```

Next: profile the remaining split-2 forward-DP/power work, which still dominates
the full search, before choosing a further cap expansion. Preserve current
completed partitions unless the source fingerprint changes.


## 2026-10-31 — reusable isolated profiler and remaining DP bottleneck

Starting head d9d5f605e7136412611e3f7ece277f44c34434f2, PR #1 open,
main unchanged. Added profile_search.py, a separate parent/worker profiler
with wall-time timeout and RLIMIT_AS, canonical rational inputs and source
fingerprints. JSON reports contain all function counts/times, forward/reverse
cache statistics, platform/Python, elapsed time and peak RSS. No production
solver/runner/verifier file changed and no checkpoint was invalidated.

Reproduce:

```bash
python profile_search.py --split 2 --max-abs-exponent 2000 --seconds 60 --memory-mib 768 > profile_local.json
python -m unittest -v test_profile
```

Actual report is committed as profile_split2_cap2000.json. Linux, CPython
3.12.14, 60s timeout, 768MiB virtual-memory limit, no concurrent tests/search.
Status not_found_bounded for this partition, 28.693807s inside cProfile,
29.073107s parent wall time, maximum child RSS 206080KiB. 37,811,044 total
calls / 36,571,857 primitive calls. Function times are profiler-affected:

| Function | Calls | Own seconds | Cumulative seconds |
| --- | ---: | ---: | ---: |
| Fraction.__pow__ | 104101 | 13.594647 | 13.720424 |
| Fraction.__hash__ | 2287050 | 2.220866 | 5.969380 |
| full_dp | 31 | 0.738626 | 21.137289 |

Cumulative times overlap. Compared with the earlier profile's 7,565,966 power
calls, this confirms the digit inversion removed most calls, but remaining
forward DP powers still account for about 47% of profiled search own time.
Different timing conditions mean this is not a controlled speedup benchmark.
The forward table cache had 31 misses and 1,244,866 hits; reverse cache had
1866 misses and 455 hits, below its 50,000-entry limit. Raising that limit
is therefore not supported by this measurement.

Three new test methods passed in 0.541s: verified found expression, canonical
target/bounded absence, real timeout, and invalid budgets/splits/caps. There
are now 39 discoverable tests; the previous 36 were not rerun because their
code and production dependencies are unchanged. A mocked launch guard verified
all eight saved partitions are skipped on resume and checkpoint bytes remain
identical. Full-domain result remains bounded absence at -2000..2000, with no
new full-domain search or unrestricted impossibility claim.

Next: measure whether duplicate forward power inputs justify a small bounded
cache, including retained big-integer memory, before changing search.py. Keep
exact Fraction results and domain unchanged; reject any optimization that
regresses independent oracle tests or materially increases memory.

## 2026-10-31 — bounded power-cache experiment

Head fafd60c2e436806be1e48dba3f55565e1808c9c7 was unchanged. Added
measure_power_cache.py as an isolated experiment, not production integration.
It wraps Fraction.__pow__ with an LRU inside its process, restores it on exit,
and enforces 60s via SIGALRM and 768MiB RLIMIT_AS. Run each size in a fresh
Linux/Python 3.12 process, sequentially, without profiler or concurrent load:

```
python measure_power_cache.py --size 0
python measure_power_cache.py --size 128
python measure_power_cache.py --size 1024
```

Raw output: power_cache_measurements.jsonl. All use digits 123456789, target
10958, split 2, cap 2000; all completed not_found_bounded.

| Entries | Seconds | RSS KiB | Hits | Misses |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 21.890750 | 201456 | 0 | 104101 |
| 128 | 21.457452 | 201096 | 11 | 104090 |
| 1024 | 20.698751 | 201180 | 104 | 103997 |

Each is one observation. Hit rates are only 0.011% and 0.100%; timing differences
are not sufficient evidence of a reliable speedup. Do not adopt the cache on
this evidence. Size zero still uses a wrapper, so it is not a pristine baseline.
RSS includes solver tables and is not retained-cache size. No new correctness
claim is derived from these experiments; production files and the completed
checkpoint remain unchanged. The full suite was not rerun. Total measurement
allocation was 180 seconds and no paid compute was used.

Next: investigate the cost of individual large exact powers and Fraction hashing,
without adding numeric pruning or claiming unrestricted impossibility. A broader
cache is not justified by these low reuse rates.

## 2026-10-31 — power/hash cost by integer size

Starting head da11cb32744a117c76bb8ae107292385ef647a92 unchanged.
Added isolated measurement scripts measure_power_sizes.py and
measure_hash_sizes.py. Run each with Python from the repository root; each
has 60s SIGALRM and 768MiB RLIMIT_AS. They temporarily wrap Fraction methods,
restore them in finally, and group timings by the next power of two above
numerator.bit_length()+denominator.bit_length(). No solver edits or pruning.

Sequential fresh Linux/Python 3.12 processes, split 2, cap 2000, exact target
10958 and digits 123456789. Both returned not_found_bounded. Raw output is
power_size_measurement.json and hash_size_measurement.json.

Power run: 21.029363s wall, RSS 200528KiB; 104101 calls, measured method time
13.934224s. Only 12 calls producing more than 4,194,304 total bits consumed
8.700568s (62.4% of measured power time). Maximum output size was 9,903,557
bits. Thus the remaining power cost is concentrated in a few very large
results rather than widespread repeated small powers.

Hash run: 22.387748s wall, RSS 200528KiB; 2287050 calls, measured method time
3.454187s. The 12 hashes above the same threshold consumed only 0.006673s.
Hashing remains aggregate overhead, but huge-power generation is the first
priority. Instrumentation overhead and one observation per method prevent
statistical speedup claims. Full suite not rerun: production unchanged.

Next: identify the digit intervals and expression structures producing those
12 large powers, then investigate exact target-directed alternatives to their
forward enumeration. Do not truncate values by bit length: small final targets
can require large intermediate values. Existing full-domain cap-2000 checkpoint
remains valid; no full-domain re-execution or unrestricted impossibility claim.
Total measurement allocation 120s, no paid resources.

## 2026-10-31 — traced the twelve giant powers

Starting head 68370e90071121f599ed735b0f9dfe4a979f92ee was unchanged.
Added trace_large_powers.py, derived from the bounded power-size measurement.
It inspects the immediate caller only after a result exceeds 4194304 bits,
records interval/split and the solver's operand expressions, and discards the
frame reference immediately. No large integers are serialized. Run:

```
python trace_large_powers.py > large_power_trace.json
```

Actual sequential isolated run: 21.826111s, not_found_bounded for split 2,
cap 2000, 60s SIGALRM / 768MiB RLIMIT_AS. All 12 events occur in full_dp(2,9),
i.e. the right substring 3456789. All start from 3^(4^5), where 4^5=1024,
then form nested powers. Largest example: (((3^(4^5))^678)^9), with numerator
plus denominator bit length 9,903,557. Every individual exponent is within
cap 2000; flattening the powers and applying the cap to the combined exponent
would incorrectly change the allowed expression space.

The root split 12 | 3456789 currently builds the entire right DP table for
exponentiation, then filters it to bounded integer exponents. That creates
these giant values even though none can serve as an exponent within the cap.
Do not globally discard large intermediate values: cancellation can need them.

Next concrete experiment: replace only the outer exponent-operand enumeration
with target-directed queries for integers -cap..cap, keeping recursive operand
construction exact. Compare runtime/memory with the current table strategy;
small caps/short intervals may still favor DP. Validate both strategies against
independent oracle sets, zero/negative/rational boundary cases and all root
partitions before adopting. Current production code/checkpoint unchanged;
no new full-domain run or impossibility claim. Raw trace committed for review.

## 2026-10-31 — target-directed exponent operands adopted

Started from df417a480be5468e94f8c2e87143c58533ad8824; remote PR #1 was
open and unchanged. Local tracked blobs matched remote before editing.
For right operands longer than four digits, reverse search now checks bounded
integer exponents against the target's exact rational roots and the left DP
first, then recursively asks whether the right interval can make that exponent.
Short operands retain table enumeration. `exponent_lookup_digits=0` forces
queries in tests; 99 forces the old strategy. Zero exponents require any nonzero
left base; negative exponents invert nonzero targets; even powers check both
base signs. Each recursive operand is strictly shorter. No intermediate value
is discarded and nested powers retain the per-node exponent bound.

Validation: `python -m unittest -q` passed 40 tests in 40.129s (40.287801s
including startup), under a 180s subprocess deadline and 768MiB RLIMIT_AS.
New independent partition oracle covers all 27 three-digit strings over 012,
plus 1234/2200/2999, caps 0/3/10, every root split, both forced exponent
strategies, reachable values and sampled half-integer misses. Returned witnesses
are independently evaluated and digit-order checked. Existing high-cap oracle,
zero/negative/rational boundaries, runner and checkpoint tests also passed.
Only an explanatory source comment changed after the test run.

The old checkpoint was explicitly rejected with input/version mismatch, then
archived byte-for-byte as checkpoint_10958_cap2000_before_exponent_queries.json.
A fresh run used:

```
python resume_search.py --max-abs-exponent 2000 --seconds 240 --per-split-seconds 45 --memory-mib 768 --checkpoint checkpoint_10958.json
```

All eight partitions completed, attempts=1 each, not_found_bounded. Worker times
sum to 23.423295s versus previous 42.278727s; peak RSS 111756KiB versus
202908KiB. Split 2: 3.186169s / 20104KiB versus 20.940156s / 202908KiB.
These are single runs, not statistical benchmarks. Full per-partition results
and source fingerprint are in the new checkpoint. Total search allocation240s,
per-child virtual memory768MiB, no paid resources. A resume with subprocess.run
patched to fail if called completed with byte-identical checkpoint: no completed
partition was recomputed. No expression found for exponents within +/-2000;
this does not establish impossibility for unrestricted integer exponents.

Next: profile split 7 (now 6.506190s / 111756KiB) and improve its remaining
forward-table cost without magnitude pruning. Add high-cap forced-query
partition tests before widening the exponent domain further. Existing profiling
JSON remains historical and records its own old source hashes. No automation
was changed.

## 2026-11-01 — exact inversion of short right operands

Started at b3755ed7dc7f35104d815ef22859ab7729c6abc2; PR #1 open,
head unchanged, all existing local tracked blobs matched the remote tree.
Read README, prior progress and active checkpoint before changing production.

Split 7 before-change profile: 14.651911s including profiler overhead,
30,948,932 calls, RSS115068KiB. Fraction hashing had 1,918,316 calls;
full_dp cumulative time6.183327s. The large left operand table was built
before trying the short right operand. Added exact inversion for right operands
of at most two digits when shorter than the left. Arithmetic is inverted for
each right value; integer powers use exact roots, reciprocals for negative
exponents, both signs for even powers, and a nonzero concatenation for exponent
zero. Zero multiplication and undefined operations are handled explicitly.
No forward value pruning or altered exponent bound. Recursive intervals shrink.
`right_inversion_digits=0` disables this path for differential testing.

Validation: 42 tests passed in110.743s (110.848657s with startup), under
180s timeout and768MiB RLIMIT_AS. New independent root-partition oracle tests
12012/01212/12300/12323/00012 at split3, caps0/3/100/2000, both right-operand
strategies:6830 queries, all reachable values plus sampled rational misses.
Every witness is independently evaluated and digit-order checked. Additional
forced exponent-query/table comparisons check cap2000 reciprocal powers,
negative exponents and all-zero failure. Existing tests also passed.
An initial full-suite attempt exceeded its180s deadline and was killed: it
combined exhaustive five-digit testing with forced4001-exponent scans for each
query. Final tests retain exhaustive right-inversion comparisons with the short
exponent table; forced high-cap exponent scans use selected boundary cases.
No assertion failure was observed in that timed-out attempt; it was not counted
as a passing test run. Reproduce final suite with `python -m unittest -q`.

Before changing the active checkpoint, load rejected it for source/version
mismatch. Archived bytes unchanged in
checkpoint_10958_cap2000_before_right_inverse.json. Fresh search command:

```
python resume_search.py --max-abs-exponent 2000 --seconds 240 --per-split-seconds 45 --memory-mib 768 --checkpoint checkpoint_10958.json
```

All8 partitions completed not_found_bounded, each attempt1. Sum worker wall
times4.783089s (previous23.423295s); peak RSS24404KiB (previous111756KiB).
Split7:0.566826s/17368KiB versus previous6.506190s/111756KiB. Separate new
split7 run0.585611s is saved in split7_right_inverse.json. These are single-run
measurements, not statistical guarantees. Resume with subprocess.run patched
to raise on invocation succeeded with byte-identical checkpoint: no reruns.

Profiles, sequential and never overlapping tests/search:

```
python profile_search.py --split 7 --max-abs-exponent 2000 --seconds 45 --memory-mib 768
```

Saved before/after JSON includes source hashes. After profile2.000298s,
5,752,446 calls,RSS20812KiB. Compare profiler results to each other, not normal
worker times. Total allocated search/profiling budgets375s (45+45+240+45),
per-child virtual memory768MiB. Tests had separate180s deadlines per attempt.
No paid resources or automation changes. No expression for10958 found with
per-node integer exponents within +/-2000; unrestricted impossibility unproven.

Next: benchmark split1 and8, now the largest worker times, and compare a larger
short-right threshold only with independent oracle tests. Keep completed
checkpoints intact; widening the exponent bound requires a distinct identity
and fresh bounded validation. No need to rerun the completed current domain
unless production changes or a specific diagnostic requires it.

## 2026-11-01 — cap5000 validated and completed

Starting PR #1 head6b117ea1a14e80d993954001b5f71a15709da70f was open and
unchanged. Existing tracked local blobs matched remote; read README, progress
and checkpoint. Production solver/runner/verifier unchanged this session.

Sequential cap2000 diagnostics (30s /768MiB each):

```
python profile_search.py --split 1 --max-abs-exponent 2000 --seconds 30 --memory-mib 768 > profile_split1_cap2000.json
python profile_search.py --split 8 --max-abs-exponent 2000 --seconds 30 --memory-mib 768 > profile_split8_cap2000.json
```

Both not_found_bounded. Profile-inclusive wall times6.022981/5.903019s,
RSS23812/23056KiB. cached_can_make largest own time1.152/1.106s; hashing
0.477/0.411s. Profiles include overhead and are not ordinary worker benchmarks.
Raw function statistics and source fingerprints saved. No new cache adopted.

Expanded all three test_large_limits tests to cap5000: independent syntax-tree
oracle, positive/negative exponents and rational-base boundary N vs N-1, and
independent evaluator checks per-node limits. `python -m unittest -v
test_large_limits` passed3 tests in7.154s (8.362508s including startup),
120s deadline /768MiB RLIMIT_AS. Combined oracle covers8513 syntax trees and
5118 reverse queries across caps200/1000/2000/5000, four inputs and both edge
settings. Previous full42-test suite remains the last full-suite run; only the
modified test module was rerun because production code is unchanged.

New domain, separate checkpoint, no cap2000 partitions reexecuted as a search:

```
python resume_search.py --max-abs-exponent 5000 --seconds 240 --per-split-seconds 45 --memory-mib 768 --checkpoint checkpoint_10958_cap5000.json
```

All8 partitions completed not_found_bounded, attempts1 each. Worker times sum
12.004513s, peak RSS24504KiB. Split1=3.988367s and8=3.467448s. Every exponent
at every node is bounded by5000; exact Fraction/digit-order rules unchanged.
This is bounded absence, not an unrestricted impossibility proof. Original
cap2000 checkpoint retained byte-for-byte. Both checkpoints were resumed with
subprocess.run patched to reject execution: completed with identical bytes.

Total search/profiling allocation300s (30+30+240), each child virtual memory
768MiB. No paid resources or automation changes. Next: use the saved profiles
to reduce repeated exact root checks before increasing the cap again. Compare
root caching only with a strict memory bound and measured hit rate; avoid
repeating the earlier unsuccessful general power-cache experiment.

## 2026-11-01 — bounded rational-root cache rejected after measurement

Started at ff351df7cf40a15d00598440a5ee11ce5c288b24, PR #1 open and unchanged.
Compared local tracked files with remote blobs (matched), then read README,
previous progress and cap5000 checkpoint. No production source changed.

Added measure_root_cache.py: isolated baseline versus LRU sizes1024/16384.
Input admission requires combined numerator/denominator bit length<=256;
larger inputs bypass the cache, preventing a fixed entry count from retaining
arbitrarily large rationals. Exponents come from the cap5000 solver. Baseline
uses the original function directly; experimental wrappers are restored in a
finally block. Workers have30s SIGALRM /768MiB RLIMIT_AS; orchestration adds a
35s hard subprocess timeout. Found witnesses would be independently verified.
Results include cap, budgets, source hash, RSS and cache hit/miss counts.

New test_root_cache.py checks independently generated exact powers (including
negative/rational bases), irrational and negative-even misses, repeat hits,
eviction and large-input bypass. `python -m unittest -v test_root_cache`:
2 tests passed in0.074s. Production unchanged, previous full suite not rerun.

Reproduction: sequentially run `python measure_root_cache.py --split S --size N`
for S=1,8 and N=0,1024,16384, three times per combination. Actual order used
sizes0/1024/16384, then16384/1024/0, then0/1024/16384, each over splits1/8.
All18 JSON rows committed in root_cache_measurements.jsonl, allnot_found_bounded.
Median wall seconds (baseline /1024 /16384):
- split1:2.869067 /3.426224 /4.816251.
- split8:2.300254 /3.845431 /4.116472.
Peak RSS KiB for those settings: split1=19996/20172/25300;
split8=19760/19900/24424. Hit rates:1024 about1.61%/2.52%;
16384 about14.00%/19.51%. Cache bookkeeping did not produce a measured median
speedup on either split, so neither cache is adopted.

Timings varied substantially (including a19.72s observation). The first batch
also overlapped the short cache tests; later two batches ran without other
local test/search commands. Three samples are not a controlled statistical
performance guarantee. The decision is conservative: no evidence justifies
adding production memory and lookup overhead. No cached limited misses are
persisted as completed production search results.

Total allocation18*30=540s search time, below600s; observed runs all completed
before alarms. No paid resources or automation changes. The existing cap5000
checkpoint resumes byte-identically with subprocess invocation prohibited.
10958 remains not_found_bounded for +/-5000 from the earlier full search;
only diagnostic splits were repeated now, not the entire completed domain.

Next: bound candidate exponents using exact integer bit lengths before root
queries (except degenerate targets0,+1,-1), and independently prove/test that
bound for both positive and reciprocal rational targets. This is a proposed
optimization, not yet implemented. Do not magnitude-prune intermediate values.
