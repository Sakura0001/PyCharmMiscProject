# CREATE SERVER

Official source: https://dev.mysql.com/doc/refman/8.0/en/create-server.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: server
  skill_name: create_server
  official_source: https://dev.mysql.com/doc/refman/8.0/en/create-server.html
  statement:
    key: create_server
    name: CREATE SERVER
    aliases: [create server]
    purpose: Create FEDERATED server metadata. Requires elevated privileges and is not written to the binary log.
  syntax_templates:
    - "CREATE SERVER server_name FOREIGN DATA WRAPPER wrapper_name OPTIONS (option [, option] ...)"
  factor_layers:
    - tier: T1
      factors: [server_state, option_shape, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    server_state:
      label: Server metadata state
      importance: important
      values: [new_name, duplicate_name]
    option_shape:
      label: OPTIONS shape
      importance: important
      values: [minimal_host_db_user, full_connection, missing_required_option]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    execution_mode:
      label: Execution safety mode
      importance: non_important
      values: [metadata_only, isolated_positive, safe_negative]
  defaults:
    server_state: new_name
    option_shape: minimal_host_db_user
    expected_status: success
    execution_mode: metadata_only
  coverage_policy:
    main_combination_axes: [server_state, option_shape, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 100
  rendering:
    statement_template: "CREATE SERVER {server_name} FOREIGN DATA WRAPPER mysql OPTIONS (HOST '127.0.0.1', DATABASE 'test', USER 'mysql_case')"
    verification_query_template: "SELECT SERVER_NAME FROM INFORMATION_SCHEMA.SERVERS WHERE SERVER_NAME = '{server_name}'"
    factor_value_bindings: {}
```
