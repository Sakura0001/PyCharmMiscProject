# 技能：Plan Factor Association From Statement

## 作用

把一个 PostgreSQL statement reference 转换为因子联想测试计划。这个流程不生成 SQL，也不修改仓库文件；它专门用于让无上下文子 agent 产出高级 SQL 专家的发散分析结果。

普通测试计划只回答“要测哪些 case”。本流程必须回答“哪些因子会影响语义、路径、结果和错误，以及一个因子出现后必须联想到哪些其他因子”。

## 固定输入来源

- statement reference：`references/statements/<category>/<domain>/<statement_key>.md`
- statement combination matrix：`references/combinations/<category>/<domain>/<statement_key>.yaml`
- 公共因子策略：`references/common/factor_policy.md`
- 覆盖库存：`references/combinations/_shared/coverage_inventory.yaml`
- 类型目录：`references/common/pg16_type_catalog.md`

如果 combination matrix 存在，它是 baseline coverage source。派生联想只能作为 derived extension 标注，不能替代 baseline required coverage。

## 输出要求

输出必须使用中文，路径和 YAML key 保持英文。必须按下面顺序组织：

1. **影响链路**
   - 用一条从语法形式到可观测结果的链路解释该 statement。
   - 示例形态：`语法形式 -> 目标对象 -> 输入来源 -> 依赖/约束 -> 执行路径 -> 返回值与可观测结果`。
   - 对 INSERT 这类写入语句，链路至少应细化到：`语法形式 -> 目标对象 -> 输入数据来源 -> 列映射 -> 数据类型转换 -> 默认值/生成值 -> 约束校验 -> 分区/继承/路由 -> 触发器/规则/RLS -> 索引/冲突处理 -> 事务/并发 -> 存储/WAL/复制 -> 返回值与可观测结果`。

2. **优先联想到的因子维度**
   - 先列 statement 自身语法因子。
   - 再列目标对象、列/类型、依赖、权限、约束、生命周期、数据规模、事务并发、环境副作用、验证 oracle。
   - 每个维度必须给具体取值，而不是只写抽象标题。

3. **因子触发规则**
   - 使用“如果看到 A，就必须联想到 B/C/D”的形式。
   - 触发规则必须跨因子，不得只是重复单个 factor 的 value 列表。
   - 每条规则要说明它影响的是正确性、错误路径、执行路径、并发、持久化，还是验证 oracle。
   - 例如：如果看到分区表，必须联想到 partition key、路由、default partition、无匹配分区、trigger 修改 key 和分区唯一约束；如果看到 unique/primary key，必须联想到重复写入、ON CONFLICT、并发冲突和二次约束。

4. **场景族版图**
   - 把触发规则合并成 scenario families。
   - 每个 scenario family 必须写明触发事实、扩展因子、生命周期顺序、验证 oracle、负例边界和清理方式。

5. **来源归因**
   - 标注哪些来自 statement reference。
   - 标注哪些来自 combination matrix / factor_contract / coverage_scope。
   - 标注哪些来自 coverage inventory 或 PG16 type catalog。
   - 标注哪些是 derived extension，由 agent 基于 SQL 专家知识发散得到。

6. **YAML association graph**
   - 最后输出可机器消费的 YAML。
   - 每个节点至少包含 `factor`、`when_seen`、`must_expand_to`、`oracle`、`sources`、`origin`。
   - `origin` 只能使用：`statement_reference`、`combination_matrix`、`coverage_inventory`、`type_catalog`、`derived_extension`。

## 禁止事项

- 不要生成 SQL。
- 不要创建、修改、删除、stage、commit 或 push 文件。
- 不要只输出普通 checklist。
- 不要把 derived extension 当成 required baseline coverage。
- 不要声称覆盖完整，除非说明覆盖来自哪个 source。

## 推荐回答骨架

```text
可以把 <STATEMENT> 的发散因子按“会不会影响语义、路径、结果、错误”的链路来想。

<impact chain>

对 <STATEMENT> 来说，我会优先联想到这些影响点：

1. **<dimension>**
   - <value or boundary>

真正高级的联想能力不应该只“枚举因子”，而应该把因子按影响机制连接起来：

如果 <trigger fact>
=> 必须联想到 <derived factors and oracles>

所以对这个项目来说，<STATEMENT> 的发散思考应该产出的是一张因子联想图谱：

YAML association graph shape:

association_graph:
  - factor: example_factor
    when_seen: [example_trigger]
    must_expand_to: [example_expansion]
    oracle: [example_observable_result]
    sources: [references/statements/...]
    origin: [statement_reference, derived_extension]
```

## 结构化配置

```yaml
structured_config:
  kind: mainflow
  skill_name: plan_factor_association_from_statement
  mainflow:
    inputs:
      statement_reference: references/statements/<category>/<domain>/<statement_key>.md
      combination_matrix: references/combinations/<category>/<domain>/<statement_key>.yaml
      factor_policy: references/common/factor_policy.md
      coverage_inventory: references/combinations/_shared/coverage_inventory.yaml
      type_catalog: references/common/pg16_type_catalog.md
    output_sections:
      - impact_chain
      - factor_dimensions
      - factor_trigger_rules
      - scenario_family_map
      - source_attribution
      - yaml_association_graph
    forbidden_outputs:
      - generated_sql
      - file_edits
      - unmarked_derived_extensions
```
