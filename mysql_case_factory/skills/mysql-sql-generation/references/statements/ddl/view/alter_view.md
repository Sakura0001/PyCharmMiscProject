# ALTER VIEW

Official source: https://dev.mysql.com/doc/refman/8.0/en/alter-view.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: view
  skill_name: alter_view
  official_source: https://dev.mysql.com/doc/refman/8.0/en/alter-view.html
  statement:
    key: alter_view
    name: ALTER VIEW
    aliases: [alter view]
    purpose: Redefine a MySQL view using CREATE VIEW-style clauses.
  syntax_templates:
    - "ALTER [ALGORITHM = {UNDEFINED | MERGE | TEMPTABLE}] [DEFINER = user] [SQL SECURITY {DEFINER | INVOKER}] VIEW view_name [(column_list)] AS select_statement [WITH [CASCADED | LOCAL] CHECK OPTION]"
  factor_layers:
    - tier: T1
      factors: [view_state, algorithm, security_type, expected_status]
    - tier: T2
      factors: [check_option]
  factors:
    view_state:
      label: View state
      importance: important
      values: [exists, missing]
    algorithm:
      label: ALGORITHM
      importance: important
      values: [omitted, undefined, merge, temptable]
    security_type:
      label: SQL SECURITY
      importance: important
      values: [omitted, definer, invoker]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    check_option:
      label: CHECK OPTION
      importance: non_important
      values: [omitted, cascaded, local]
  defaults:
    view_state: exists
    algorithm: omitted
    security_type: omitted
    expected_status: success
    check_option: omitted
  coverage_policy:
    main_combination_axes: [view_state, algorithm, security_type, expected_status]
    non_main_factors: [check_option]
    python_expand_threshold: 120
  rendering:
    statement_template: "ALTER {algorithm_sql}{security_sql}VIEW {view_name} AS SELECT id_col FROM {table_name}{check_option_sql}"
    verification_query_template: "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{view_name}'"
    factor_value_bindings:
      algorithm_sql:
        factor: algorithm
        values: {omitted: "", undefined: "ALGORITHM=UNDEFINED ", merge: "ALGORITHM=MERGE ", temptable: "ALGORITHM=TEMPTABLE "}
      security_sql:
        factor: security_type
        values: {omitted: "", definer: "SQL SECURITY DEFINER ", invoker: "SQL SECURITY INVOKER "}
      check_option_sql:
        factor: check_option
        values: {omitted: "", cascaded: " WITH CASCADED CHECK OPTION", local: " WITH LOCAL CHECK OPTION"}
```
