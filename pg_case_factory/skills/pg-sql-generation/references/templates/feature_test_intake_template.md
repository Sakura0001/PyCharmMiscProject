# Template: Feature Test Intake

用于大型测试库中“给定一个 feature 后启动测试闭环”的输入模板。使用者应先填这个模板，再进入 `references/mainflow/generate_sql_from_request.md` 或 `references/mainflow/run_feature_test_loop.md`。

```yaml
feature_key: ""
feature_summary: ""
postgres_version: "16.4"
statement_scope:
  primary_statements: []
  related_statements: []
  query_involved: false
  ddl_involved: false
  dml_involved: false
  transaction_involved: false
base_object_scope:
  object_kinds: []
  object_templates: []
  unsupported_objects_as_negative_cases: []
factor_seed:
  user_named_factors: []
  required_common_rules:
    - references/common/factor_policy.md
    - references/common/association_policy.md
  required_statement_references: []
query_context:
  required: false
  query_shapes: []
  data_fixture_shapes: []
  data_distribution: []
  index_context: []
  hint_context:
    include_hint_absent: true
    include_hint_present: true
  statistics_context: []
  optimizer_guc_context: []
  oracle:
    result: ""
    row_order: ""
    plan_observation: ""
execution_context:
  executor: ["psql", "-X", "-v", "ON_ERROR_STOP=1", "-f", "{sql}"]
  sql_dir: artifacts/generated_sql/
  evaluations_dir: artifacts/evaluations/
loop_budget:
  max_iterations: 1
  stop_on_clean: true
  promotion_requires_human_review: true
acceptance_gates:
  lifecycle_plan_audit: required
  generated_sql_execution: required
  execution_report_audit: required
  failure_diagnosis: required_when_failed
  feedback_promotion: required_when_failed
```

## 使用规则

- `feature_key` 必须稳定，后续 artifact 文件名使用它作为前缀。
- `statement_scope.primary_statements` 决定优先读取哪些 statement reference。
- 只要 feature 需要查询验证，`query_context.required` 必须为 true，并读取：
  - `references/common/query_context_policy.md`
  - `references/common/query_oracle_policy.md`
- `factor_seed.user_named_factors` 是用户已想到的点，不是完整覆盖；agent 仍要通过 association graph 发散。
- `loop_budget.max_iterations` 控制执行闭环轮数，不代表自动晋升 baseline。
