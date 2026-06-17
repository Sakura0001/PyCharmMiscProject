# 技能：IMPORT FOREIGN SCHEMA

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-importforeignschema.html

```sql
IMPORT FOREIGN SCHEMA remote_schema
    [ { LIMIT TO | EXCEPT } ( table_name [, ...] ) ]
    FROM SERVER server_name
    INTO local_schema
    [ OPTIONS ( option 'value' [, ...] ) ]
```

PG16 关键约束：
- 用户必须拥有外部服务器的 **USAGE** 权限和目标 schema 的 **CREATE** 权限。**不需要 superuser 权限**。
- 新创建的外部表由发出命令的用户拥有。
- 外部表以正确的列定义和选项创建以匹配远程表。
- 默认导入远程 schema 中的**所有表和视图**。
- LIMIT TO：仅导入匹配指定表名的表。
- EXCEPT：排除指定表名，导入其余所有表。
- OPTIONS：导入选项，名称/值取决于各 FDW。
- IMPORT FOREIGN SCHEMA 符合 SQL 标准，但 OPTIONS 子句是 PostgreSQL 扩展。
- 导入操作依赖于已存在的 FDW 和外部服务器，这些前置对象需要由 superuser 创建。

## 语句作用

官方说明：IMPORT FOREIGN SCHEMA — import table definitions from a foreign server

该 reference 关注外部 schema 导入语句的语法分支、LIMIT TO / EXCEPT 过滤行为、FDW 和外部服务器依赖、USAGE + CREATE 权限边界和 OPTIONS 传递行为。

IMPORT FOREIGN SCHEMA **不直接涉及列类型选择**——列定义由远程表结构决定，FDW 自动匹配。但创建的外部表包含列定义，列数据类型由远程 schema 决定。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（IMPORT FOREIGN SCHEMA 基本形式 / LIMIT TO 形式 / EXCEPT 形式）
- object_state：目标 schema 对象状态（local_schema 存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- filter_clause：过滤子句形态（无过滤 / LIMIT TO / EXCEPT）
- options_clause：OPTIONS 子句形态（省略 / 指定）
- server_dependency：外部服务器依赖（有效服务器 / 无效服务器 / 无 USAGE 权限）
- fdw_dependency：FDW 依赖（支持 import 的 FDW / 不支持 import 的 FDW）

### T3：对象名与输入形态因子
- remote_schema_name_shape：远程 schema 名称形态
- local_schema_name_shape：本地 schema 名称形态
- server_name_shape：外部服务器名称形态
- table_name_shape：LIMIT TO / EXCEPT 中的表名形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（usage_on_server + create_on_schema / no_usage / no_create / superuser）
- server_existence：外部服务器存在性（存在 / 不存在）
- schema_existence：本地 schema 存在性（存在 / 不存在）
- fdw_import_capability：FDW 是否支持 IMPORT FOREIGN SCHEMA（支持 / 不支持）

### T5：异常与边界因子
- nonexistent_server：外部服务器不存在
- nonexistent_local_schema：本地 schema 不存在
- no_usage_privilege：无外部服务器 USAGE 权限
- no_create_privilege：无目标 schema CREATE 权限
- fdw_not_support_import：FDW 不支持 IMPORT FOREIGN SCHEMA
- table_name_mismatch：LIMIT TO / EXCEPT 中的表名不存在于远程 schema
- duplicate_foreign_table：导入的表名与本地已有对象冲突

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 IMPORT FOREIGN SCHEMA 全部语法分支（3 个顶层形式：基本 / LIMIT TO / EXCEPT）。
- 不需要覆盖所有基表中所有的列类型——列定义由远程表结构决定。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- IMPORT FOREIGN SCHEMA 需要 USAGE 权限于外部服务器和 CREATE 权限于目标 schema，不需要 superuser 权限。
- 必须前置准备 FDW 和外部服务器（这些需要 superuser 创建），必须在生命周期计划中显式标注环境依赖。
- 必须覆盖目标 schema 存在时的成功导入路径、目标 schema 不存在时的失败路径。
- LIMIT TO / EXCEPT 过滤子句需要代表性覆盖。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备（FDW + 服务器 + schema）、目标 IMPORT FOREIGN SCHEMA 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- FDW 是否支持 IMPORT FOREIGN SCHEMA 是关键行为边界，需要覆盖不支持路径。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限、服务器依赖、schema 存在性或 FDW import 能力的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖（基本 / LIMIT TO / EXCEPT）
  - 目标 schema 存在 / 不存在全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖（USAGE + CREATE / 无 USAGE / 无 CREATE）
