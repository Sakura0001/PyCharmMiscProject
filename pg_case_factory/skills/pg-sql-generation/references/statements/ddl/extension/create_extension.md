# 技能：CREATE EXTENSION

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createextension.html

```sql
CREATE EXTENSION [ IF NOT EXISTS ] extension_name
    [ WITH ] [ SCHEMA schema_name ]
             [ VERSION version ]
             [ CASCADE ]
```

PG16 关键约束：
- 加载扩展需要与创建其组成对象相同的权限。对于许多扩展，这意味着需要 **superuser** 权限。
- 如果扩展在其 control 文件中被标记为 **trusted**，则拥有当前数据库 **CREATE** 权限的任何用户都可以安装该扩展。
- 执行 CREATE EXTENSION 的用户将成为该扩展的 owner，通常也成为其创建对象的 owner。
- 扩展本身不属于任何 schema（全局唯一），但其包含的对象可以属于指定 schema。
- SCHEMA 子句：如果 control 文件指定了 schema 参数，则不能被覆盖——冲突时将报错；但如果同时指定了 CASCADE，冲突的 schema_name 被忽略（仅应用于依赖扩展）。
- CASCADE 自动安装依赖扩展，VERSION 子句不应用于自动安装的依赖扩展。
- 安装扩展需要系统上已安装扩展的支持文件。
- 可通过 pg_available_extensions 或 pg_available_extension_versions 系统视图查询可用扩展。

## 语句作用

官方说明：CREATE EXTENSION — install an extension

该 reference 关注扩展安装语句的语法分支、IF NOT EXISTS 行为、SCHEMA/VERSION/CASCADE 子句组合、权限边界（superuser / trusted 扩展 / 普通 CREATE 权限）和依赖扩展自动安装路径。

CREATE EXTENSION **不涉及列类型定义**——它安装预定义的扩展对象集。但扩展安装后会向数据库添加类型、函数、操作符等对象，这些属于扩展内部定义而非语句直接控制。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（CREATE EXTENSION / CREATE EXTENSION IF NOT EXISTS）
- object_state：目标 extension 对象状态（不存在 / 已存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- if_not_exists_clause：IF NOT EXISTS 子句开关（省略 / 指定）
- schema_clause：SCHEMA 子句形态（省略 / 指定 schema_name / control_file_schema_conflict）
- version_clause：VERSION 子句形态（省略 / 指定 version / 指定无效版本）
- cascade_clause：CASCADE 子句开关（省略 / 指定）
- extension_trust_level：扩展信任级别（trusted / untrusted）

### T3：对象名与输入形态因子
- extension_name_shape：extension 名称形态
- schema_name_shape：SCHEMA 目标名称形态
- version_string_shape：VERSION 字符串形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（superuser / create_privilege_user / non_superuser_no_create）
- schema_existence：目标 schema 存在性（存在 / 不存在）
- dependency_extension_state：依赖扩展状态（已安装 / 未安装 / CASCADE 自动安装）
- control_file_presence：扩展 control 文件存在性（系统已安装 / 系统未安装）

