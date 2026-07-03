# EXPLAIN

Official source: https://dev.mysql.com/doc/refman/8.0/en/explain.html

```yaml
structured_config:
  kind: statement
  category: utility
  domain: plan
  skill_name: explain
  official_source: https://dev.mysql.com/doc/refman/8.0/en/explain.html
  statement:
    key: explain
    name: EXPLAIN
    aliases: [explain, describe, desc]
    purpose: Inspect MySQL execution plans or table metadata.
  syntax_templates:
    - "EXPLAIN [FORMAT = format_name] explainable_stmt"
    - "EXPLAIN ANALYZE select_statement"
    - "{EXPLAIN | DESCRIBE | DESC} tbl_name [col_name | wild]"
  factor_layers:
    - tier: T1
      factors: [statement_branch, target_shape, expected_status]
    - tier: T2
      factors: [format_shape]
  factors:
    statement_branch:
      label: EXPLAIN branch
      importance: important
      values: [query_plan, analyze_query, table_describe]
    target_shape:
      label: Target statement
      importance: important
      values: [select_statement, dml_statement, table_name]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    format_shape:
      label: FORMAT option
      importance: non_important
      values: [omitted, traditional, json, tree]
  defaults:
    statement_branch: query_plan
    target_shape: select_statement
    expected_status: success
    format_shape: omitted
  coverage_policy:
    main_combination_axes: [statement_branch, target_shape, expected_status]
    non_main_factors: [format_shape]
    python_expand_threshold: 100
  rendering:
    statement_template: "EXPLAIN SELECT * FROM {table_name} WHERE int_col = 1"
    verification_query_template: ""
    factor_value_bindings: {}
```
