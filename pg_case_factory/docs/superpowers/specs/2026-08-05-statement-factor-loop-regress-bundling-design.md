# 全语句因子循环与 Regress 无损装箱设计

## 1. 状态与结论

- 设计状态：已批准方案，待实现计划。
- 兼容目标：PostgreSQL 18.4。
- 输入范围：仓库 `statement_support_inventory.yaml` 登记的全部 183 条语句。
- 输出边界：SQL-only regress 输入包、静态报告、映射和 schedules。
- 核心方案：先完整展开覆盖点，再按共享 fixture 无损装箱。

本设计把“覆盖数量”和“SQL 文件数量”拆开：覆盖点不减少，重复的建表、建索引、
数据准备和清理可以在同一文件中复用。一个 SQL 文件不再等同于一个 executable
obligation，而是一个共享场景容器；文件内的每个可归因判断使用独立 subcase 标识。

## 2. 背景

当前 v0.3 主流程是：

```text
feature document
  -> feature manifest
  -> PostgreSQL 18.4 applicability review
  -> compiled coverage plan
  -> executable obligations
  -> stable regress mapping
  -> bounded shards
  -> numbered SQL files
  -> static validation
  -> schedules + package
```

仓库当前固定盘点为：

```text
statement                         183
statement × factor              3,357
statement × factor × value      9,978
renderable statement               41
reference_only statement          142
runtime_verified statement           0
```

现有生成合同要求“一个 executable obligation 对应一个 SQL 文件”。这保证了归因，
但会重复创建相同的表、索引、类型、数据和清理逻辑。例如 3 种表形态分别覆盖 6 种
INSERT 形式时，当前模型通常产生 18 个完整文件；实际可以保留 18 个覆盖点，同时只
生成 3 个文件，每个文件复用一种表形态并包含 6 个独立 INSERT subcase。

## 3. 目标

1. 建立适用于 DDL、DML、DCL、TCL、utility、session 和 cursor 语句的公共循环。
2. 外层稳定遍历全部 183 条 statement，内层审查该 statement 的全部因子和值。
3. 遇到 `reference_only` 时先补齐生成资产，通过 readiness gate 后再继续。
4. 保留完整 PostgreSQL 18.4 因子、对象、表形态、列类型和生命周期覆盖。
5. 保留成功、预期失败和 justified N/A 的分类闭环。
6. 通过复用兼容 fixture 减少 SQL 文件数及重复 setup/cleanup。
7. 让每个原始覆盖点仍可追溯、定位、静态审计和独立统计。
8. 支持按 statement 和 bundle 断点续跑，不因单轮失败丢失已验证进度。
9. 最终产物可以带入内网执行，但本项目不声称已经完成数据库运行验证。

## 4. 非目标

1. 不通过 sampling、pairwise、轮转删值或代表值替代完整核心覆盖。
2. 不追求数学上的最少 SQL 文件数；稳定、可复现和可审计优先。
3. 不连接数据库，不生成 expected transcript，不比较 Reference/DUT。
4. 不把 `runtime_verified_statements` 从 0 自动提升。
5. 不跨 SQL 文件共享易污染的持久测试对象。
6. 不把无法用 SQL-only 表达的多会话、重启或故障事件伪装成已执行。

## 5. 核心术语

### 5.1 Statement

仓库 inventory 中的一条稳定 `statement_key`，例如 `create_index`、`insert`、
`set_transaction`。

### 5.2 Factor-value

`statement × factor × value` 的最小适用性审查单元。全仓库当前共有 9,978 行。

### 5.3 Coverage atom

不可再拆的覆盖记账单元。它描述一个目标 statement 在确定因子赋值、依赖、前置状态
和预期分类下的一个可归因判断。压缩前后 coverage atom 集合必须完全相同。

### 5.4 Fixture

执行一组 atom 所需的共享环境，包括对象定义、表形态、列类型、数据、索引、约束、
trigger、权限、事务包络、session 设置和清理责任。

### 5.5 Bundle

一个最终 regress SQL 文件对应的共享场景。bundle 包含一次 pre-cleanup、一次 fixture
setup、一个或多个 subcase，以及一次 final cleanup。

### 5.6 Subcase

bundle 内一个可归因判断。每个 executable coverage atom 必须精确映射到一个 subcase。

## 6. 不变量

以下条件是硬门禁：

