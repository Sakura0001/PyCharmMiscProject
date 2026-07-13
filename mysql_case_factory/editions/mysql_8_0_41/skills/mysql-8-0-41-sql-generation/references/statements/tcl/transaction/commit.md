# COMMIT

Official source: https://dev.mysql.com/doc/refman/8.0/en/commit.html

```yaml
structured_config:
  kind: statement
  category: tcl
  domain: transaction
  skill_name: commit
  official_source: https://dev.mysql.com/doc/refman/8.0/en/commit.html
  statement:
    key: commit
    name: COMMIT
    aliases: [commit]
    purpose: Commit a MySQL transaction.
  syntax_templates:
    - "COMMIT [WORK] [AND [NO] CHAIN] [[NO] RELEASE]"
  factor_layers:
    - tier: T1
      factors: [work_keyword, chain_mode, release_mode, expected_status]
  factors:
    work_keyword:
      label: WORK keyword
      importance: important
      values: [omitted, present]
    chain_mode:
      label: Chain mode
      importance: important
      values: [omitted, and_chain, and_no_chain]
    release_mode:
      label: Release mode
      importance: important
      values: [omitted, release, no_release]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    work_keyword: omitted
    chain_mode: omitted
    release_mode: omitted
    expected_status: success
  coverage_policy:
    main_combination_axes: [work_keyword, chain_mode, release_mode, expected_status]
    non_main_factors: []
    python_expand_threshold: 120
  rendering:
    statement_template: "COMMIT{work_sql}{chain_sql}{release_sql}"
    verification_query_template: ""
    factor_value_bindings:
      work_sql:
        factor: work_keyword
        values: {omitted: "", present: " WORK"}
      chain_sql:
        factor: chain_mode
        values: {omitted: "", and_chain: " AND CHAIN", and_no_chain: " AND NO CHAIN"}
      release_sql:
        factor: release_mode
        values: {omitted: "", release: " RELEASE", no_release: " NO RELEASE"}
```
