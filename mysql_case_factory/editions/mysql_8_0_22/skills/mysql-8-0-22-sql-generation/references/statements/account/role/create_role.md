# CREATE ROLE

Official source: https://dev.mysql.com/doc/refman/8.0/en/create-role.html

```yaml
structured_config:
  kind: statement
  category: account
  domain: role
  skill_name: create_role
  official_source: https://dev.mysql.com/doc/refman/8.0/en/create-role.html
  statement:
    key: create_role
    name: CREATE ROLE
    aliases: [create role]
    purpose: Create MySQL roles.
  syntax_templates:
    - "CREATE ROLE [IF NOT EXISTS] role [, role] ..."
  factor_layers:
    - tier: T1
      factors: [if_not_exists, role_name_shape, role_state, expected_status]
  factors:
    if_not_exists:
      label: IF NOT EXISTS
      importance: important
      values: [omitted, present]
    role_name_shape:
      label: Role name
      importance: important
      values: [simple_role, quoted_role]
    role_state:
      label: Role state
      importance: important
      values: [missing, already_exists]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    if_not_exists: omitted
    role_name_shape: simple_role
    role_state: missing
    expected_status: success
  coverage_policy:
    main_combination_axes: [if_not_exists, role_name_shape, role_state, expected_status]
    non_main_factors: []
    python_expand_threshold: 100
  rendering:
    statement_template: "CREATE ROLE {if_not_exists_sql}'case_role'"
    verification_query_template: "SELECT USER FROM mysql.user WHERE USER = 'case_role'"
    factor_value_bindings:
      if_not_exists_sql:
        factor: if_not_exists
        values: {omitted: "", present: "IF NOT EXISTS "}
```