```text
required = success + expected_failure + justified_na
missing = 0

executable_atoms_before_packing = executable_subcases_after_packing
missing_atoms_after_packing = 0
duplicate_atom_mappings = 0
```

同时满足：

- 每个 `success` 或 `expected_failure` atom 精确进入一个 SQL 文件和一个 subcase。
- `justified_na` 保留理由但不生成伪 SQL。
- 一个 atom 不得被两个文件重复记账。
- 一个文件中的辅助语句不自动获得另一个 statement 的覆盖信用。
- 默认 20,000 门禁按 executable atom 数计算，不按压缩后的 SQL 文件数计算。
- 压缩只能复用 fixture 和生命周期骨架，不能删除 atom 或修改 atom 的因子赋值。

## 7. 总体架构

主流程分为四个可恢复循环。

### 7.1 循环 A：Statement readiness 与因子审查

```text
freeze inventory and policy digests

for statement in stable_statement_inventory:
    ensure_statement_ready(statement)

    for factor in statement.factor_inventory:
        for value in factor.values:
            review_applicability(statement, factor, value)

    validate_statement_factor_ledger(statement)
    checkpoint(statement, factors_reconciled)
```

该循环完成后，183、3,357、9,978 三层 inventory 必须全部可核账，不允许 pending。

### 7.2 循环 B：Coverage atom 展开

```text
for statement in stable_statement_inventory:
    build_dependency_graph(statement)
    design_test_points(statement)
    expand_coverage_atoms(statement)
    reconcile_statement_atoms(statement)
    checkpoint(statement, atoms_expanded)
```

该阶段只生成覆盖账本，不生成最终 SQL，也不进行压缩。

### 7.3 循环 C：无损装箱

```text
for compatible_fixture_bucket in stable_bucket_order:
    order_atoms_by_stable_coverage_order()
    pack_atoms_into_bounded_bundles()
    validate_packing_conservation()
    freeze_bundle_and_subcase_mapping()
```

允许同一 bundle 包含不同 statement 的 subcase，但必须满足 fixture、状态、事务、权限、
环境和清理兼容条件。覆盖归属始终记录在各自 subcase 上。

### 7.4 循环 D：生成、静态验证与打包

```text
while next_generation_shard_exists:
    claim_one_shard()
    generate_assigned_bundle_files()
    statically_validate_real_files()
    complete_or_record_failure()

validate_whole_batch()
generate_schedules_and_package()
```

最终 package 只有在全部 statement ledger、atom reconciliation、bundle mapping 和
generation shard 均通过后才能生成。

## 8. Statement 状态机

每条 statement 使用以下状态：

```text
discovered
  -> readiness_passed
  -> factors_reconciled
  -> atoms_expanded
  -> packing_eligible
  -> mapping_frozen
  -> generated
  -> statically_validated
  -> packaged
```

状态规则：

- 当前状态证据和 SHA 不匹配时禁止前进。
- readiness、factor 或 atom 阶段失败时停留在当前 statement，不静默跳过。
- 已冻结 mapping 后修改 reference、factor、plan 或 packing policy，必须创建新 run。
- 中间可以输出明确标记为 partial 的进度报告，但不能输出最终 package。

## 9. Reference-only Readiness Gate

当前 142 条 `reference_only` statement 不能直接当作可自动生成。每条 statement 在进入
factor loop 前必须满足：

1. PostgreSQL 18.4 官方语法和 source locator 完整。
2. statement reference 中所有 factor 及 factor value 有稳定 key。
3. 9,978 行账本中属于该 statement 的记录与 reference 双向一致。
4. SQL 模板所需占位符均有 binding、resolver 或明确的 Agent 生成合同。
5. combination matrix 列出 required baseline、合法组合、失败组合和具体原因。
6. object、relation、table、column type 的适用范围有明确决定。
7. 表、索引、约束、trigger、类型、角色等依赖形成有向无环图。
8. 至少存在一种合法的 verification 和幂等 cleanup 方案。
9. 需要外部环境的场景具有 `external_sql_fixture` 路由和 harness 边界。
10. statement、placeholder、factor mapping、combination matrix 和 dialect 审计通过。

Readiness 通过只表示“具备生成输入的静态资产”，不表示数据库执行成功。

## 10. 因子循环与覆盖展开

### 10.1 固定 inventory

每轮保存并绑定以下输入的路径、版本和 SHA：

