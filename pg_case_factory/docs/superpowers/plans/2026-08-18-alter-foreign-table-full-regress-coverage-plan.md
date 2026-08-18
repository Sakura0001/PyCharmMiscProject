# ALTER FOREIGN TABLE 全量 Regress 覆盖计划

## 1. 当前状态与完成定义

- 语句序号：剩余语句循环第 11 条。
- 当前状态：`complete`。
- 正式 SQL 生成门禁：已通过。
- 完成定义：采用已确认的 `factor_value_independent_loop_v1`。官方语法值、103 个 canonical 因子值、适用的表/列/类型库存成员和事务风险逐项形成主覆盖义务；每条本地义务由一个真实 SQL program 独立见证，12 条外表索引义务逐成员交给 `create_index`；可到达的非法值生成独立 expected-failure。最终 SQL 经过字节级守恒、style 校验和隔离 PostgreSQL 18.4 双轮执行。

本语句已经满足上述完成定义并发布；183 语句循环的下一条为 `alter_function`。

## 2. 冻结输入

| 输入 | SHA-256 |
|---|---|
| `references/statements/ddl/foreign_table/alter_foreign_table.md` | `b1921c442b7fda3f61fc9a17209f2ec4689eabc20b7f7887b2f6e1d3850e71a8` |
| `references/combinations/ddl/foreign_table/alter_foreign_table.yaml` | `dfff0d2751020e74c1c79bdac82aa024185f24db1e81f0adb9d4a6b9d40e4090` |
| `references/common/pg18_type_catalog.md` | `7524c183d614ac74e902eb7d3b7ef652f2ff2dfc51266fb3db9a252f94c37792` |
| `references/common/pg18_column_structure_catalog.yaml` | `5b1a275b91314838b2bcea57f01927cd1e316345010ebf53abaf5c578e630412` |
| PostgreSQL 18.4 `src/backend/parser/gram.y` | `7e548b673a1e03eb3a56c5eb9ad92d8e11095fac76e14cb258ca851f58274724` |
| PostgreSQL 18.4 `src/backend/commands/tablecmds.c` | `06299417dadb0f4a1ab94ef3d7ac2c53e202061a6996f40cf6637822629b2592` |

官方文档坐标：PostgreSQL 18 `ALTER FOREIGN TABLE` synopsis 与说明；本地实际执行目标固定为 PostgreSQL 18.4。

## 3. 官方语法账本

官方语法分成 4 个互斥 branch、27 个 target intent：

| branch | intent 数 | intent |
|---|---:|---|
| `branch_action_list` | 24 | ADD/DROP COLUMN、ALTER TYPE、SET/DROP DEFAULT、SET/DROP NOT NULL、SET STATISTICS、SET/RESET attribute options、SET STORAGE、column OPTIONS、ADD/VALIDATE/DROP CONSTRAINT、4 类 trigger、SET WITHOUT OIDS、INHERIT/NO INHERIT、OWNER、table OPTIONS |
| `branch_rename_column` | 1 | RENAME COLUMN |
| `branch_rename_table` | 1 | RENAME TABLE |
| `branch_set_schema` | 1 | SET SCHEMA |

官方 synopsis 中的可选词、互斥 alternative 和有限列表边界已经冻结为 46 条 modifier axis、109 个 axis value。加上 27 个 target intent，共 136 条 GRM 义务。renderer 不得临时推断可选词：

```text
official intent rows       =  27
official modifier values   = 109
grammar obligations        = 136
```

`action_list_cardinality` 是语言分区，不是自由二值轴。固定 `one_action` 后，27 个 intent 的单 action 官方语法条件积精确为 1,156 个 tuple；`multiple_actions` 必须在带前后状态的顺序产品中另行编译，禁止把 `1,156 × 2` 冒充多 action 覆盖。

现有 canonical `alter_action` 只有 18 个值。以下 6 个官方 action 不允许消失，作为 GRM 义务独立进入 interaction universe：

```text
set_statistics
set_attribute_options
reset_attribute_options
set_storage
enable_replica_trigger
enable_always_trigger
```

列表语法按 `zero/one/many` 和有意义的顺序边界建模，不枚举无限长度文本。单 action、两 action 顺序交互、全 action 一次性链、重复同 action、互相冲突 action 分别成为独立语义类；每类使用冻结最大长度和兼容 resolver，不能以抽样替代完整有限域。

