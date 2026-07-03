# ALTER RESOURCE GROUP

Official source: https://dev.mysql.com/doc/refman/8.0/en/alter-resource-group.html

```yaml
structured_config:
  kind: statement
  category: admin
  domain: resource_group
  skill_name: alter_resource_group
  official_source: https://dev.mysql.com/doc/refman/8.0/en/alter-resource-group.html
  statement:
    key: alter_resource_group
    name: ALTER RESOURCE GROUP
    aliases: [alter resource group]
    purpose: Alter VCPU, priority, or enablement for a MySQL resource group.
  syntax_templates:
    - "ALTER RESOURCE GROUP group_name [VCPU = vcpu_spec] [THREAD_PRIORITY = N] [ENABLE|DISABLE] [FORCE]"
  factor_layers:
    - tier: T1
      factors: [group_state, alteration_shape, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    group_state:
      label: Resource group state
      importance: important
      values: [exists, missing, builtin_group]
    alteration_shape:
      label: Alteration branch
      importance: important
      values: [change_vcpu, change_priority, enable_disable, force]
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
    alteration_shape: enable_disable
    expected_status: success
    execution_mode: metadata_only
  coverage_policy:
    main_combination_axes: [group_state, alteration_shape, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 100
  rendering:
    statement_template: "ALTER RESOURCE GROUP {resource_group_name} DISABLE"
    verification_query_template: "SELECT RESOURCE_GROUP_NAME FROM INFORMATION_SCHEMA.RESOURCE_GROUPS WHERE RESOURCE_GROUP_NAME = '{resource_group_name}'"
    factor_value_bindings: {}
```
