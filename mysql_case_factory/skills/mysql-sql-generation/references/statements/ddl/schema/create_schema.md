# CREATE SCHEMA

Official source: https://dev.mysql.com/doc/refman/8.0/en/create-database.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: schema
  skill_name: create_schema
  official_source: https://dev.mysql.com/doc/refman/8.0/en/create-database.html
  statement:
    key: create_schema
    name: CREATE SCHEMA
    aliases: [create schema]
    purpose: MySQL CREATE SCHEMA synonym for CREATE DATABASE.
  syntax_templates:
    - "CREATE SCHEMA [IF NOT EXISTS] db_name [create_option] ..."
  factor_layers:
    - tier: T1
      factors: [if_not_exists, expected_status]
    - tier: T2
      factors: [charset_option, collation_option, encryption_option]
  factors:
    if_not_exists:
      label: IF NOT EXISTS
      importance: important
      values: [omitted, present]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    charset_option:
      label: CHARACTER SET option
      importance: non_important
      values: [omitted, utf8mb4]
    collation_option:
      label: COLLATE option
      importance: non_important
      values: [omitted, utf8mb4_0900_ai_ci]
    encryption_option:
      label: ENCRYPTION option
      importance: non_important
      values: [omitted, default, y, n]
  defaults:
    if_not_exists: omitted
    expected_status: success
    charset_option: omitted
    collation_option: omitted
    encryption_option: omitted
  coverage_policy:
    main_combination_axes: [if_not_exists, expected_status]
    non_main_factors: [charset_option, collation_option, encryption_option]
    python_expand_threshold: 80
  rendering:
    statement_template: "CREATE SCHEMA {if_not_exists_sql}{database_name}"
    verification_query_template: "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{database_name}'"
    factor_value_bindings:
      if_not_exists_sql:
        factor: if_not_exists
        values: {omitted: "", present: "IF NOT EXISTS "}
```