## 4. Canonical 因子账本

当前 reference/matrix 定义 32 个因子、103 个值。`expected_status`、verification 和 cleanup 不作为自由输入轴；别名失败因子绑定到同一首因，不重复相乘。

| 因子族 | 数量 | 处理规则 |
|---|---:|---|
| branch/action | 4 branch + 18 canonical action | 按 branch 条件分区；另加入第 3 节 6 个 GRM action |
| object/name state | table/column/constraint/parent/new target shapes | 合法词法做条件积；不存在、冲突、qualified/reserved parser 边界做隔离负例 |
| relation targeting | IF EXISTS、ONLY、`*` | action-list/rename-column 使用 3 个合法 scope；rename-table/set-schema 不接受 ONLY/`*` |
| privilege | owner/non-owner/superuser、type USAGE、SET ROLE、schema CREATE | 按 PostgreSQL 18.4 检查顺序构造真值表；首个失败条件独占覆盖信用 |
| constraint/notice | NOT VALID、validate、IF EXISTS notice | 状态由 fixture 派生，不与不可能状态自由相乘 |
| verification/cleanup | 4 + 4 | 仅挂靠，不改变 semantic tuple 数量 |

## 5. 类型库存与当前精确条件积

七份类型 selector 均保留各自义务身份，即使多个 selector 最终解析为同一 `pg_type` 也不去重：

| selector | 成员数 |
|---|---:|
| `structured_config.types` | 85 |
| concrete built-ins | 85 |
| auto-array element types | 79 |
| pseudo-types | 26 |
| declaration aliases | 16 |
| typmod declarations | 60 |
| user-defined archetypes | 8 |
| 合计 | **359** |

类型只在 `ADD COLUMN` 与 `ALTER COLUMN TYPE` 两个真实 type-binding role 中消费。

## 6. 外表拓扑

当前语句的 foreign-table target 使用 7 个可执行拓扑：

```text
standalone
inheritance_parent
inheritance_child
inheritance_parent_and_child
partition_leaf_range
partition_leaf_list
partition_leaf_hash
```

拓扑不是报告标签，而是 interaction assignment 和 fixture route 的组成部分。PostgreSQL 18.4 实测检查顺序：

| 场景 | 结果 |
|---|---|
| standalone ADD/TYPE | 类型自身结果 |
| inheritance parent/middle，plain 或 `*` | 递归成功或类型自身失败 |
| inheritance parent/middle，`ONLY`，类型合法 | `42P16`，必须同步子表 |
| inheritance parent/middle，`ONLY`，类型非法 | 类型解析错误先发生 |
| partition leaf ADD，任意类型 | `42809`，不能给 partition 增加列 |
| partition leaf ALTER TYPE，任意类型 | `42P16`，不能修改继承列类型 |

## 7. 当前已证明的逻辑交互数量

公共目标语法域：

```text
IF EXISTS(2) × relation scope(3) × table-name shape(3) = 18
```

两个 type-consuming intent：

```text
ADD COLUMN local grammar
= COLUMN keyword(2) × IF NOT EXISTS(2) × COLLATE clause(2) × constraint cardinality(3)
= 24

ALTER COLUMN TYPE local grammar
= COLUMN keyword(2) × SET DATA spelling(2) × COLLATE clause(2)
= 8
```

因此当前子空间：

```text
ADD COLUMN       = 359 × 7 × 18 × 24 = 1,085,616
ALTER COLUMN TYPE= 359 × 7 × 18 ×  8 =   361,872
合计                                      1,447,488
```

按 PostgreSQL 18.4 check-order resolver 重算：

| outcome | ADD COLUMN | ALTER TYPE | 合计 |
|---|---:|---:|---:|
| success | 249,120 | 82,320 | **331,440** |
| expected failure | 836,496 | 279,552 | **1,116,048** |
| 总计 | 1,085,616 | 361,872 | **1,447,488** |

PG18.4 对 359 个类型逐项校准 `COLLATE "C"`：29 个成功、316 个以 `42804` 拒绝、14 个非法 typmod 先以 `22023` 拒绝；partition leaf 的 ADD guard 更早返回 `42809`。按 grammar×topology 全积后，新增的首因分布中 `collation_not_supported_by_type` 为 363,168 格。该分布已由 assignment-driven resolver 重算，不再沿用未包含完整 COLLATE 轴的旧成功数。

