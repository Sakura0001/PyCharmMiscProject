# ALTER LOGFILE GROUP

Official source: https://dev.mysql.com/doc/refman/8.0/en/alter-logfile-group.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: logfile_group
  skill_name: alter_logfile_group
  official_source: https://dev.mysql.com/doc/refman/8.0/en/alter-logfile-group.html
  statement:
    key: alter_logfile_group
    name: ALTER LOGFILE GROUP
    aliases: [alter logfile group]
    purpose: Add an undo file to an NDB Disk Data logfile group.
  syntax_templates:
    - "ALTER LOGFILE GROUP logfile_group ADD UNDOFILE 'undo_file' [INITIAL_SIZE [=] size] [ENGINE [=] engine_name]"
  factor_layers:
    - tier: T1
      factors: [logfile_group_state, undofile_shape, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    logfile_group_state:
      label: Logfile group state
      importance: important
      values: [exists, missing, wrong_engine]
    undofile_shape:
      label: Undo file shape
      importance: important
      values: [relative_file, duplicate_file, missing_undofile]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    execution_mode:
      label: Execution safety mode
      importance: non_important
      values: [skip_ndb, isolated_positive, safe_negative]
  defaults:
    logfile_group_state: exists
    undofile_shape: relative_file
    expected_status: failure
    execution_mode: skip_ndb
  coverage_policy:
    main_combination_axes: [logfile_group_state, undofile_shape, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 80
  rendering:
    statement_template: "ALTER LOGFILE GROUP {logfile_group_name} ADD UNDOFILE '{logfile_group_name}_extra.dat' ENGINE = NDB"
    verification_query_template: "SELECT LOGFILE_GROUP_NAME FROM INFORMATION_SCHEMA.FILES WHERE LOGFILE_GROUP_NAME = '{logfile_group_name}'"
    factor_value_bindings: {}
```
