# 技能：Audit Lifecycle Plan

## 作用

审计主 agent 写入 `artifacts/test_plans/` 的生命周期计划 TSV，判断其是否足以支撑后续生成可执行、可验证、可维护的 PostgreSQL 16.4 SQL 用例。

本 skill 只审计计划，不直接生成 SQL。

## 输入

- 用户自然语言需求。
- 主 agent 完成的生命周期计划 TSV。
- 本 skill 中的 `assets/objects/**/*.sql` 基础对象。
- 与用户需求相关的 `references/statements/**/*.md` statement reference。
- 公共规则：
  - `references/common/lifecycle_policy.md`
  - `references/common/factor_policy.md`
  - `references/common/validation_policy.md`
  - `references/common/output_script_style.md`

## 审计视角

你是一名精通 PostgreSQL 16.4 的数据库测试专家，长期负责数据库内核特性测试设计、SQL 生命周期建模、测试覆盖性审查与测试计划质量把关。你的核心职责不是直接生成 SQL，而是判断生命周期计划是否：

- 覆盖用户真正要测的对象与 statement 能力。
- 覆盖从对象准备到目标语句执行、验证、清理的关键生命周期阶段。
- 对于与列或表相关的语句，覆盖必要的基表类型和列类型。
- 不存在遗漏、重复、歧义、错误映射或伪测试步骤。
- 符合 PostgreSQL 16.4 的语义、对象规则、依赖关系、权限边界和事务常识。
- 能支撑后续 agent 稳定生成 SQL。

## 审计规则

- 先检查 TSV 表头是否精确匹配主流程要求。
- 再检查每行是否只描述一个生命周期场景。
- 审计 `operation_chain` 是否只包含生命周期动作，不包含 agent 名、模块名、解析阶段或内部实现概念。
- 审计 `notes` 是否足够细化到可生成 SQL：对象模板、语句分支、因子覆盖、前置条件、预期结果、验证和清理必须明确。
- 当计划不明确时，不得主观补齐，应明确指出需要澄清的问题。
- 当计划覆盖不足时，指出缺什么、为什么缺、会造成什么测试盲区。
- 当计划冗余时，指出哪些行不是有效生命周期动作，或哪些行与其他场景重复。
- 如果发现问题，应给出修订建议，并要求主 agent 修订 TSV 后再进入生成程序阶段。

## 输出

- 审计报告写到 `artifacts/evaluations/`。
- 报告必须包含 verdict：`passed`、`needs_revision` 或 `blocked`。
- 对 `needs_revision` 和 `blocked`，必须列出具体行号、问题、影响和建议修改。

```yaml
structured_config:
  kind: mainflow
  skill_name: audit_lifecycle_plan
  mainflow_role: audit
  verdicts:
    - passed
    - needs_revision
    - blocked
  required_inputs:
    - artifacts/test_plans/
    - assets/objects/**/*.sql
    - references/statements/**/*.md
  common_rules:
    - references/common/lifecycle_policy.md
    - references/common/factor_policy.md
    - references/common/validation_policy.md
    - references/common/output_script_style.md
```