这个数字是交互空间的诊断口径，不是物理 SQL 数量，也不再作为简化因子循环的生成门禁。

当前还可独立复算两个诊断口径，但二者都不是最终发布数量：

| 诊断口径 | 数量 | 用途 |
|---|---:|---|
| 每个列成员分别与其 consumer action、7 拓扑和全部适用单 action 语法交互 | 2,763,054 | 证明 1,569 条 member/action 义务没有只挂一个代表语法；不同维度之间使用 baseline，属于边际核账 |
| 将同一 action 消费的全部列维度无条件机械互乘 | 948,669,233,975,254,511,538 | 仅作为伪组合上界；包含互斥状态、不可构造 fixture 和被更早检查遮蔽的复合失败，严禁直接生成 |

上述大规模 interaction 数保留用于后续组合增强，不作为本轮“每个因子值均被真实 SQL 覆盖”的完成条件。本轮以义务账本为准：每个适用因子值至少一条主见证，不能由其他值、注释或元数据代替。

按全局 V2 第 7.5.1 节，20 个列维度描述同一个 `target_column` role；每条 INV 义务使用“一个 credited member + 其他维度的 resolver-derived compatible baseline”，不同目录标题不伪造成 20 个独立列角色。语法、表拓扑和目标词法仍是独立轴，必须完整相乘。由此得到已经冻结的单 action candidate 基础宇宙：

```text
带 target-column INV 的 interaction = 2,763,054
无列库存 action 的 baseline         =     3,822
single-action candidate total        = 2,766,876
```

这 2,766,876 格逐一包含全部 1,557 条本语句列 member/action 义务、27 个 intent 的单 action grammar tuple、7 种 foreign-table 拓扑和 3 种既存表名词法；另 12 条 index-role obligation 通过逐成员 handoff 承接。它仍不包含 isolated canonical negatives、权限真值表、事务/并发风险和 multiple-action 顺序产品，因此不是最终总数。

当前已完成的条件过滤切片：

| 切片 | candidate | executable | impossible | PG18.4 结果摘要 |
|---|---:|---:|---:|---|
| `collation × COLLATE clause`（ADD/TYPE） | 40,320 | 20,160 | 20,160 | success 6,720；其余按 `42809/42P16/42704/42804` 唯一首因 |
| `ADD nullability × constraint cardinality` | 27,216 | 17,136 | 10,080 | success 5,760；`42809` 7,344；`42P16` 1,152；`42601` 2,880 |
| `ADD generation_mode × constraint cardinality` | 36,288 | 25,200 | 11,088 | success 6,240；`42809` 10,800；`42P16` 1,248；`42P17` 4,608；`0A000` 1,152；`42804` 1,152 |
| `ADD identity_mode × constraint cardinality` | 18,144 | 13,104 | 5,040 | success 5,280；`42809` 5,616；`42P16` 1,056；非整数 identity `22023` 1,152 |
| `ADD default_state × constraint cardinality` | 39,312 | 27,216 | 12,096 | success 9,120；`42809` 11,664；`42P16` 1,824；`42804` 1,152；默认表达式列引用/子查询 `0A000` 3,456 |

`impossible` 只表示同一 assignment 自相矛盾，例如 `collation=omitted_type_default` 配 `COLLATE present`，不会生成 SQL；对应 grammar value 和 inventory member均在其他 executable tuple 中逐项结算。`constraint_cardinality=many` 不得被机械排除：PG18.4 已实测 `DEFAULT 1 NOT NULL`、generated+NOT NULL、identity+NOT NULL 均成功，因此 nullable/generated/identity 成员会与 resolver 选择的兼容 secondary constraint 形成真实 many tuple；identity+DEFAULT 等不兼容对则进入独立 expected-failure 产品。PG18.4 还修正了列目录：`NOT NULL ENFORCED`、`NOT NULL NOT ENFORCED`、`NULL NOT NULL` 是 parser-reachable `42601`，而重复 `NOT NULL NOT NULL` 成功。

## 8. 20 个列结构维度的消费计划