- `statement_support_inventory.yaml`
- `postgresql_18_4_factor_audit.tsv`
- `pg18_factor_catalog.md`
- `pg18_type_catalog.md`
- compatibility profile
- statement reference
- matching combination matrix
- common factor/lifecycle/validation/output/naming policies
- object templates

### 10.2 每因子审查

每个 factor-value 必须分类为：

- `covered`：进入至少一个 test point。
- `expected_failure`：形成具体且单一原因的失败 atom。
- `justified_na`：保留具体不适用理由，不生成 SQL。

禁止用“已被相近值代表”“规模太大”或“暂时不测”作为 justified N/A 理由。

### 10.3 Axis 角色

- 会改变目标语义、错误类型、对象状态或观察结果的因子进入 `core_axes`。
- 同一 test point 的全部 core axes 做完整笛卡尔积。
- 与主语义独立的因子可以拆成单独 test point，但其全部值仍必须形成 atom。
- 因子是否拆点属于覆盖设计决策，必须有语义理由；packing 阶段无权改变它。
- table-backed statement 必须显式决定完整 relation/table、列类型、数据、事务、索引、
  约束和 trigger 适用性。

### 10.4 Mandatory risk 闭环

每条 statement 都必须逐项决定以下 12 类风险，不能因为某条语句看起来简单就省略：

```text
syntax
operation
lifecycle
data_profile
large_value_toast
transaction
partitioning
index_constraint_trigger
privilege
maintenance
concurrency
restart_recovery
```

不适用的风险必须给出 statement-specific 理由；特性或语句暴露的新边界作为额外风险
保留。风险决定必须落到 test point、external fixture 或 justified N/A，不能只留在说明
文档中。

### 10.5 Coverage atom 合同

建议 atom 至少包含：

```yaml
atom_id: ATM-insert-table-form-000001
statement_key: insert
test_point_id: TP-INSERT-VALUES
requirement_ids: [REQ-ALL-STATEMENTS]
factor_assignments: {}
outcome: success
reason: null
generation_route: single_sql
execution_harness: null
fixture_requirements: {}
pre_state: {}
target_intent: "INSERT one row using an explicit column list"
observable_assertion: "the inserted deterministic row is queryable"
post_state: {}
cleanup_requirements: {}
source_evidence: []
```

`expected_failure` atom 的 `reason` 必须非空；`justified_na` 不进入 bundle mapping。

## 11. 依赖设计

每条 statement 在展开 atom 前建立依赖图：

```text
environment/session
  -> schema/role/tablespace/extension/server
  -> type/function/procedure
  -> table/view/materialized view/foreign table
  -> column/data
  -> index/constraint/trigger/policy
  -> target statement
  -> deterministic verification
  -> reverse-order cleanup
```

不是所有节点都对所有 statement 适用。适用性由 statement reference、combination
matrix 和 factor ledger 决定，不能为凑规模无脑关联。

对于表相关语句，至少显式决定：

- 5 个 table 正交维度；
- 7 个 column-type inventory 维度；
- partition、inheritance 和 relation kind；
- index、constraint、trigger 的适用交互；
- NULL、空、边界、多行、重复、大值/TOAST 等数据形态；
- autocommit、事务、savepoint、commit、rollback 等状态。

## 12. 无损装箱算法

### 12.1 两阶段原则

装箱器只能读取已冻结 atom ledger：

1. 先证明 atom 集合完整。
2. 再减少承载这些 atom 的文件数量。

装箱器不得新增、删除、重新分类或改写 atom。

### 12.2 Fixture signature

每个 atom 计算规范化 `fixture_signature`，至少包含：

```text
environment/harness class
database and session boundary
required privilege identity
transaction envelope
schema and object graph
relation/table shape
column definitions and types
index/constraint/trigger prerequisites
seed data profile
state model
cleanup strategy
```

signature 相同只是候选条件，仍需通过状态兼容检查。

### 12.3 状态模型

bundle 必须选择一种状态模型：

- `isolated_reset`：每个 subcase 前恢复确定的基线状态，subcase 之间不依赖。
- `cumulative_lifecycle`：subcase 按显式依赖链推进对象或数据状态。

禁止隐式依赖前一个 subcase 的偶然副作用。`cumulative_lifecycle` 必须保存 subcase DAG，
并保证顺序唯一、无环且可通过 bundle 的 pre-cleanup 重跑。

