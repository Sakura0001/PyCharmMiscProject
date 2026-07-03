# DROP SERVER

Official source: https://dev.mysql.com/doc/refman/8.0/en/drop-server.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: server
  skill_name: drop_server
  official_source: https://dev.mysql.com/doc/refman/8.0/en/drop-server.html
  statement:
    key: drop_server
    name: DROP SERVER
    aliases: [drop server]
    purpose: Drop FEDERATED server metadata.
  syntax_templates:
    - "DROP SERVER [IF EXISTS] server_name"
  factor_layers:
    - tier: T1
      factors: [if_exists, server_state, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    if_exists:
      label: IF EXISTS
      importance: important
      values: [omitted, present]
    server_state:
      label: Server metadata state
      importance: important
      values: [exists, missing]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    execution_mode:
      label: Execution safety mode
      importance: non_important
      values: [metadata_only, isolated_positive, safe_negative]
  defaults:
    if_exists: omitted
    server_state: exists
    expected_status: success
    execution_mode: metadata_only
  coverage_policy:
    main_combination_axes: [if_exists, server_state, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 80
  rendering:
    statement_template: "DROP SERVER {if_exists_sql}{server_name}"
    verification_query_template: "SELECT SERVER_NAME FROM INFORMATION_SCHEMA.SERVERS WHERE SERVER_NAME = '{server_name}'"
    factor_value_bindings:
      if_exists_sql:
        factor: if_exists
        values: {omitted: "", present: "IF EXISTS "}
```
