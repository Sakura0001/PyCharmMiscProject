# 主流程：Run Feature Test Loop

## 作用

给定一个 feature 和已生成的 SQL 目录，执行测试闭环，发现失败、诊断失败、沉淀下一轮候选。这个流程用于大型测试库中反复验证一个 feature，而不是替代 SQL 生成流程。

## 前置输入

- `references/templates/feature_test_intake_template.md`
- 已生成 SQL：`artifacts/generated_sql/<feature_key>/`
- 已通过审计的生命周期计划和生成程序，或用户明确提供的 SQL 目录。
- 公共规则：
  - `references/common/execution_loop_policy.md`
  - `references/common/failure_diagnosis_policy.md`
  - `references/common/feedback_promotion_policy.md`
  - `references/common/query_oracle_policy.md`（查询相关 feature 必读）

## 执行步骤

1. 确认 SQL case 元数据。

   每个 SQL 文件建议包含：

   ```sql
   -- case_id: feature_case_001
   -- expected_status: success
   -- expected_sqlstate:
   ```

2. 执行 SQL 并生成 execution report。

   ```bash
   python3 tools/run_generated_sql.py \
     --sql-dir artifacts/generated_sql/<feature_key> \
     --feature <feature_key> \
     --output artifacts/evaluations/<feature_key>_execution_report.yaml
   ```

3. 审计 execution report。

   ```bash
   python3 tools/audit_execution_report.py \
     --report artifacts/evaluations/<feature_key>_execution_report.yaml
   ```

4. 若存在失败，生成 failure diagnosis。

   ```bash
   python3 tools/diagnose_execution_failures.py \
     --report artifacts/evaluations/<feature_key>_execution_report.yaml \
     --output artifacts/evaluations/<feature_key>_failure_diagnosis.yaml
   ```

5. 生成 feedback promotion candidates。

   ```bash
   python3 tools/promote_execution_feedback.py \
     --diagnosis artifacts/evaluations/<feature_key>_failure_diagnosis.yaml \
     --output artifacts/evaluations/<feature_key>_promotion_candidates.yaml
   ```

6. 需要多轮时，使用编排器。

   ```bash
   python3 tools/run_feature_test_loop.py \
     --sql-dir artifacts/generated_sql/<feature_key> \
     --feature <feature_key> \
     --artifacts-dir artifacts/evaluations \
     --max-iterations 3
   ```

## 多轮循环规则

- 第 1 轮用 baseline SQL 执行。
- 若 `final_status=clean`，记录当前覆盖通过。
- 若 `final_status=failures_detected`，读取 promotion candidates，先做人工审查。
- 审查通过后，才允许把候选加入 association graph、combination matrix 或 regression SQL。
- 下一轮必须能说明新增 case 来自哪个失败类别和哪个因子触发规则。

## 查询类 feature 额外步骤

查询 feature 在进入 loop 前必须确认：

- 有无 hint 都有覆盖。
- 数据分布覆盖空表、小表、大表、倾斜、高选择性、低选择性。
- 索引上下文覆盖无索引、普通索引、partial index、expression index、多列索引。
- `query_result_oracle` 明确 row_order 是否要求稳定。
- `EXPLAIN` / `plan_observation` 是强 oracle 还是 observe only。

## 输出产物

编排器会写出：

- `<feature_key>_iteration_001_execution_report.yaml`
- `<feature_key>_iteration_001_execution_audit.yaml`
- `<feature_key>_iteration_001_failure_diagnosis.yaml`
- `<feature_key>_iteration_001_promotion_candidates.yaml`
- `<feature_key>_loop_report.yaml`

这些都属于 `artifacts/evaluations/`。

## 完成标准

- `audit_execution_report.py` 通过。
- clean loop：`feature_test_loop_report.summary.final_status=clean`。
- failed loop：必须存在 failure diagnosis 和 feedback promotion candidates。
- 所有 candidates 都保持 `derived_extension: true`、`requires_human_review: true`、`counts_toward_required_baseline: false`。