### 12.4 兼容条件

atoms 只有同时满足以下条件才能进入同一 bundle：

- fixture signature 兼容；
- session、权限和 external harness 路由兼容；
- transaction envelope 可组合；
- 对象名和对象状态不冲突；
- verification 输出稳定且可分段归因；
- cleanup 可以覆盖 bundle 创建的全部对象；
- 任一 subcase 不会使后续 subcase 的声明前置条件失效，或已有明确 reset；
- 文件大小和 subcase 数未超过上限。

成功或预期失败本身不强制拆文件；真正决定是否拆分的是失败后的事务/对象状态能否
恢复到下一个 subcase 声明的前置状态。

### 12.5 跨 statement 装箱

允许跨 statement，但采用以下规则：

- 每个 subcase 保留唯一 `statement_key` 和 `atom_id`。
- 辅助 SQL 不计为辅助 statement 的覆盖；只有对应 atom 才能获得覆盖信用。
- 同一 atom 不得在另一个 statement 轮次再次入包。
- 跨 statement lifecycle 必须使用 `cumulative_lifecycle` 并声明依赖边。
- 跨 statement 不能破坏各 statement 自己的 `missing = 0` 报告。

### 12.6 稳定装箱策略

使用确定性的 stable first-fit：

1. 按 fixture signature 排序。
2. 桶内按 statement inventory 顺序、test point、axis value 顺序、atom ID 排序。
3. 依次放入第一个兼容且未达到上限的 bundle。
4. 不为追求极限压缩进行非确定性全局优化。

默认建议值：

```text
max_subcases_per_bundle = 50
max_bundle_bytes        = 1 MiB
max_atoms_per_shard     = 500
max_files_per_shard     = 100
```

这些值在创建 batch 时冻结；修改后创建新 run，不重写已发布编号。

## 13. Regress 文件合同

当前“一文件一判断”调整为“一文件一共享场景、多个可归因 subcase”。其他写作规范保持。

```text
Huawei header
session settings（仅必要时）
pre-cleanup
shared fixture setup
shared seed data

subcase marker
subcase-local reset/setup（需要时）
target SQL
deterministic verification

...更多 subcase...

final cleanup
```

文件要求：

- 文件名继续使用 `<prefix><NNNNN>.sql`。
- 全部自建对象继续使用对应 `<prefix>_<NNNNN>_` 前缀。
- 文件级对象前缀是最终权威规则；通用 `tab_`、`idx_`、`func_`、`proc_` 只能作为
  文件前缀后的语义片段，例如 `pcf_00001_tab_base`，不得产生跨文件共享名称。
- 表脚本第一个和最后一个可执行语句仍为覆盖全部创建表的
  `DROP TABLE IF EXISTS ...;`。
- 每个 subcase 使用稳定注释标记，例如 `PCF00001-SC001`。
- marker 至少绑定 subcase ID、atom ID 和目标 statement；不在注释中堆积完整 YAML。
- 每个 subcase 的目标 SQL 和 verification 在文件中可定位。
- expected failure 的具体原因归属到 subcase，而不是模糊归属到整个文件。
- 目录查询必须显式投影、schema-qualified 并稳定排序。
- 文件保持 UTF-8、LF 和恰好一个 EOF 换行。
- 禁止真实凭据、实例级设置、宿主机命令和不稳定环境值。

示意：

```sql
-- canonical Huawei header omitted from this abbreviated illustration
DROP TABLE IF EXISTS pcf_00001_base_table;

CREATE TABLE pcf_00001_base_table (
    id integer PRIMARY KEY,
    payload text
);

-- subcase: PCF00001-SC001 atom=ATM-INSERT-000001 statement=insert
INSERT INTO pcf_00001_base_table(id, payload) VALUES (1, 'alpha');
SELECT id, payload
FROM pcf_00001_base_table
WHERE id = 1
ORDER BY id;

-- subcase: PCF00001-SC002 atom=ATM-INSERT-000002 statement=insert
INSERT INTO pcf_00001_base_table(id, payload)
SELECT 2, 'beta';
SELECT id, payload
FROM pcf_00001_base_table
WHERE id = 2
ORDER BY id;

DROP TABLE IF EXISTS pcf_00001_base_table;
```

## 14. 映射与数据合同调整

### 14.1 多对一映射

