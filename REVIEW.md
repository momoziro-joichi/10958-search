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
| Regression evidence | test_*.py, width3_full_tests.json | Integrated run on 2026-11-13: 74 passed in 150.782s (merge_review_full_tests.json); excludes the 2026-11-15 storage addition; historical baseline: 51 passed in 145.731s |
| Exact cap boundary | test_cap20000_boundaries.py | Positive/negative exponent 20000 accepted at cap 20000, rejected at 19999; internal powers checked before cancellation |
| Symbolic experiments | strategy_probe.py, classify_symbolic.py, benchmark_symbolic_cache.py | Separate diagnostic path; optional bounded cache, unresolved outcomes retained |
| Experimental storage primitive | structural_checkpoint.py, test_structural_checkpoint.py | Validated atomic storage only; no integrated resumable search; three focused tests recorded on 2026-11-15 |
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
Documentation-only edits do not change tested bytes. However, commit 4535bc3
added structural_checkpoint.py and test_structural_checkpoint.py after the
74-test run. Their three focused tests are recorded separately in PROGRESS.md;
74 plus 3 is not evidence of a 77-test integrated pass. The manifest remains
historical evidence and must not be relabeled as covering those added files.
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
coverage only. A storage primitive now exists, but no integrated experimental
per-mask checkpoint/resume runner is implemented. Its caller must supply a
trusted source/input identity and exclusive path ownership. Locking, parent
directory fsync, worker integration, and interruption/skip validation are
follow-up work. Record counts do not authenticate mathematical correctness.

The uncapped seven-digit diagnostic result applies only to 1234567 -> 10958.
The production nine-digit result remains bounded by 20000 at every power node.
Neither establishes unrestricted nine-digit impossibility. A complete enumeration
with unresolved outcomes is not a completed negative target result.

Do not require a new eight/nine-digit experiment, larger cap, generic power/root
cache trial or stable speedup claim to merge these correctness changes. Such work,
experimental persistence, concurrent embedding and repository restructuring are
follow-up scope. The optional symbolic cache is distinct from the rejected
production power/root cache experiments.

## 2026-11-16 scope decision and remaining review

Retain the small, isolated experimental storage primitive already present in
4535bc3, explicitly as a primitive rather than a production feature. Avoid a
history rewrite or broad experiment extraction during this review. Freeze code
scope here: any new enumeration engine, fusion experiment, semantic value
compression, cap-free target-directed engine, or resumable diagnostic runner
belongs on a follow-up branch. This is a scope recommendation, not approval.

Remaining blockers:

1. With the added primitive retained, obtain one integrated test result for the
   final code/test bytes, as required by the existing merge criteria. Reuse the
   74-test evidence for its original bytes; do not rerun the completed cap20000
   production exploration or checkpoint-resume experiment. Record source
   hashes, environment, duration, exit code, and actual discovered test count.
2. Complete final human review and check the final head/base, required checks
   and branch protections immediately before any Draft-state or merge action.
   Empty commit-status data is not a successful CI result.

The source-role documentation discrepancy is addressed above. No test run,
production search, Draft-state transition, approval, or merge is performed by
this documentation change. Research speed comparisons belong to their measured
input/domain; they do not establish nine-digit performance or impossibility.
