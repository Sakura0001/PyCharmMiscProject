# HELP

Official source: https://dev.mysql.com/doc/refman/8.0/en/help.html

```yaml
structured_config:
  kind: statement
  category: utility
  domain: help
  skill_name: help
  official_source: https://dev.mysql.com/doc/refman/8.0/en/help.html
  statement:
    key: help
    name: HELP
    aliases: [help]
    purpose: Query MySQL server-side help tables.
  syntax_templates:
    - "HELP 'search_string'"
  factor_layers:
    - tier: T1
      factors: [search_shape, help_table_state, expected_status]
  factors:
    search_shape:
      label: Search string
      importance: important
      values: [contents, category, topic, pattern, unknown]
    help_table_state:
      label: Help table state
      importance: important
      values: [initialized, missing]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    search_shape: topic
    help_table_state: initialized
    expected_status: success
  coverage_policy:
    main_combination_axes: [search_shape, help_table_state, expected_status]
    non_main_factors: []
    python_expand_threshold: 80
  rendering:
    statement_template: "HELP 'SELECT'"
    verification_query_template: ""
    factor_value_bindings: {}
```
