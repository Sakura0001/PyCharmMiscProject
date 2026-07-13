# INSTALL COMPONENT

Official source: https://dev.mysql.com/doc/refman/8.0/en/install-component.html

```yaml
structured_config:
  kind: statement
  category: admin
  domain: component
  skill_name: install_component
  official_source: https://dev.mysql.com/doc/refman/8.0/en/install-component.html
  statement:
    key: install_component
    name: INSTALL COMPONENT
    aliases: [install component]
    purpose: Install MySQL components by URN, including the SET clause added in 8.0.33.
  syntax_templates:
    - "INSTALL COMPONENT 'component_urn' [, 'component_urn'] ..."
    - "INSTALL COMPONENT 'component_urn' [, 'component_urn'] ... SET [GLOBAL | PERSIST] component_variable = expr"
  factor_layers:
    - tier: T1
      factors: [component_count, urn_shape, expected_status]
    - tier: T5
      factors: [set_clause, execution_mode]
  factors:
    component_count:
      label: Component count
      importance: important
      values: [single, multiple]
    urn_shape:
      label: Component URN shape
      importance: important
      values: [valid_existing, missing_component, invalid_urn]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    execution_mode:
      label: Execution safety mode
      importance: non_important
      values: [safe_negative, isolated_positive, skip_dynamic_load]
    set_clause:
      label: Component variable SET clause
      importance: non_important
      values: [omitted, global, persist]
  defaults:
    component_count: single
    urn_shape: missing_component
    expected_status: failure
    execution_mode: safe_negative
    set_clause: omitted
  coverage_policy:
    main_combination_axes: [component_count, urn_shape, expected_status]
    non_main_factors: [set_clause, execution_mode]
    python_expand_threshold: 80
  rendering:
    statement_template: "INSTALL COMPONENT '{component_urn}'"
    verification_query_template: "SELECT URN FROM mysql.component WHERE URN = '{component_urn}'"
    factor_value_bindings: {}
```
