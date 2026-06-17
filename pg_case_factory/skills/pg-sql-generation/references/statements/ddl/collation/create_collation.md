# 技能：CREATE COLLATION

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createcollation.html

### Synopsis 形式 1：定义新校对规则（参数形式）

```sql
CREATE COLLATION [ IF NOT EXISTS ] name (
    [ LOCALE = locale, ]
    [ LC_COLLATE = lc_collate, ]
    [ LC_CTYPE = lc_ctype, ]
    [ PROVIDER = provider, ]
    [ DETERMINISTIC = boolean, ]
    [ RULES = rules, ]
    [ VERSION = version ]
)
```

### Synopsis 形式 2：复制已有校对规则

```sql
CREATE COLLATION [ IF NOT EXISTS ] name FROM existing_collation
```

**重要行为说明**：
- CREATE COLLATION 有两种形式：参数定义和从已有校对规则复制。
- `IF NOT EXISTS` 在同名校对规则已存在时不抛出错误，仅发出通知。但**不保证**已存在的校对规则与预期定义一致。
- `PROVIDER` 为 `icu`（需服务器编译时启用 ICU）或 `libc`（默认）。
- `LOCALE` 是 `LC_COLLATE` 和 `LC_CTYPE` 的快捷设置（仅 libc provider），不能同时指定 LOCALE 和 LC_COLLATE/LC_CTYPE。
- `DETERMINISTIC` 默认 `true`。设为 `false` 时启用区分大小写/重音的比较，**仅 ICU provider 支持**非确定性校对规则。
- `RULES` 仅 ICU provider 支持，用于自定义校对规则（ICU Tailoring Rules）。
- `VERSION` 通常自动计算，仅用于 pg_upgrade 复制已有安装的版本信息。
- CREATE COLLATION 获取 `SHARE ROW EXCLUSIVE` 锁于 `pg_collation`，故同时只能运行一条。
- 必须有目标 schema 的 CREATE 权限。
- libc locale 必须适用于当前数据库编码。
- CREATE COLLATION **不直接涉及列类型**，但校对规则被列定义引用（`text COLLATE collation_name`）。

## 语句作用

官方说明：CREATE COLLATION — define a new collation

该 reference 关注校对规则定义语句的语法分支、locale/provider 设置、ICU 规则定制与 IF NOT EXISTS 行为，不负责覆盖表/列/索引类型组合。

CREATE COLLATION **不直接涉及列类型**，具体表现为：
- 语句仅定义校对规则的排序/比较行为
- 校对规则被列定义引用（`text COLLATE collation_name`），但不需按列类型展开
- locale/icu 设置是校对规则核心参数

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支（define_with_params、from_existing）
- object_state：目标 Collation 对象存在性（不存在、已存在）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- if_not_exists_clause：IF NOT EXISTS 子句（absent、present_no_conflict、present_with_conflict）
- provider：校对规则提供者（libc_default、icu）
- deterministic_option：确定性选项（true_default、false_icu_only）

### T3：对象名与输入形态因子
- collation_name_shape：校对规则名称形态（plain_identifier、quoted_identifier、schema_qualified）
- locale_setting：locale 设置方式（LOCALE_only、LC_COLLATE_LC_CTYPE_separate、LOCALE_with_provider）— 仅参数形式
- from_collation_shape：源校对规则形态（existing_builtin_collation、existing_user_collation、nonexistent_collation）— 仅 FROM 形式
- rules_setting：ICU 规则设置（no_rules、with_rules）— 仅 ICU provider

### T4：依赖对象与环境因子
- privilege_level：权限级别（schema_owner_with_create、non_schema_owner）
- icu_availability：ICU 可用性（icu_available、icu_not_available）
- locale_validity：locale 有效性（valid_locale_for_encoding、invalid_locale_for_encoding）
- from_collation_dependency：源校对规则依赖（FROM 形式）

### T5：异常与边界因子
- duplicate_collation：重名冲突（同schema同名→error或IF NOT EXISTS notice）
- invalid_locale_for_encoding：locale 不适用于当前数据库编码 → error
- icu_not_available：ICU provider 不可用 → error
- nondeterministic_non_icu：非 ICU provider 使用 DETERMINISTIC=false → error
- rules_non_icu：非 ICU provider 使用 RULES → error
- locale_and_lc_conflict：同时指定 LOCALE 和 LC_COLLATE/LC_CTYPE → error
- insufficient_privilege：无目标 schema 的 CREATE 权限 → error

### T6：验证与清理因子
- verification_mode：验证方式（pg_collation_catalog_query、actual_collation_usage）
- cleanup_mode：清理方式（DROP_COLLATION、DROP_COLLATION_IF_EXISTS、DROP_COLLATION_CASCADE）

## 覆盖策略

