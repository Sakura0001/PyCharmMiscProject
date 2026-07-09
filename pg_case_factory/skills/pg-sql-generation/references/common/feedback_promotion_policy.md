# 公共规则：Feedback Promotion Policy

## 作用

闭环执行会发现新失败、新边界和新组合，但这些发现不能自动进入正式 coverage。必须先作为 `feedback_promotion_candidates` 产物，由 agent 或人工审查后再进入下一轮计划或 baseline。

`tools/promote_execution_feedback.py` 读取 `failure_diagnosis_report` 并输出候选列表。

## feedback_promotion_candidates 合同

```yaml
schema_version: 1
kind: feedback_promotion_candidates
feature:
  key: create_index_expression
candidates:
  - id: unexpected_failure__case_001
    promotion_type: bug_reproduction_candidate
    feature_key: create_index_expression
    case_id: case_001
    source_category: unexpected_failure
    source_reason: "23505"
    sql_path: artifacts/generated_sql/create_index/001.sql
    derived_extension: true
    requires_human_review: true
    counts_toward_required_baseline: false
    recommended_action: minimize and review as possible product bug
```

## 晋升原则

- 每个候选都必须有 `derived_extension: true`。
- 每个候选都必须有 `requires_human_review: true`。
- 每个候选都必须有 `counts_toward_required_baseline: false`。
- 自动发现的候选不能替代 combination matrix 里的 required coverage。
- 候选进入正式 baseline 前，必须补齐 factor attribution、oracle、清理策略和稳定性证据。

## promotion_type 映射

- `unexpected_failure` -> `bug_reproduction_candidate`
- `unexpected_success` -> `negative_oracle_review_candidate`
- `sqlstate_mismatch` -> `failure_oracle_review_candidate`
- `result_mismatch` -> `semantic_bug_candidate`
- `plan_mismatch` -> `plan_derived_extension_candidate`
- `cleanup_failure` -> `cleanup_hardening_candidate`
- `unclassified_failure` -> `manual_triage_candidate`

## 人工审查 checklist

审查候选时至少确认：

- 是否能单独复现。
- 是否依赖脏环境、并发时序或随机数据。
- SQLSTATE、结果、计划或副作用 oracle 是否合理。
- 是否已有 baseline 覆盖同一机制。
- 是否应该加入 statement reference、association graph、combination matrix，还是只作为 bug reproduction 保存。

## 进入下一轮的方式

候选审查通过后，可以三种方式进入下一轮：

- 加入 factor association graph，作为某个因子触发的 `must_expand_to`。
- 加入 statement combination matrix，标记为人工确认后的 derived extension。
- 保留为独立 regression SQL，专门验证已确认 bug。
