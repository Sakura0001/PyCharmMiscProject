# 从请求生成 SQL 测试

## 目标

把特性文档或自然语言 SQL 测试请求转成 PostgreSQL 18.4 的可追溯覆盖计划、可恢复 test-point jobs、SQL/case manifests 和差分回归证据。不要在常驻 Python 中写死 statement 或生命周期知识。

## 路由

- 输入包含特性文档：从 `references/mainflow/analyze_feature_document.md` 开始。
- 输入只有自然语言请求：把原始请求原样保存到 run 的 `inputs/`，建立带 source locator 的最小 feature manifest，再进入同一特性流程。
- 输入只要求审计已有计划：读取 `references/mainflow/audit_lifecycle_plan.md`。
- 输入只要求创建 statement reference：读取 `references/mainflow/create_statement_reference.md`。

## 固定流程

1. 创建 `artifacts/runs/<run-id>/`；不得清空整个 `artifacts/`。
2. 按 `analyze_feature_document.md` 保存输入并建立 `feature_manifest.yaml`。
3. 按 `design_feature_coverage_plan.md` 枚举全部适用 inventory，写 `coverage_plan.yaml` 并展开 obligations。
4. 要求 `required = success + expected_failure + justified_na` 且 `missing = 0`。
5. 按 `orchestrate_test_points.md` 创建一个 durable job/test point，逐点调用 `write_sql_program.md` 生成 SQL 和 case manifests。
6. 对 executable obligations 与 case manifests 做一一核对；不得静默跳过失败、类型或对象形态。
7. 按 `execute_differential_regression.md` 在 upstream PostgreSQL 18.4 和 DUT 上执行、规范化、比较并生成 finding/regression artifacts。

## 知识来源

- 基础对象：`assets/objects/**/*.sql`
- statement references：`references/statements/**/*.md`
- baseline matrices：`references/combinations/**/*.yaml`
- PG18.4 profile/inventory：
  - `references/common/compatibility_profile.yaml`
  - `references/common/statement_support_inventory.yaml`
  - `references/common/pg18_factor_catalog.md`
  - `references/common/pg18_type_catalog.md`
- 公共规则：output、factor、lifecycle、validation、naming references

优先消费匹配的正式 combination matrix。矩阵未审计通过时，不要把自由推理生成的组合计入 required baseline。新增组合标为 derived extension，但不能替代完整 inventory obligation。

## 产物要求

- 所有新产物写入当前 `artifacts/runs/<run-id>/`。
- 每个 SQL 文件只判断一个可归因结果，并包含前置清理、准备、目标操作、验证和结束清理。
- 每个 executable obligation 都有 case manifest；`justified_na` 有明确 reason。
- 发现差异时保留 SQL、两端执行记录、规范化规则和 diff。
- 不保存真实凭据；存储日志和底层根因由用户负责。

```yaml
structured_config:
  kind: mainflow
  skill_name: generate_sql_from_request
  compatibility_target: postgresql-18.4
  run_root: artifacts/runs/<run-id>/
  feature_workflow:
    analyze: references/mainflow/analyze_feature_document.md
    design: references/mainflow/design_feature_coverage_plan.md
    orchestrate: references/mainflow/orchestrate_test_points.md
    execute: references/mainflow/execute_differential_regression.md
  require_complete_inventory: true
  sampling_allowed: false
```
