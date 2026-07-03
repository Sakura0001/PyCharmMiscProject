# ALTER TABLESPACE

Official source: https://dev.mysql.com/doc/refman/8.0/en/alter-tablespace.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: tablespace
  skill_name: alter_tablespace
  official_source: https://dev.mysql.com/doc/refman/8.0/en/alter-tablespace.html
  statement:
    key: alter_tablespace
    name: ALTER TABLESPACE
    aliases: [alter tablespace]
    purpose: Alter MySQL tablespace state or files.
  syntax_templates:
    - "ALTER TABLESPACE tablespace_name ADD DATAFILE 'file_name' [ENGINE [=] engine_name]"
    - "ALTER UNDO TABLESPACE tablespace_name SET {ACTIVE|INACTIVE}"
  factor_layers:
    - tier: T1
      factors: [tablespace_state, alteration_shape, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    tablespace_state:
      label: Tablespace state
      importance: important
      values: [exists, missing, non_empty]
    alteration_shape:
      label: Alteration branch
      importance: important
      values: [add_datafile, set_active, set_inactive, ndb_drop_file]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    execution_mode:
      label: Execution safety mode
      importance: non_important
      values: [isolated_positive, safe_negative, skip_ndb]
  defaults:
    tablespace_state: exists
    alteration_shape: add_datafile
    expected_status: success
    execution_mode: isolated_positive
  coverage_policy:
    main_combination_axes: [tablespace_state, alteration_shape, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 100
  rendering:
    statement_template: "ALTER TABLESPACE {tablespace_name} ADD DATAFILE '{tablespace_name}_extra.ibd' ENGINE = InnoDB"
    verification_query_template: "SELECT TABLESPACE_NAME FROM INFORMATION_SCHEMA.FILES WHERE TABLESPACE_NAME = '{tablespace_name}'"
    factor_value_bindings: {}
```
