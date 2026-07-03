# ALTER USER

Official source: https://dev.mysql.com/doc/refman/8.0/en/alter-user.html

```yaml
structured_config:
  kind: statement
  category: account
  domain: user
  skill_name: alter_user
  official_source: https://dev.mysql.com/doc/refman/8.0/en/alter-user.html
  statement:
    key: alter_user
    name: ALTER USER
    aliases: [alter user]
    purpose: Alter MySQL user authentication, password lifecycle, account lock, and attributes available in 8.0.22.
  syntax_templates:
    - "ALTER USER [IF EXISTS] user [auth_option] [, user [auth_option]] ... [require_clause] [connect_options] [account_options] [COMMENT 'comment' | ATTRIBUTE 'json_object']"
  factor_layers:
    - tier: T1
      factors: [if_exists, account_state, alter_branch, expected_status]
    - tier: T2
      factors: [auth_shape, password_lifecycle_shape, account_lock_shape, attribute_shape]
  factors:
    if_exists:
      label: IF EXISTS
      importance: important
      values: [omitted, present]
    account_state:
      label: Account state
      importance: important
      values: [exists, missing]
    alter_branch:
      label: ALTER USER branch
      importance: important
      values: [authentication, password_expire, account_lock, resource_limits, comment_attribute]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    auth_shape:
      label: Authentication shape
      importance: non_important
      values: [identified_by_password, identified_with_plugin, discard_old_password]
    password_lifecycle_shape:
      label: Password lifecycle
      importance: non_important
      values: [omitted, password_expire, password_history, password_reuse_interval]
    account_lock_shape:
      label: Account lock
      importance: non_important
      values: [omitted, lock, unlock]
    attribute_shape:
      label: COMMENT or ATTRIBUTE
      importance: non_important
      values: [omitted, comment, attribute_json]
  defaults:
    if_exists: omitted
    account_state: exists
    alter_branch: authentication
    expected_status: success
    auth_shape: identified_by_password
    password_lifecycle_shape: omitted
    account_lock_shape: omitted
    attribute_shape: omitted
  coverage_policy:
    main_combination_axes: [if_exists, account_state, alter_branch, expected_status]
    non_main_factors: [auth_shape, password_lifecycle_shape, account_lock_shape, attribute_shape]
    python_expand_threshold: 180
  rendering:
    statement_template: "ALTER USER {if_exists_sql}'case_user'@'localhost' IDENTIFIED BY 'case_password_456'"
    verification_query_template: "SELECT USER, HOST FROM mysql.user WHERE USER = 'case_user' AND HOST = 'localhost'"
    factor_value_bindings:
      if_exists_sql:
        factor: if_exists
        values: {omitted: "", present: "IF EXISTS "}
```
