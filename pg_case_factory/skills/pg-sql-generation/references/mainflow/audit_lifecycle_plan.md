# 审计生命周期与覆盖计划

## 目标

审计 `artifacts/runs/<run-id>/plans/coverage_plan.yaml` 及可选生命周期 TSV，判断其能否支撑可执行、可验证、可恢复的 PostgreSQL 18.4 SQL 用例。本流程只审计计划，不生成 SQL。

## 输入

- 原始请求和 `inputs/feature_manifest.yaml`
- `plans/coverage_plan.yaml` 与 `plans/coverage_obligations.json`
- 可选的 `plans/lifecycle/*.tsv`
- 相关对象模板、statement references、combination matrices
- PG18.4 compatibility profile、factor/type inventories 和公共规则

## 审计顺序

1. 校验 feature、requirement、test point、axis 和 dependency 引用。
2. 检查每条 requirement 是否映射到可观察结果和至少一个 test point。
3. 对每个 axis 检查 `coverage_mode: complete`、非空 `inventory_source` 和完整 values。拒绝代表值、抽样值或未声明默认值。
4. 逐项检查语句分支、对象/relation/table 类型、列类型、数据形态、生命周期、事务、权限、依赖与文档明确要求的并发/恢复边界。
5. 检查每个 test point 是否只表达一个清晰意图，并对全部 core axes 做笛卡尔积。
6. 检查不适用或不支持的 inventory 值是否仍在 axis 中，并被 `expected_failure` 或 `justified_na + reason` 分类。
7. 运行 `pg-case plan validate` 和 `pg-case plan expand --require-complete`，确认：

```text
required = success + expected_failure + justified_na
missing = 0
```

8. 对可选生命周期 TSV，检查每行只描述一个场景，并形成“前置清理 -> 对象准备 -> 目标语句 -> 稳定验证 -> 结束清理”的闭环。
9. 检查计划仅使用 PostgreSQL 18.4 语义；PG16 基线未经 compatibility audit 不得直接声明为 PG18.4 ready。
10. 把审计结果写到 `plans/audits/`，verdict 只能是 `passed`、`needs_revision` 或 `blocked`。

对非 `passed` 结果列出 requirement/test-point/axis/obligation ID、问题、测试盲区和可执行修订建议。修订后重新审计，不得绕过门禁。

```yaml
structured_config:
  kind: mainflow
  skill_name: audit_lifecycle_plan
  mainflow_role: audit
  compatibility_target: postgresql-18.4
  verdicts: [passed, needs_revision, blocked]
  require_complete_inventory: true
  require_missing_zero: true
```
