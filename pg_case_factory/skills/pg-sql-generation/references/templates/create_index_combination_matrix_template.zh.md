# CREATE INDEX 组合矩阵执行模板说明

## 用途

本文件是 `create_index_combination_matrix_template.yaml` 的中文审阅版，用来说明
`CREATE INDEX` 组合矩阵应该如何填写和审计。

目标不是让 AI 根据自然语言重新理解 `CREATE INDEX` 因子，而是把每个可执行组合、
预期成功组合、预期失败组合、对象覆盖范围、列类型覆盖范围和失败原因提前写入文件。
后续 runner 只能读取组合矩阵并机械展开，不允许在矩阵外自行推导 SQL。

## 文件位置

推荐机器可读模板：

```text
skills/pg-sql-generation/references/templates/create_index_combination_matrix_template.yaml
```

后续正式矩阵建议放到：

```text
skills/pg-sql-generation/references/combinations/ddl/index/create_index.yaml
```

## 核心原则

1. `create_index.md` 负责定义因子和值。
2. `create_index.yaml` 负责定义哪些因子组合可以生成 SQL。
3. 成功组合和失败组合都必须显式写出。
4. 失败组合必须写明稳定失败原因，不能只写 `invalid`。
5. AI 不允许根据规范临时理解并发明新组合。
6. runner 不允许生成矩阵文件中没有声明的 SQL shape。

## 覆盖范围

### 目标 relation 覆盖

`CREATE INDEX` 官方作用对象是 relation，可以是 table 或 materialized view。
模板要求显式覆盖：

```yaml
required_relation_kinds:
  - regular_table
  - unlogged_table
  - temporary_table
  - partitioned_table_parent
  - partitioned_table_leaf
  - inherited_parent_table
  - inherited_child_table
  - materialized_view
```

同时要显式列出不适用对象：

```yaml
negative_relation_kinds:
  - plain_view
  - foreign_table
  - sequence
```

这里的重点是：不能只写“表类型按需要覆盖”。每个 statement 的矩阵必须把目标对象范围列清楚。

### 表类型覆盖

`CREATE INDEX` 必须覆盖表形态，因为下列因子依赖表类型：

- `ONLY`
- `CONCURRENTLY`
- 分区表索引递归和附着行为
- 临时表上的并发创建行为
- 继承表的索引行为
- 物化视图索引行为

模板中 `table_coverage.required` 必须是 `true`。

### 列类型覆盖

`CREATE INDEX` 必须覆盖所有 PostgreSQL 16 可作为表列声明的数据类型。

模板中必须写成：

```yaml
column_type_coverage:
  required: true
  coverage_mode: exhaustive
  inventory_source: references/common/pg16_type_catalog.md
  required_type_set: all_pg16_column_types
  expansion_mode: expand_every_type
  require_each_type_success_or_failure: true
```

含义是：

- 所有 PG16 列类型都必须进入测试。
- 每个类型至少生成一个 `CREATE INDEX` 用例。
- 支持当前索引方法的类型生成成功路径。
- 不支持当前索引方法的类型生成失败路径。
- 不允许静默跳过任何列类型。

## 因子契约

模板已经把 `create_index.md` 中现有因子全部列入 `factor_contract`：

```text
statement_branch
method
column_source
unique
predicate
include
concurrently
expected_status
order
nulls
if_not_exists
nulls_distinct
only
name_style
collation
opclass
column_type_compatibility
with_storage
tablespace
expression_index
invalid_combination
syntax_error
concurrent_failure
partition_constraint
verification_mode
cleanup_mode
```

后续审计工具应该检查：

1. 矩阵中使用的因子是否都存在于 `create_index.md`。
2. 矩阵中使用的因子值是否都存在于 `create_index.md`。
3. `factor_contract.required_values` 是否都至少被一个组合覆盖。
4. 每个失败组合是否有 `expected_error.reason` 或 `compatibility.failure_when.reason`。

## 动态输入

`CREATE INDEX` 组合矩阵不能自己猜表名、列名或列类型。它依赖三个输入：

```yaml
dynamic_inputs:
  table_manifest:
    required: true
  type_catalog:
    required: true
  column_manifest:
    required: true
```

其中：

- `table_manifest` 来自建表流程，提供表名、relation kind 和列清单。
- `type_catalog` 是 PG16 类型目录，提供所有列类型、样例值、边界值和索引能力。
- `column_manifest` 是实际表内列的结构化清单，供组合矩阵选择列。

## 组合组写法

每个组合组代表一类可展开的 SQL 组合。组合组必须说明：

```yaml
id: 稳定 ID
title: 人类可读标题
expected_status_policy: 成功/失败如何判定
factors: 本组覆盖的因子值
expansion: 是否按 relation kind、method、column type 展开
compatibility: 哪些情况成功，哪些情况失败
sql_shape: SQL 模板
verification: 验证方式
cleanup: 清理方式
```

示例：B-tree 单列索引覆盖全部列类型。

```yaml
- id: btree_single_column_all_pg16_column_types
  expected_status_policy: per_column_type
  default_expected_status: failure
  factors:
    statement_branch: single_column_btree
    method: btree
    column_source: all_template_columns
    unique: "false"
    predicate: "false"
    include: "false"
    concurrently: "false"
  expansion:
    column_types:
      mode: exhaustive
      source: coverage_scope.column_type_coverage.required_type_set
  compatibility:
    success_when:
      - column.capabilities contains btree
    failure_when:
      - condition: column.capabilities not contains btree
        reason: btree_operator_class_missing
  sql_shape:
    template: CREATE INDEX {index_name} ON {table_name} USING btree ({key_column});
```

这表示 runner 要遍历所有 PG16 列类型：

- 有 btree 能力的类型生成成功 SQL。
- 没有 btree 能力的类型也要生成失败 SQL。
- 两者都不能跳过。

## 必须包含的 CREATE INDEX 组合族

第一版 `CREATE INDEX` 正式矩阵至少应该包含：

```text
btree 单列 + 全部列类型
btree 多列 + 支持/不支持 method 边界
UNIQUE 成功路径与非 btree 失败路径
partial index + 全部列类型
INCLUDE 支持 method 与不支持 method
expression index 简单表达式与复杂表达式
hash + 全部列类型
gist/spgist/gin/brin + 全部列类型
CONCURRENTLY 正常路径与事务块失败路径
IF NOT EXISTS 名称冲突路径
ASC/DESC、NULLS FIRST/LAST、NULLS DISTINCT
storage parameter 有效值和无效值
TABLESPACE 有效、缺失、权限不足
opclass 默认、非默认、类型不匹配
ONLY 在分区和非分区 relation 上的行为
显式 syntax error 路径
```

## 审计规则

模板最后的 `audit_rules` 是后续审计工具应该执行的最低规则：

- 不允许 AI 或 runner 在矩阵外推导组合。
- 所有矩阵因子必须存在于 `create_index.md`。
- 所有矩阵因子值必须存在于 `create_index.md`。
- 所有 required factor value 必须被覆盖。
- 目标 relation 覆盖必须显式且完整。
- 所有 PG16 列类型必须生成 success 或 failure 用例。
- 所有失败路径必须有明确原因。
- 所有组合必须声明清理方式。

## 后续落地顺序

1. 新增 `references/common/pg16_type_catalog.md`。
2. 用本模板创建正式 `references/combinations/ddl/index/create_index.yaml`。
3. 写审计工具检查矩阵和 `create_index.md` 是否一致。
4. 修改主流程，让 AI 选择组合矩阵，不再临时理解因子生成 SQL。
