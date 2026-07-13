# GRANT

Official source: https://dev.mysql.com/doc/refman/8.0/en/grant.html

```yaml
structured_config:
  kind: statement
  category: dcl
  domain: privilege
  skill_name: grant
  official_source: https://dev.mysql.com/doc/refman/8.0/en/grant.html
  statement:
    key: grant
    name: GRANT
    aliases: [grant]
    purpose: Grant MySQL privileges, roles, or proxy privileges.
  syntax_templates:
    - "GRANT priv_type [(column_list)] [, priv_type [(column_list)]] ... ON object_type priv_level TO user_or_role [, user_or_role] ... [WITH GRANT OPTION]"
    - "GRANT role [, role] ... TO user_or_role [, user_or_role] ... [WITH ADMIN OPTION]"
  factor_layers:
    - tier: T1
      factors: [statement_branch, privilege_scope, grantee_shape, expected_status]
    - tier: T2
      factors: [grant_option_shape]
  factors:
    statement_branch:
      label: GRANT branch
      importance: important
      values: [privilege_grant, role_grant, proxy_grant]
    privilege_scope:
      label: Privilege scope
      importance: important
      values: [global, database, table, column, routine]
    grantee_shape:
      label: Grantee
      importance: important
      values: [user_account, role_name]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    grant_option_shape:
      label: Grant option
      importance: non_important
      values: [omitted, with_grant_option, with_admin_option]
  defaults:
    statement_branch: privilege_grant
    privilege_scope: table
    grantee_shape: user_account
    expected_status: success
    grant_option_shape: omitted
  coverage_policy:
    main_combination_axes: [statement_branch, privilege_scope, grantee_shape, expected_status]
    non_main_factors: [grant_option_shape]
    python_expand_threshold: 120
  rendering:
    statement_template: "GRANT SELECT ON {table_name} TO 'case_user'@'localhost'"
    verification_query_template: "SHOW GRANTS FOR 'case_user'@'localhost'"
    factor_value_bindings: {}
```
