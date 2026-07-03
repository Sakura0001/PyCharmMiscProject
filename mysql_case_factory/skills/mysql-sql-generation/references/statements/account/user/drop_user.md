# DROP USER

Official sources:

- https://dev.mysql.com/doc/refman/8.0/en/drop-user.html
- https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-22.html

```yaml
structured_config:
  kind: statement
  category: account
  domain: user
  skill_name: drop_user
  official_source: https://dev.mysql.com/doc/refman/8.0/en/drop-user.html
  statement:
    key: drop_user
    name: DROP USER
    aliases: [drop user]
    purpose: Drop MySQL user accounts, including 8.0.22 stored-object safety checks.
  syntax_templates:
    - "DROP USER [IF EXISTS] user [, user] ..."
  factor_layers:
    - tier: T1
      factors: [if_exists, account_state, stored_object_dependency, expected_status]
  factors:
    if_exists:
      label: IF EXISTS
      importance: important
      values: [omitted, present]
    account_state:
      label: Account state
      importance: important
      values: [exists, missing]
    stored_object_dependency:
      label: Stored object dependency
      importance: important
      values: [none, orphan_or_adopt_risk]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    if_exists: omitted
    account_state: exists
    stored_object_dependency: none
    expected_status: success
  coverage_policy:
    main_combination_axes: [if_exists, account_state, stored_object_dependency, expected_status]
    non_main_factors: []
    python_expand_threshold: 120
  rendering:
    statement_template: "DROP USER {if_exists_sql}'case_user'@'localhost'"
    verification_query_template: "SELECT USER, HOST FROM mysql.user WHERE USER = 'case_user' AND HOST = 'localhost'"
    factor_value_bindings:
      if_exists_sql:
        factor: if_exists
        values: {omitted: "", present: "IF EXISTS "}
```
