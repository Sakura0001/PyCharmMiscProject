# SET RESOURCE GROUP

Official source: https://dev.mysql.com/doc/refman/8.0/en/set-resource-group.html

```yaml
structured_config:
  kind: statement
  category: admin
  domain: resource_group
  skill_name: set_resource_group
  official_source: https://dev.mysql.com/doc/refman/8.0/en/set-resource-group.html
  statement:
    key: set_resource_group
    name: SET RESOURCE GROUP
    aliases: [set resource group]
    purpose: Assign the current session or named threads to a resource group.
  syntax_templates:
    - "SET RESOURCE GROUP group_name [FOR thread_id [, thread_id] ...]"
  factor_layers:
    - tier: T1
      factors: [assignment_target, group_state, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    assignment_target:
      label: Assignment target
      importance: important
      values: [current_thread, explicit_thread, invalid_thread]
    group_state:
      label: Resource group state
      importance: important
      values: [exists, missing, disabled_group]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    execution_mode:
      label: Execution safety mode
      importance: non_important
      values: [metadata_only, isolated_positive, safe_negative]
  defaults:
    assignment_target: current_thread
    group_state: exists
    expected_status: success
    execution_mode: metadata_only
  coverage_policy:
    main_combination_axes: [assignment_target, group_state, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 100
  rendering:
    statement_template: "SET RESOURCE GROUP {resource_group_name}"
    verification_query_template: "SELECT RESOURCE_GROUP_NAME FROM INFORMATION_SCHEMA.RESOURCE_GROUPS WHERE RESOURCE_GROUP_NAME = '{resource_group_name}'"
    factor_value_bindings: {}
```
