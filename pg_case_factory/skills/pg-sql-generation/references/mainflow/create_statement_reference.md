# 技能：Create Statement Reference

## 作用

为 PostgreSQL 16.4 statement 创建或补齐 `references/statements/<category>/<domain>/<statement_key>.md`。本 skill 用于规范 statement reference 的内容结构，使其既能被 agent 用来做测试设计，也能被后续工具读取结构化配置。

## 输入

- 用户指定的 statement，例如 `CREATE TABLESPACE`、`ALTER TYPE`。
- PostgreSQL 16 官方语法。
- 同类 statement reference 示例，例如 `references/statements/ddl/index/create_index.md`、`references/statements/dml/table/insert.md`。
- 标准模板：`references/templates/statement_reference_template.md`。

## 输出位置

- 新增或更新：`references/statements/<category>/<domain>/<statement_key>.md`
- 不在 helper code 或 runner 中写入 statement 专用逻辑。
- 不在 statement reference 中写死完整生命周期；生命周期由 mainflow 和 common 规则组合生成。

## 编写流程

1. 确定 category、domain 与 statement_key，使用小写 snake_case，例如 `ddl/tablespace/create_tablespace`、`dml/table/insert`。
2. 查询 PostgreSQL 16 官方语法，保留所有顶层 synopsis 分支。
3. 描述语句作用，并明确该 skill 的职责边界。
4. 按 T1-T6 分级测试因子：
   - T1：核心语义因子。
   - T2：重要行为因子。
   - T3：对象名与输入形态因子。
   - T4：依赖对象与环境因子。
   - T5：异常与边界因子。
   - T6：验证与清理因子。
5. 定义覆盖策略：
   - 是否覆盖所有语法分支。
   - 是否覆盖所有基表。
   - 是否覆盖所有列类型。
   - T1 是否完整笛卡尔积。
   - T2 是否参与主组合或降级为代表性覆盖。
   - T3 及之后因子如何挂靠。
6. 定义生成约束：
   - 成功路径。
   - 失败路径。
   - 前置依赖。
   - 权限、事务、锁、环境限制。
   - 验证和清理要求。
7. 定义挂靠规则与规模控制规则。
8. 补齐 `structured_config`，至少包含：
   - `kind: statement`
   - `category`
   - `domain`
   - `skill_name`
   - `statement.key`
   - `statement.name`
   - `statement.aliases`
   - `syntax_templates`
   - `factor_layers`
   - `factors`
   - `coverage_policy`
   - `rendering`

## 覆盖口径

- 对涉及表、列、表达式、索引、约束或数据访问的 statement，默认需要分析是否覆盖所有基表和列类型。
- 对不引用表列的对象级 statement，例如 role、database、tablespace，应明确写出“不需要覆盖所有基表/列类型”的原因。
- 对支持 `IF EXISTS`、`IF NOT EXISTS`、`OR REPLACE`、`CASCADE`、`RESTRICT` 等开关的 statement，必须覆盖正常路径、no-op 或替换语义、冲突边界和失败路径。
- 需要 superuser、文件系统、复制连接、外部服务、非事务环境或特殊集群配置的分支，必须显式标注环境依赖，不得伪造为普通成功路径。

```yaml
structured_config:
  kind: mainflow
  skill_name: create_statement_reference
  mainflow_role: create_statement_reference
  template: references/templates/statement_reference_template.md
  required_sections:
    - 语句作用
    - 官方语法范围补充
    - 测试因子分级
    - 覆盖策略
    - 生成约束
    - 挂靠规则
    - 规模控制规则
    - 结构化配置
```
