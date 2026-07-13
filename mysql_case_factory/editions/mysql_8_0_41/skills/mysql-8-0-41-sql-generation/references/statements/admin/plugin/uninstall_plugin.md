# UNINSTALL PLUGIN

Official source: https://dev.mysql.com/doc/refman/8.0/en/uninstall-plugin.html

```yaml
structured_config:
  kind: statement
  category: admin
  domain: plugin
  skill_name: uninstall_plugin
  official_source: https://dev.mysql.com/doc/refman/8.0/en/uninstall-plugin.html
  statement:
    key: uninstall_plugin
    name: UNINSTALL PLUGIN
    aliases: [uninstall plugin]
    purpose: Uninstall a server plugin. Default coverage avoids unloading production plugins.
  syntax_templates:
    - "UNINSTALL PLUGIN plugin_name"
  factor_layers:
    - tier: T1
      factors: [plugin_state, dependency_shape, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    plugin_state:
      label: Plugin state
      importance: important
      values: [installed_test_plugin, missing, builtin_or_protected]
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
    plugin_state: missing
    dependency_shape: none
    expected_status: failure
    execution_mode: safe_negative
  coverage_policy:
    main_combination_axes: [plugin_state, dependency_shape, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 80
  rendering:
    statement_template: "UNINSTALL PLUGIN {plugin_name}"
    verification_query_template: "SELECT PLUGIN_NAME FROM INFORMATION_SCHEMA.PLUGINS WHERE PLUGIN_NAME = '{plugin_name}'"
    factor_value_bindings: {}
```
