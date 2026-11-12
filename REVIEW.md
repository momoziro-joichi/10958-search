# Review guide

Current implementation baseline: 6a0e5cd (2026-11-11).

| Review area | Files | Purpose |
| --- | --- | --- |
| Exact solver | search.py | Fraction arithmetic, integer-power inversion, tuple lookup, right operand inversion through3 digits |
| Independent verifier | verify_expression.py | Digit order/count, grammar, exact result, per-node exponent cap |
| Resource bounds | run_search.py | Child timeout and virtual memory limits |
| Resume | resume_search.py | Validated identity, atomic checkpoint, completed partition reuse |
| Regression evidence | test_*.py, width3_full_tests.json | Latest recorded full run:51 passed in145.731s |
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

Reproduce tests: `python -m unittest -q` under240s/768MiB.
Resume current search:
```bash
python resume_search.py --max-abs-exponent 20000 --seconds 240 --per-split-seconds 30 --memory-mib 768 --checkpoint checkpoint_10958_cap20000_width3.json
```
Older checkpoints are historical and may have incompatible source fingerprints.
Do not migrate their completed flags. Further performance work is separate from
reviewing the existing correctness/resource-control changes. No merge is performed
by this guide. Avoid moving or deleting evidence in the same correctness review;
any later repository layout cleanup should be a separate change.