- 次优先保证：
  - LIMIT TO / EXCEPT 过滤行为代表性覆盖
  - OPTIONS 子句代表性覆盖
  - FDW import 能力边界覆盖
  - 表名冲突边界覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: foreign_schema
  skill_name: import_foreign_schema
  official_source: https://www.postgresql.org/docs/16/sql-importforeignschema.html
  statement:
    key: import_foreign_schema
    name: IMPORT FOREIGN SCHEMA
    aliases:
    - IMPORT FOREIGN SCHEMA
    - import foreign schema
    - import_foreign_schema
    purpose: import table definitions from a foreign server
  syntax_templates:
  - "IMPORT FOREIGN SCHEMA remote_schema [ { LIMIT TO | EXCEPT } ( table_name [,\
    \ ...] ) ] FROM SERVER server_name INTO local_schema [ OPTIONS ( option 'value'\
    \ [, ... ] ) ]"
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
    - filter_clause
    - options_clause
    - server_dependency
    - fdw_dependency
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - remote_schema_name_shape
    - local_schema_name_shape
    - server_name_shape
    - table_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - server_existence
    - schema_existence
    - fdw_import_capability
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_server
    - nonexistent_local_schema
    - no_usage_privilege
    - no_create_privilege
    - fdw_not_support_import
    - table_name_mismatch
    - duplicate_foreign_table
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
      - key: branch_basic
        label: IMPORT FOREIGN SCHEMA remote_schema FROM SERVER server_name INTO local_schema
      - key: branch_limit_to
        label: IMPORT FOREIGN SCHEMA remote_schema LIMIT TO (table_names) FROM SERVER server_name INTO local_schema
      - key: branch_except
        label: IMPORT FOREIGN SCHEMA remote_schema EXCEPT (table_names) FROM SERVER server_name INTO local_schema
    object_state:
      label: 目标 schema 对象状态
      importance: important
      values:
      - key: exists
        label: 本地 schema 存在
      - key: not_exists
        label: 本地 schema 不存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    filter_clause:
      label: 过滤子句形态
      importance: important
      values:
      - key: no_filter
        label: 无过滤 (导入所有表)
      - key: limit_to
        label: LIMIT TO (仅导入指定表)
      - key: except
        label: EXCEPT (排除指定表)
    options_clause:
      label: OPTIONS 子句形态
      importance: non_important
      values:
      - key: omitted
        label: 省略 OPTIONS
      - key: specified
        label: 指定 OPTIONS
    server_dependency:
      label: 外部服务器依赖
      importance: non_important
      values:
      - key: valid_server
        label: 有效外部服务器
      - key: invalid_server
        label: 不存在的外部服务器
      - key: no_usage_privilege
        label: 无 USAGE 权限的外部服务器
    fdw_dependency:
      label: FDW 依赖
      importance: non_important
      values:
      - key: fdw_supports_import
        label: FDW 支持 IMPORT FOREIGN SCHEMA
      - key: fdw_not_support_import
        label: FDW 不支持 IMPORT FOREIGN SCHEMA
    remote_schema_name_shape:
      label: 远程 schema 名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
    local_schema_name_shape:
      label: 本地 schema 名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
      - key: nonexistent_schema
        label: 不存在的 schema
    server_name_shape:
      label: 外部服务器名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: nonexistent_server
        label: 不存在的服务器
    table_name_shape:
      label: LIMIT TO / EXCEPT 中的表名形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: nonexistent_table
        label: 远程不存在但本地不报错的表名
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - key: usage_and_create
        label: USAGE on server + CREATE on schema → success
      - key: no_usage
        label: 无 USAGE 权限 → error
      - key: no_create
        label: 无 CREATE 权限 → error
      - key: superuser
        label: superuser (隐含所有权限)
    server_existence:
      label: 外部服务器存在性
      importance: non_important
      values:
      - key: server_exists
        label: 外部服务器存在
      - key: server_not_exists
        label: 外部服务器不存在 → error
    schema_existence:
      label: 本地 schema 存在性
      importance: non_important
      values:
      - key: schema_exists
        label: 本地 schema 存在
      - key: schema_not_exists
        label: 本地 schema 不存在 → error
    fdw_import_capability:
      label: FDW 是否支持 IMPORT FOREIGN SCHEMA
      importance: non_important
      values:
      - key: supports_import
        label: FDW 支持 import → success
      - key: not_supports_import
        label: FDW 不支持 import → error
    nonexistent_server:
      label: 外部服务器不存在
      importance: non_important
      values:
      - key: server_exists
        label: 服务器存在
      - key: server_missing
        label: 服务器不存在 → error
    nonexistent_local_schema:
      label: 本地 schema 不存在
      importance: non_important
      values:
      - key: schema_exists
        label: schema 存在
      - key: schema_missing
        label: schema 不存在 → error
    no_usage_privilege:
      label: 无外部服务器 USAGE 权限
      importance: non_important
      values:
      - key: has_usage
        label: 有 USAGE 权限 → success
      - key: lacks_usage
        label: 无 USAGE 权限 → error
    no_create_privilege:
      label: 无目标 schema CREATE 权限
      importance: non_important
      values:
      - key: has_create
        label: 有 CREATE 权限 → success
      - key: lacks_create
        label: 无 CREATE 权限 → error
    fdw_not_support_import:
      label: FDW 不支持 IMPORT FOREIGN SCHEMA
      importance: non_important
      values:
      - key: fdw_supports
        label: FDW 支持 import
      - key: fdw_not_supports
        label: FDW 不支持 import → error
    table_name_mismatch:
      label: LIMIT TO / EXCEPT 中的表名不存在于远程 schema
      importance: non_important
      values:
      - key: table_exists_remote
        label: 表名存在于远程 schema
      - key: table_not_exists_remote
        label: 表名不存在于远程 schema (行为边界，取决于 FDW)
    duplicate_foreign_table:
      label: 导入的表名与本地已有对象冲突
      importance: non_important
      values:
      - key: no_conflict
        label: 无冲突
      - key: name_conflict
        label: 表名与本地已有对象冲突 → error
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_class_catalog_query
        label: pg_class 系统目录查询 (验证外部表存在)
      - key: error_assertion
        label: 错误断言
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: drop_foreign_tables
        label: 删除导入的外部表
      - key: drop_schema
        label: 删除本地 schema
      - key: drop_server
        label: 删除外部服务器
      - key: drop_fdw
        label: 删除 FDW
  notes:
    no_superuser_required: IMPORT FOREIGN SCHEMA 不需要 superuser 权限，仅需 USAGE 权限于外部服务器和 CREATE 权限于目标 schema。
    fdw_server_dependency: FDW 和外部服务器需要由 superuser 前置创建，这是环境依赖。
    column_types_from_remote: 列定义由远程表结构决定，不需要手动选择列类型。
    filter_behavior: LIMIT TO 仅导入指定表，EXCEPT 排除指定表，无过滤则导入所有。
    fdw_import_support: FDW 是否支持 IMPORT FOREIGN SCHEMA 取决于 FDW 实现。
    sql_standard_conformance: IMPORT FOREIGN SCHEMA 符合 SQL 标准，OPTIONS 子句是 PostgreSQL 扩展。
  defaults:
    expected_status: success
    privilege_level: usage_and_create
    object_state: exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - filter_clause
    - options_clause
    - server_dependency
    - fdw_dependency
    - remote_schema_name_shape
    - local_schema_name_shape
    - server_name_shape
    - table_name_shape
    - privilege_level
    - server_existence
    - schema_existence
    - fdw_import_capability
    - nonexistent_server
    - nonexistent_local_schema
    - no_usage_privilege
    - no_create_privilege
    - fdw_not_support_import
    - table_name_mismatch
    - duplicate_foreign_table
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "IMPORT FOREIGN SCHEMA {remote_schema} [ {filter_clause} ] FROM SERVER {server_name} INTO {local_schema} [ OPTIONS ( {options} ) ]"
    verification_query_template: "SELECT relname FROM pg_class WHERE relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = '{local_schema}') AND relkind = 'f'"
    factor_value_bindings:
      filter_clause:
        no_filter: ""
        limit_to: "LIMIT TO ( {table_names} )"
        except: "EXCEPT ( {table_names} )"
```
