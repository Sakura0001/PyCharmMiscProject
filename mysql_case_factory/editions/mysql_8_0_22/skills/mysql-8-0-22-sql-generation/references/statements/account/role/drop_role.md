# DROP ROLE

Official source: https://dev.mysql.com/doc/refman/8.0/en/drop-role.html

```yaml
structured_config:
  kind: statement
  category: account
  domain: role
  skill_name: drop_role
  official_source: https://dev.mysql.com/doc/refman/8.0/en/drop-role.html
  statement:
    key: drop_role
    name: DROP ROLE
    aliases: [drop role]
    purpose: Drop MySQL roles.
  syntax_templates:
    - "DROP ROLE [IF EXISTS] role [, role] ..."
  factor_layers:
    - tier: T1
      factors: [if_exists, role_state, expected_status]
  factors:
    if_exists:
      label: IF EXISTS
      importance: important
      values: [omitted, present]
    role_state:
      label: Role state
      importance: important
      values: [exists, missing]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    if_exists: omitted
    role_state: exists
    expected_status: success
  coverage_policy:
    main_combination_axes: [if_exists, role_state, expected_status]
    non_main_factors: []
    python_expand_threshold: 80
  rendering:
    statement_template: "DROP ROLE {if_exists_sql}'case_role'"
    verification_query_template: "SELECT USER FROM mysql.user WHERE USER = 'case_role'"
    factor_value_bindings:
      if_exists_sql:
        factor: if_exists
        values: {omitted: "", present: "IF EXISTS "}
```
