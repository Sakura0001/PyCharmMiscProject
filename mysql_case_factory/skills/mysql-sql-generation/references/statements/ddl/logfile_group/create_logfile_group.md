# CREATE LOGFILE GROUP

Official source: https://dev.mysql.com/doc/refman/8.0/en/create-logfile-group.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: logfile_group
  skill_name: create_logfile_group
  official_source: https://dev.mysql.com/doc/refman/8.0/en/create-logfile-group.html
  statement:
    key: create_logfile_group
    name: CREATE LOGFILE GROUP
    aliases: [create logfile group]
    purpose: Create an NDB Disk Data logfile group. Community InnoDB-only environments should keep this as skipped or negative coverage.
  syntax_templates:
    - "CREATE LOGFILE GROUP logfile_group ADD UNDOFILE 'undo_file' [INITIAL_SIZE [=] size] [ENGINE [=] engine_name]"
  factor_layers:
    - tier: T1
      factors: [engine_shape, undofile_shape, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    engine_shape:
      label: Storage engine branch
      importance: important
      values: [ndb, ndbcluster, innodb_invalid]
    undofile_shape:
      label: Undo file shape
      importance: important
      values: [relative_file, absolute_file, missing_undofile]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    execution_mode:
      label: Execution safety mode
      importance: non_important
      values: [skip_ndb, isolated_positive, safe_negative]
  defaults:
    engine_shape: ndb
    undofile_shape: relative_file
    expected_status: failure
    execution_mode: skip_ndb
  coverage_policy:
    main_combination_axes: [engine_shape, undofile_shape, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 100
  rendering:
    statement_template: "CREATE LOGFILE GROUP {logfile_group_name} ADD UNDOFILE '{logfile_group_name}.dat' ENGINE = NDB"
    verification_query_template: "SELECT LOGFILE_GROUP_NAME FROM INFORMATION_SCHEMA.FILES WHERE LOGFILE_GROUP_NAME = '{logfile_group_name}'"
    factor_value_bindings: {}
```
