# DROP LOGFILE GROUP

Official source: https://dev.mysql.com/doc/refman/8.0/en/drop-logfile-group.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: logfile_group
  skill_name: drop_logfile_group
  official_source: https://dev.mysql.com/doc/refman/8.0/en/drop-logfile-group.html
  statement:
    key: drop_logfile_group
    name: DROP LOGFILE GROUP
    aliases: [drop logfile group]
    purpose: Drop an NDB Disk Data logfile group.
  syntax_templates:
    - "DROP LOGFILE GROUP logfile_group [ENGINE [=] engine_name]"
  factor_layers:
    - tier: T1
      factors: [logfile_group_state, engine_shape, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    logfile_group_state:
      label: Logfile group state
      importance: important
      values: [exists, missing, tablespace_depends]
    engine_shape:
      label: Storage engine branch
      importance: important
      values: [ndb, ndbcluster, innodb_invalid]
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
    engine_shape: ndb
    expected_status: failure
    execution_mode: skip_ndb
  coverage_policy:
    main_combination_axes: [logfile_group_state, engine_shape, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 80
  rendering:
    statement_template: "DROP LOGFILE GROUP {logfile_group_name} ENGINE = NDB"
    verification_query_template: "SELECT LOGFILE_GROUP_NAME FROM INFORMATION_SCHEMA.FILES WHERE LOGFILE_GROUP_NAME = '{logfile_group_name}'"
    factor_value_bindings: {}
```
