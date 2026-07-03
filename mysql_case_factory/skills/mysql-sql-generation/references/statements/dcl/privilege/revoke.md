# REVOKE

Official source: https://dev.mysql.com/doc/refman/8.0/en/revoke.html

```yaml
structured_config:
  kind: statement
  category: dcl
  domain: privilege
  skill_name: revoke
  official_source: https://dev.mysql.com/doc/refman/8.0/en/revoke.html
  statement:
    key: revoke
    name: REVOKE
    aliases: [revoke]
    purpose: Revoke MySQL privileges, roles, or proxy privileges.
  syntax_templates:
    - "REVOKE priv_type [(column_list)] [, priv_type [(column_list)]] ... ON object_type priv_level FROM user_or_role [, user_or_role] ..."
    - "REVOKE ALL [PRIVILEGES], GRANT OPTION FROM user_or_role [, user_or_role] ..."
    - "REVOKE role [, role] ... FROM user_or_role [, user_or_role] ..."
  factor_layers:
    - tier: T1
      factors: [statement_branch, privilege_scope, grantee_shape, expected_status]
    - tier: T2
      factors: [grant_option_shape]
  factors:
    statement_branch:
      label: REVOKE branch
      importance: important
      values: [privilege_revoke, all_privileges_revoke, role_revoke, proxy_revoke]
    privilege_scope:
      label: Privilege scope
      importance: important
      values: [global, database, table, column, routine]
    grantee_shape:
      label: Grantee
      importance: important
      values: [user_account, role_name, missing_user]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    grant_option_shape:
      label: Grant option branch
      importance: non_important
      values: [omitted, grant_option_only]
  defaults:
    statement_branch: privilege_revoke
    privilege_scope: table
    grantee_shape: user_account
    expected_status: success
    grant_option_shape: omitted
  coverage_policy:
    main_combination_axes: [statement_branch, privilege_scope, grantee_shape, expected_status]
    non_main_factors: [grant_option_shape]
    python_expand_threshold: 140
  rendering:
    statement_template: "REVOKE SELECT ON {table_name} FROM 'case_user'@'localhost'"
    verification_query_template: "SHOW GRANTS FOR 'case_user'@'localhost'"
    factor_value_bindings: {}
```
