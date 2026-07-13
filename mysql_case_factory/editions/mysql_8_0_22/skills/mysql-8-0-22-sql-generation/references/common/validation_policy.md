# Validation Policy

MySQL SQL cases must make expected success and expected failure explicit.

```yaml
structured_config:
  skill_name: validation_policy
  statement: common
  success_validation:
    - information_schema_query
    - show_statement
    - select_runtime_probe
  failure_validation:
    - expected_error_code_or_sqlstate
    - object_absence_check
  cleanup:
    - drop_created_objects
    - rollback_when_transactional
```
