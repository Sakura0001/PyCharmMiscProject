# CHECK TABLE

Official source: https://dev.mysql.com/doc/refman/8.0/en/check-table.html

```yaml
structured_config:
  kind: statement
  category: utility
  domain: maintenance
  skill_name: check_table
  official_source: https://dev.mysql.com/doc/refman/8.0/en/check-table.html
  statement:
    key: check_table
    name: CHECK TABLE
    aliases: [check table]
    purpose: Check MySQL table or view integrity.
  syntax_templates:
    - "CHECK TABLE tbl_name [, tbl_name] ... [option] ..."
  factor_layers:
    - tier: T1
      factors: [target_state, check_option, expected_status]
    - tier: T2
      factors: [engine_shape]
  factors:
    target_state:
      label: Target state
      importance: important
      values: [table_exists, view_exists, missing]
    check_option:
      label: Check option
      importance: important
      values: [omitted, for_upgrade, quick, fast, medium, extended, changed]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    engine_shape:
      label: Storage engine
      importance: non_important
      values: [innodb, myisam, archive, csv]
  defaults:
    target_state: table_exists
    check_option: omitted
    expected_status: success
    engine_shape: innodb
  coverage_policy:
    main_combination_axes: [target_state, check_option, expected_status]
    non_main_factors: [engine_shape]
    python_expand_threshold: 120
  rendering:
    statement_template: "CHECK TABLE {table_name}"
    verification_query_template: ""
    factor_value_bindings: {}
```
