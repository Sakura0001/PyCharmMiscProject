# PG16 因子融入现有体系设计

## 背景

当前 `pg_case_factory` 已经收敛为“标准 Codex skill + statement reference + 最小通用引擎”。现有因子体系以 statement reference 为中心，每个 `skills/pg-sql-generation/references/statements/**/*.md` 文件独立声明：

- `factor_layers`：T1-T6 因子分层。
- `factors`：本 statement 的局部因子和值。
- `coverage_policy`：主组合因子、附属因子和规模阈值。
- `rendering`：SQL 渲染模板和因子值绑定。

部门整理的 `1.txt` 是另一类资产：它不是单条 statement 的因子定义，而是按 PostgreSQL 16 对象域和能力域整理的全局测试维度，例如 database、domain、column、table、index、function、procedure、trigger、schema、extension、role、operator、publication、routine、sequence、tablespace、rule、view、materialized view、cast、system catalog、text search、FDW、transaction 和 DML。

本设计的目标是把 `1.txt` 中的因子融入现有体系，同时保留现有 statement reference 的可归因性和生成规模控制能力。

## 目标

1. 将 `1.txt` 标准化为可复用的 PG16 全局因子目录。
2. 为现有 statement reference 增加“从全局因子到局部因子”的映射规范。
3. 保留现有 T1-T6、`factors`、`coverage_policy` 和 `rendering` 结构，不推倒重来。
4. 支持按对象域分批迁移，避免一次性批量修改 183 个 statement reference 带来的风险。
5. 让后续审计可以明确判断：哪些部门因子已覆盖，哪些被排除，哪些存在缺口。

## 非目标

1. 本设计不直接修改 `1.txt`。
2. 本设计不直接批量重写所有 statement reference。
3. 本设计不改变现有 Python 引擎的核心职责。
4. 本设计不让全局因子目录直接决定 SQL 生成数量。
5. 本设计不把生命周期计划写死进 statement reference。

## 推荐方案

采用“全局因子目录 + statement 映射层 + 分批融入”的方式。

新增一个公共 reference：

```text
skills/pg-sql-generation/references/common/pg16_factor_catalog.md
```

新增一个映射模板：

```text
skills/pg-sql-generation/references/templates/factor_catalog_mapping_template.md
```

每个需要融入部门因子的 statement reference 后续增加一个 `factor_catalog_mapping` 结构，用来说明：

- 引用了哪个全局对象域。
- 哪些全局因子被映射到本 statement 的局部因子。
- 这些因子在本 statement 中落到 T1-T6 哪一层。
- 这些因子参与主组合、代表性覆盖，还是轮转挂靠。
- 哪些全局因子被排除，以及排除原因。

全局因子目录只回答“PG16 有哪些可测维度”。具体 statement 是否把某个因子放进主组合，仍由 statement reference 的 `coverage_policy.main_combination_axes` 和 `coverage_policy.non_main_factors` 决定。

## 结构设计

### 全局因子目录

`pg16_factor_catalog.md` 以对象域为单位组织。每个对象域包含对象元信息、适用 statement、因子组、因子值、默认分层、默认覆盖角色和注意事项。

模板：

```yaml
structured_config:
  kind: factor_catalog
  skill_name: pg16_factor_catalog
  version: pg16
  object_domains:
    database:
      key: database
      label: 数据库
      applies_to:
        - create_database
        - alter_database
        - drop_database
      factor_groups:
        naming:
          key: naming
          label: 命名因子
          default_tier: T3
          default_coverage_role: rotate_attach
          factors:
            name_shape:
              key: name_shape
              label: 数据库名称形态
              description: 覆盖普通标识符、引号标识符、保留字、长度边界和非法字符。
              values:
                - key: valid_unquoted_lower
                  label: 合法未加引号小写名称
                  expected_status: success
                - key: quoted_reserved_keyword
                  label: 加双引号的保留字
                  expected_status: success
                - key: reserved_keyword_unquoted
                  label: 未加引号保留字
                  expected_status: failure
                - key: max_length_63_bytes
                  label: 63 字节名称边界
                  expected_status: success
                - key: over_length_64_bytes
                  label: 64 字节名称边界
                  expected_status: boundary
              notes:
                - PostgreSQL 标识符按字节限制，名称边界必须按实际编码和截断语义确认。
```

