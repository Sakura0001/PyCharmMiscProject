# 公共规则：Query Oracle Policy

## 作用

查询相关 feature 不能只看 SQL 是否执行成功。必须明确查询结果、排序、计划、hint、统计信息、MVCC 可见性和数据分布的 oracle 边界。

本文件与 `references/common/query_context_policy.md` 配套使用：

- `query_context_policy.md` 负责联想到哪些查询上下文需要覆盖。
- `query_oracle_policy.md` 负责规定这些上下文应该如何判断正确。

## oracle 类型

### query_result_oracle

用于判断返回行是否正确：

- 行集合完全相等。
- 多重集合相等，允许不同 row_order。
- 精确 row_order，相当于 SQL 中存在稳定 `ORDER BY`。
- 聚合结果、窗口函数结果、分组结果逐列比较。
- NULL、NaN、infinity、collation、timezone 等特殊值必须显式声明比较规则。

建议 SQL 内部输出稳定、可 diff 的结果，例如：

```sql
SELECT jsonb_agg(to_jsonb(q) ORDER BY stable_key)
FROM (
    SELECT id, payload
    FROM target_table
    WHERE flag
    ORDER BY id
) AS q;
```

### query_error_oracle

用于负例查询：

- 是否失败。
- SQLSTATE 是否匹配。
- 错误发生阶段是 parse、rewrite、plan 还是 execute。
- prepared statement 下错误是在 `PREPARE`、`EXECUTE` 还是参数绑定阶段出现。

### plan_observation

用于观察计划路径，不默认等同于语义 oracle：

- `EXPLAIN (FORMAT JSON)` 能否显示预期 node。
- 是否使用索引、分区裁剪、并行计划、join strategy。
- hint 生效与不生效的对照。
- 统计信息变化后计划是否合理变化。

计划 oracle 必须写清楚强弱：

- `must_match`：该 feature 本身就是计划选择或 hint 行为。
- `observe_only`：只记录计划，用于诊断性能或覆盖，不作为失败依据。
- `anti_plan`：明确不应出现某种 node，例如不应全表扫描。

### side_effect_oracle

用于带副作用的查询或查询驱动语句：

- volatile function 调用次数。
- CTE materialization 行为是否影响副作用。
- SELECT INTO / CTAS / INSERT ... SELECT 的目标表状态。
- 锁、快照、临时对象、统计信息是否符合预期。

## row_order 规则

- 没有 `ORDER BY` 时不得用物理输出顺序作为强 oracle。
- 若 feature 关注排序、索引扫描顺序、merge join 输出顺序，必须在 notes 中声明 `row_order: required`。
- 若只关注集合语义，声明 `row_order: ignored` 并使用稳定排序后的聚合结果比较。

## hint 与无 hint 对照

任何涉及 hint 的 feature 至少设计两类 case：

- `hint_absent`：无 hint，确认 baseline 行为和结果。
- `hint_present`：有 hint，确认 hint 被解析、接受或拒绝。

若 hint 影响计划，还要加：

- hint 存在但不可用。
- hint 与 GUC 冲突。
- hint 与索引、统计信息、分区裁剪、join order 的交互。
- hint 不应改变语义结果，只能改变计划或执行路径。

## 数据构造要求

查询 fixture 不能只有三五行 happy path。至少考虑：

- 空表、单行、小表、大表。
- 高选择性、低选择性、均匀分布、强倾斜分布。
- 重复值、唯一值、热点值。
- NULL 分布、极值、边界值。
- 多表 join 中父子表规模比例变化。
- 分区边界、default partition、无匹配分区。
- 类型转换、collation、timezone、encoding、numeric precision。

## 与索引和统计信息的关系

查询 feature 必须考虑：

- 无索引、有普通索引、有表达式索引、有 partial index、有多列索引。
- fresh statistics、stale statistics、缺失 statistics。
- `ANALYZE` 前后。
- extended statistics 对多列相关性的影响。
- prepared statement 下 generic plan 与 custom plan 的差异。

## 输出建议

在测试计划 notes 中明确：

```yaml
query_oracle:
  result: query_result_oracle
  row_order: ignored
  plan_observation:
    mode: observe_only
    explain: EXPLAIN (FORMAT JSON, COSTS OFF)
  hint_mode:
    - hint_absent
    - hint_present
  data_distribution:
    - empty
    - skewed
    - high_selectivity
```
