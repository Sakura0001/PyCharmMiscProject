# 技能：STATEMENT_NAME

## 使用方式

创建或补齐 `references/statements/<category>/<domain>/<statement_key>.md` 时，以本模板为骨架。保留 Markdown 给 agent 做测试设计判断，同时补齐 `structured_config` 给工具和后续生成流程稳定读取。

注意：本模板自身使用 `kind: template`，复制到正式 statement reference 后必须改为 `kind: statement`。

## 语句作用

说明该 PostgreSQL 18.4 statement 的用途、SQL/用户可见测试职责和不负责的边界。

## 官方语法范围补充

```sql
-- 粘贴 PostgreSQL 18.4 官方 synopsis；复杂语句保留所有顶层语法分支。
```

## 测试因子分级

### T1：核心语义因子
- 语句分支
- 目标对象状态
- 成功路径与失败路径

### T2：重要行为因子
- 官方 synopsis 中影响语义的关键可选子句

### T3：对象名与输入形态因子
- 合法普通标识符
- schema 限定标识符
- 双引号标识符
- 已存在对象名
- 不存在对象名
- 非法名称或非法参数值

### T4：依赖对象与环境因子
- role、schema、tablespace、extension、server 等依赖
- 权限、owner、事务、锁或环境限制

### T5：异常与边界因子
- 语法合法但语义非法的组合
- 语法非法的组合
- 对象类型不匹配

### T6：验证与清理因子
- 系统目录验证
- 对象可用性验证
- 幂等清理

## 覆盖策略

- 需要覆盖所有 STATEMENT_NAME 语法分支。
- 按语句是否引用表、列、表达式或数据，决定是否覆盖所有基表和所有列类型。
- T1 因子做笛卡尔积覆盖。
- 所有适用 inventory axis 都使用 `coverage_mode: complete` 并声明来源。
- T2 及之后因子可以拆分到独立 test point，但每个适用值都必须进入 obligation。
- 必须同时保留成功路径与失败路径。
- 不得使用代表值、sampling、pairwise 或轮转挂靠替代完整 relation/table/type 或语法 inventory。

## 生成约束

- 每个样本必须包含明确的前置对象准备、目标语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 需要特殊权限、外部服务、文件系统或非事务环境的分支必须显式标注。

## 挂靠规则

- 语义独立的附属因子可以拆到独立 test point，但仍需完整枚举其 inventory。
- 单条样本可以绑定多个因子，但不得破坏主覆盖归因或产生冲突 classification。

## 规模控制规则

- 优先保证语句分支、对象状态、成功/失败路径和 T1 主因子。
- 完整保留每个适用 T2-T6 inventory 值；必要时拆分 test point 和降低并发。
- 规模过大时断点续跑，不裁剪 inventory。

## 结构化配置

```yaml
structured_config:
  kind: template
  template_for: statement
  compatibility_target: postgresql-18.4
  category: example_category
  domain: example_domain
  skill_name: example_statement
  statement:
    key: example_statement
    name: EXAMPLE STATEMENT
    aliases:
      - example statement
      - 示例语句
    purpose: 简要说明 statement 的用途
  syntax_templates:
    - EXAMPLE STATEMENT object_name
  factor_layers:
    - tier: T1
      name: 核心语义因子
      factors: [statement_branch, object_state, expected_status]
  factors:
    statement_branch:
      label: 语句分支
      importance: important
      values:
        - key: default_branch
          label: 默认分支
    object_state:
      label: 目标对象状态
      importance: important
      values:
        - absent
        - exists
    expected_status:
      label: 预期结果
      importance: important
      values:
        - success
        - failure
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes: [statement_branch, object_state, expected_status]
    non_main_factors: []
    axis_coverage_mode: complete
    sampling_allowed: false
    python_expand_threshold: 200
  rendering:
    statement_template: EXAMPLE STATEMENT {object_name}
    verification_query_template: ""
    factor_value_bindings: {}
```
