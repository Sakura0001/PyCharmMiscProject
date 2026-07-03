# SET ROLE

Official source: https://dev.mysql.com/doc/refman/8.0/en/set-role.html

```yaml
structured_config:
  kind: statement
  category: session
  domain: authorization
  skill_name: set_role
  official_source: https://dev.mysql.com/doc/refman/8.0/en/set-role.html
  statement:
    key: set_role
    name: SET ROLE
    aliases: [set role]
    purpose: Set active roles for the current MySQL session.
  syntax_templates:
    - "SET ROLE {DEFAULT | NONE | ALL | ALL EXCEPT role [, role] ... | role [, role] ...}"
  factor_layers:
    - tier: T1
      factors: [role_selection, role_state, expected_status]
  factors:
    role_selection:
      label: Role selection
      importance: important
      values: [default_roles, none, all_roles, all_except, explicit_list]
    role_state:
      label: Role state
      importance: important
      values: [granted, not_granted, missing]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    role_selection: default_roles
    role_state: granted
    expected_status: success
  coverage_policy:
    main_combination_axes: [role_selection, role_state, expected_status]
    non_main_factors: []
    python_expand_threshold: 80
  rendering:
    statement_template: "SET ROLE DEFAULT"
    verification_query_template: "SELECT CURRENT_ROLE()"
    factor_value_bindings: {}
```