| 维度 | 本语句消费方式 |
|---|---|
| column_count_and_position | ADD/DROP 条件积 |
| column_name_shape | 全部列级 action 与 RENAME COLUMN |
| data_type_and_typmod | ADD/ALTER TYPE 全 359 类型义务 |
| collation | ADD/ALTER TYPE 的 collatable/non-collatable/不存在边界 |
| nullability | ADD、SET/DROP NOT NULL、ADD CONSTRAINT |
| default_state | ADD、SET/DROP DEFAULT |
| generation_mode | ADD COLUMN 合法 generated 与可达负例 |
| identity_mode | ADD COLUMN 的 ALWAYS/BY DEFAULT/sequence options 合法条件积；非整数类型为 expected failure |
| primary_key_participation | ADD/ADD CONSTRAINT 隔离 expected failure |
| unique_constraint | ADD/ADD CONSTRAINT 隔离 expected failure |
| check_constraint | ADD/ADD/VALIDATE/DROP CONSTRAINT |
| foreign_key_role | ADD/ADD CONSTRAINT 隔离 expected failure |
| index_role | 由 `create_index` 承接 foreign-table index 拒绝；handoff 必须绑定实际 owner witness |
| partition_key_role | 7 拓扑条件积和 partition guard |
| inheritance_role | local/inherited/merged 与递归 scope |
| storage_and_compression | ADD COLUMN、SET STORAGE 和 compression 拒绝边界 |
| statistics_target | SET STATISTICS、SET/RESET attribute options |
| dependency_state | DROP/TYPE/RENAME/DROP CONSTRAINT 的 RESTRICT/CASCADE/重建 |
| dropped_or_existing_column_state | duplicate/existing/dropped-slot/nonexistent/IF EXISTS |
| data_profile | 不检查远端一致性的可观察 no-check 路径；需要本地可控 FDW fixture |

每个维度的成员全集来自冻结的 `pg18_column_structure_catalog.yaml`。当前目录包含 208 个直接成员并引用 359 个 selector-qualified 类型成员，总计 567 个义务；其中 151 个 legal state、35 个 reachable failure、22 个 structural boundary。PG18.4 校准确认 `NOT NULL ENFORCED`、`NOT NULL NOT ENFORCED` 和 `NULL NOT NULL` 均为可达 `42601`，目录语义 SHA 已更新为 `5abcfdd6e905d3e2475e29c0ff85e6bca683425ce95bc8c1e994807671e6e998`。成员 count、ordinal、来源和语义 SHA 已可独立复算。每个成员按 consumer action 形成独立义务，其他维度由 renderer 选择合法固定 baseline；baseline 不取得该 SQL 的主覆盖信用。

成员按本语句声明的全部 consumer action 投影后形成 1,569 条唯一 `dimension × member × action` 义务，而不是每个成员只挑一个 action 取证。类型维度的 359 个成员分别投影到 ADD COLUMN 和 ALTER COLUMN TYPE，得到 718 条；index-role 的 12 个成员逐项 handoff 给 `create_index`，不是一个 scope-level 总括 N/A。

PostgreSQL 18.4 实测还确认：foreign table 支持 ALWAYS/BY DEFAULT identity column、virtual/stored generated column、PGLZ compression 与合法 SET STORAGE；PK、UNIQUE、FK 在 foreign table 上均为 `0A000`，未知 compression 为 `22023`，定长 integer 使用 EXTERNAL storage 为 `0A000`。这些结果进入 relation-specific compatibility resolver，不能从官方 synopsis 是否展示该词法形态进行猜测。

## 9. 正式生成规则（简化因子循环）

1. 先编译完整义务账本：GRM 官方语法值、SFV canonical 因子值、INV 表/列/类型成员、RISK 事务风险。
2. 对每个适用的本地义务生成一条 SQL program；该义务是唯一主覆盖信用，其他维度只选合法 baseline。
3. 可到达 PostgreSQL 目标检查的非法值必须生成隔离 expected-failure，记录精确 SQLSTATE；不可把它记为 N/A。
4. 每条 SQL 都包含独立的完整 fixture、恰好一条目标 `ALTER FOREIGN TABLE`、结果或目录 oracle，以及可重复执行的清理。
5. 物理文件和对象使用同源稳定编号；最终字节重新提取主义务，要求 expected/actual obligation bag 完全相等。
6. delegated 义务必须逐成员保留 owner statement，不得用一个 scope-level N/A 合并；本轮 12 条 `index_role` 义务交给 `create_index`。
7. 不做全局笛卡尔积。后续若增加组合强度，作为独立 interaction 产品追加，不能破坏本轮因子值账本守恒。

