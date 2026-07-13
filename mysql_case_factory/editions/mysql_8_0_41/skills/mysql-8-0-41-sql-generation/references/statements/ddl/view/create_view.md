# CREATE VIEW

Official source: https://dev.mysql.com/doc/refman/8.0/en/create-view.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: view
  skill_name: create_view
  official_source: https://dev.mysql.com/doc/refman/8.0/en/create-view.html
  statement:
    key: create_view
    name: CREATE VIEW
    aliases: [create view]
    purpose: Create a MySQL view with algorithm, definer, security, and check-option coverage.
  syntax_templates:
    - "CREATE [OR REPLACE] [ALGORITHM = {UNDEFINED | MERGE | TEMPTABLE}] [DEFINER = user] [SQL SECURITY {DEFINER | INVOKER}] VIEW view_name [(column_list)] AS select_statement [WITH [CASCADED | LOCAL] CHECK OPTION]"
  factor_layers:
    - tier: T1
      factors: [or_replace, algorithm, security_type, expected_status]
    - tier: T2
      factors: [column_list_shape, check_option]
  factors:
    or_replace:
      label: OR REPLACE
      importance: important
      values: [omitted, present]
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
    column_list_shape:
      label: Column list
      importance: non_important
      values: [omitted, explicit]
    check_option:
      label: CHECK OPTION
      importance: non_important
      values: [omitted, cascaded, local]
  defaults:
    or_replace: omitted
    algorithm: omitted
    security_type: omitted
    expected_status: success
    column_list_shape: omitted
    check_option: omitted
  coverage_policy:
    main_combination_axes: [or_replace, algorithm, security_type, expected_status]
    non_main_factors: [column_list_shape, check_option]
    python_expand_threshold: 160
  rendering:
    statement_template: "CREATE {or_replace_sql}{algorithm_sql}{security_sql}VIEW {view_name} AS SELECT id_col, int_col FROM {table_name}{check_option_sql}"
    verification_query_template: "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{view_name}'"
    factor_value_bindings:
      or_replace_sql:
        factor: or_replace
        values: {omitted: "", present: "OR REPLACE "}
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
