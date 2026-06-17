# 技能：CREATE OPERATOR FAMILY

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createopfamily.html

```sql
CREATE OPERATOR FAMILY name USING index_method
```

## 语句作用

官方说明：CREATE OPERATOR FAMILY — define a new operator family

该 reference 关注 operator family 的创建和 USING index_method 标识，不负责定义 operator family 内部元素（通过 ALTER OPERATOR FAMILY ADD/DROP 管理）逻辑本身。CREATE OPERATOR FAMILY 是最简单的 DDL 语句之一，仅有 name 和 USING index_method 两个必选参数；创建后 operator family 为空容器，需要通过 CREATE OPERATOR CLASS 或 ALTER OPERATOR FAMILY ADD 增加内容。CREATE OPERATOR FAMILY 是对象级 DDL，不要求覆盖普通表中的所有列类型或所有表类型，但 USING index_method 是关键覆盖维度。注意：需要 superuser 或在目标 schema 有 CREATE 权限才能创建 operator family。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- target_object_state：目标 operator family 对象状态
- expected_status：预期结果

### T2：重要行为因子
- privilege_context：权限上下文

### T3：对象名与输入形态因子
- name_shape：operator family 名形态

### T4：依赖对象与环境因子
- dependency_state：依赖对象状态
- index_method_shape：索引方法形态

### T5：异常与边界因子
- invalid_combination：非法组合
- ownership_boundary：所有权边界

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 需要覆盖所有 CREATE OPERATOR FAMILY 语法分支。
- 不需要覆盖所有基表。
- 不需要覆盖每张基表中所有的列类型。
- CREATE OPERATOR FAMILY 是对象级 DDL，不要求覆盖普通表中的所有列类型或所有表类型。
- USING index_method 是关键覆盖维度，需要覆盖代表性索引方法。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖对象成功创建、重名冲突与非法定义路径。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 CREATE OPERATOR FAMILY 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- USING index_method 必须覆盖代表性索引方法（btree、hash、gist、gin、spgist、brin）。
- 需要 superuser 或 CREATE 权限的分支必须在生命周期计划中显式标注环境依赖。

## 指靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与状态机相关的因子必须挂靠到满足前置状态的样本上。
- 索引方法形态因子在成功和失败分支上轮转挂靠，覆盖代表性 index_method。

## 规模控制规则

- 优先保证官方语法分支、目标对象状态、核心输入形态和成功/失败路径。
- 次优先保证 USING index_method 代表性覆盖和权限上下文代表性覆盖。
- 低优先级命名、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: operator_family
  skill_name: create_operator_family
  official_source: https://www.postgresql.org/docs/16/sql-createopfamily.html
  statement:
    key: create_operator_family
    name: CREATE OPERATOR FAMILY
    aliases:
    - create operator family
    - CREATE OPERATOR FAMILY
    purpose: define a new operator family
  syntax_templates:
  - "CREATE OPERATOR FAMILY name USING index_method"
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
    - privilege_context
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - dependency_state
    - index_method_shape
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
        label: CREATE OPERATOR FAMILY 唯一语法分支
    target_object_state:
      label: 目标 operator family 对象状态
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
    privilege_context:
      label: 权限上下文
      importance: non_important
      values:
      - superuser
      - schema_create_privilege
      - insufficient_privilege
    name_shape:
      label: operator family 名形态
      importance: non_important
      values:
      - plain_identifier
      - schema_qualified
      - quoted_identifier
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - ready
      - missing_dependency
    index_method_shape:
      label: 索引方法形态
      importance: non_important
      values:
      - btree
      - hash
      - gist
      - gin
      - spgist
      - brin
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
      - schema_owner
      - non_privileged
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
    - privilege_context
    - name_shape
    - dependency_state
    - index_method_shape
    - invalid_combination
    - ownership_boundary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - target_object_state
  rendering:
    statement_template: CREATE OPERATOR FAMILY {name} USING {index_method}
    verification_query_template: ''
    factor_value_bindings: {}
```
