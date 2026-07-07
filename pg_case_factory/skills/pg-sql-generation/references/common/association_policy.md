# 技能：association_policy

## 作用

定义 hybrid Factor Association Planner 的公共规则。Planner 用既有 reference 与 catalog 事实生成可审计的 scenario family；LLM 只能在规则结果之后补充明确标记的 derived extension，不能替代 baseline coverage。

## 事实来源

Planner 只能把下列材料作为事实输入：

- statement reference：语句因子、取值、tier、渲染提示、约束、oracle 提示和生命周期提示。
- combination matrix：required baseline 组合、coverage scope、expected status、失败原因和 post coverage extension policy。
- factor catalog：跨 statement 复用的对象域、因子组、因子、取值、默认 tier 与 coverage role。
- type catalog：类型族、类型能力、兼容性边界和可用于列/值覆盖的类型事实。
- coverage inventory：全局已知 coverage 义务、负例库存、对象/关系/列类型覆盖状态和缺口。

不得把 LLM 推断、用户口头偏好、历史运行痕迹或实现细节直接当作 baseline 事实；这些内容必须先被写回上述结构化材料并通过人工或审计确认。

## 规则顺序

1. 读取并规范化既有事实。
2. 运行 deterministic rule operators，生成稳定 scenario family、coverage obligation、生命周期草案、oracle 绑定和清理责任。
3. 检查 baseline matrix coverage 是否完整。
4. 只有在 baseline audit 通过后，才允许生成 LLM-derived ideas。
5. LLM-derived ideas 必须写入 marked derived extensions，并声明来源、假设、风险和人工提升条件。

Deterministic rule operators 永远先于 LLM-derived ideas 执行。LLM 不能删除、重排或覆盖 deterministic rules 产生的 required baseline 义务。

## Scenario Family 要求

每个 scenario family 必须声明：

- `trigger_facts`：来自哪些 statement reference、matrix、factor catalog、type catalog 或 coverage inventory 字段。
- `lifecycle`：前置清理、对象准备、目标语句、验证、结束清理的闭环。
- `oracle`：成功路径验证、失败路径稳定错误原因或行为可观测点。
- `cleanup`：幂等清理动作与反向依赖顺序。
- `coverage_tags`：对象类型、关系类型、列/值类型、数据画像、依赖、权限、事务、统计信息、负例等覆盖标签。
- `why`：该 family 存在的原因，以及它保护的 baseline 或 extension 缺口。

缺少任一字段的 family 不得进入可执行计划。

## Baseline 与 Derived Extension

- Required baseline matrix coverage 只由 combination matrix 和被人工提升后的结构化规则满足。
- Derived extensions 不计入 required baseline matrix coverage。
- Derived extensions 可以用于探索新交互、风险补充和后续 catalog/matrix 提升候选。
- Derived extension 被人工提升前，必须保留 `derived_extension: true`、来源说明、触发假设和稳定 oracle。
- 人工提升后，应同步更新 statement reference、combination matrix、factor catalog/type catalog 或 coverage inventory 中对应事实，再从 baseline pipeline 重新生成。

## 结构化配置

```yaml
structured_config:
  kind: association_policy
  skill_name: association_policy
  statement: common
  association_model:
    mode: hybrid_rule_first
    fact_sources:
      - statement_references
      - combination_matrices
      - factor_catalog
      - type_catalog
      - coverage_inventory
    deterministic_rules_before_llm: true
    llm_ideas_allowed_as: marked_derived_extensions
    derived_extensions_count_for_required_baseline: false
    require_manual_promotion_for_baseline: true
  scenario_family_contract:
    required_fields:
      - trigger_facts
      - lifecycle
      - oracle
      - cleanup
      - coverage_tags
      - why
```
