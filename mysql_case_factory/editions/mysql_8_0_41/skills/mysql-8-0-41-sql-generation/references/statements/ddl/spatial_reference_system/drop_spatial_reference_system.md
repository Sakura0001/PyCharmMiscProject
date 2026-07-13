# DROP SPATIAL REFERENCE SYSTEM

Official source: https://dev.mysql.com/doc/refman/8.0/en/drop-spatial-reference-system.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: spatial_reference_system
  skill_name: drop_spatial_reference_system
  official_source: https://dev.mysql.com/doc/refman/8.0/en/drop-spatial-reference-system.html
  statement:
    key: drop_spatial_reference_system
    name: DROP SPATIAL REFERENCE SYSTEM
    aliases: [drop spatial reference system, drop srs]
    purpose: Drop a user-defined spatial reference system by SRID.
  syntax_templates:
    - "DROP SPATIAL REFERENCE SYSTEM [IF EXISTS] srid"
  factor_layers:
    - tier: T1
      factors: [if_exists, srid_state, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    if_exists:
      label: IF EXISTS
      importance: important
      values: [omitted, present]
    srid_state:
      label: SRID state
      importance: important
      values: [user_defined_exists, missing, reserved_or_builtin, column_dependency]
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
    srid_state: user_defined_exists
    expected_status: success
    execution_mode: metadata_only
  coverage_policy:
    main_combination_axes: [if_exists, srid_state, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 100
  rendering:
    statement_template: "DROP SPATIAL REFERENCE SYSTEM {if_exists_sql}{srs_id}"
    verification_query_template: "SELECT SRS_ID FROM INFORMATION_SCHEMA.ST_SPATIAL_REFERENCE_SYSTEMS WHERE SRS_ID = {srs_id}"
    factor_value_bindings:
      if_exists_sql:
        factor: if_exists
        values: {omitted: "", present: "IF EXISTS "}
```
