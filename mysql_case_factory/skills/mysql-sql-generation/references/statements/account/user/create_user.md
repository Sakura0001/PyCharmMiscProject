# CREATE USER

Official sources:

- https://dev.mysql.com/doc/refman/8.0/en/create-user.html
- https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-22.html

```yaml
structured_config:
  kind: statement
  category: account
  domain: user
  skill_name: create_user
  official_source: https://dev.mysql.com/doc/refman/8.0/en/create-user.html
  statement:
    key: create_user
    name: CREATE USER
    aliases: [create user]
    purpose: Create MySQL user accounts with 8.0.22 authentication and account options.
  syntax_templates:
    - "CREATE USER [IF NOT EXISTS] user [auth_option] [, user [auth_option]] ... [default_role_clause] [require_clause] [connect_options] [account_options] [COMMENT 'comment' | ATTRIBUTE 'json_object']"
  factor_layers:
    - tier: T1
      factors: [if_not_exists, account_name_shape, auth_shape, expected_status]
    - tier: T2
      factors: [default_role_shape, ssl_require_shape, account_lock_shape, password_lifecycle_shape]
  factors:
    if_not_exists:
      label: IF NOT EXISTS
      importance: important
      values: [omitted, present]
    account_name_shape:
      label: user@host account name
      importance: important
      values: [user_localhost, user_percent_host, quoted_user]
    auth_shape:
      label: Authentication option
      importance: important
      values: [omitted, identified_by_password, identified_with_plugin, random_password]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    default_role_shape:
      label: DEFAULT ROLE clause
      importance: non_important
      values: [omitted, default_role]
    ssl_require_shape:
      label: REQUIRE clause
      importance: non_important
      values: [omitted, ssl, x509]
    account_lock_shape:
      label: ACCOUNT LOCK / UNLOCK
      importance: non_important
      values: [omitted, lock, unlock]
    password_lifecycle_shape:
      label: Password lifecycle
      importance: non_important
      values: [omitted, password_expire, password_history, failed_login_attempts]
  defaults:
    if_not_exists: omitted
    account_name_shape: user_localhost
    auth_shape: identified_by_password
    expected_status: success
    default_role_shape: omitted
    ssl_require_shape: omitted
    account_lock_shape: omitted
    password_lifecycle_shape: omitted
  coverage_policy:
    main_combination_axes: [if_not_exists, account_name_shape, auth_shape, expected_status]
    non_main_factors: [default_role_shape, ssl_require_shape, account_lock_shape, password_lifecycle_shape]
    python_expand_threshold: 180
  rendering:
    statement_template: "CREATE USER {if_not_exists_sql}'case_user'@'localhost' IDENTIFIED BY 'case_password_123'"
    verification_query_template: "SELECT USER, HOST FROM mysql.user WHERE USER = 'case_user' AND HOST = 'localhost'"
    factor_value_bindings:
      if_not_exists_sql:
        factor: if_not_exists
        values: {omitted: "", present: "IF NOT EXISTS "}
```
