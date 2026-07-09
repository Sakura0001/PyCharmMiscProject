# 公共规则：Failure Diagnosis Policy

## 作用

执行失败后不要直接把 case 判成“产品 bug”。必须先把失败按机制聚类，再决定下一步是修生成器、修 oracle、补 fixture、还是提炼 bug reproduction。

`tools/diagnose_execution_failures.py` 读取 `feature_execution_report` 并输出 `failure_diagnosis_report`。

## failure_diagnosis_report 合同

```yaml
schema_version: 1
kind: failure_diagnosis_report
feature:
  key: insert_unique_conflict
summary:
  total_cases: 20
  failed_cases: 3
  cluster_count: 2
clusters:
  - category: unexpected_failure
    reason: "23505"
    case_count: 2
    cases:
      - case_id: insert_unique_conflict_001
        sql_path: artifacts/generated_sql/insert/001.sql
        expected_status: success
        observed_status: failure
        observed_sqlstate: "23505"
```

## 诊断类别

- `unexpected_failure`
  预期成功但实际失败。优先检查 fixture、权限、对象生命周期、SQL 语法、版本差异，再考虑产品 bug。
- `unexpected_success`
  预期失败但实际成功。优先检查负例 oracle、SQLSTATE、约束是否真的生效、版本语义差异。
- `sqlstate_mismatch`
  都是失败，但 SQLSTATE 与预期不一致。优先确认错误阶段和 expected_sqlstate。
- `result_mismatch`
  SQL 成功但 `oracle_result.status=mismatch`。优先审查 query_result_oracle、row_order、NULL、collation、timezone、浮点比较。
- `plan_mismatch`
  SQL 成功但 `plan_observation.status=mismatch`。优先审查统计信息、GUC、hint、索引、数据分布和计划 oracle 强弱。
- `cleanup_failure`
  主体 case 可能成功，但清理失败。先修 cleanup，否则下一轮会污染环境。
- `unclassified_failure`
  缺少足够字段。先补 execution report 信息，再做判断。

## 诊断顺序

1. 先检查 execution report audit 是否通过。
2. 再确认失败是否稳定复现。
3. 再判断是生成问题、环境问题、oracle 问题、还是数据库行为问题。
4. 最后才生成 feedback promotion candidates。

## 查询类失败特别规则

查询失败要额外确认：

- 是否缺失 `ORDER BY` 却用了强 row_order oracle。
- hint 是否改变了计划但不应改变结果。
- `EXPLAIN` 计划观察是否因为统计信息或 GUC 漂移而不稳定。
- prepared statement 是否走 generic plan。
- MVCC 快照和隔离级别是否符合 case 设计。
