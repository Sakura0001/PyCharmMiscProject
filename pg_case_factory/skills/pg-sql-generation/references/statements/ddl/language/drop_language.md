# 技能：DROP LANGUAGE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-droplanguage.html

```sql
DROP [ PROCEDURAL ] LANGUAGE [ IF EXISTS ] name [ CASCADE | RESTRICT ]
```

## 语句作用

官方说明：DROP LANGUAGE — remove a procedural language

该 reference 关注 procedural language 的删除、依赖级联和权限边界，不负责维护 language 创建逻辑本身。DROP LANGUAGE 是对象级 DDL，不要求覆盖普通表中的所有列类型或所有表类型。注意：执行 DROP LANGUAGE 必须是 superuser 或 language 的 owner。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- target_object_state：目标 language 对象状态
- expected_status：预期结果

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句
- cascade_clause：CASCADE/RESTRICT 子句
- privilege_context：权限上下文

### T3：对象名与输入形态因子
- name_shape：language 名形态

### T4：依赖对象与环境因子
- dependency_state：依赖对象状态
- cascade_behavior：级联行为

### T5：异常与边界因子
- invalid_combination：非法组合
- ownership_boundary：所有权边界

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 需要覆盖所有 DROP LANGUAGE 语法分支。
- 不需要覆盖所有基表。
- 不需要覆盖每张基表中所有的列类型。
- DROP LANGUAGE 是对象级 DDL，不要求覆盖普通表中的所有列类型或所有表类型。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标对象存在时的成功删除路径，以及目标对象不存在时的失败路径。
- IF EXISTS 必须覆盖不存在对象的代表性 no-op 路径。
- CASCADE/RESTRICT 必须覆盖存在依赖对象下的 RESTRICT 失败与 CASCADE 成功路径。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 DROP LANGUAGE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- DROP LANGUAGE 需要 superuser 或 owner 权限，必须在生命周期计划中显式标注环境依赖。

## 指靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与状态机相关的因子必须挂靠到满足前置状态的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象状态、核心输入形态和成功/失败路径。
- 次优先保证关键可选子句（IF EXISTS、CASCADE/RESTRICT）、权限上下文和环境上下文代表性覆盖。
- 低优先级命名、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: language
  skill_name: drop_language
  official_source: https://www.postgresql.org/docs/16/sql-droplanguage.html
  statement:
    key: drop_language
    name: DROP LANGUAGE
    aliases:
    - drop language
    - DROP LANGUAGE
    purpose: remove a procedural language
  syntax_templates:
  - "DROP [ PROCEDURAL ] LANGUAGE [ IF EXISTS ] name [ CASCADE | RESTRICT ]"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - target_object_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - if_exists_clause
    - cascade_clause
    - privilege_context
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - dependency_state
    - cascade_behavior
  - tier: T5
    name: 异常与边界因子
    factors:
    - invalid_combination
    - ownership_boundary
  - tier: T6
    name: 验证与清理因子
    factors:
    - verification_mode
    - cleanup_mode
  factors:
    statement_branch:
      label: 官方语法分支
      importance: important
      values:
      - key: branch_1
        label: DROP LANGUAGE 唯一语法分支
    target_object_state:
      label: 目标 language 对象状态
      importance: important
      values:
      - exists
      - missing
      - exists_with_dependents
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_exists_clause:
      label: IF EXISTS 子句
      importance: non_important
      values:
      - absent
      - present
    cascade_clause:
      label: CASCADE/RESTRICT 子句
      importance: non_important
      values:
      - restrict_default
      - restrict_explicit
      - cascade
    privilege_context:
      label: 权限上下文
      importance: non_important
      values:
      - superuser
      - owner
      - non_owner
      - insufficient_privilege
    name_shape:
      label: language 名形态
      importance: non_important
      values:
      - plain_identifier
      - quoted_identifier
      - missing_object
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - no_dependents
      - has_dependents
    cascade_behavior:
      label: 级联行为
      importance: non_important
      values:
      - restrict_blocks
      - cascade_succeeds
    invalid_combination:
      label: 非法组合
      importance: non_important
      values:
      - none
      - syntax_valid_semantic_error
    ownership_boundary:
      label: 所有权边界
      importance: non_important
      values:
      - superuser
      - owner
      - non_owner
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query
      - effect_query
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_objects
      - reset_state
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - target_object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_clause
    - privilege_context
    - name_shape
    - dependency_state
    - cascade_behavior
    - invalid_combination
    - ownership_boundary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - target_object_state
  rendering:
    statement_template: DROP [ PROCEDURAL ] LANGUAGE {name}
    verification_query_template: ''
    factor_value_bindings: {}
```
