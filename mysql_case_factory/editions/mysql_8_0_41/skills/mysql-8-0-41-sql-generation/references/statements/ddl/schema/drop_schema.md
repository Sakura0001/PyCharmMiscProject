# DROP SCHEMA

Official source: https://dev.mysql.com/doc/refman/8.0/en/drop-database.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: schema
  skill_name: drop_schema
  official_source: https://dev.mysql.com/doc/refman/8.0/en/drop-database.html
  statement:
    key: drop_schema
    name: DROP SCHEMA
    aliases: [drop schema]
    purpose: MySQL DROP SCHEMA synonym for DROP DATABASE.
  syntax_templates:
    - "DROP SCHEMA [IF EXISTS] db_name"
  factor_layers:
    - tier: T1
      factors: [if_exists, schema_state, expected_status]
  factors:
    if_exists:
      label: IF EXISTS
      importance: important
      values: [omitted, present]
    schema_state:
      label: Schema state
      importance: important
      values: [exists, missing]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    if_exists: omitted
    schema_state: exists
    expected_status: success
  coverage_policy:
    main_combination_axes: [if_exists, schema_state, expected_status]
    non_main_factors: []
    python_expand_threshold: 80
  rendering:
    statement_template: "DROP SCHEMA {if_exists_sql}{database_name}"
    verification_query_template: "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{database_name}'"
    factor_value_bindings:
      if_exists_sql:
        factor: if_exists
        values: {omitted: "", present: "IF EXISTS "}
```