`mapping.json` 从 obligation 与文件一一映射，调整为 atom 到 subcase 一一映射、多个
subcase 到文件多对一映射：

```json
{
  "atom_id": "ATM-INSERT-000001",
  "statement_key": "insert",
  "bundle_id": "BND-00001",
  "sql_filename": "PCF00001.sql",
  "object_prefix": "pcf_00001_",
  "subcase_id": "PCF00001-SC001",
  "subcase_ordinal": 1
}
```

### 14.2 批次计数

`batch.json` 和 `package.json` 分开记录：

```text
statement_count
factor_count
factor_value_count
required_atom_count
executable_atom_count
justified_na_atom_count
sql_file_count
bundle_count
subcase_count
compression_ratio = executable_atom_count / sql_file_count
```

不得用 `sql_file_count` 冒充覆盖数量。

### 14.3 Shard 所有权

- generation job 以 bundle/file 为写入所有权单位。
- 一个 shard 可以包含多个 bundle，但同时受 atom 数和文件数双上限控制。
- 生成者只能写 shard 分配的最终 SQL 文件。
- 生成者不能修改 atom ledger、mapping、bundle plan、job store 或其他 shard 文件。

## 15. 静态验收

### 15.1 Statement 与因子验收

- 183 条 statement 均有终态。
- 3,357 个 statement-factor pair 均可核账。
- 9,978 个 factor-value row 无 pending、missing 或无理由排除。
- reference-only statement 均有 readiness 证据。

### 15.2 Atom 验收

- requirement、test point、axis、dependency 引用有效。
- core axes 完整展开。
- 每个 atom 只有一个 outcome。
- expected failure 和 justified N/A 理由具体。
- 每条 statement 独立满足 reconciliation。

### 15.3 Packing conservation 验收

比较装箱前后 atom ID 多重集合：

```text
missing executable atoms    = 0
duplicate executable atoms  = 0
unexpected executable atoms = 0
```

同时验证 fixture signature、state model、subcase DAG、容量上限和跨 statement 归属。

### 15.4 SQL 文件验收

- 分配文件集合与实际文件集合完全一致。
- 文件名、对象前缀、header、编码和 EOF 合法。
- 每个分配 subcase marker 精确出现一次。
- 每个 marker 后存在目标 statement 和稳定 verification。
- shared setup 和 final cleanup 覆盖全部创建对象。
- 表级首尾清理满足现有规范。
- 不存在未分配 subcase、跨文件对象冲突或不稳定目录输出。

### 15.5 验后防篡改

验证报告绑定实际 SQL SHA。修改 validated SQL、mapping、bundle plan 或 atom ledger 后，
旧 validated 状态失效；正式做法是创建新 run 并重新编号，而不是沿用旧证据。

## 16. 错误与恢复

- readiness 失败：记录 statement、缺失资产和具体修订动作，修复后重试同一 statement。
- factor reconciliation 失败：禁止进入 atom 展开。
- atom reconciliation 失败：禁止进入 packing。
- packing conservation 失败：禁止冻结 mapping。
- SQL 静态验收失败：bundle job 进入 failed，修复并 retry，不领取第二个冲突 shard。
- 全批验收失败：禁止 package，保留已验证 bundle 的不可变证据。
- final package 只有在 183 条 statement 全部通过时产生。

## 17. DML 压缩示例

假设 INSERT 覆盖：

```text
table_form = regular, unlogged, temporary                 3
insert_form = values, select, default_values,
              overriding_system, on_conflict, returning   6
```

若二者是核心 axes，则覆盖 atom 仍为：

```text
3 × 6 = 18 atoms
```

未压缩：

```text
18 atoms -> 18 SQL files
```

按 table fixture 装箱后：

```text
regular table bundle   -> 6 INSERT subcases
unlogged table bundle  -> 6 INSERT subcases
temporary table bundle -> 6 INSERT subcases

18 atoms -> 3 SQL files
compression ratio = 6.0
```

测试点仍为 18，只减少了 15 份重复建表、数据准备和清理。

## 18. DDL 与跨语句示例

同一表 fixture 上可以形成显式生命周期 bundle：

```text
CREATE INDEX subcase
ALTER INDEX subcase
DML verification subcase
DROP INDEX subcase
```

