# FLUSH

Official source: https://dev.mysql.com/doc/refman/8.0/en/flush.html

```yaml
structured_config:
  kind: statement
  category: admin
  domain: server
  skill_name: flush
  official_source: https://dev.mysql.com/doc/refman/8.0/en/flush.html
  statement:
    key: flush
    name: FLUSH
    aliases: [flush]
    purpose: Flush MySQL server caches, logs, privileges, tables, and status.
  syntax_templates:
    - "FLUSH [NO_WRITE_TO_BINLOG | LOCAL] flush_option [, flush_option] ..."
    - "FLUSH TABLES tbl_name [, tbl_name] ... [WITH READ LOCK | FOR EXPORT]"
  factor_layers:
    - tier: T1
      factors: [flush_option, binlog_modifier, expected_status]
    - tier: T2
      factors: [table_flush_shape, privilege_context]
  factors:
    flush_option:
      label: FLUSH option
      importance: important
      values: [binary_logs, engine_logs, error_logs, general_logs, hosts, logs, optimizer_costs, privileges, status, user_resources, tables]
    binlog_modifier:
      label: Binary logging modifier
      importance: important
      values: [omitted, no_write_to_binlog, local]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    table_flush_shape:
      label: TABLES shape
      importance: non_important
      values: [not_tables, all_tables, table_list, with_read_lock, for_export]
    privilege_context:
      label: Privilege context
      importance: non_important
      values: [sufficient, insufficient]
  defaults:
    flush_option: privileges
    binlog_modifier: omitted
    expected_status: success
    table_flush_shape: not_tables
    privilege_context: sufficient
  coverage_policy:
    main_combination_axes: [flush_option, binlog_modifier, expected_status]
    non_main_factors: [table_flush_shape, privilege_context]
    python_expand_threshold: 180
  rendering:
    statement_template: "FLUSH STATUS"
    verification_query_template: ""
    factor_value_bindings: {}
```
