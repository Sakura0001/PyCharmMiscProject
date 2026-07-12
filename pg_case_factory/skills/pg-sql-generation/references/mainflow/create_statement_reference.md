# 创建 PostgreSQL 18.4 Statement Reference

## 目标

创建或补齐 `references/statements/<category>/<domain>/<statement_key>.md`，使 agent 能按 PostgreSQL 18.4 官方语义设计完整覆盖，工具能稳定读取结构化配置。

## 输入

- 用户指定的 statement
- PostgreSQL 18.4 官方 synopsis 与正文
- `references/common/compatibility_profile.yaml`
- `references/common/statement_support_inventory.yaml`
- PG18.4 factor/type catalogs
- 同类 statement reference 和 matching combination matrix
- `references/templates/statement_reference_template.md`

## 编写步骤

1. 确定 category、domain 和小写 snake_case statement key。
2. 读取 PostgreSQL 18.4 官方文档，保留全部顶层 synopsis 分支、选项、约束和版本差异。记录官方 ref/source 标识。
3. 对照 support inventory 与 16.4 -> 18.4 compatibility audit。未审计项标为 pending，不得冒充 ready。
4. 定义语句作用、SQL 可观察结果和边界；不写底层日志或根因逻辑。
5. 按 T1-T6 组织因子：核心语义、重要行为、名称/输入形态、依赖/环境、异常/边界、验证/清理。
6. 对涉及表、列、表达式、索引、约束或数据访问的 statement，引用完整 PG18.4 relation/table/type inventory。对不适用的 inventory 给出明确原因。
7. 完整覆盖所有语法分支与每个适用 inventory 值；核心 axes 做笛卡尔积。不得用 representative、sampling、pairwise 或轮转值替代完整覆盖。
8. 定义成功、expected failure、权限、事务、锁、外部环境、稳定验证和幂等清理约束。
9. 需要 superuser、文件系统、复制连接、外部服务、非事务环境或特殊集群配置的分支，显式声明环境依赖；不要伪造普通成功路径。
10. 补齐 `structured_config`：kind/category/domain/skill_name、statement、syntax_templates、factor_layers、factors、coverage_policy、rendering 和 compatibility target。
11. 运行 statement reference、factor mapping、combination matrix 与 PG18.4 compatibility audits；全部通过后才更新 ready 状态。

## 覆盖门禁

- 每个适用语法分支、对象类型、relation/table 类型和列类型必须进入 required coverage。
- 不适用或不支持的值不得从 inventory 静默删除；在计划中分类为 `justified_na` 或 `expected_failure` 并给 reason。
- `IF EXISTS`、`IF NOT EXISTS`、`OR REPLACE`、`CASCADE`、`RESTRICT` 等分支必须覆盖正常、no-op/替换、冲突和失败语义。
- 规模过大时拆分 test points 并断点执行，不裁剪 inventory。

```yaml
structured_config:
  kind: mainflow
  skill_name: create_statement_reference
  mainflow_role: create_statement_reference
  compatibility_target: postgresql-18.4
  template: references/templates/statement_reference_template.md
  require_complete_inventory: true
  sampling_allowed: false
```
