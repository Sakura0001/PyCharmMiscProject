# CREATE RESOURCE GROUP

Official source: https://dev.mysql.com/doc/refman/8.0/en/create-resource-group.html

```yaml
structured_config:
  kind: statement
  category: admin
  domain: resource_group
  skill_name: create_resource_group
  official_source: https://dev.mysql.com/doc/refman/8.0/en/create-resource-group.html
  statement:
    key: create_resource_group
    name: CREATE RESOURCE GROUP
    aliases: [create resource group]
    purpose: Create a MySQL resource group. Runtime behavior is platform and privilege sensitive.
  syntax_templates:
    - "CREATE RESOURCE GROUP group_name TYPE = {SYSTEM|USER} [VCPU = vcpu_spec] [THREAD_PRIORITY = N] [ENABLE|DISABLE]"
  factor_layers:
    - tier: T1
      factors: [group_type, vcpu_shape, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    group_type:
      label: Resource group type
      importance: important
      values: [system, user]
    vcpu_shape:
      label: VCPU shape
      importance: important
      values: [omitted, single_cpu, range, invalid_cpu]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    execution_mode:
      label: Execution safety mode
      importance: non_important
      values: [metadata_only, isolated_positive, safe_negative]
  defaults:
    group_type: user
    vcpu_shape: omitted
    expected_status: success
    execution_mode: metadata_only
  coverage_policy:
    main_combination_axes: [group_type, vcpu_shape, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 100
  rendering:
    statement_template: "CREATE RESOURCE GROUP {resource_group_name} TYPE = USER"
    verification_query_template: "SELECT RESOURCE_GROUP_NAME FROM INFORMATION_SCHEMA.RESOURCE_GROUPS WHERE RESOURCE_GROUP_NAME = '{resource_group_name}'"
    factor_value_bindings: {}
```
