# UNINSTALL COMPONENT

Official source: https://dev.mysql.com/doc/refman/8.0/en/uninstall-component.html

```yaml
structured_config:
  kind: statement
  category: admin
  domain: component
  skill_name: uninstall_component
  official_source: https://dev.mysql.com/doc/refman/8.0/en/uninstall-component.html
  statement:
    key: uninstall_component
    name: UNINSTALL COMPONENT
    aliases: [uninstall component]
    purpose: Uninstall MySQL components by URN.
  syntax_templates:
    - "UNINSTALL COMPONENT 'component_urn' [, 'component_urn'] ..."
  factor_layers:
    - tier: T1
      factors: [component_state, dependency_shape, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    component_state:
      label: Component state
      importance: important
      values: [installed_test_component, missing, protected_component]
    dependency_shape:
      label: Dependency shape
      importance: important
      values: [none, active_dependency]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    execution_mode:
      label: Execution safety mode
      importance: non_important
      values: [safe_negative, isolated_positive, skip_dynamic_load]
  defaults:
    component_state: missing
    dependency_shape: none
    expected_status: failure
    execution_mode: safe_negative
  coverage_policy:
    main_combination_axes: [component_state, dependency_shape, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 80
  rendering:
    statement_template: "UNINSTALL COMPONENT '{component_urn}'"
    verification_query_template: "SELECT URN FROM mysql.component WHERE URN = '{component_urn}'"
    factor_value_bindings: {}
```
