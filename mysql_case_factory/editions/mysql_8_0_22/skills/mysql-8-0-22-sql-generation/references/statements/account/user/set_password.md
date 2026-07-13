# SET PASSWORD

Official source: https://dev.mysql.com/doc/refman/8.0/en/set-password.html

```yaml
structured_config:
  kind: statement
  category: account
  domain: user
  skill_name: set_password
  official_source: https://dev.mysql.com/doc/refman/8.0/en/set-password.html
  statement:
    key: set_password
    name: SET PASSWORD
    aliases: [set password]
    purpose: Assign passwords for MySQL accounts.
  syntax_templates:
    - "SET PASSWORD [FOR user] = auth_option"
  factor_layers:
    - tier: T1
      factors: [target_account_shape, password_shape, expected_status]
  factors:
    target_account_shape:
      label: Target account
      importance: important
      values: [current_user, explicit_user, missing_user]
    password_shape:
      label: Password assignment
      importance: important
      values: [plain_text_password, random_password]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    target_account_shape: explicit_user
    password_shape: plain_text_password
    expected_status: success
  coverage_policy:
    main_combination_axes: [target_account_shape, password_shape, expected_status]
    non_main_factors: []
    python_expand_threshold: 80
  rendering:
    statement_template: "SET PASSWORD FOR 'case_user'@'localhost' = 'case_password_789'"
    verification_query_template: "SELECT USER, HOST FROM mysql.user WHERE USER = 'case_user' AND HOST = 'localhost'"
    factor_value_bindings: {}
```
