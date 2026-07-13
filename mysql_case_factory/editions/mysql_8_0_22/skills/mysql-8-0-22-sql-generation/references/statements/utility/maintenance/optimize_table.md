# OPTIMIZE TABLE

Official source: https://dev.mysql.com/doc/refman/8.0/en/optimize-table.html

```yaml
structured_config:
  kind: statement
  category: utility
  domain: maintenance
  skill_name: optimize_table
  official_source: https://dev.mysql.com/doc/refman/8.0/en/optimize-table.html
  statement:
    key: optimize_table
    name: OPTIMIZE TABLE
    aliases: [optimize table]
    purpose: Optimize MySQL table storage and statistics.
  syntax_templates:
    - "OPTIMIZE [NO_WRITE_TO_BINLOG | LOCAL] TABLE tbl_name [, tbl_name] ..."
  factor_layers:
    - tier: T1
      factors: [target_state, binlog_modifier, expected_status]
    - tier: T2
      factors: [engine_shape]
  factors:
    target_state:
      label: Target state
      importance: important
      values: [table_exists, view_exists, missing]
    binlog_modifier:
      label: Binary logging modifier
      importance: important
      values: [omitted, no_write_to_binlog, local]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    engine_shape:
      label: Storage engine
      importance: non_important
      values: [innodb, myisam, archive]
  defaults:
    target_state: table_exists
    binlog_modifier: omitted
    expected_status: success
    engine_shape: innodb
  coverage_policy:
    main_combination_axes: [target_state, binlog_modifier, expected_status]
    non_main_factors: [engine_shape]
    python_expand_threshold: 100
  rendering:
    statement_template: "OPTIMIZE TABLE {table_name}"
    verification_query_template: ""
    factor_value_bindings: {}
```
