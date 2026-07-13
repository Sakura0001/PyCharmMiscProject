# DROP VIEW

Official source: https://dev.mysql.com/doc/refman/8.0/en/drop-view.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: view
  skill_name: drop_view
  official_source: https://dev.mysql.com/doc/refman/8.0/en/drop-view.html
  statement:
    key: drop_view
    name: DROP VIEW
    aliases: [drop view]
    purpose: Drop one or more MySQL views.
  syntax_templates:
    - "DROP VIEW [IF EXISTS] view_name [, view_name] ... [RESTRICT | CASCADE]"
  factor_layers:
    - tier: T1
      factors: [if_exists, view_state, expected_status]
    - tier: T2
      factors: [multi_view_shape, restrict_cascade]
  factors:
    if_exists:
      label: IF EXISTS
      importance: important
      values: [omitted, present]
    view_state:
      label: View state
      importance: important
      values: [exists, missing]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    multi_view_shape:
      label: Number of views
      importance: non_important
      values: [single, multiple]
    restrict_cascade:
      label: RESTRICT or CASCADE parsed no-op
      importance: non_important
      values: [omitted, restrict, cascade]
  defaults:
    if_exists: omitted
    view_state: exists
    expected_status: success
    multi_view_shape: single
    restrict_cascade: omitted
  coverage_policy:
    main_combination_axes: [if_exists, view_state, expected_status]
    non_main_factors: [multi_view_shape, restrict_cascade]
    python_expand_threshold: 100
  rendering:
    statement_template: "DROP VIEW {if_exists_sql}{view_name}{restrict_sql}"
    verification_query_template: "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{view_name}'"
    factor_value_bindings:
      if_exists_sql:
        factor: if_exists
        values: {omitted: "", present: "IF EXISTS "}
      restrict_sql:
        factor: restrict_cascade
        values: {omitted: "", restrict: " RESTRICT", cascade: " CASCADE"}
```
