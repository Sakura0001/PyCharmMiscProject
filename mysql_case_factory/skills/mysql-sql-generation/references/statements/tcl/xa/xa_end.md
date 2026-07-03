# XA END

Official source: https://dev.mysql.com/doc/refman/8.0/en/xa-statements.html

```yaml
structured_config:
  kind: statement
  category: tcl
  domain: xa
  skill_name: xa_end
  official_source: https://dev.mysql.com/doc/refman/8.0/en/xa-statements.html
  statement:
    key: xa_end
    name: XA END
    aliases: [xa end]
    purpose: End an active XA transaction branch.
  syntax_templates:
    - "XA END xid [SUSPEND [FOR MIGRATE]]"
  factor_layers:
    - tier: T1
      factors: [xid_state, suspend_shape, expected_status]
  factors:
    xid_state:
      label: XID state
      importance: important
      values: [active_xid, missing_xid, prepared_xid]
    suspend_shape:
      label: SUSPEND modifier
      importance: important
      values: [omitted, suspend, suspend_for_migrate]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    xid_state: active_xid
    suspend_shape: omitted
    expected_status: success
  coverage_policy:
    main_combination_axes: [xid_state, suspend_shape, expected_status]
    non_main_factors: []
    python_expand_threshold: 80
  rendering:
    statement_template: "XA END '{xa_xid}'"
    verification_query_template: ""
    factor_value_bindings: {}
```