## 10. 本地运行合同

- 目标实例：隔离 PostgreSQL 18.4，不复用本机 5432 的 PostgreSQL 16。
- 每个正式 program 从干净状态执行两遍。
- success 必须为 `00000` 且 oracle 为 true。
- expected failure 必须命中计划 SQLSTATE、目标 phase 和唯一首因，失败后对象状态不变。
- 两遍标准化输出、退出状态、SQLSTATE、oracle、cleanup/restore 结果必须一致。
- 所有 program 执行后必须恢复基线；残留 schema/table/role/server/FDW 为 0。

## 11. 完成门禁与证据

- [x] 359 个类型义务编译并经代表值在 PostgreSQL 18.4 校准。
- [x] 7 个 foreign-table 拓扑进入真实 assignment。
- [x] 4 branch / 27 official intent 账本冻结。
- [x] 46 条 official modifier axis / 109 个 value 冻结，GRM 总义务为 136。
- [x] 单 action 官方语法条件积 1,156 条守恒，`multiple_actions` 已与单 action 分区。
- [x] 6 个 canonical action gap 显式记录为 GRM obligation。
- [x] 20 个列结构维度逐一绑定 consumer 或 handoff。
- [x] type/topology 子空间 1,447,488 条守恒测试通过。
- [x] partition/inheritance/`ONLY` check-order 在 PostgreSQL 18.4 实测。
- [x] `pg18_column_structure_catalog.yaml` 的 567 个成员、count 和语义 SHA 冻结。
- [x] 567 个成员向全部 consumer action 投影为 1,569 条唯一义务。
- [x] 单 target-column role 的 1,557 条本地义务与全部单 action 语法/7 拓扑完整相乘为 2,763,054 格；无列 baseline 3,822 格；基础总计 2,766,876。
- [x] identity/generated/compression/storage 与 PK/UNIQUE/FK 的 PG18.4 relation-specific 结果校准。
- [x] type/COLLATE/topology 检查顺序对 1,447,488 格完成 assignment-driven outcome 重算。
- [x] collation、ADD-nullability、ADD-generation、ADD-identity、ADD-default 五个条件切片完成 candidate/executable/impossible 守恒。
- [x] 因子循环账本编译为 1,817 条决定：1,805 条本地 SQL，12 条逐成员 delegated handoff。
- [x] 27 intent 的 grammar 值、103 个 canonical statement-factor row、20 个列维度及 359 个类型成员均有本地或 delegated disposition。
- [x] 最终字节实际见证守恒通过：missing `0`、duplicate `0`、unknown `0`、semantic mismatch `0`。
- [x] 1,805 个 SQL program 已生成，serial/external schedules 已发布，regress style validator 为 `PASS`。
- [x] PostgreSQL 18.4（`server_version_num=180004`）两遍完整运行：每遍 1,805 条，总计 3,610 条。
- [x] 两遍 execution、SQLSTATE、oracle、cleanup、transcript、structured-result mismatch 均为 `0`。
- [x] 静态 package SHA-256：`aa3253fa97dce46c9ced6e7959cc9f77b528b511d8cefd4d0abf1453ecb6f700`。
- [x] runtime run-01 SHA-256：`1a950f3feffe08a9e955f5861963a0a745ecc4698b18dff639630209aa03ac51`。
- [x] runtime run-02 SHA-256：`c2251c0095da1df239321e081140d60526e5cdc900f824c3de3dbb834f4dc63f`。
- [x] two-run comparison SHA-256：`593dd6fbd3fdc22453d8eec7beb3f08626de41afce029e63c36491b94e8eb6e3`。
- [x] runtime validation SHA-256：`84b7ed1ee8913770dcad8e04d6590b20fa207a19f6899eff6022670b5b4ef073`。
- [x] 本语句在 183 语句循环计划中勾选；下一条为 `alter_function`。
