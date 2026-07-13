# Factor Policy

Defines shared factor expansion policy for MySQL SQL generation. Statement
references decide which factors are main axes and which are attached
representative factors.

## Rules

- Important factors use full Cartesian coverage.
- Non-important factors are rotated onto main combinations.
- If there are fewer main combinations than attached factor values, clone main
  skeletons until every non-important value is covered at least once.
- When generation size exceeds the statement threshold, preserve T1 main axes
  first, then reduce T2 coverage, then rotate T3 and later tiers.
- Attached factors must not hide the root cause of success/failure cases or
  break lifecycle prerequisites.

```yaml
structured_config:
  skill_name: factor_policy
  statement: common
  factor_policy:
    important_factor_strategy: full_cross
    non_important_factor_strategy: rotate_attach
    clone_main_skeleton_if_needed: true
    preserve_main_axes_first: true
```
