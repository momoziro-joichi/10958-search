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
