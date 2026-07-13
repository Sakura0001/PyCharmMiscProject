# REPAIR TABLE

Official source: https://dev.mysql.com/doc/refman/8.0/en/repair-table.html

```yaml
structured_config:
  kind: statement
  category: utility
  domain: maintenance
  skill_name: repair_table
  official_source: https://dev.mysql.com/doc/refman/8.0/en/repair-table.html
  statement:
    key: repair_table
    name: REPAIR TABLE
    aliases: [repair table]
    purpose: Repair MyISAM, ARCHIVE, and CSV tables; InnoDB is covered as unsupported/negative behavior.
  syntax_templates:
    - "REPAIR [NO_WRITE_TO_BINLOG | LOCAL] TABLE tbl_name [, tbl_name] ... [QUICK] [EXTENDED] [USE_FRM]"
  factor_layers:
    - tier: T1
      factors: [target_state, repair_option, expected_status]
    - tier: T2
      factors: [binlog_modifier, engine_shape]
  factors:
    target_state:
      label: Target state
      importance: important
      values: [table_exists, view_exists, missing]
    repair_option:
      label: Repair option
      importance: important
      values: [omitted, quick, extended, use_frm]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    binlog_modifier:
      label: Binary logging modifier
      importance: non_important
      values: [omitted, no_write_to_binlog, local]
    engine_shape:
      label: Storage engine
      importance: non_important
      values: [myisam, archive, csv, innodb_unsupported]
  defaults:
    target_state: table_exists
    repair_option: omitted
    expected_status: success
    binlog_modifier: omitted
    engine_shape: myisam
  coverage_policy:
    main_combination_axes: [target_state, repair_option, expected_status]
    non_main_factors: [binlog_modifier, engine_shape]
    python_expand_threshold: 120
  rendering:
    statement_template: "REPAIR TABLE {table_name}"
    verification_query_template: ""
    factor_value_bindings: {}
```
