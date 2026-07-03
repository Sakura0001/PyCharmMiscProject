# CREATE SPATIAL REFERENCE SYSTEM

Official source: https://dev.mysql.com/doc/refman/8.0/en/create-spatial-reference-system.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: spatial_reference_system
  skill_name: create_spatial_reference_system
  official_source: https://dev.mysql.com/doc/refman/8.0/en/create-spatial-reference-system.html
  statement:
    key: create_spatial_reference_system
    name: CREATE SPATIAL REFERENCE SYSTEM
    aliases: [create spatial reference system, create srs]
    purpose: Create a user-defined spatial reference system by SRID.
  syntax_templates:
    - "CREATE [OR REPLACE] SPATIAL REFERENCE SYSTEM [IF NOT EXISTS] srid srs_attribute ..."
  factor_layers:
    - tier: T1
      factors: [replace_shape, if_not_exists, srid_shape, expected_status]
    - tier: T2
      factors: [attribute_shape]
  factors:
    replace_shape:
      label: OR REPLACE
      importance: important
      values: [omitted, or_replace]
    if_not_exists:
      label: IF NOT EXISTS
      importance: important
      values: [omitted, present]
    srid_shape:
      label: SRID shape
      importance: important
      values: [user_range, reserved_range, duplicate_srid]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    attribute_shape:
      label: SRS attributes
      importance: non_important
      values: [required_geographic, required_projected, missing_attribute, invalid_wkt]
  defaults:
    replace_shape: omitted
    if_not_exists: omitted
    srid_shape: user_range
    expected_status: success
    attribute_shape: required_geographic
  coverage_policy:
    main_combination_axes: [replace_shape, if_not_exists, srid_shape, expected_status]
    non_main_factors: [attribute_shape]
    python_expand_threshold: 120
  rendering:
    statement_template: "CREATE SPATIAL REFERENCE SYSTEM {srs_id} NAME '{spatial_ref_name}' DEFINITION 'GEOGCS[\"{spatial_ref_name}\",DATUM[\"D\",SPHEROID[\"S\",6378137,298.257223563]],PRIMEM[\"Greenwich\",0],UNIT[\"degree\",0.017453292519943278]]' ORGANIZATION 'MYSQL_CASE_FACTORY' IDENTIFIED BY {srs_id}"
    verification_query_template: "SELECT SRS_ID FROM INFORMATION_SCHEMA.ST_SPATIAL_REFERENCE_SYSTEMS WHERE SRS_ID = {srs_id}"
    factor_value_bindings: {}
```