### 字段规范

全局因子目录字段：

```text
object_domains.<domain_key>.key
对象域稳定标识，使用小写 snake_case 或现有 domain 名称。

object_domains.<domain_key>.label
中文展示名。

object_domains.<domain_key>.applies_to
建议适用的 statement key 列表。

factor_groups.<group_key>.default_tier
默认 T1-T6 分层。具体 statement 可以在映射中覆盖。

factor_groups.<group_key>.default_coverage_role
默认覆盖角色，允许值为 main_axis、representative、rotate_attach、audit_only。

factors.<factor_key>.values
标准取值清单。取值必须有稳定 key，避免只用中文文本。

values[].expected_status
该取值天然倾向的结果，允许值为 success、failure、boundary、context_dependent。

notes
保留语义边界、版本差异、权限依赖、环境依赖等说明。
```

### Statement 映射层

每个 statement reference 可以在 `structured_config` 中增加：

```yaml
factor_catalog_mapping:
  source_catalog: references/common/pg16_factor_catalog.md
  object_domain: database
  imported_factors:
    - catalog_factor: database.naming.name_shape
      local_factor: database_name_shape
      target_tier: T3
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: CREATE DATABASE 需要覆盖名称合法性、保留字、长度边界和引号语义。

    - catalog_factor: database.options.owner
      local_factor: owner_clause
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: statement_specific_subset
      selected_values:
        - omitted
        - current_user
        - valid_other_role
        - nonexistent_role
        - no_set_role_privilege
      reason: OWNER 子句影响权限与 SET ROLE 语义。

  promoted_factors:
    - catalog_factor: database.options.template
      local_factor: template_clause
      from_default_tier: T4
      target_tier: T2
      reason: 在 CREATE DATABASE 中 TEMPLATE 是官方关键选项，影响成功路径和失败路径。

  excluded_factors:
    - catalog_factor: database.options.allow_connections
      reason: DROP DATABASE 不创建或修改 ALLOW_CONNECTIONS，该因子不适用。

  coverage_notes:
    - 全局命名因子在本 statement 中只做轮转挂靠，不进入主笛卡尔积。
```

字段含义：

```text
catalog_factor
全局因子路径，格式为 object_domain.factor_group.factor。

local_factor
当前 statement reference 内的因子名，应与 factors 中的 key 对齐。

target_tier
映射到当前 statement 的 T1-T6 分层。

coverage_role
当前 statement 的覆盖角色，允许值为 main_axis、representative_or_main、representative、rotate_attach、audit_only。

value_policy
取值处理策略，允许值为 reuse_catalog_values、statement_specific_subset、statement_specific_override。

selected_values
当 value_policy 为 statement_specific_subset 时，列出实际使用的 catalog value key。

promoted_factors
说明被提升层级的因子，避免审计时误判。

excluded_factors
说明不适用或暂不纳入的因子，必须写明原因。
```

## 分层和覆盖规则

全局因子默认按以下口径映射到现有 T1-T6：

```text
T1：语句分支、对象状态、预期成功/失败、核心语义路径。
T2：官方 synopsis 中影响语义的关键可选子句和行为选项。
T3：对象名、输入形态、标识符、参数形式、字面量形态。
T4：依赖对象、权限、角色、schema、tablespace、extension、事务、锁、外部服务和环境限制。
T5：异常、非法组合、边界值、冲突路径、类型不匹配、权限失败。
T6：验证方式、系统表检查、对象可用性验证、清理策略。
```

覆盖角色规则：

```text
main_axis
进入 coverage_policy.main_combination_axes，参与主笛卡尔积。

representative_or_main
默认做代表性覆盖；若该 statement 的核心语义依赖该因子，可提升为 main_axis。

representative
每个关键取值至少在代表性成功或失败样本中出现。

rotate_attach
进入 coverage_policy.non_main_factors，按现有 factor_policy 轮转挂靠。

audit_only
只作为审计清单，不直接进入生成。
```

