# Review guide

Production implementation baseline: 6a0e5cd (2026-11-11).
Review starting head: 66c70e7 (2026-11-13). Later experimental additions
are part of this PR's review scope, but are not production dependencies.

| Review area | Files | Purpose |
| --- | --- | --- |
| Exact solver | search.py | Fraction arithmetic, integer-power inversion, tuple lookup, right operand inversion through3 digits |
| Independent verifier | verify_expression.py | Digit order/count, grammar, exact result, per-node exponent cap |
| Resource bounds | run_search.py | Child timeout and virtual memory limits |
| Resume | resume_search.py | Validated identity, atomic checkpoint, completed partition reuse |
| Regression evidence | test_*.py, width3_full_tests.json | Latest integrated run: 74 passed in 150.782s (merge_review_full_tests.json); historical baseline: 51 passed in 145.731s |
| Exact cap boundary | test_cap20000_boundaries.py | Positive/negative exponent 20000 accepted at cap 20000, rejected at 19999; internal powers checked before cancellation |
| Symbolic experiments | strategy_probe.py, classify_symbolic.py, benchmark_symbolic_cache.py | Separate diagnostic path; optional bounded cache, unresolved outcomes retained |
| Experimental regression coverage | test_strategy_probe.py, test_symbolic_runner.py, test_symbolic_cache.py, test_structural_partitions.py | Definedness, unknown outcomes, cache cleanup and structural partition coverage |
| Current search evidence | checkpoint_10958_cap20000_width3.json | All8 partitions completed; cap20000; not_found_bounded |
| Historical evidence | Other checkpoint/profile/measurement JSON, experiment_*.py, measure_*.py, benchmark_right_width.py | Not required by production execution; retain for reproducibility |
| Chronology | PROGRESS.md | Trials, rejected optimizations, conditions and next steps |

Read solver/verifier first, then resource/resume code, then tests. Historical
experiments are not additional production dependencies. Generic power caching
and root caching were investigated but not adopted. Tuple lookup and three-digit
right inversion were adopted. Do not repeat rejected cache trials without new evidence.

Latest recorded search:2.984012s summed worker time,14336KiB peak RSS; total
budget240s,30s per child,768MiB virtual memory. Full tests ran concurrently,
so this is not an isolated speed benchmark. No unrestricted impossibility proof.

Reproduce tests: `python -m unittest -q` under 240s/768MiB on Linux.
`merge_review_identity.json` records the SHA-256 of every Python source/test
used for the integrated run and the completed-checkpoint reuse check.
Documentation-only edits after that run do not change those tested bytes.
Resume current search:
```bash
python resume_search.py --max-abs-exponent 20000 --seconds 240 --per-split-seconds 30 --memory-mib 768 --checkpoint checkpoint_10958_cap20000_width3.json
```
Older checkpoints are historical and may have incompatible source fingerprints.
Do not migrate their completed flags. Further performance work is separate from
reviewing the existing correctness/resource-control changes. No merge is performed
by this guide. Avoid moving or deleting evidence in the same correctness review;
any later repository layout cleanup should be a separate change.

## Merge criteria when keeping experiments in this PR

Keep the experiments in this PR as explicitly experimental, standard-library
diagnostics. They do not replace the production solver. The following are
review criteria, not a claim of approval or a request to merge automatically.

| Priority | Required acceptance condition | Minimum evidence |
| --- | --- | --- |
| P0 | Production and experimental files and results are distinguished in PR text and this guide | File-role table above; no claim that historical 51-test output covers later additions |
| P0 | The integrated test suite passes after the final code/test change | One `python -m unittest -q` run under 240s/768MiB; record source baseline, added tests, environment and exit status |
| P1 | Per-node positive and negative exponent limits apply at 20000 and just below it | test_cap20000_boundaries.py; existing small-space oracle and width3 regressions remain included |
| P1 | Current production source identity matches the completed checkpoint | Recompute identity from the four production files; load all eight records and resume a temporary copy with subprocess launches prohibited |
| P1 | Unsupported symbolic cases stay unresolved; invalid arithmetic cannot become an accepted witness through simplification | Existing symbolic definedness, low-bit/direct-arithmetic and unknown-outcome tests; read matches_target branches |
| P1 | Experimental caching restores module state and releases entries on success and timeout/memory exceptions | test_symbolic_runner.py and test_symbolic_cache.py; default cache remains disabled |
| P1 | Resource and resume claims match the implementation | Linux production worker timeout/RLIMIT_AS; diagnostic signal timeout is not a durable resumable worker system |
| P2 | Final reviewed head/base and GitHub checks are current; review is completed before leaving Draft | Recheck PR metadata and available checks immediately before merge; absence of checks is not a passing CI result |

The diagnostic cache wrapper is for a single process/single thread, not
concurrent embedding. Its entry limit is not a byte limit; the address-space
limit remains necessary. Structural token-mask tests establish disjoint
coverage only: no experimental per-mask checkpoint/resume is implemented.

The uncapped seven-digit diagnostic result applies only to 1234567 -> 10958.
The production nine-digit result remains bounded by 20000 at every power node.
Neither establishes unrestricted nine-digit impossibility. A complete enumeration
with unresolved outcomes is not a completed negative target result.

Do not require a new eight/nine-digit experiment, larger cap, generic power/root
cache trial or stable speedup claim to merge these correctness changes. Such work,
experimental persistence, concurrent embedding and repository restructuring are
follow-up scope. The optional symbolic cache is distinct from the rejected
production power/root cache experiments.
