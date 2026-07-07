# Hybrid Factor Association Planner 版图

## 目标

Hybrid Factor Association Planner 是 `pg-sql-generation` skill 的规划层。它读取现有 statement reference、combination matrix、factor catalog、type catalog 和 coverage inventory，把分散的因子事实转成可审计的 scenario family、coverage obligation、生命周期、oracle 和 cleanup 计划。

Planner 不替代当前 matrix baseline。它先用 deterministic rules 覆盖 required baseline，再把额外想法作为 marked derived extension 输出，等待人工提升。

## 输入地图

| 输入 | 路径 | 用途 |
| --- | --- | --- |
| statement reference | `skills/pg-sql-generation/references/statements/**/*.md` | 读取 statement key、语法分支、局部因子、取值、约束、默认生命周期和 oracle 提示。 |
| combination matrix | `skills/pg-sql-generation/references/combinations/**/*.yaml` | 读取 required baseline 组合、coverage scope、expected status、稳定失败原因和 extension policy。 |
| factor catalog | `skills/pg-sql-generation/references/common/pg16_factor_catalog.md` | 读取跨 statement 复用的对象域、因子组、因子、取值、tier 和 coverage role。 |
| type catalog | `skills/pg-sql-generation/references/common/pg16_type_catalog.md` | 读取类型族、类型能力、兼容性边界和列/值覆盖事实。 |
| coverage inventory | `skills/pg-sql-generation/references/combinations/_shared/coverage_inventory.yaml` | 读取全局 coverage 义务、负例库存、对象/关系/列类型覆盖缺口和已覆盖范围。 |
| common policies | `skills/pg-sql-generation/references/common/*.md` | 读取因子组合、生命周期、验证清理、输出风格和 association policy。 |

## Pipeline Stages

1. **Factor reader**
   解析 statement reference、matrix、catalog 和 inventory 中的结构化 YAML，保留字段来源路径，形成可追溯 fact graph。

2. **Semantic tagger**
   为因子、取值和 coverage scope 标注稳定语义标签，例如 `relation_kind`、`column_type`、`data_profile`、`schema_mutation`、`dependency_state`、`privilege_environment`、`transaction_sensitive`、`optimizer_sensitive`、`negative_control`。

3. **Association engine**
   对语义标签运行 deterministic association operators，识别哪些因子必须形成 scenario family，哪些只作为轮转附属覆盖。

4. **Constraint solver**
   合并 statement 约束、matrix expected status、类型能力、对象依赖、权限/环境前置条件和互斥条件，剔除不可执行组合，并把失败路径拆成单一原因。

5. **Coverage obligation builder**
   从 matrix coverage scope 和 inventory 缺口生成 `coverage_obligations`，明确 required baseline、representative coverage、negative control 和 derived extension 候选。

6. **Lifecycle planner**
   为每个 family 生成闭环生命周期：前置清理、对象准备、目标语句、验证、结束清理；成功路径与失败路径分开。

7. **Oracle binder**
   绑定稳定验证方式：系统目录查询、对象可用性查询、确定性结果查询、稳定错误原因或必要的裁剪后 explain 观察点。

8. **Execution feedback learner**
   读取执行结果和审计结果，只更新 derived extension 候选、缺口记录或人工提升建议；不得自动改写 required baseline 事实。

## Association Operators

| Operator | 触发事实 | 产出 |
| --- | --- | --- |
| object kind | target object、object domain、statement category | 对象种类覆盖 family，例如 database、schema、table-backed object、index-like object。 |
| type/value | column type、value literal、type capability | 类型族、值边界、操作符/方法兼容性 family。 |
| data profile | row count、nullability、duplicate、distribution、expression input | 数据画像 family，覆盖空表、单行、多行、NULL、重复值、选择性差异。 |
| schema mutation | alter/drop/rename/rewrite、dependent object | 生命周期变更 family，覆盖变更前后 oracle 与清理责任。 |
| dependency | referenced object、owned object、extension/function/operator dependency | 依赖存在、缺失、级联、受保护对象 family。 |
| privilege/environment | owner、role、search_path、tablespace、extension、server setting | 权限、环境准备、session 级开关和失败原因 family。 |
| transaction/concurrency | concurrently、transaction block、lock mode、active connection | 事务边界、锁行为、并发限制和禁止场景 family。 |
| optimizer/statistics | statistics target、ANALYZE state、selectivity、planner option | 统计信息与优化器可观测行为 family。 |
| version delta | PG version support、deprecated syntax、new option | 版本差异、兼容性和跳过条件 family。 |
| negative control | expected failure、invalid value、missing dependency、coverage inventory negative case | 单一稳定失败原因 family。 |

