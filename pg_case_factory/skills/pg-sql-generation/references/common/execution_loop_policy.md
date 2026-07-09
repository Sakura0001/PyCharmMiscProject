# 公共规则：Execution Loop Policy

## 作用

当一个 feature 已经生成 SQL case 后，agent 必须用闭环方式验证它，而不是只静态检查文件。闭环目标是持续回答四个问题：

- 生成的 SQL 是否可执行。
- 观测结果是否符合 case oracle。
- 失败是否可归类、可复现、可最小化。
- 失败反馈能否成为下一轮 derived extension。

## 标准链路

```text
feature intake
-> factor association plan
-> lifecycle / combination plan
-> SQL generation
-> execution report
-> audit execution report
-> failure diagnosis
-> feedback promotion candidates
-> human-reviewed next iteration
```

自动化工具负责执行、记录、审计和聚类。新增 coverage、修改 baseline、改变 oracle 必须由 agent 或人工显式审查，不能由执行失败自动改写。

## 工具入口

- `tools/run_generated_sql.py`
  执行一个 SQL 目录，生成 `feature_execution_report`。
- `tools/audit_execution_report.py`
  审计 execution report 的 schema、case 必填字段和状态合法性。
- `tools/diagnose_execution_failures.py`
  把失败 case 聚类成可处理的问题类别。
- `tools/promote_execution_feedback.py`
  把诊断结果转换成需要人工审查的 derived extension 候选。
- `tools/run_feature_test_loop.py`
  编排多轮执行、审计、诊断和反馈晋升，并写出 loop summary。

## SQL case 元数据

每个 SQL 文件前 20 行可以声明 case 元数据：

```sql
-- case_id: insert_unique_conflict_001
-- expected_status: failure
-- expected_sqlstate: 23505
```

规则：

- `case_id` 缺失时默认使用 SQL 文件名 stem。
- `expected_status` 只能是 `success` 或 `failure`，缺省为 `success`。
- `expected_sqlstate` 只在预期失败路径中使用。
- 查询类 case 若需要结果、计划或排序 oracle，应在 SQL 内部输出可比对结果，或在 report 中补充 `oracle_result` / `plan_observation`。

## feature_execution_report 合同

`feature_execution_report` 必须是 YAML mapping，并包含：

```yaml
schema_version: 1
kind: feature_execution_report
feature:
  key: example_feature
runner:
  executor: ["psql", "-X", "-v", "ON_ERROR_STOP=1", "-f", "{sql}"]
  sql_dir: artifacts/generated_sql/example_feature
summary:
  case_count: 12
  failed_cases: 1
cases:
  - case_id: example_case_001
    sql_path: artifacts/generated_sql/example_feature/001.sql
    expected_status: success
    expected_sqlstate: ""
    observed_status: failure
    observed_sqlstate: "23505"
    status: failed
    exit_code: 1
    stdout: ""
    stderr: "..."
    duration_ms: 17
```

每个 `cases[]` 至少包含：

- `case_id`
- `sql_path`
- `expected_status`
- `observed_status`
- `status`
- `exit_code`

`status` 只能是：

- `passed`
- `failed`
- `expected_failure_matched`
- `skipped`
- `unsupported`

## loop report 合同

`tools/run_feature_test_loop.py` 生成 `feature_test_loop_report`：

```yaml
schema_version: 1
kind: feature_test_loop_report
feature:
  key: example_feature
loop_config:
  sql_dir: artifacts/generated_sql/example_feature
  artifacts_dir: artifacts/evaluations
  max_iterations: 3
  stop_on_clean: true
summary:
  iterations: 2
  final_status: failures_detected
  total_failed_cases: 3
  total_promotion_candidates: 3
iterations:
  - iteration: 1
    status: failures_detected
    execution_report_path: artifacts/evaluations/example_feature_iteration_001_execution_report.yaml
    audit_report_path: artifacts/evaluations/example_feature_iteration_001_execution_audit.yaml
    failure_diagnosis_path: artifacts/evaluations/example_feature_iteration_001_failure_diagnosis.yaml
    promotion_candidates_path: artifacts/evaluations/example_feature_iteration_001_promotion_candidates.yaml
```

## 停止条件

一轮循环结束后：

- `audit_failed`：停止，先修 report 或 runner。
- `clean` 且 `stop_on_clean=true`：停止，记录为当前 coverage 下通过。
- `failures_detected`：输出 diagnosis 和 promotion candidates，再由 agent 决定是否生成下一轮 SQL。
- 达到 `max_iterations`：停止，保留全部中间产物。

## 质量门禁

- 任何自动发现的新场景都只能作为 `derived_extension`。
- `derived_extension` 不得替代 statement combination matrix 中的 required baseline coverage。
- 失败 case 必须先最小化、稳定复现、确认 oracle，再进入正式测试库。
- 查询类 feature 必须同时读取 `references/common/query_context_policy.md` 和 `references/common/query_oracle_policy.md`。
