# ALTER DATABASE

Official sources:

- https://dev.mysql.com/doc/refman/8.0/en/alter-database.html
- https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-22.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: database
  skill_name: alter_database
  official_source: https://dev.mysql.com/doc/refman/8.0/en/alter-database.html
  statement:
    key: alter_database
    name: ALTER DATABASE
    aliases: [alter database, alter schema]
    purpose: Alter MySQL database defaults and MySQL 8.0.22 read-only state.
  syntax_templates:
    - "ALTER {DATABASE | SCHEMA} [db_name] alter_option ..."
  factor_layers:
    - tier: T1
      factors: [statement_branch, database_name_shape, expected_status]
    - tier: T2
      factors: [charset_option, collation_option, encryption_option, read_only_option]
  factors:
    statement_branch:
      label: DATABASE or SCHEMA keyword
      importance: important
      values: [database_keyword, schema_keyword]
    database_name_shape:
      label: Database name
      importance: important
      values: [explicit, omitted_current]
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
    read_only_option:
      label: READ ONLY option
      importance: non_important
      values: [omitted, default, zero, one]
  defaults:
    statement_branch: database_keyword
    database_name_shape: explicit
    expected_status: success
    charset_option: utf8mb4
    collation_option: omitted
    encryption_option: omitted
    read_only_option: omitted
  coverage_policy:
    main_combination_axes: [statement_branch, database_name_shape, expected_status]
    non_main_factors: [charset_option, collation_option, encryption_option, read_only_option]
    python_expand_threshold: 100
  rendering:
    statement_template: "ALTER {keyword_sql} {database_name} CHARACTER SET utf8mb4"
    verification_query_template: "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{database_name}'"
    factor_value_bindings:
      keyword_sql:
        factor: statement_branch
        values: {database_keyword: "DATABASE", schema_keyword: "SCHEMA"}
```
