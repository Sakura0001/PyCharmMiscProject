# DEALLOCATE PREPARE

Official source: https://dev.mysql.com/doc/refman/8.0/en/deallocate-prepare.html

```yaml
structured_config:
  kind: statement
  category: prepared
  domain: prepared_statement
  skill_name: deallocate
  official_source: https://dev.mysql.com/doc/refman/8.0/en/deallocate-prepare.html
  statement:
    key: deallocate
    name: DEALLOCATE PREPARE
    aliases: [deallocate prepare, drop prepare]
    purpose: Deallocate a MySQL session prepared statement.
  syntax_templates:
    - "{DEALLOCATE | DROP} PREPARE stmt_name"
  factor_layers:
    - tier: T1
      factors: [statement_branch, prepared_state, expected_status]
  factors:
    statement_branch:
      label: Keyword branch
      importance: important
      values: [deallocate_prepare, drop_prepare]
    prepared_state:
      label: Prepared statement state
      importance: important
      values: [exists, missing]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    statement_branch: deallocate_prepare
    prepared_state: exists
    expected_status: success
  coverage_policy:
    main_combination_axes: [statement_branch, prepared_state, expected_status]
    non_main_factors: []
    python_expand_threshold: 100
  rendering:
    statement_template: "{deallocate_sql} {prepared_name}"
    verification_query_template: ""
    factor_value_bindings:
      deallocate_sql:
        factor: statement_branch
        values:
          deallocate_prepare: "DEALLOCATE PREPARE"
          drop_prepare: "DROP PREPARE"
```
