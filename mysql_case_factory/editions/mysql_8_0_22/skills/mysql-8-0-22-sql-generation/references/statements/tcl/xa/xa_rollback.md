# XA ROLLBACK

Official source: https://dev.mysql.com/doc/refman/8.0/en/xa-statements.html

```yaml
structured_config:
  kind: statement
  category: tcl
  domain: xa
  skill_name: xa_rollback
  official_source: https://dev.mysql.com/doc/refman/8.0/en/xa-statements.html
  statement:
    key: xa_rollback
    name: XA ROLLBACK
    aliases: [xa rollback]
    purpose: Roll back an XA transaction branch.
  syntax_templates:
    - "XA ROLLBACK xid"
  factor_layers:
    - tier: T1
      factors: [xid_state, expected_status]
  factors:
    xid_state:
      label: XID state
      importance: important
      values: [prepared_xid, ended_xid, active_xid, missing_xid]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    xid_state: prepared_xid
    expected_status: success
  coverage_policy:
    main_combination_axes: [xid_state, expected_status]
    non_main_factors: []
    python_expand_threshold: 60
  rendering:
    statement_template: "XA ROLLBACK '{xa_xid}'"
    verification_query_template: ""
    factor_value_bindings: {}
```
