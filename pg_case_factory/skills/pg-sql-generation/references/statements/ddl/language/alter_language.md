# 技能：ALTER LANGUAGE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alterlanguage.html

```sql
ALTER [ PROCEDURAL ] LANGUAGE name RENAME TO new_name
ALTER [ PROCEDURAL ] LANGUAGE name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
```

## 语句作用

官方说明：ALTER LANGUAGE — change the definition of a procedural language

该 reference 关注 procedural language 的重命名和属主变更，不负责定义 language handler 函数本身。ALTER LANGUAGE 是对象级 DDL，不要求覆盖普通表中的所有列类型或所有表类型。注意：执行 ALTER LANGUAGE 必须是 superuser 或 language 的 owner；OWNER TO 分支还需目标角色具备相应权限。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- target_object_state：目标 language 对象状态
- expected_status：预期结果

### T2：重要行为因子
- alter_action：ALTER 动作类型
- new_owner_shape：新 owner 形态（仅适用于 OWNER TO 分支）
- privilege_context：权限上下文

### T3：对象名与输入形态因子
- name_shape：language 名形态
- new_name_shape：新名/新 owner 名形态

### T4：依赖对象与环境因子
- dependency_state：依赖对象状态
- rename_conflict：重命名冲突状态

### T5：异常与边界因子
- invalid_combination：非法组合
- ownership_boundary：所有权边界

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 需要覆盖所有 ALTER LANGUAGE 语法分支。
- 不需要覆盖所有基表。
- 不需要覆盖每张基表中所有的列类型。
- ALTER LANGUAGE 是对象级 DDL，不要求覆盖普通表中的所有列类型或所有表类型。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须预创建可被修改的目标 language，并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标对象存在时的成功修改路径、目标对象不存在时的失败路径。
- RENAME TO 与 OWNER TO 分支需要保持独立归因。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 ALTER LANGUAGE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- ALTER LANGUAGE 需要 superuser 或 owner 权限，必须在生命周期计划中显式标注环境依赖。

## 指靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与状态机相关的因子必须挂靠到满足前置状态的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象状态、核心输入形态和成功/失败路径。
- 次优先保证关键可选子句（RENAME TO、OWNER TO）、权限上下文和环境上下文代表性覆盖。
- 低优先级命名、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: language
  skill_name: alter_language
  official_source: https://www.postgresql.org/docs/16/sql-alterlanguage.html
  statement:
    key: alter_language
    name: ALTER LANGUAGE
    aliases:
    - alter language
    - ALTER LANGUAGE
    purpose: change the definition of a procedural language
  syntax_templates:
  - "ALTER [ PROCEDURAL ] LANGUAGE name RENAME TO new_name\nALTER [ PROCEDURAL\
    \ ] LANGUAGE name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER\
    \ }"
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
    - alter_action
    - new_owner_shape
    - privilege_context
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - name_shape
    - new_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - dependency_state
    - rename_conflict
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
      - key: branch_rename
        label: RENAME TO 分支
      - key: branch_owner
        label: OWNER TO 分支
    target_object_state:
      label: 目标 language 对象状态
      importance: important
      values:
      - exists
      - missing
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    alter_action:
      label: ALTER 动作类型
      importance: important
      values:
      - rename
      - owner_change
    new_owner_shape:
      label: 新 owner 形态
      importance: non_important
      values:
      - plain_role
      - current_role
      - current_user
      - session_user
      - missing_role
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
    new_name_shape:
      label: 新名/新 owner 名形态
      importance: non_important
      values:
      - plain_identifier
      - quoted_identifier
      - existing_name_conflict
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - ready
      - missing_dependency
    rename_conflict:
      label: 重命名冲突状态
      importance: non_important
      values:
      - new_name_available
      - new_name_conflict
    invalid_combination:
      label: 非法组合
      importance: non_important
      values:
      - none
      - syntax_valid_semantic_error
      - object_type_mismatch
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
    - alter_action
    - new_owner_shape
    - privilege_context
    - name_shape
    - new_name_shape
    - dependency_state
    - rename_conflict
    - invalid_combination
    - ownership_boundary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - target_object_state
  rendering:
    statement_template: ALTER [ PROCEDURAL ] LANGUAGE {name}
    verification_query_template: ''
    factor_value_bindings: {}
```
