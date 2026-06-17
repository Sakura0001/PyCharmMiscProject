# 技能：ALTER TRIGGER

## 官方语法范围

来源：https://www.postgresql.org/docs/16/sql-altertrigger.html

### Synopsis 形式 1：重命名 (RENAME TO)

```sql
ALTER TRIGGER name ON table_name RENAME TO new_name
```

### Synopsis 形式 2：扩展依赖 ([ NO ] DEPENDS ON EXTENSION)

```sql
ALTER TRIGGER name ON table_name [ NO ] DEPENDS ON EXTENSION extension_name
```

## 语句作用

官方说明：ALTER TRIGGER — change the definition of a trigger

该 reference 关注触发器修改语句的两种语法分支（RENAME TO、DEPENDS ON EXTENSION）、前置依赖、权限边界与成功/失败路径。

ALTER TRIGGER 语法相对简单，仅有 RENAME 和 DEPENDS ON EXTENSION 两种形式。不直接涉及列数据类型选择。权限要求是必须拥有触发器所在表的所有权。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支（RENAME TO、DEPENDS ON EXTENSION）
- object_state：目标触发器对象存在性（exists、not_exists）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- rename_target：重命名目标形态（simple、quoted、reserved_word、duplicate_name）
- extension_target：扩展目标形态（extension_exists、extension_not_exists、NO_DEPENDS）
- partitioned_table_effect：分区表上重命名是否级联到分区（partitioned_table、regular_table）

### T3：对象名与输入形态因子
- trigger_name_shape：触发器名形态（simple、quoted、reserved_word、schema_qualified）
- table_name_shape：表名形态（simple、quoted、schema_qualified）
- new_name_shape：新名称形态（simple、quoted、reserved_word）

### T4：依赖对象与环境因子
- privilege_level：权限级别（superuser、table_owner、non_owner_no_privilege）
- extension_dependency：扩展依赖（extension_installed、extension_not_installed）
- table_dependency：表依赖（table_exists、table_not_exists）

### T5：异常与边界因子
- target_trigger_not_exists：目标触发器不存在
- permission_insufficient：权限不足（非表Owner）
- target_extension_not_exists：扩展不存在
- identifier_length_exceeded：标识符长度超限
- trigger_name_duplicate：重命名后与现有触发器同名

### T6：验证与清理因子
- verification_mode：验证方式（pg_trigger_catalog_query、information_schema_triggers）
- cleanup_mode：清理方式（DROP_TRIGGER、DROP_TRIGGER_IF_EXISTS）

## 覆盖策略

- 必须覆盖所有两种 ALTER TRIGGER 语法分支。
- 不需要覆盖所有基表列类型。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。
- 如果生成规模超过 100 万，优先裁剪 T3-T6，再裁剪局部语法开关，最后才允许压缩语句分支数量。

## 生成约束

