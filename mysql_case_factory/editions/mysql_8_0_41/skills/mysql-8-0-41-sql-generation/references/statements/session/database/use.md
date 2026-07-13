# USE

Official source: https://dev.mysql.com/doc/refman/8.0/en/use.html

```yaml
structured_config:
  kind: statement
  category: session
  domain: database
  skill_name: use
  official_source: https://dev.mysql.com/doc/refman/8.0/en/use.html
  statement:
    key: use
    name: USE
    aliases: [use]
    purpose: Change the default database for the current MySQL session.
  syntax_templates:
    - "USE db_name"
  factor_layers:
    - tier: T1
      factors: [database_state, privilege_state, expected_status]
    - tier: T2
      factors: [name_shape]
  factors:
    database_state:
      label: Database state
      importance: important
      values: [exists, missing]
    privilege_state:
      label: Privilege state
      importance: important
      values: [has_privilege, no_privilege]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    name_shape:
      label: Database name shape
      importance: non_important
      values: [simple, quoted]
  defaults:
    database_state: exists
    privilege_state: has_privilege
    expected_status: success
    name_shape: simple
  coverage_policy:
    main_combination_axes: [database_state, privilege_state, expected_status]
    non_main_factors: [name_shape]
    python_expand_threshold: 80
  rendering:
    statement_template: "USE {database_name}"
    verification_query_template: "SELECT DATABASE()"
    factor_value_bindings: {}
```