全局因子不能直接改变生成规模。任何因子要进入主组合，必须在对应 statement reference 中显式出现在 `coverage_policy.main_combination_axes`。

## 融入流程

### 第一步：标准化 `1.txt`

把 `1.txt` 中的自由缩进清单按对象域整理进 `pg16_factor_catalog.md`。标准化时只做结构化和命名，不强行决定 statement 级覆盖策略。

处理规则：

1. 顶层标题转为 `object_domain`。
2. 二级标题转为 `factor_group`。
3. 三级及以下条目转为 `factor` 或 `value`。
4. 明显表示 SQL 语句或对象操作的条目进入 `applies_to` 或 `notes`。
5. 明显表示验证方式的条目进入 T6 相关 factor group。
6. 明显表示非法、冲突、权限不足、环境不可用的条目标记 `expected_status: failure` 或 `context_dependent`。

### 第二步：建立映射模板

新增 `factor_catalog_mapping_template.md`，让后续补齐 statement reference 时都有统一格式。

模板必须包含：

- 映射入口说明。
- YAML 结构示例。
- `coverage_role` 枚举说明。
- `value_policy` 枚举说明。
- 排除因子说明规则。
- 审计 checklist。

### 第三步：按对象域试点

先选高复用且边界清晰的对象域试点：

```text
database
domain
schema
role_user_group
tablespace
extension
sequence
```

每个对象域至少完成：

1. 全局因子标准化。
2. 对应 CREATE / ALTER / DROP reference 的映射建议。
3. 已覆盖、未覆盖、排除项的审计结果。
4. 一个完整 statement reference 示例。

### 第四步：批量推广

试点稳定后，再进入第二批和第三批。

第二批：

```text
column
table
index
view
materialized_view
cast
system_catalog
```

第三批：

```text
function
procedure
routine
trigger
operator
publication
rule
text_search
foreign_data
transaction
dml
```

## 审计规则

每个对象域融入后，必须生成或手工维护审计结论，至少回答：

```text
1. 该对象域包含哪些 catalog factor。
2. 每个 catalog factor 是否已映射到至少一个 statement reference。
3. 每个 mapped factor 是否存在于对应 statement 的 factors 中。
4. target_tier 是否与 factor_layers 对齐。
5. coverage_role 为 main_axis 的因子是否出现在 coverage_policy.main_combination_axes。
6. coverage_role 为 rotate_attach 的因子是否出现在 coverage_policy.non_main_factors。
7. 被排除的因子是否写明了 statement 级原因。
8. 是否存在全局因子已经覆盖但 statement 中重复定义不同语义的情况。
```

建议新增审计输出位置：

```text
docs/pg16_factor_catalog_mapping_status.md
```

该文档记录每个对象域的迁移状态、覆盖缺口和下一步动作。

## 示例：DATABASE 对象域

全局目录示例：

```yaml
object_domains:
  database:
    key: database
    label: 数据库
    applies_to:
      - create_database
      - alter_database
      - drop_database
    factor_groups:
      naming:
        key: naming
        label: 命名因子
        default_tier: T3
        default_coverage_role: rotate_attach
        factors:
          name_shape:
            key: name_shape
            label: 数据库名称形态
            values:
              - key: valid_unquoted_lower
                label: 合法未加引号小写名称
                expected_status: success
              - key: valid_quoted_upper
                label: 加双引号全大写名称
                expected_status: success
              - key: invalid_special_char_unquoted
                label: 未加引号特殊字符
                expected_status: failure
              - key: max_length_63_bytes
                label: 63 字节边界
                expected_status: success
              - key: over_length_64_bytes
                label: 64 字节边界
                expected_status: boundary
      options:
        key: options
        label: CREATE/ALTER DATABASE 选项
        default_tier: T2
        default_coverage_role: representative_or_main
        factors:
          owner:
            key: owner
            label: OWNER 子句
            values:
              - key: omitted
                label: 省略 OWNER
                expected_status: success
              - key: valid_current_user
                label: 当前用户
                expected_status: success
              - key: nonexistent_user
                label: 不存在的用户
                expected_status: failure
          template:
            key: template
            label: TEMPLATE 子句
            values:
              - key: default_template1
                label: 默认 template1
                expected_status: success
              - key: template0
                label: template0
                expected_status: success
              - key: nonexistent_template
                label: 不存在模板
                expected_status: failure
```

