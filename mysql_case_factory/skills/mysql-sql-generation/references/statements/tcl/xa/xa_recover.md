# XA RECOVER

Official source: https://dev.mysql.com/doc/refman/8.0/en/xa-statements.html

```yaml
structured_config:
  kind: statement
  category: tcl
  domain: xa
  skill_name: xa_recover
  official_source: https://dev.mysql.com/doc/refman/8.0/en/xa-statements.html
  statement:
    key: xa_recover
    name: XA RECOVER
    aliases: [xa recover]
    purpose: List prepared XA transaction branches.
  syntax_templates:
    - "XA RECOVER [CONVERT XID]"
  factor_layers:
    - tier: T1
      factors: [convert_xid_shape, privilege_context, expected_status]
  factors:
    convert_xid_shape:
      label: CONVERT XID
      importance: important
      values: [omitted, convert_xid]
    privilege_context:
      label: XA_RECOVER_ADMIN privilege
      importance: important
      values: [sufficient, insufficient]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    convert_xid_shape: omitted
    privilege_context: sufficient
    expected_status: success
  coverage_policy:
    main_combination_axes: [convert_xid_shape, privilege_context, expected_status]
    non_main_factors: []
    python_expand_threshold: 40
  rendering:
    statement_template: "XA RECOVER"
    verification_query_template: ""
    factor_value_bindings: {}
```
