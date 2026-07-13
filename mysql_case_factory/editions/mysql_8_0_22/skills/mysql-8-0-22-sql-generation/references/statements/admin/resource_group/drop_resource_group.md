# DROP RESOURCE GROUP

Official source: https://dev.mysql.com/doc/refman/8.0/en/drop-resource-group.html

```yaml
structured_config:
  kind: statement
  category: admin
  domain: resource_group
  skill_name: drop_resource_group
  official_source: https://dev.mysql.com/doc/refman/8.0/en/drop-resource-group.html
  statement:
    key: drop_resource_group
    name: DROP RESOURCE GROUP
    aliases: [drop resource group]
    purpose: Drop a MySQL resource group.
  syntax_templates:
    - "DROP RESOURCE GROUP group_name [FORCE]"
  factor_layers:
    - tier: T1
      factors: [group_state, force_shape, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    group_state:
      label: Resource group state
      importance: important
      values: [exists, missing, assigned_threads, builtin_group]
    force_shape:
      label: FORCE clause
      importance: important
      values: [omitted, force]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    execution_mode:
      label: Execution safety mode
      importance: non_important
      values: [metadata_only, isolated_positive, safe_negative]
  defaults:
    group_state: exists
    force_shape: omitted
    expected_status: success
    execution_mode: metadata_only
  coverage_policy:
    main_combination_axes: [group_state, force_shape, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 100
  rendering:
    statement_template: "DROP RESOURCE GROUP {resource_group_name}"
    verification_query_template: "SELECT RESOURCE_GROUP_NAME FROM INFORMATION_SCHEMA.RESOURCE_GROUPS WHERE RESOURCE_GROUP_NAME = '{resource_group_name}'"
    factor_value_bindings: {}
```