`CREATE INDEX` 可以触发 relation kind、column type、data profile、transaction/concurrency、optimizer/statistics 和 negative control operators，但这些 operators 是通用规则，不以 `CREATE INDEX` 为边界。

## Scenario Family 输出 Schema

```yaml
kind: factor_association_plan
target_statement:
  key: create_index
  name: CREATE INDEX
association_model:
  mode: hybrid_rule_first
  baseline_source: combination_matrix
factor_profiles:
  factor_name:
    source: statement_reference
    semantic_tags:
      - column_type
    values: []
scenario_families:
  - id: column_type_matrix
    title: Column type compatibility matrix
    origin: deterministic_rule
    derived_extension: false
    trigger_facts:
      sources:
        - combination_matrix.coverage_scope.column_type_coverage
        - type_catalog.type_sets.all_pg16_column_types
      types:
        - integer
        - jsonb
    operators:
      - type/value
    lifecycle:
      - setup
      - target_statement
      - verification
      - cleanup
    oracle:
      success: stable catalog or behavior query
      failure: stable expected error reason
    cleanup:
      idempotent: true
      reverse_dependency_order: true
    coverage_tags:
      - baseline
      - column_type
    why: Required because the matrix declares column-type coverage.
coverage_obligations:
  - id: column_type_required_baseline
    source: combination_matrix
    required_for_baseline: true
    trigger_facts:
      sources:
        - combination_matrix.coverage_scope.column_type_coverage
    satisfied_by:
      - column_type_matrix
quality_gates:
  - deterministic_rules_complete
  - baseline_matrix_coverage_preserved
  - scenario_family_contract_complete
```

## Quality Gates

- **Fact provenance**：每个 family 和 obligation 都能追溯到 statement reference、matrix、catalog 或 inventory 字段。
- **Rule-first determinism**：deterministic operators 必须先运行；相同输入产生稳定 family id 和 coverage tags。
- **Baseline preservation**：required matrix coverage 不得被 derived extension 替代。
- **Scenario contract completeness**：每个 family 必须包含 trigger facts、lifecycle、oracle、cleanup、coverage tags 和 why。
- **Failure attribution**：失败路径只允许一个稳定失败原因；多个失败原因必须拆成多个 family 或场景。
- **Cleanup closure**：生命周期必须可复跑，清理动作幂等，并按反向依赖顺序执行。
- **No statement hardcoding**：示例可以使用 `CREATE INDEX`，规则和输出结构必须适用于任意 statement。
- **Extension marking**：LLM idea、执行反馈 idea 和人工未确认 idea 必须标记为 derived extension。

## 与当前 Matrix Baseline / Derived Extension 模型的关系

当前模型中，combination matrix 负责 required baseline SQL 组合，baseline 审计通过后才允许追加 marked derived extensions。Planner 位于 matrix 与 SQL 渲染之间：

1. Matrix 声明必须覆盖什么。
2. Planner 把必须覆盖的事实转成 scenario family 和 obligation。
3. Lifecycle planner 与 oracle binder 为这些 family 补齐执行闭环。
4. SQL 生成流程根据 plan、statement reference、对象模板和公共规则渲染脚本。
5. Derived extensions 单独输出，只作为探索和提升候选，不计入 required baseline。

因此，Planner 扩展的是“如何从事实发现高价值场景族”的能力，不改变 matrix baseline 的权威地位。
