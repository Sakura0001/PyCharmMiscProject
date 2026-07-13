# SET

Official source: https://dev.mysql.com/doc/refman/8.0/en/set-variable.html

```yaml
structured_config:
  kind: statement
  category: session
  domain: runtime_parameter
  skill_name: set
  official_source: https://dev.mysql.com/doc/refman/8.0/en/set-variable.html
  statement:
    key: set
    name: SET
    aliases: [set, set variable]
    purpose: Set MySQL user variables, local variables, system variables, names, character set, or transaction characteristics.
  syntax_templates:
    - "SET variable = expr [, variable = expr] ..."
    - "SET [GLOBAL | SESSION | PERSIST | PERSIST_ONLY] system_var_name = expr"
    - "SET NAMES charset_name [COLLATE collation_name]"
    - "SET CHARACTER SET charset_name"
  factor_layers:
    - tier: T1
      factors: [statement_branch, scope_shape, expected_status]
    - tier: T2
      factors: [value_shape, privilege_context]
  factors:
    statement_branch:
      label: SET branch
      importance: important
      values: [user_variable, session_system_variable, global_system_variable, persist_system_variable, set_names, set_character_set]
    scope_shape:
      label: Variable scope
      importance: important
      values: [implicit, session, global, persist, persist_only]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    value_shape:
      label: Assigned value
      importance: non_important
      values: [literal, expression, default_keyword]
    privilege_context:
      label: Privilege context
      importance: non_important
      values: [sufficient, insufficient]
  defaults:
    statement_branch: user_variable
    scope_shape: implicit
    expected_status: success
    value_shape: literal
    privilege_context: sufficient
  coverage_policy:
    main_combination_axes: [statement_branch, scope_shape, expected_status]
    non_main_factors: [value_shape, privilege_context]
    python_expand_threshold: 140
  rendering:
    statement_template: "SET @case_value = 1"
    verification_query_template: "SELECT @case_value"
    factor_value_bindings: {}
```