### T5：异常与边界因子
- duplicate_extension_name：重名冲突
- nonexistent_extension_script：扩展脚本文件不存在
- nonexistent_schema：目标 schema 不存在
- control_file_schema_conflict：control 文件 schema 与指定 schema 冲突
- insufficient_privilege：权限不足
- invalid_version：无效版本
- if_not_exists_no_op：IF NOT EXISTS 遇已存在对象（no-op 路径）

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 CREATE EXTENSION 全部语法分支（2 个顶层形式）。
- 不需要覆盖所有基表和所有列类型，因为 CREATE EXTENSION 不涉及表/列/索引组合。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖对象成功创建、重名冲突、非法定义与依赖对象缺失路径。
- 支持 `IF NOT EXISTS` 时，需要分别覆盖正常创建、no-op 语义与冲突边界。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 CREATE EXTENSION 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- CREATE EXTENSION 需要与创建组成对象相同的权限；对于大多数扩展需要 superuser 权限，必须在生成样本中显式标注。
- trusted 扩展可由拥有 CREATE 权限的用户安装，此路径需要代表性覆盖。
- 扩展不支持 schema 限定名（全局唯一），命名空间因子仅覆盖 extension_name 形态。
- CASCADE 自动安装依赖扩展的路径需要代表性覆盖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限、schema 存在性、依赖扩展或 control 文件依赖的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标对象存在 / 不存在 / 冲突全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖（superuser / trusted / 普通 CREATE 权限）
- 次优先保证：
  - IF NOT EXISTS 子句代表性覆盖
  - SCHEMA / VERSION / CASCADE 子句代表性覆盖
  - 依赖扩展自动安装代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: extension
  skill_name: create_extension
  official_source: https://www.postgresql.org/docs/16/sql-createextension.html
  statement:
    key: create_extension
    name: CREATE EXTENSION
    aliases:
    - CREATE EXTENSION
    - create extension
    - create_extension
    purpose: install an extension
  syntax_templates:
  - "CREATE EXTENSION [ IF NOT EXISTS ] extension_name [ WITH ] [ SCHEMA schema_name\
    \ ] [ VERSION version ] [ CASCADE ]"
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
    - if_not_exists_clause
    - schema_clause
    - version_clause
    - cascade_clause
    - extension_trust_level
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - extension_name_shape
    - schema_name_shape
    - version_string_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - schema_existence
    - dependency_extension_state
    - control_file_presence
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_extension_name
    - nonexistent_extension_script
    - nonexistent_schema
    - control_file_schema_conflict
    - insufficient_privilege
    - invalid_version
    - if_not_exists_no_op
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
      - key: branch_create_extension
        label: CREATE EXTENSION extension_name
      - key: branch_create_extension_if_not_exists
        label: CREATE EXTENSION IF NOT EXISTS extension_name
    object_state:
      label: 目标 extension 对象状态
      importance: important
      values:
      - key: not_exists
        label: 扩展不存在
      - key: already_exists
        label: 扩展已存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_not_exists_clause:
      label: IF NOT EXISTS 子句开关
      importance: important
      values:
      - key: omitted
        label: 省略 IF NOT EXISTS
      - key: specified
        label: 指定 IF NOT EXISTS
    schema_clause:
      label: SCHEMA 子句形态
      importance: important
      values:
      - key: omitted
        label: 省略 SCHEMA
      - key: specified_schema
        label: 指定 schema_name
      - key: control_file_schema_conflict
        label: 与 control 文件 schema 冲突
    version_clause:
      label: VERSION 子句形态
      importance: non_important
      values:
      - key: omitted
        label: 省略 VERSION (使用默认版本)
      - key: specified_version
        label: 指定有效 version
      - key: invalid_version
        label: 指定无效 version
    cascade_clause:
      label: CASCADE 子句开关
      importance: non_important
      values:
      - key: omitted
        label: 省略 CASCADE
      - key: specified
        label: 指定 CASCADE (自动安装依赖扩展)
    extension_trust_level:
      label: 扩展信任级别
      importance: non_important
      values:
      - key: trusted
        label: trusted 扩展 (可由非 superuser 安装)
      - key: untrusted
        label: untrusted 扩展 (需要 superuser)
    extension_name_shape:
      label: extension 名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
      - key: reserved_word_name
        label: 保留字作为名称
      - key: nonexistent_extension
        label: 系统未安装的扩展名
      - key: duplicate_name
        label: 已存在的扩展名
    schema_name_shape:
      label: SCHEMA 目标名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
      - key: nonexistent_schema
        label: 不存在的 schema 名称
    version_string_shape:
      label: VERSION 字符串形态
      importance: non_important
      values:
      - key: identifier_form
        label: 标识符形式
      - key: string_literal_form
        label: 字符串字面量形式
      - key: invalid_version_string
        label: 无效版本字符串
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - key: superuser
        label: 超级用户
      - key: create_privilege_user
        label: 拥有 CREATE 权限的非 superuser (仅 trusted 扩展)
      - key: non_superuser_no_create
        label: 无 CREATE 权限的非 superuser
    schema_existence:
      label: 目标 schema 存在性
      importance: non_important
      values:
      - key: schema_exists
        label: 目标 schema 存在
      - key: schema_not_exists
        label: 目标 schema 不存在
    dependency_extension_state:
      label: 依赖扩展状态
      importance: non_important
      values:
      - key: already_installed
        label: 依赖扩展已安装
      - key: not_installed_no_cascade
        label: 依赖扩展未安装且无 CASCADE
      - key: not_installed_with_cascade
        label: 依赖扩展未安装但有 CASCADE
    control_file_presence:
      label: 扩展 control 文件存在性
      importance: non_important
      values:
      - key: installed_on_system
        label: 扩展支持文件已安装在系统上
      - key: not_installed_on_system
        label: 扩展支持文件未安装在系统上
    duplicate_extension_name:
      label: 重名冲突
      importance: non_important
      values:
      - key: no_conflict
        label: 无冲突
      - key: same_name_conflict
        label: 同名扩展已存在
    nonexistent_extension_script:
      label: 扩展脚本文件不存在
      importance: non_important
      values:
      - key: script_exists
        label: 扩展脚本文件存在
      - key: script_missing
        label: 扩展脚本文件不存在
    nonexistent_schema:
      label: 目标 schema 不存在
      importance: non_important
      values:
      - key: schema_exists
        label: schema 存在
      - key: schema_missing
        label: schema 不存在
    control_file_schema_conflict:
      label: control 文件 schema 与指定 schema 冲突
      importance: non_important
      values:
      - key: no_conflict
        label: 无冲突 (省略 SCHEMA 或 schema 一致)
      - key: conflict_without_cascade
        label: 冲突且无 CASCADE → error
      - key: conflict_with_cascade_ignored
        label: 冲突但有 CASCADE → 忽略冲突
    insufficient_privilege:
      label: 权限不足
      importance: non_important
      values:
      - key: sufficient_privilege
        label: 权限充足
      - key: non_superuser_untrusted_extension
        label: 非 superuser 安装 untrusted 扩展 → error
      - key: no_create_privilege_trusted
        label: 无 CREATE 权限安装 trusted 扩展 → error
    invalid_version:
      label: 无效版本
      importance: non_important
      values:
      - key: valid_version
        label: 有效版本
      - key: nonexistent_version
        label: 不存在的版本 → error
    if_not_exists_no_op:
      label: IF NOT EXISTS 遇已存在对象
      importance: non_important
      values:
      - key: new_install
        label: 正常安装 (不存在)
      - key: no_op_notice
        label: IF NOT EXISTS 遇已存在 → notice (no-op)
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_available_extensions_query
        label: pg_available_extensions 查询
      - key: pg_extension_catalog_query
        label: pg_extension 系统目录查询
      - key: error_assertion
        label: 错误断言
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_extension
      - drop_extension_cascade
      - schema_cleanup
  notes:
    extension_not_schema_qualified: 扩展名称不属于任何 schema，是全局唯一的数据库级对象。
    trusted_extension_privilege: trusted 扩展可由拥有 CREATE 权限的用户安装，非 trusted 扩展需要 superuser。
    cascade_auto_install_deps: CASCADE 自动安装依赖扩展，VERSION 子句不应用于依赖扩展。
    control_file_schema_override: 如果 control 文件指定了 schema 参数，CREATE EXTENSION 的 SCHEMA 子句不能覆盖它。
    extension_installs_objects: CREATE EXTENSION 不直接涉及列类型定义，但扩展安装后会向数据库添加类型、函数、操作符等对象。
  defaults:
    expected_status: success
    privilege_level: superuser
    object_state: not_exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_not_exists_clause
    - schema_clause
    - version_clause
    - cascade_clause
    - extension_trust_level
    - extension_name_shape
    - schema_name_shape
    - version_string_shape
    - privilege_level
    - schema_existence
    - dependency_extension_state
    - control_file_presence
    - duplicate_extension_name
    - nonexistent_extension_script
    - nonexistent_schema
    - control_file_schema_conflict
    - insufficient_privilege
    - invalid_version
    - if_not_exists_no_op
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CREATE EXTENSION [ IF NOT EXISTS ] {extension_name} [ WITH ] [ SCHEMA {schema_name} ] [ VERSION {version} ] [ CASCADE ]"
    verification_query_template: "SELECT extname FROM pg_extension WHERE extname = '{extension_name}'"
    factor_value_bindings: {}
```
