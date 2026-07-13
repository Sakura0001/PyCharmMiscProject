# XA PREPARE

Official source: https://dev.mysql.com/doc/refman/8.0/en/xa-statements.html

```yaml
structured_config:
  kind: statement
  category: tcl
  domain: xa
  skill_name: xa_prepare
  official_source: https://dev.mysql.com/doc/refman/8.0/en/xa-statements.html
  statement:
    key: xa_prepare
    name: XA PREPARE
    aliases: [xa prepare]
    purpose: Prepare an ended XA transaction branch.
  syntax_templates:
    - "XA PREPARE xid"
  factor_layers:
    - tier: T1
      factors: [xid_state, expected_status]
  factors:
    xid_state:
      label: XID state
      importance: important
      values: [ended_xid, active_xid, missing_xid, already_prepared]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    xid_state: ended_xid
    expected_status: success
  coverage_policy:
    main_combination_axes: [xid_state, expected_status]
    non_main_factors: []
    python_expand_threshold: 60
  rendering:
    statement_template: "XA PREPARE '{xa_xid}'"
    verification_query_template: ""
    factor_value_bindings: {}
```
