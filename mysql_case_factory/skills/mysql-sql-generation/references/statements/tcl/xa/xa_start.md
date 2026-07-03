# XA START

Official source: https://dev.mysql.com/doc/refman/8.0/en/xa-statements.html

```yaml
structured_config:
  kind: statement
  category: tcl
  domain: xa
  skill_name: xa_start
  official_source: https://dev.mysql.com/doc/refman/8.0/en/xa-statements.html
  statement:
    key: xa_start
    name: XA START
    aliases: [xa start, xa begin]
    purpose: Start an XA transaction branch.
  syntax_templates:
    - "XA {START | BEGIN} xid [JOIN | RESUME]"
  factor_layers:
    - tier: T1
      factors: [statement_branch, xid_state, modifier_shape, expected_status]
  factors:
    statement_branch:
      label: START or BEGIN
      importance: important
      values: [start, begin]
    xid_state:
      label: XID state
      importance: important
      values: [new_xid, active_xid, prepared_xid]
    modifier_shape:
      label: JOIN or RESUME
      importance: important
      values: [omitted, join, resume]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    statement_branch: start
    xid_state: new_xid
    modifier_shape: omitted
    expected_status: success
  coverage_policy:
    main_combination_axes: [statement_branch, xid_state, modifier_shape, expected_status]
    non_main_factors: []
    python_expand_threshold: 120
  rendering:
    statement_template: "XA {branch_sql} '{xa_xid}'"
    verification_query_template: ""
    factor_value_bindings:
      branch_sql:
        factor: statement_branch
        values: {start: "START", begin: "BEGIN"}
```