只有为这些 statement 分别存在 atom 时，四个 subcase 才分别计入覆盖。若 INSERT 只是
为了验证索引后的数据可用性，它只属于 CREATE/ALTER INDEX atom 的 verification，不能
提前计作 INSERT statement 自身的因子覆盖。

## 19. 产物布局

建议保持当前 `artifacts/regress/<run-id>/`，增加 statement、atom 和 bundle 层：

```text
artifacts/regress/<run-id>/
├── batch.json
├── mapping.json
├── jobs.json
├── statements/
│   └── <statement-key>.json
├── atoms/
│   └── <statement-key>.json
├── bundles/
│   └── BND-00001.json
├── shards/
├── sql/
│   └── PCF00001.sql
├── reports/
│   ├── statements/
│   ├── packing/
│   └── shards/
├── schedules/
└── package.json
```

## 20. 分阶段落地顺序

### 阶段 1：合同与控制层

1. 新增 coverage atom、bundle、subcase 和多对一 mapping contract。
2. 把 20,000 门禁固定为 executable atom 门禁。
3. 实现 packing conservation 和稳定装箱。
4. 把 generation job 所有权调整为 bundle/file。
5. 扩展静态 SQL 验收以识别多个 subcase。

### 阶段 2：INSERT 试点

1. 使用全部适用 table/type/data/transaction 因子建立 INSERT atom ledger。
2. 按表 fixture 装箱。
3. 对比装箱前后 atom 集合，要求零缺失、零重复。
4. 验证每个文件可复跑、可归因、可清理。

### 阶段 3：CREATE INDEX 迁移试点

1. 将现有普通表 + CREATE INDEX 的 22,464 文件级样本转换为 atom 基线。
2. 使用新装箱器复用表和数据 fixture。
3. 保持成功/失败分类和全部核心组合不变。
4. 比较旧 manifest 与新 atom ledger，证明覆盖没有减少。

### 阶段 4：41 条 renderable statement

按 statement loop 逐条完成 atom、bundle、SQL 和静态报告，验证公共模型不依赖 DML
或 CREATE INDEX 特例。

### 阶段 5：142 条 reference-only statement

按对象域逐条通过 readiness gate，再进入相同公共 loop。不得为追求进度绕过缺失
binding、matrix、dependency 或 verification。

### 阶段 6：全 183 条 package

冻结全量 inventory、atom ledger、bundle mapping 和编号，完成所有 shard 后生成内网
所需 SQL-only regress package。

## 21. 验收标准

最终实现必须同时满足：

1. inventory 与 SHA 被固定，兼容目标为 PostgreSQL 18.4。
2. 183/3,357/9,978 三层账本完整，无 pending。
3. 142 条 reference-only statement 均有 readiness 结论；未通过者阻止最终 package。
4. 每条 statement 的 factor、test point 和 atom reconciliation 均 `missing = 0`。
5. 每个 executable atom 精确映射到一个 SQL 文件和一个 subcase。
6. 装箱前后 executable atom 集合完全一致。
7. justified N/A 不生成 SQL，但保留具体理由。
8. 默认 20,000 门禁按 executable atom 计数。
9. 至少 INSERT 和 CREATE INDEX 试点的 SQL 文件数低于 executable atom 数。
10. 所有 SQL 通过 header、编号、对象前缀、subcase、验证、清理、编码和稳定性检查。
11. 所有生成 shard 为 validated，才允许生成 schedules 和 package。
12. package 明确记录未执行数据库、未包含 expected、未进行差分比较。
13. Doctor 保持 0 error；新增合同、装箱、恢复和防篡改测试全部通过。

## 22. 关键设计决策摘要

- 外层循环单位是 statement，内层循环单位是 factor-value。
- 覆盖证明单位是 coverage atom，不是 SQL 文件。
- 压缩发生在 coverage 完整展开之后。
- SQL 文件是 bundle，一个 bundle 可以包含多个 subcase。
- 跨 statement 装箱允许，但覆盖信用严格归属到 atom。
- 公共 fixture 只在单个可复跑文件内复用，不依赖其他 SQL 文件的残留状态。
- 成功与预期失败都可以成为 subcase；是否同包由状态兼容性决定。
- 20,000 是真实 executable atom 的欠覆盖门禁，不是文件数量配额。
- reference-only statement 必须先补齐 readiness，不能跳过。
- 最终交付是内网待执行的 SQL-only regress 输入包，不是运行通过证明。
