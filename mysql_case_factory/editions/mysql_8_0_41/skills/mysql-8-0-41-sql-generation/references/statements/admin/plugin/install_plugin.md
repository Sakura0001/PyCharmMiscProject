# INSTALL PLUGIN

Official source: https://dev.mysql.com/doc/refman/8.0/en/install-plugin.html

```yaml
structured_config:
  kind: statement
  category: admin
  domain: plugin
  skill_name: install_plugin
  official_source: https://dev.mysql.com/doc/refman/8.0/en/install-plugin.html
  statement:
    key: install_plugin
    name: INSTALL PLUGIN
    aliases: [install plugin]
    purpose: Install a server plugin from a shared library. Default coverage should avoid loading arbitrary libraries.
  syntax_templates:
    - "INSTALL PLUGIN plugin_name SONAME 'shared_library_name'"
  factor_layers:
    - tier: T1
      factors: [plugin_state, library_shape, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    plugin_state:
      label: Plugin state
      importance: important
      values: [not_installed, already_installed]
    library_shape:
      label: Shared library shape
      importance: important
      values: [existing_library, missing_library, invalid_soname]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    execution_mode:
      label: Execution safety mode
      importance: non_important
      values: [safe_negative, isolated_positive, skip_dynamic_load]
  defaults:
    plugin_state: not_installed
    library_shape: missing_library
    expected_status: failure
    execution_mode: safe_negative
  coverage_policy:
    main_combination_axes: [plugin_state, library_shape, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 80
  rendering:
    statement_template: "INSTALL PLUGIN {plugin_name} SONAME 'missing_mysql_case_plugin.so'"
    verification_query_template: "SELECT PLUGIN_NAME FROM INFORMATION_SCHEMA.PLUGINS WHERE PLUGIN_NAME = '{plugin_name}'"
    factor_value_bindings: {}
```