- 必须覆盖 CREATE COLLATION 的两种语法分支（参数定义、FROM 复制）。
- 必须覆盖 libc 和 ICU 两种 provider。
- 必须覆盖 DETERMINISTIC true 和 false（仅 ICU）。
- CREATE COLLATION 不涉及列类型组合；locale/icu 设置是核心覆盖维度。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合：当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
- T3、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖对象成功创建、重名冲突、非法定义与依赖对象缺失路径。
- 支持 IF NOT EXISTS 时，需要分别覆盖正常创建、no-op 与冲突边界。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 CREATE COLLATION 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 测试 collation 优先使用 `CREATE COLLATION <name> FROM "C"` 构造，避免依赖环境特定 locale。
- ICU 相关分支需要标注 ICU 可用性环境依赖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- locale_setting 仅挂靠到参数定义分支。
- from_collation_shape 仅挂靠到 FROM 复制分支。
- rules_setting 仅挂靠到 ICU provider 分支。
- T4 因子仅挂靠到需要依赖对象、权限、ICU 环境的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖（两种形式）
  - libc / ICU provider 全覆盖
  - 目标对象存在 / 不存在 / 冲突全覆盖
  - IF NOT EXISTS 行为全覆盖
  - 成功 / 失败路径全覆盖
- 次优先保证：
  - DETERMINISTIC true/false 覆盖
  - ICU 规则代表性覆盖
  - locale 设置方式代表性覆盖
  - FROM 复制代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: collation
  skill_name: create_collation
  official_source: https://www.postgresql.org/docs/16/sql-createcollation.html
  statement:
    key: create_collation
    name: CREATE COLLATION
    aliases:
    - CREATE COLLATION
    - create collation
    - create_collation
    purpose: define a new collation
  syntax_templates:
  - "CREATE COLLATION [ IF NOT EXISTS ] name ( [ LOCALE = locale, ] [ LC_COLLATE = lc_collate, ] [ LC_CTYPE = lc_ctype, ] [ PROVIDER = provider, ] [ DETERMINISTIC = boolean, ] [ RULES = rules, ] [ VERSION = version ] )"
  - "CREATE COLLATION [ IF NOT EXISTS ] name FROM existing_collation"
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
    - provider
    - deterministic_option
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - collation_name_shape
    - locale_setting
    - from_collation_shape
    - rules_setting
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - icu_availability
    - locale_validity
    - from_collation_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_collation
    - invalid_locale_for_encoding
    - icu_not_available
    - nondeterministic_non_icu
    - rules_non_icu
    - locale_and_lc_conflict
    - insufficient_privilege
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
      - key: branch_define_with_params
        label: 参数定义形式
      - key: branch_from_existing
        label: 从已有校对规则复制 (FROM)
    object_state:
      label: 目标Collation对象存在性
      importance: important
      values:
      - key: not_exists
        label: 校对规则不存在
      - key: already_exists
        label: 校对规则已存在 (同schema同名)
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_not_exists_clause:
      label: IF NOT EXISTS子句
      importance: important
      values:
      - key: absent
        label: 不使用IF NOT EXISTS
      - key: present_no_conflict
        label: IF NOT EXISTS且无冲突 (正常创建)
      - key: present_with_conflict
        label: IF NOT EXISTS且有冲突 (发出notice，不保证定义一致)
    provider:
      label: 校对规则提供者
      importance: important
      values:
      - key: libc_default
        label: libc (默认provider)
      - key: icu
        label: ICU (需服务器编译时启用ICU支持)
    deterministic_option:
      label: 确定性选项
      importance: important
      values:
      - key: true_default
        label: DETERMINISTIC = true (默认，确定性比较)
      - key: false_icu_only
        label: DETERMINISTIC = false (仅ICU，非确定性比较)
    collation_name_shape:
      label: 校对规则名称形态
      importance: non_important
      values:
      - key: plain_identifier
        label: 合法普通标识符
      - key: quoted_identifier
        label: 双引号标识符 (如 "de_DE")
      - key: schema_qualified
        label: Schema限定标识符
    locale_setting:
      label: locale设置方式 (仅参数定义)
      importance: non_important
      values:
      - key: LOCALE_only
        label: 仅LOCALE (快捷设置LC_COLLATE+LC_CTYPE)
      - key: LC_COLLATE_LC_CTYPE_separate
        label: LC_COLLATE + LC_CTYPE 分别设置
      - key: LOCALE_with_provider
        label: LOCALE + PROVIDER组合
    from_collation_shape:
      label: 源校对规则形态 (仅FROM形式)
      importance: non_important
      values:
      - key: existing_builtin_collation
        label: 内置校对规则 (如 "C", "en_US.utf8")
      - key: existing_user_collation
        label: 用户定义校对规则
      - key: nonexistent_collation
        label: 不存在的校对规则 → error
    rules_setting:
      label: ICU规则设置 (仅ICU provider)
      importance: non_important
      values:
      - key: no_rules
        label: 无RULES子句
      - key: with_rules
        label: RULES子句 (ICU Tailoring Rules)
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: schema_owner_with_create
        label: 有目标Schema的CREATE权限
      - key: non_schema_owner
        label: 无目标Schema的CREATE权限 → error
    icu_availability:
      label: ICU可用性
      importance: non_important
      values:
      - key: icu_available
        label: ICU可用 (服务器编译时启用)
      - key: icu_not_available
        label: ICU不可用 → PROVIDER=icu error
    locale_validity:
      label: locale有效性
      importance: non_important
      values:
      - key: valid_locale_for_encoding
        label: locale适用于当前数据库编码
      - key: invalid_locale_for_encoding
        label: locale不适用于当前数据库编码 → error
    from_collation_dependency:
      label: 源校对规则依赖 (仅FROM形式)
      importance: non_important
      values:
      - key: from_exists
        label: 源校对规则存在
      - key: from_not_exists
        label: 源校对规则不存在 → error
    duplicate_collation:
      label: 重名冲突
      importance: non_important
      values:
      - key: same_schema_same_name_no_ifne
        label: 同schema同名且无IF NOT EXISTS → error
      - key: same_schema_same_name_with_ifne
        label: 同schema同名且有IF NOT EXISTS → notice
    invalid_locale_for_encoding:
      label: locale不适用于编码
      importance: non_important
      values:
      - key: wrong_encoding_locale
        label: locale与数据库编码不匹配 → error
    icu_not_available:
      label: ICU不可用
      importance: non_important
      values:
      - key: provider_icu_no_support
        label: PROVIDER=icu但服务器未启用ICU → error
    nondeterministic_non_icu:
      label: 非确定性非ICU
      importance: non_important
      values:
      - key: deterministic_false_libc
        label: PROVIDER=libc且DETERMINISTIC=false → error
    rules_non_icu:
      label: RULES非ICU
      importance: non_important
      values:
      - key: rules_with_libc
        label: PROVIDER=libc且RULES子句 → error
    locale_and_lc_conflict:
      label: LOCALE与LC_COLLATE/LC_CTYPE冲突
      importance: non_important
      values:
      - key: locale_with_lc_collate
        label: 同时指定LOCALE和LC_COLLATE → error
      - key: locale_with_lc_ctype
        label: 同时指定LOCALE和LC_CTYPE → error
    insufficient_privilege:
      label: 权限不足
      importance: non_important
      values:
      - key: no_create_on_schema
        label: 无目标Schema的CREATE权限 → error
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_collation_catalog_query
        label: pg_collation 系统目录查询
      - key: actual_collation_usage
        label: 实际使用校对规则 (SELECT ... COLLATE collation_name)
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_COLLATION
        label: DROP COLLATION name
      - key: DROP_COLLATION_IF_EXISTS
        label: DROP COLLATION IF EXISTS name
      - key: DROP_COLLATION_CASCADE
        label: DROP COLLATION name CASCADE
  notes:
    two_forms: CREATE COLLATION 有两种形式（参数定义、FROM 复制），各自有不同的依赖和约束。
    provider_libc_icu: PROVIDER 为 libc (默认) 或 icu (需服务器启用 ICU)。
    deterministic_false_icu_only: DETERMINISTIC=false 仅 ICU provider 支持。
    rules_icu_only: RULES 仅 ICU provider 支持。
    locale_lc_conflict: 不能同时指定 LOCALE 和 LC_COLLATE/LC_CTYPE。
    if_not_exists_no_guarantee: IF NOT EXISTS 不保证已存在校对规则与预期定义一致。
    share_row_exclusive_lock: CREATE COLLATION 获取 SHARE ROW EXCLUSIVE 锁，同时只能运行一条。
    preferred_from_c: 测试优先使用 FROM "C" 构造校对规则，避免依赖环境特定 locale。
  defaults:
    expected_status: success
    object_state: not_exists
    provider: libc_default
    deterministic_option: true_default
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_not_exists_clause
    - provider
    - deterministic_option
    - collation_name_shape
    - locale_setting
    - from_collation_shape
    - rules_setting
    - privilege_level
    - icu_availability
    - locale_validity
    - from_collation_dependency
    - duplicate_collation
    - invalid_locale_for_encoding
    - icu_not_available
    - nondeterministic_non_icu
    - rules_non_icu
    - locale_and_lc_conflict
    - insufficient_privilege
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CREATE COLLATION {if_not_exists} {collation_name} ( {collation_params} )"
    verification_query_template: "SELECT count(*) FROM pg_collation WHERE collname = '{collation_name}'"
    factor_value_bindings:
      if_not_exists_clause:
        absent: ""
        present_no_conflict: "IF NOT EXISTS"
        present_with_conflict: "IF NOT EXISTS"
      statement_branch:
        branch_define_with_params: "( LOCALE = ... )"
        branch_from_existing: "FROM existing_collation"
```
