# RENAME USER

Official sources:

- https://dev.mysql.com/doc/refman/8.0/en/rename-user.html
- https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-22.html

```yaml
structured_config:
  kind: statement
  category: account
  domain: user
  skill_name: rename_user
  official_source: https://dev.mysql.com/doc/refman/8.0/en/rename-user.html
  statement:
    key: rename_user
    name: RENAME USER
    aliases: [rename user]
    purpose: Rename MySQL user accounts, including 8.0.22 stored-object safety checks.
  syntax_templates:
    - "RENAME USER old_user TO new_user [, old_user TO new_user] ..."
  factor_layers:
    - tier: T1
      factors: [source_account_state, target_account_state, stored_object_dependency, expected_status]
  factors:
    source_account_state:
      label: Source account state
      importance: important
      values: [exists, missing]
    target_account_state:
      label: Target account state
      importance: important
      values: [missing, already_exists]
    stored_object_dependency:
      label: Stored object adoption or orphan risk
      importance: important
      values: [none, orphan_or_adopt_risk]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    source_account_state: exists
    target_account_state: missing
    stored_object_dependency: none
    expected_status: success
  coverage_policy:
    main_combination_axes: [source_account_state, target_account_state, stored_object_dependency, expected_status]
    non_main_factors: []
    python_expand_threshold: 100
  rendering:
    statement_template: "RENAME USER 'case_user'@'localhost' TO 'case_user_renamed'@'localhost'"
    verification_query_template: "SELECT USER, HOST FROM mysql.user WHERE USER = 'case_user_renamed' AND HOST = 'localhost'"
    factor_value_bindings: {}
```
