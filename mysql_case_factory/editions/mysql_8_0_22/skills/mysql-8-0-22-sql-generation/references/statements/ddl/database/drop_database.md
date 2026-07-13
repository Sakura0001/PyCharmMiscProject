# DROP DATABASE

Official source: https://dev.mysql.com/doc/refman/8.0/en/drop-database.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: database
  skill_name: drop_database
  official_source: https://dev.mysql.com/doc/refman/8.0/en/drop-database.html
  statement:
    key: drop_database
    name: DROP DATABASE
    aliases: [drop database, drop schema]
    purpose: Drop a MySQL database or schema.
  syntax_templates:
    - "DROP {DATABASE | SCHEMA} [IF EXISTS] db_name"
  factor_layers:
    - tier: T1
      factors: [statement_branch, if_exists, database_state, expected_status]
  factors:
    statement_branch:
      label: DATABASE or SCHEMA keyword
      importance: important
      values: [database_keyword, schema_keyword]
    if_exists:
      label: IF EXISTS
      importance: important
      values: [omitted, present]
    database_state:
      label: Database state
      importance: important
      values: [exists, missing]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    statement_branch: database_keyword
    if_exists: omitted
    database_state: exists
    expected_status: success
  coverage_policy:
    main_combination_axes: [statement_branch, if_exists, database_state, expected_status]
    non_main_factors: []
    python_expand_threshold: 100
  rendering:
    statement_template: "DROP {keyword_sql} {if_exists_sql}{database_name}"
    verification_query_template: "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{database_name}'"
    factor_value_bindings:
      keyword_sql:
        factor: statement_branch
        values: {database_keyword: "DATABASE", schema_keyword: "SCHEMA"}
      if_exists_sql:
        factor: if_exists
        values: {omitted: "", present: "IF EXISTS "}
```
