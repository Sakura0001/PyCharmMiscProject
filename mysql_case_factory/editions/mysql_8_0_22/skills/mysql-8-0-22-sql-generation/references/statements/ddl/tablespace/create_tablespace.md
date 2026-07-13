# CREATE TABLESPACE

Official source: https://dev.mysql.com/doc/refman/8.0/en/create-tablespace.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: tablespace
  skill_name: create_tablespace
  official_source: https://dev.mysql.com/doc/refman/8.0/en/create-tablespace.html
  statement:
    key: create_tablespace
    name: CREATE TABLESPACE
    aliases: [create tablespace]
    purpose: Create MySQL tablespaces. InnoDB metadata scenarios are separable from filesystem and NDB-only execution.
  syntax_templates:
    - "CREATE TABLESPACE tablespace_name ADD DATAFILE 'file_name' [ENGINE [=] engine_name]"
    - "CREATE UNDO TABLESPACE tablespace_name ADD DATAFILE 'file_name'"
  factor_layers:
    - tier: T1
      factors: [tablespace_kind, datafile_shape, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    tablespace_kind:
      label: Tablespace kind
      importance: important
      values: [innodb_general, undo, ndb_disk_data]
    datafile_shape:
      label: Datafile shape
      importance: important
      values: [relative_file, absolute_file, missing_datafile]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    execution_mode:
      label: Execution safety mode
      importance: non_important
      values: [isolated_positive, safe_negative, skip_ndb]
  defaults:
    tablespace_kind: innodb_general
    datafile_shape: relative_file
    expected_status: success
    execution_mode: isolated_positive
  coverage_policy:
    main_combination_axes: [tablespace_kind, datafile_shape, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 120
  rendering:
    statement_template: "CREATE TABLESPACE {tablespace_name} ADD DATAFILE '{tablespace_name}.ibd' ENGINE = InnoDB"
    verification_query_template: "SELECT TABLESPACE_NAME FROM INFORMATION_SCHEMA.FILES WHERE TABLESPACE_NAME = '{tablespace_name}'"
    factor_value_bindings: {}
```
