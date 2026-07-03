# Naming Rules

Generated MySQL identifiers should be deterministic and short enough for the
64-character MySQL identifier limit.

```yaml
structured_config:
  skill_name: naming_rules
  statement: common
  max_identifier_length: 64
  prefixes:
    table: tab_
    index: idx_
    view: vw_
    database: db_
```