- 必须预创建可被修改的目标触发器对象，并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标对象存在时的成功修改路径、目标对象不存在时的失败路径。
- RENAME / DEPENDS ON EXTENSION 分支需要保持独立归因。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备（创建表、创建触发器函数、创建触发器）、目标 ALTER TRIGGER 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 对需要 superuser、文件系统、复制连接、tablespace 目录、扩展、外部服务或非事务环境的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子中 trigger_name_shape 挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T3 因子中 table_name_shape 挂靠到所有分支的样本上轮转注入。
- T3 因子中 new_name_shape 挂靠到 RENAME 分支的样本上。
- T4 因子仅挂靠到需要依赖对象、权限、extension 的分支。
- T4 因子中 privilege_level 挂靠到所有分支，确保权限路径被覆盖。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖（2种形式）
  - 目标对象存在 / 不存在全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - 官方 Synopsis 中的可选关键字代表性覆盖
  - extension、owner 等依赖对象代表性覆盖
  - 分区表级联效果代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖：
  - identifier 边界条件
  - 触发器名/表名形态变体

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: trigger
  skill_name: alter_trigger
  official_source: https://www.postgresql.org/docs/16/sql-altertrigger.html
  statement:
    key: alter_trigger
    name: ALTER TRIGGER
    aliases:
    - ALTER TRIGGER
    - alter trigger
    - alter_trigger
    purpose: change the definition of a trigger
  syntax_templates:
  - |
    ALTER TRIGGER name ON table_name RENAME TO new_name
  - |
    ALTER TRIGGER name ON table_name [ NO ] DEPENDS ON EXTENSION extension_name
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - object_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - rename_target
    - extension_target
    - partitioned_table_effect
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - trigger_name_shape
    - table_name_shape
    - new_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - extension_dependency
    - table_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - target_trigger_not_exists
    - permission_insufficient
    - target_extension_not_exists
    - identifier_length_exceeded
    - trigger_name_duplicate
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
        label: 重命名 (RENAME TO new_name)
      - key: branch_2
        label: 扩展依赖 ([ NO ] DEPENDS ON EXTENSION)
    object_state:
      label: 目标触发器对象存在性
      importance: important
      values:
      - key: exists
        label: 触发器存在
      - key: not_exists
        label: 触发器不存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    rename_target:
      label: 重命名目标形态
      importance: important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: reserved_word
        label: 保留字标识符
      - key: duplicate_name
        label: 已存在触发器名（同表内冲突）
    extension_target:
      label: 扩展目标形态
      importance: important
      values:
      - key: extension_exists
        label: 扩展已安装
      - key: extension_not_exists
        label: 扩展未安装
      - key: NO_DEPENDS
        label: NO DEPENDS ON EXTENSION（解除依赖）
    partitioned_table_effect:
      label: 分区表级联效果
      importance: important
      values:
      - key: partitioned_table
        label: 分区表（重命名级联到分区）
      - key: regular_table
        label: 普通表（仅影响自身）
    trigger_name_shape:
      label: 触发器名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: reserved_word
        label: 保留字标识符
      - key: schema_qualified
        label: Schema 限定标识符（非法 - 触发器不支持schema限定）
    table_name_shape:
      label: 表名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: schema_qualified
        label: Schema 限定标识符
    new_name_shape:
      label: 新名称形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: reserved_word
        label: 保留字标识符
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: superuser
        label: 超级用户
      - key: table_owner
        label: 表 Owner
      - key: non_owner_no_privilege
        label: 非表Owner（失败路径）
    extension_dependency:
      label: 扩展依赖
      importance: non_important
      values:
      - key: extension_installed
        label: 扩展已安装
      - key: extension_not_installed
        label: 扩展未安装
    table_dependency:
      label: 表依赖
      importance: non_important
      values:
      - key: table_exists
        label: 目标表存在
      - key: table_not_exists
        label: 目标表不存在
    target_trigger_not_exists:
      label: 目标触发器不存在
      importance: non_important
      values:
      - key: trigger_not_found
        label: 触发器名不存在
    permission_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - key: not_table_owner
        label: 非表Owner无法修改触发器
    target_extension_not_exists:
      label: 扩展不存在
      importance: non_important
      values:
      - key: extension_name_not_found
        label: DEPENDS ON EXTENSION 指定不存在的扩展
    identifier_length_exceeded:
      label: 标识符长度超限
      importance: non_important
      values:
      - key: over_63_chars
        label: 标识符超过63字符
    trigger_name_duplicate:
      label: 重命名后同名冲突
      importance: non_important
      values:
      - key: same_table_same_name
        label: 同表内已有同名触发器
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_trigger_catalog_query
        label: pg_trigger 系统目录查询
      - key: information_schema_triggers
        label: information_schema.triggers 查询
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_TRIGGER
        label: DROP TRIGGER name ON table_name
      - key: DROP_TRIGGER_IF_EXISTS
        label: DROP TRIGGER IF EXISTS name ON table_name
  defaults:
    expected_status: success
    object_state: exists
    partitioned_table_effect: regular_table
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - expected_status
    non_main_factors:
    - rename_target
    - extension_target
    - partitioned_table_effect
    - trigger_name_shape
    - table_name_shape
    - new_name_shape
    - privilege_level
    - extension_dependency
    - table_dependency
    - target_trigger_not_exists
    - permission_insufficient
    - target_extension_not_exists
    - identifier_length_exceeded
    - trigger_name_duplicate
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
  rendering:
    statement_template: "ALTER TRIGGER name ON table_name RENAME TO new_name"
    verification_query_template: "SELECT tgname FROM pg_trigger WHERE tgname = '{trigger_name}'"
    factor_value_bindings:
      extension_target:
        extension_exists: "DEPENDS ON EXTENSION extension_name"
        extension_not_exists: "DEPENDS ON EXTENSION nonexistent_extension"
        NO_DEPENDS: "NO DEPENDS ON EXTENSION extension_name"
```
```