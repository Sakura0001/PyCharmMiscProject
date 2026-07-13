# CHECKSUM TABLE

Official source: https://dev.mysql.com/doc/refman/8.0/en/checksum-table.html

```yaml
structured_config:
  kind: statement
  category: utility
  domain: maintenance
  skill_name: checksum_table
  official_source: https://dev.mysql.com/doc/refman/8.0/en/checksum-table.html
  statement:
    key: checksum_table
    name: CHECKSUM TABLE
    aliases: [checksum table]
    purpose: Report MySQL table checksums.
  syntax_templates:
    - "CHECKSUM TABLE tbl_name [, tbl_name] ... [QUICK | EXTENDED]"
  factor_layers:
    - tier: T1
      factors: [target_state, checksum_option, expected_status]
    - tier: T2
      factors: [engine_shape]
  factors:
    target_state:
      label: Target state
      importance: important
      values: [table_exists, view_exists, missing]
    checksum_option:
      label: Checksum option
      importance: important
      values: [omitted, quick, extended]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    engine_shape:
      label: Storage engine
      importance: non_important
      values: [innodb, myisam]
  defaults:
    target_state: table_exists
    checksum_option: omitted
    expected_status: success
    engine_shape: innodb
  coverage_policy:
    main_combination_axes: [target_state, checksum_option, expected_status]
    non_main_factors: [engine_shape]
    python_expand_threshold: 100
  rendering:
    statement_template: "CHECKSUM TABLE {table_name}"
    verification_query_template: ""
    factor_value_bindings: {}
```
