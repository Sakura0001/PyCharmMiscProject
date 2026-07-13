# SET DEFAULT ROLE

Official source: https://dev.mysql.com/doc/refman/8.0/en/set-default-role.html

```yaml
structured_config:
  kind: statement
  category: account
  domain: role
  skill_name: set_default_role
  official_source: https://dev.mysql.com/doc/refman/8.0/en/set-default-role.html
  statement:
    key: set_default_role
    name: SET DEFAULT ROLE
    aliases: [set default role]
    purpose: Set default roles for MySQL accounts.
  syntax_templates:
    - "SET DEFAULT ROLE {NONE | ALL | role [, role] ...} TO user_or_role [, user_or_role] ..."
  factor_layers:
    - tier: T1
      factors: [role_selection, account_state, expected_status]
  factors:
    role_selection:
      label: Default role selection
      importance: important
      values: [none, all_roles, explicit_list]
    account_state:
      label: Account state
      importance: important
      values: [exists, missing]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    role_selection: explicit_list
    account_state: exists
    expected_status: success
  coverage_policy:
    main_combination_axes: [role_selection, account_state, expected_status]
    non_main_factors: []
    python_expand_threshold: 80
  rendering:
    statement_template: "SET DEFAULT ROLE 'case_role' TO 'case_user'@'localhost'"
    verification_query_template: "SELECT DEFAULT_ROLE_USER FROM mysql.default_roles WHERE USER = 'case_user'"
    factor_value_bindings: {}
```
