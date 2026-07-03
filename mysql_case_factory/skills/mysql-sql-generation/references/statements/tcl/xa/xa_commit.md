# XA COMMIT

Official source: https://dev.mysql.com/doc/refman/8.0/en/xa-statements.html

```yaml
structured_config:
  kind: statement
  category: tcl
  domain: xa
  skill_name: xa_commit
  official_source: https://dev.mysql.com/doc/refman/8.0/en/xa-statements.html
  statement:
    key: xa_commit
    name: XA COMMIT
    aliases: [xa commit]
    purpose: Commit an XA transaction branch.
  syntax_templates:
    - "XA COMMIT xid [ONE PHASE]"
  factor_layers:
    - tier: T1
      factors: [xid_state, one_phase_shape, expected_status]
  factors:
    xid_state:
      label: XID state
      importance: important
      values: [prepared_xid, ended_xid, active_xid, missing_xid]
    one_phase_shape:
      label: ONE PHASE
      importance: important
      values: [omitted, one_phase]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    xid_state: prepared_xid
    one_phase_shape: omitted
    expected_status: success
  coverage_policy:
    main_combination_axes: [xid_state, one_phase_shape, expected_status]
    non_main_factors: []
    python_expand_threshold: 80
  rendering:
    statement_template: "XA COMMIT '{xa_xid}'{one_phase_sql}"
    verification_query_template: ""
    factor_value_bindings:
      one_phase_sql:
        factor: one_phase_shape
        values: {omitted: "", one_phase: " ONE PHASE"}
```
