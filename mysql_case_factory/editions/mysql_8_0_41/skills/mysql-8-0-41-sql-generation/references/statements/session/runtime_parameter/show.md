# SHOW

Official source: https://dev.mysql.com/doc/refman/8.0/en/show.html

```yaml
structured_config:
  kind: statement
  category: session
  domain: runtime_parameter
  skill_name: show
  official_source: https://dev.mysql.com/doc/refman/8.0/en/show.html
  statement:
    key: show
    name: SHOW
    aliases: [show]
    purpose: Generate MySQL SHOW statement-family cases.
  syntax_templates:
    - "SHOW VARIABLES [LIKE 'pattern' | WHERE expr]"
    - "SHOW STATUS [LIKE 'pattern' | WHERE expr]"
    - "SHOW GRANTS [FOR user_or_role]"
    - "SHOW CREATE TABLE tbl_name"
    - "SHOW WARNINGS [LIMIT row_count]"
  factor_layers:
    - tier: T1
      factors: [statement_branch, filter_shape, expected_status]
    - tier: T2
      factors: [target_shape]
  factors:
    statement_branch:
      label: SHOW branch
      importance: important
      values: [variables, status, grants, create_table, warnings, errors]
    filter_shape:
      label: LIKE / WHERE filter
      importance: important
      values: [omitted, like_pattern, where_expression]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    target_shape:
      label: Target object or account
      importance: non_important
      values: [none, table_name, user_account]
  defaults:
    statement_branch: variables
    filter_shape: omitted
    expected_status: success
    target_shape: none
  coverage_policy:
    main_combination_axes: [statement_branch, filter_shape, expected_status]
    non_main_factors: [target_shape]
    python_expand_threshold: 120
  rendering:
    statement_template: "SHOW VARIABLES"
    verification_query_template: ""
    factor_value_bindings: {}
```
