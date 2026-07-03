# SELECT

Official source: https://dev.mysql.com/doc/refman/8.0/en/select.html

```yaml
structured_config:
  kind: statement
  category: dml
  domain: query
  skill_name: select
  official_source: https://dev.mysql.com/doc/refman/8.0/en/select.html
  statement:
    key: select
    name: SELECT
    aliases: [select, query]
    purpose: Generate MySQL 8.0.22 SELECT query cases while excluding later INTERSECT/EXCEPT syntax.
  syntax_templates:
    - "SELECT [ALL | DISTINCT | DISTINCTROW] select_expr [, select_expr] ... [FROM table_references] [WHERE where_condition] [GROUP BY ...] [HAVING where_condition] [ORDER BY ...] [LIMIT ...] [locking_clause]"
  factor_layers:
    - tier: T1
      factors: [projection_shape, from_shape, predicate_shape, expected_status]
    - tier: T2
      factors: [grouping_shape, ordering_limit_shape, locking_clause, into_destination]
  factors:
    projection_shape:
      label: Projection
      importance: important
      values: [star, explicit_columns, expression, aggregate]
    from_shape:
      label: FROM shape
      importance: important
      values: [single_table, inner_join, subquery]
    predicate_shape:
      label: Predicate
      importance: important
      values: [omitted, where_filter, having_filter]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    grouping_shape:
      label: GROUP BY
      importance: non_important
      values: [omitted, group_by_column]
    ordering_limit_shape:
      label: ORDER BY and LIMIT
      importance: non_important
      values: [omitted, order_by, limit, order_by_limit]
    locking_clause:
      label: Locking read
      importance: non_important
      values: [omitted, for_update, for_share, nowait, skip_locked]
    into_destination:
      label: SELECT INTO destination
      importance: non_important
      values: [omitted, variables, outfile, dumpfile]
  defaults:
    projection_shape: explicit_columns
    from_shape: single_table
    predicate_shape: omitted
    expected_status: success
    grouping_shape: omitted
    ordering_limit_shape: omitted
    locking_clause: omitted
    into_destination: omitted
  coverage_policy:
    main_combination_axes: [projection_shape, from_shape, predicate_shape, expected_status]
    non_main_factors: [grouping_shape, ordering_limit_shape, locking_clause, into_destination]
    python_expand_threshold: 200
  rendering:
    statement_template: "SELECT id_col, int_col FROM {table_name}{where_sql}{locking_sql}"
    verification_query_template: ""
    factor_value_bindings:
      where_sql:
        factor: predicate_shape
        values: {omitted: "", where_filter: " WHERE int_col IS NOT NULL", having_filter: " WHERE int_col IS NOT NULL"}
      locking_sql:
        factor: locking_clause
        values: {omitted: "", for_update: " FOR UPDATE", for_share: " FOR SHARE", nowait: " FOR UPDATE NOWAIT", skip_locked: " FOR UPDATE SKIP LOCKED"}
```
