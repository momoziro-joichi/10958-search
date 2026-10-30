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
