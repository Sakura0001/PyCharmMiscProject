# ALTER SERVER

Official source: https://dev.mysql.com/doc/refman/8.0/en/alter-server.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: server
  skill_name: alter_server
  official_source: https://dev.mysql.com/doc/refman/8.0/en/alter-server.html
  statement:
    key: alter_server
    name: ALTER SERVER
    aliases: [alter server]
    purpose: Alter FEDERATED server metadata options.
  syntax_templates:
    - "ALTER SERVER server_name OPTIONS (option [, option] ...)"
  factor_layers:
    - tier: T1
      factors: [server_state, option_update_shape, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    server_state:
      label: Server metadata state
      importance: important
      values: [exists, missing]
    option_update_shape:
      label: OPTIONS update
      importance: important
      values: [change_host, change_database, invalid_option]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    execution_mode:
      label: Execution safety mode
      importance: non_important
      values: [metadata_only, isolated_positive, safe_negative]
  defaults:
    server_state: exists
    option_update_shape: change_host
    expected_status: success
    execution_mode: metadata_only
  coverage_policy:
    main_combination_axes: [server_state, option_update_shape, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 80
  rendering:
    statement_template: "ALTER SERVER {server_name} OPTIONS (HOST 'localhost')"
    verification_query_template: "SELECT SERVER_NAME FROM INFORMATION_SCHEMA.SERVERS WHERE SERVER_NAME = '{server_name}'"
    factor_value_bindings: {}
```
