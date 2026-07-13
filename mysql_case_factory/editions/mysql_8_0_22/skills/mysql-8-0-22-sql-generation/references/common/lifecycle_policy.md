# Lifecycle Policy

Lifecycle plans describe SQL object setup, target statement execution,
verification, and cleanup. They must not describe parser, renderer, or agent
implementation stages.

```yaml
structured_config:
  skill_name: lifecycle_policy
  statement: common
  action_order:
    - setup
    - target
    - verify
    - cleanup
  cleanup_required: true
```