`CREATE DATABASE` 映射示例：

```yaml
factor_catalog_mapping:
  source_catalog: references/common/pg16_factor_catalog.md
  object_domain: database
  imported_factors:
    - catalog_factor: database.naming.name_shape
      local_factor: database_name_shape
      target_tier: T3
      coverage_role: rotate_attach
      value_policy: statement_specific_subset
      selected_values:
        - valid_unquoted_lower
        - valid_quoted_upper
        - invalid_special_char_unquoted
        - max_length_63_bytes
        - over_length_64_bytes
      reason: CREATE DATABASE 需要覆盖数据库名称输入形态和边界。
    - catalog_factor: database.options.owner
      local_factor: owner_clause
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: statement_specific_subset
      selected_values:
        - omitted
        - valid_current_user
        - nonexistent_user
      reason: OWNER 子句影响权限和角色切换。
    - catalog_factor: database.options.template
      local_factor: template_clause
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: statement_specific_subset
      selected_values:
        - default_template1
        - template0
        - nonexistent_template
      reason: TEMPLATE 子句影响数据库复制来源和编码 locale 兼容性。
```

## 对现有引擎的影响

短期内不需要修改 `src/pg_case_factory`。现有引擎仍读取 statement reference 中的 `factors`、`coverage_policy` 和 `rendering`。

中期可以增加一个可选审计工具，但不要求生成器依赖它：

```text
tools/audit_factor_catalog_mapping.py
```

该工具只做静态检查：

- 读取 `pg16_factor_catalog.md`。
- 读取 statement reference。
- 检查 `factor_catalog_mapping` 的路径、层级、覆盖角色和本地因子是否一致。
- 输出审计报告。

生成 SQL 的核心路径不直接读取全局因子目录，避免把全局目录变成隐藏的生成逻辑。

## 验收标准

设计落地后，第一阶段验收标准：

1. `pg16_factor_catalog.md` 至少标准化第一批对象域。
2. `factor_catalog_mapping_template.md` 可直接复制到 statement reference 使用。
3. 至少一个对象域完成端到端示例，例如 database：
   - 全局因子目录有 database。
   - `create_database.md` 有 `factor_catalog_mapping`。
   - 映射中的本地因子存在于 `factors`。
   - 覆盖角色与 `coverage_policy` 一致。
4. 审计报告能列出 mapped、excluded 和 gap。
5. 现有 `build_bindings`、`load_skill`、`render_statement` 行为不受影响。

## 风险和处理

### 风险：全局因子过细导致 statement reference 膨胀

处理方式：全局目录允许完整保留细节，但 statement 只映射适用子集。低优先级因子使用 `audit_only` 或 `rotate_attach`。

### 风险：对象域因子和 statement 语义因子混淆

处理方式：全局目录只表达对象域可测维度；statement reference 决定是否提升为 T1/T2。

### 风险：同一因子在多个 statement 中命名不一致

处理方式：`factor_catalog_mapping.local_factor` 显式记录本地名称，后续审计只要求语义映射清晰，不强制所有 statement 使用同一个 local factor 名。

### 风险：历史 reference 与新目录语义冲突

处理方式：迁移时优先记录 `coverage_notes` 和审计 gap，不在第一阶段强制批量重命名。

## 实施顺序建议

1. 新增 `pg16_factor_catalog.md`，先覆盖第一批对象域。
2. 新增 `factor_catalog_mapping_template.md`。
3. 为 `create_database.md` 增加完整映射示例。
4. 为 `alter_database.md` 和 `drop_database.md` 增加映射，验证同一对象域在 CREATE / ALTER / DROP 中如何裁剪。
5. 新增审计状态文档 `docs/pg16_factor_catalog_mapping_status.md`。
6. 再按 domain、schema、role/user/group、tablespace、extension、sequence 推广。

## 决策

采用“全局因子目录 + statement 映射层 + 分批融入”的方案。该方案保留现有 statement reference 的局部自治能力，同时让部门因子形成统一来源，适合后续持续审计和增量迁移。
