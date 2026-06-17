# 技能：CREATE LANGUAGE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createlanguage.html

```sql
CREATE [ OR REPLACE ] [ TRUSTED ] [ PROCEDURAL ] LANGUAGE name
    HANDLER call_handler [ INLINE inline_handler ] [ VALIDATOR valfunction ]
CREATE [ OR REPLACE ] [ TRUSTED ] [ PROCEDURAL ] LANGUAGE name
```

## 语句作用

官方说明：CREATE LANGUAGE — define a new procedural language

该 reference 关注 procedural language 的创建、替换、信任属性和依赖函数状态，不负责定义 handler/inline/validator 函数的实现逻辑本身。CREATE LANGUAGE 是对象级 DDL，不要求覆盖普通表中的所有列类型或所有表类型。注意：该语句需要 superuser 权限才能执行（只有 superuser 可以创建 procedural language）；第二种语法形式（不带 HANDLER）是过时用法，会被解释为 CREATE EXTENSION，仅用于向后兼容旧转出文件。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- target_object_state：目标 language 对象状态
- expected_status：预期结果

### T2：重要行为因子
- or_replace_clause：OR REPLACE 子句
- trusted_clause：TRUSTED 子句
- handler_clause：HANDLER 子句
- inline_clause：INLINE 子句
- validator_clause：VALIDATOR 子句
- privilege_context：权限上下文

### T3：对象名与输入形态因子
- name_shape：language 名形态
- handler_name_shape：handler/inline/validator 函数名形态

### T4：依赖对象与环境因子
- dependency_state：依赖函数状态
- superuser_requirement：superuser 环境依赖

### T5：异常与边界因子
- invalid_combination：非法组合
- ownership_boundary：所有权边界

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 需要覆盖所有 CREATE LANGUAGE 语法分支。
- 不需要覆盖所有基表。
- 不需要覆盖每张基表中所有的列类型。
- CREATE LANGUAGE 是对象级 DDL，不要求覆盖普通表中的所有列类型或所有表类型。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖对象成功创建、OR REPLACE 替换语义、重名冲突、非法定义与依赖函数缺失路径。
- OR REPLACE 需要分别覆盖正常创建、替换语义与冲突边界。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 CREATE LANGUAGE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- CREATE LANGUAGE 需要 superuser 权限，必须在生命周期计划中显式标注环境依赖，不得伪造为普通成功路径。
- HANDLER 函数必须满足 language handler 的签名要求；VALIDATOR 函数必须满足 validator 的签名要求。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与状态机相关的因子必须挂靠到满足前置状态的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象状态、核心输入形态和成功/失败路径。
- 次优先保证关键可选子句（OR REPLACE、TRUSTED、HANDLER、INLINE、VALIDATOR）、权限上下文和环境上下文代表性覆盖。
- 低优先级命名、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: language
  skill_name: create_language
  official_source: https://www.postgresql.org/docs/16/sql-createlanguage.html
  statement:
    key: create_language
    name: CREATE LANGUAGE
    aliases:
    - create language
    - CREATE LANGUAGE
    purpose: define a new procedural language
  syntax_templates:
  - "CREATE [ OR REPLACE ] [ TRUSTED ] [ PROCEDURAL ] LANGUAGE name\n    HANDLER\
    \ call_handler [ INLINE inline_handler ] [ VALIDATOR valfunction ]\nCREATE [\
    \ OR REPLACE ] [ TRUSTED ] [ PROCEDURAL ] LANGUAGE name"
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
    - or_replace_clause
    - trusted_clause
    - handler_clause
    - inline_clause
    - validator_clause
    - privilege_context
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - name_shape
    - handler_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - dependency_state
    - superuser_requirement
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
        label: 带 HANDLER 的完整语法形式
      - key: branch_2
        label: 不带 HANDLER 的过时形式（解释为 CREATE EXTENSION）
    target_object_state:
      label: 目标 language 对象状态
      importance: important
      values:
      - absent
      - exists
      - exists_conflict
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    or_replace_clause:
      label: OR REPLACE 子句
      importance: non_important
      values:
      - absent
      - present_replace_new
      - present_replace_existing
    trusted_clause:
      label: TRUSTED 子句
      importance: non_important
      values:
      - absent
      - present
    handler_clause:
      label: HANDLER 子句
      importance: non_important
      values:
      - handler_exists
      - handler_missing
    inline_clause:
      label: INLINE 子句
      importance: non_important
      values:
      - absent
      - present
    validator_clause:
      label: VALIDATOR 子句
      importance: non_important
      values:
      - absent
      - present
    privilege_context:
      label: 权限上下文
      importance: non_important
      values:
      - superuser
      - non_superuser
    name_shape:
      label: language 名形态
      importance: non_important
      values:
      - plain_identifier
      - schema_qualified
      - quoted_identifier
    handler_name_shape:
      label: handler/inline/validator 函数名形态
      importance: non_important
      values:
      - plain_function
      - schema_qualified_function
      - missing_function
    dependency_state:
      label: 依赖函数状态
      importance: non_important
      values:
      - ready
      - missing_handler
      - missing_validator
      - wrong_signature
    superuser_requirement:
      label: superuser 环境依赖
      importance: non_important
      values:
      - superuser_available
      - superuser_required_only
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
      - non_superuser
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
    - or_replace_clause
    - trusted_clause
    - handler_clause
    - inline_clause
    - validator_clause
    - privilege_context
    - name_shape
    - handler_name_shape
    - dependency_state
    - superuser_requirement
    - invalid_combination
    - ownership_boundary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - target_object_state
  rendering:
    statement_template: CREATE [ OR REPLACE ] [ TRUSTED ] [ PROCEDURAL ] LANGUAGE {name}
    verification_query_template: ''
    factor_value_bindings: {}
```
