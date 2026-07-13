# CREATE DATABASE

Official source: https://dev.mysql.com/doc/refman/8.0/en/create-database.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: database
  skill_name: create_database
  official_source: https://dev.mysql.com/doc/refman/8.0/en/create-database.html
  statement:
    key: create_database
    name: CREATE DATABASE
    aliases: [create database, create schema]
    purpose: Create a MySQL database or schema with MySQL 8.0.22 options.
  syntax_templates:
    - "CREATE {DATABASE | SCHEMA} [IF NOT EXISTS] db_name [create_option] ..."
  factor_layers:
    - tier: T1
      factors: [statement_branch, if_not_exists, expected_status]
    - tier: T2
      factors: [charset_option, collation_option, encryption_option]
  factors:
    statement_branch:
      label: DATABASE or SCHEMA keyword
      importance: important
      values: [database_keyword, schema_keyword]
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
    statement_branch: database_keyword
    if_not_exists: omitted
    expected_status: success
    charset_option: omitted
    collation_option: omitted
    encryption_option: omitted
  coverage_policy:
    main_combination_axes: [statement_branch, if_not_exists, expected_status]
    non_main_factors: [charset_option, collation_option, encryption_option]
    python_expand_threshold: 100
  rendering:
    statement_template: "CREATE {keyword_sql} {if_not_exists_sql}{database_name}{charset_sql}{collation_sql}{encryption_sql}"
    verification_query_template: "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{database_name}'"
    factor_value_bindings:
      keyword_sql:
        factor: statement_branch
        values: {database_keyword: "DATABASE", schema_keyword: "SCHEMA"}
      if_not_exists_sql:
        factor: if_not_exists
        values: {omitted: "", present: "IF NOT EXISTS "}
      charset_sql:
        factor: charset_option
        values: {omitted: "", utf8mb4: " CHARACTER SET utf8mb4"}
      collation_sql:
        factor: collation_option
        values: {omitted: "", utf8mb4_0900_ai_ci: " COLLATE utf8mb4_0900_ai_ci"}
      encryption_sql:
        factor: encryption_option
        values: {omitted: "", default: " ENCRYPTION DEFAULT", y: " ENCRYPTION 'Y'", n: " ENCRYPTION 'N'"}
```
