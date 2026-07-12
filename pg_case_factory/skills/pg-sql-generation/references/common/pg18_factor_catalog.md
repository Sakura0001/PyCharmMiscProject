# 技能：PostgreSQL 18.4 Factor Catalog

## 作用

本目录将现有 PG16 因子目录版本化到 PostgreSQL 18.4。它不复制 647 行基线内容，而是以逐 statement、逐 factor、逐 value 的兼容审计账本控制继承，避免两个目录静默漂移。

## 继承规则

- 基线目录：`references/common/pg16_factor_catalog.md`。
- 目标契约：`references/common/compatibility_profile.yaml`。
- 逐值证据：`references/common/postgresql_18_4_factor_audit.tsv`（随 Skill 一起打包）。
- 只有账本中 `catalog_readiness=static_ready` 的 statement 因子值可作为 PG18.4 静态目录输入；这不代表已执行数据库测试。
- `pending` 不得被生成器、计划审计器或报告显示成 PG18.4 ready。
- PG18 新语法或新语义必须在 statement matrix 的 `pg18_compatibility.test_points` 中有 reference-parity 测试点。

当前可重复审计快照包含 183 个 statement、3,357 个 statement-factor pair 和 9,978 条 statement-factor-value 记录。53 个受影响 matrix 对应 105 个必测 reference-parity point；所有 105 个 point 都显式列出 `affected_values`，合计 132 个 factor-value binding。以上只证明静态目录和必测点闭包，不证明 SQL 已渲染或数据库已执行。

## 结构化配置

```yaml
structured_config:
  kind: inherited_factor_catalog
  skill_name: pg18_factor_catalog
  version: pg18.4
  inherits:
    path: references/common/pg16_factor_catalog.md
    version: pg16
  compatibility_profile: references/common/compatibility_profile.yaml
  statement_support_inventory: references/common/statement_support_inventory.yaml
  factor_value_ledger: references/common/postgresql_18_4_factor_audit.tsv
  inheritance_policy:
    unit: statement_factor_value
    ready_column: catalog_readiness
    required_ready_value: static_ready
    pending_is_ready: false
    runtime_verified_separately: true
```
