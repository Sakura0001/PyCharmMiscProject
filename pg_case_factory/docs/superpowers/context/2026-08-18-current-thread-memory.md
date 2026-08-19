# 当前任务完整记忆与续接上下文

更新时间：2026-08-18

状态：`active_handoff_context`

适用仓库：`/Users/yuyu/PyCharmMiscProject/pg_case_factory`

当前分支：`codex/mysql-8022-8041-parity`

当前 HEAD：`729835e test: publish alter foreign table factor regress`

## 1. 这份文档的用途

本文档保存当前对话中已经确认的用户意图、生成方法、完成状态、运行环境、证据位置、提交记录和下一步动作，供压缩上下文、重新打开任务或换执行者时无损续接。

本文档不保存模型内部推理、隐藏指令、临时猜测或已经被事实推翻的中间结论。出现冲突时，优先级如下：

1. 用户最新明确确认的要求；
2. `docs/superpowers/specs/2026-08-18-factor-value-loop-regress-design.md`；
3. 当前语句专用计划与已经通过的机器证据；
4. 更早的全交互/V2 设计仅作历史参考。

## 2. 用户最终目标

用户要为 PostgreSQL 语句生成全量 regress SQL，用于授权、隔离、可清理的本地测试环境。

长期目标是按冻结的 183 条语句顺序，逐条生成并验证完整用例。对每一条语句：

- 官方语法中的所有适用值都要覆盖；
- 当前项目 canonical 因子账本中的每个因子值都要覆盖；
- 与语句真实相关的表结构、列结构、类型、权限、对象状态、依赖、事务及必要风险都要覆盖；
- 非法但可到达目标检查的情况也是正式用例，必须生成 expected-failure；
- 每个语句完成后在循环计划中打勾，然后再进入下一条；
- 每完成一条，应通知用户检查生成质量；
- 用户接受每条语句几百、几千甚至更多 SQL，完整性优先于数量小。

## 3. 当前有效的简化生成方法

用户认为早期 V2 全交互流程过于复杂、单个语句耗时过长，已经明确批准简化为“因子值独立循环全覆盖”。正式设计位于：

`docs/superpowers/specs/2026-08-18-factor-value-loop-regress-design.md`

核心规则如下。

### 3.1 四类覆盖义务

每条语句的 required obligation ledger 是以下四类义务的并集：

| kind | 内容 |
|---|---|
| `GRM` | 官方 branch、action、可选关键字、有限 alternative、列表边界 |
| `SFV` | 项目 canonical statement factor/value，绑定 canonical row id |
| `INV` | 适用的关系、表、列结构、类型及其他共享库存成员 |
| `RISK` | 权限、对象状态、事务、并发、重启、外部能力等必要边界 |

同一库存成员如果在多个 action 中承担不同目标语义，就按 consumer action 分别形成义务。例如某类型既用于 `ADD COLUMN`，又用于 `ALTER COLUMN TYPE`，必须分别有真实 witness。

### 3.2 一义务一主用例

每个本地覆盖义务生成一条独立 SQL program：

- 精确一个 `primary_obligation_id`；
- 同一 canonical factor key 在单个用例中最多一个主值；
- 其他维度使用 resolver 选出的合法 baseline；
- baseline 不领取主覆盖信用；
- 主值必须真实出现在目标 SQL、必要 fixture、事务/harness operation 或可查询状态中；
- 注释和 sidecar metadata 不能单独作为覆盖证明；
- alias 可以复用模板，但 obligation、编号和结算记录不能合并；
- 每个文件恰好一次被测 target statement。

### 3.3 非法值

非法值是正式覆盖的一部分：

- 能到达 PostgreSQL 目标检查并被拒绝的值必须生成 isolated expected-failure；
- 固定五位 SQLSTATE；
- 只有一个 primary failure；
- 其他 fixture 条件保持合法，不能被更早错误遮蔽；
- 失败后验证对象和目录状态没有非预期变化；
- target 失败后仍必须执行最终清理；
- 两轮执行的 SQLSTATE、输出和状态必须一致。

只有语句本质上无法消费且有明确 owner statement 承接的义务，才允许逐成员 `delegated`。不得用一个 scope-level N/A 吞掉整个库存。

### 3.4 不做全局笛卡尔积

当前正式生成不要求所有普通因子两两或多维相乘。以下情况才建立专门组合义务：

- 官方语法明确要求组合；
- 一个值的合法性依赖另一个值；
- 两值形成明确合法/非法 alternative；
- PostgreSQL 检查顺序必须通过复合 fixture 观察；
- 多 action、事务、并发、重启本身就是独立风险。

以下数字只能作为诊断，不决定 SQL 数量：

- 所有因子值的机械乘积；
- 表结构、列结构七维或二十维的无条件乘积；
- expected status、verification、cleanup 的自由乘积；
- 类型 × 所有 action × 所有拓扑 × 所有权限的机械积。

### 3.5 守恒等式

```text
Bag(required obligation ids where disposition in {covered, expected_failure})
= Bag(primary obligation ids extracted from final validated programs)

Bag(required obligation ids where disposition = delegated)
= Bag(source obligation ids from validated handoff records)

missing   = 0
duplicate = 0
unknown   = 0
```

validator 必须从最终 SQL/harness 字节重新提取主见证，不能只相信 planner metadata。

## 4. SQL 写作要求

所有生成 SQL 遵循 `regress-output-script-style` 规范：

- 文件名和对象名前缀同源、稳定、连续编号；
- 固定 header；
- 幂等 pre-cleanup；
- 完整 fixture；
- 精确一次目标语句；
- success 或 expected-failure oracle；
- 无条件 final cleanup；
- runner 负责 cleanup 后残留检查；
- 输出必须确定，避免裸 OID、PID、随机值和不稳定顺序；
- 失败目标不能让后续 oracle 停留在 aborted transaction 中。

对于涉及表或列的语句，不能用无意义的一列表冒充完整结构。通常应包含：

- 稳定主键或标识列；
- 被测列；
- 辅助列；
- 必要约束；
- 明确类型；
- 确定性测试数据；
- 与 primary obligation 冲突时，由 resolver 明确调整 fixture。

## 5. 本地运行合同

正式完成一条语句前，所有本地 SQL 必须在隔离 PostgreSQL 18.4 中执行两遍：

1. 验证实例版本；
2. 每个 case 执行前检查该编号对象残留为零；
3. 执行 run-01；
4. 无条件 cleanup；
5. 验证残留为零；
6. 相同条件执行 run-02；
7. 比较规范化 stdout、stderr、退出状态、SQLSTATE、oracle 和 cleanup；
8. 任一 mismatch 都不能勾选当前语句。

success 必须为 `00000`，expected-failure 必须命中计划 SQLSTATE。

当前 PostgreSQL 18.4 环境：

| 项目 | 值 |
|---|---|
| binaries | `/tmp/pgcf-postgresql-18.4-install/bin` |
| socket | `/tmp/pgcf-pg18-aft-sock-20260818` |
| port | `55484` |
| database | `pgcf_aft` |
| server_version_num | `180004` |
| 每文件超时 | `30s` |
| 默认并行度 | `1`，串行 |

本机 5432 上的 PostgreSQL 16 不得被该正式运行流程复用或修改。

## 6. 项目全局库存

冻结 statement inventory：

`skills/pg-sql-generation/references/common/statement_support_inventory.yaml`

可读因子清单：

`docs/superpowers/specs/2026-08-10-remaining-statement-factor-inventory.md`

全局统计：

| 项目 | 数量 |
|---|---:|
| 语句 | 183 |
| statement factors | 3,357 |
| canonical factor values | 9,978 |
| retained statements | 6 |
| 原始待生成 statements | 177 |
| 原始待生成 factors | 3,277 |
| 原始待生成 factor values | 9,676 |
| PG18 compatibility-only values | 10 |

六条 retained statements：

- cursor：`close`、`declare`、`fetch`、`move`；
- DCL：`grant`、`revoke`。

这些 retained 包仍属于全局范围，但新流程若重新纳入，必须映射到当前 obligation ledger 后才能领取新覆盖信用。

## 7. 对话过程中的重要需求演进

### 7.1 DML 阶段

最初用户要求根据：

`docs/superpowers/specs/2026-08-05-statement-factor-loop-regress-bundling-design.md`

生成全量 DML 用例，并按 PostgreSQL 官方语法逐语法检查。

用户特别指出并要求补齐：

- `INSERT ... ON CONFLICT DO NOTHING`；
- `INSERT ... ON CONFLICT DO UPDATE`。

当时的核心教训：不能因为某个语法已经存在模板或注释就认为因子已覆盖；必须确认因子进入计划、最终 SQL、oracle 和 regress 包。补齐后重新生成 DML，原有 DML 用例要求保留。

### 7.2 目录整理

用户选择统一 regress 目录方案 A：

```text
artifacts/regress/by-factor/<sql用途>/<对象域>/<statement>/
```

目录要与因子/语句分类对应。Cursor、DCL、DML 和后续语句都应遵循统一目录，不散落到临时目录。

### 7.3 Cursor 与 DCL

Cursor 和 DCL 已生成并整理到统一 regress 范围，当前 statement cycle 将对应六条语句标记为 retained existing。

### 7.4 多 SQL、多会话写作规范

用户曾要求下载并学习：

`https://github.com/Gongliangbiao/pg_skills/tree/main/skills`

用户随后澄清，目的是学习用例写作规范，不是为了强行给所有语句增加多会话。结论：

- 语句语义需要多会话时使用真实 A/B session harness；
- restart/external 义务使用专用 runner/manifest；
- 单会话即可确定的语句不为形式引入多会话；
- 注释、普通 probe 或文件末尾立即 DROP 不能替代真实并发/重启。

### 7.5 全交互 V2 设计与简化

曾设计并多轮审计：

`docs/superpowers/specs/2026-08-12-full-statement-regress-coverage-generation-design.md`

该规格解决了大量严格覆盖数学、hash DAG、实际语义提取、shard、runtime、handoff 和全局 package 问题，但执行代价过高。用户明确要求简化：“只要保证每个语句的所有因子都覆盖到”。

因此当前活跃生成口径已经切换到 2026-08-18 factor-value loop。08-12 V2 规格保留为未来高强度交互增强设计，不是当前逐语句完成门禁。

## 8. 当前顺序循环状态

机器状态：

`artifacts/intermediates/remaining-statement-factor-cycle/progress.json`

可读计划：

`docs/superpowers/plans/2026-08-10-remaining-statement-factor-regress-cycle.md`

当前完成情况：

| 序号 | statement | canonical factors/values | SQL 文件 | 状态 |
|---:|---|---:|---:|---|
| 001 | `abort` | 13 / 43 | 61 | completed |
| 002 | `alter_aggregate` | 20 / 52 | 783 | completed |
| 003 | `alter_collation` | 20 / 47 | 174 | completed |
| 004 | `alter_conversion` | 24 / 62 | 216 | completed |
| 005 | `alter_database` | 31 / 90 | 1,420 | completed |
| 006 | `alter_default_privileges` | 26 / 77 | 4,271 | completed |
| 007 | `alter_domain` | 33 / 109 | 908 | completed |
| 008 | `alter_event_trigger` | 20 / 56 | 159 | completed |
| 009 | `alter_extension` | 24 / 67 | 416 | completed |
| 010 | `alter_foreign_data_wrapper` | 26 / 67 | 155 | completed |
| 011 | `alter_foreign_table` | 32 / 103 | 1,805 | completed |
| 012 | `alter_function` | 24 / 85 | 123 | completed |
| 013 | `alter_group` | — | — | next pending |

`progress.json.next_pending_statement` 当前必须为 `alter_group`。

## 9. ALTER FOREIGN TABLE 已完成工作

### 9.1 采用的方法

专用实现计划：

`docs/superpowers/plans/2026-08-18-alter-foreign-table-factor-loop-regress.md`

可读覆盖计划：

`docs/superpowers/plans/2026-08-18-alter-foreign-table-full-regress-coverage-plan.md`

该语句将早期 `2,766,876` 条单 action candidate 和约 `9.4867×10^20` 的机械组合上界降为诊断数据，正式采用一义务一主用例。

最终账本：

```text
required decisions       1,817
local SQL programs       1,805
delegated handoffs          12
canonical factor rows      103
```

12 条 delegated obligation 是 `index_role` 各成员，由 `create_index` 承接；不能生成语义错误的 ALTER FOREIGN TABLE index case。

### 9.2 生成目录

SQL 与 schedules：

`artifacts/regress/by-factor/ddl/foreign_table/alter_foreign_table/`

其中：

- `ALTERFOREIGNTABLE0001.sql` 至 `ALTERFOREIGNTABLE1805.sql`；
- `serial_schedule`；
- `external_schedule`。

证据目录：

`artifacts/intermediates/remaining-statement-factor-cycle/alter_foreign_table/`

主要文件：

- `factor-loop-plan.json`；
- `plan.json`；
- `coverage.json`；
- `handoff.json`；
- `actual-factor-witness-report.json`；
- `package.json`；
- `validation.json`；
- `runtime-run-01.json`；
- `runtime-run-02.json`；
- `runtime-two-run-comparison.json`；
- `runtime-validation.json`。

### 9.3 静态结果

```text
SQL files                         1,805
decisions                         1,817
delegated                            12
canonical factor rows               103 / 103
actual primary witnesses          1,817 / 1,817
missing obligation count              0
duplicate obligation count            0
unknown obligation count              0
semantic witness mismatch count       0
style validator                    PASS
```

静态 package SHA-256：

`aa3253fa97dce46c9ced6e7959cc9f77b528b511d8cefd4d0abf1453ecb6f700`

注意：`package.json` 和 `validation.json` 的 `runtime_status` 保持 `not_run_static_sql_only` 是有意的静态边界；正式 runtime 结论保存在独立 `runtime-validation.json`，不要为了显示运行完成而篡改静态 package。

### 9.4 PG18.4 双轮结果

```text
planned programs                  1,805
run-01 executions                 1,805
run-02 executions                 1,805
total executions                  3,610
missing executions                    0
unexpected executions                 0
execution failures                    0
SQLSTATE mismatches                   0
oracle failures                       0
cleanup failures                      0
transcript mismatches                 0
structured-result mismatches          0
```

证据 SHA-256：

| 文件 | SHA-256 |
|---|---|
| `validation.json` | `7da57a4d297abefb9f123d57096ec5c05e69809935ebaa7a7a3aa74800df5edb` |
| `actual-factor-witness-report.json` | `89ea122d53ba5e020ba4334f312780aab55c3085ad79e38cf15123a405275f62` |
| `runtime-run-01.json` | `1a950f3feffe08a9e955f5861963a0a745ecc4698b18dff639630209aa03ac51` |
| `runtime-run-02.json` | `c2251c0095da1df239321e081140d60526e5cdc900f824c3de3dbb834f4dc63f` |
| `runtime-two-run-comparison.json` | `593dd6fbd3fdc22453d8eec7beb3f08626de41afce029e63c36491b94e8eb6e3` |
| `runtime-validation.json` | `84b7ed1ee8913770dcad8e04d6590b20fa207a19f6899eff6022670b5b4ef073` |

### 9.5 最终验证

最终验证命令覆盖：

- PG18 列结构目录；
- PG18 类型目录；
- ALTER FOREIGN TABLE grammar/inventory 编译；
- factor-loop ledger；
- renderer；
- actual witness validator；
- PG18 runtime；
- remaining statement regress；
- statement factor cycle；
- Python 编译；
- regress SQL style；
- `git diff --check`。

最新结果：`Ran 117 tests in 196.289s — OK`，style validator `PASS`。

## 10. ALTER FOREIGN TABLE 实现文件

| 文件 | 作用 |
|---|---|
| `src/pg_case_factory/alter_foreign_table_regress.py` | 官方 grammar、类型/列目录、PG18 outcome helper |
| `src/pg_case_factory/alter_foreign_table_factor_loop.py` | 编译 1,817 决定，形成 1,805 cases + 12 handoffs |
| `src/pg_case_factory/alter_foreign_table_factor_render.py` | 渲染完整 SQL program |
| `src/pg_case_factory/alter_foreign_table_factor_validate.py` | 从最终字节提取主见证并做守恒 |
| `src/pg_case_factory/alter_foreign_table_factor_runtime.py` | PostgreSQL 18.4 串行双跑与比较 |
| `tests/test_alter_foreign_table_regress.py` | grammar、类型、列适用性与诊断空间 |
| `tests/test_alter_foreign_table_factor_loop.py` | ledger、ID、baseline、disposition、守恒 |
| `tests/test_alter_foreign_table_factor_render.py` | renderer、完整 program、fixture、oracle、cleanup |
| `tests/test_alter_foreign_table_factor_validate.py` | 实际 witness 与 mutation 门禁 |
| `tests/test_alter_foreign_table_factor_runtime.py` | 双跑、SQLSTATE、cleanup、确定性 |

## 11. ALTER FOREIGN TABLE 提交记录

从计划到发布的提交顺序：

```text
b12a4b4 docs: plan alter foreign table factor loop
b9e8ede feat: compile alter foreign table factor loop
66d8edb feat: plan one alter foreign table case per factor
29a524a feat: render alter foreign table column factors
c68076c feat: render alter foreign table constraints
bab4337 feat: render alter foreign table structural factors
ddc368f feat: render all alter foreign table factor values
6e0975d feat: assemble alter foreign table regress programs
75629b9 feat: validate and publish alter foreign table factor loop
88ffd0c test: add alter foreign table pg18 runtime
9d2cd6a fix: calibrate alter foreign table factor cases
729835e test: publish alter foreign table factor regress
```

正式 artifacts 原本受 `.gitignore` 的 `artifacts/` 规则影响，本次为保证 SQL 和证据随提交保存，使用精确路径强制加入；没有放开整个 artifacts 忽略规则。

## 12. ALTER FOREIGN TABLE 运行校准中解决的问题

完整双跑前曾发现并修复以下真实问题：

- OPTIONS baseline 与实际 option state 不一致；
- SET STORAGE 中 DEFAULT/PLAIN 与 MAIN/EXTENDED/EXTERNAL 的 PG18 outcome 需要类型相关解析；
- missing relation SQLSTATE 应为 `42P01`；
- non-owner、SET ROLE、type USAGE fixture 不完整；
- inheritance fixture 缺共同列或 NO INHERIT 前置状态；
- column rename/drop 后的 oracle 使用了旧名字；
- zero-column case 没有真正构造零列表外表；
- dependency blocked change 未标 expected failure；
- check constraint drop fixture 缺目标 constraint；
- default 表达式不稳定；
- generated expression 自引用；
- incompatible literal SQLSTATE 应为 `22P02`；
- non-collatable/collation fixture 需要合法现存 collation；
- cleanup 顺序和角色/schema 清理不幂等；
- system column 负例预期错误。

所有这些修复已经进入最终 SQL、单元测试和双轮运行证据。

旧发布包在重生成前被可恢复地移到：

- `/tmp/pgcf-aft-stale-sql-20260818`；
- `/tmp/pgcf-aft-stale-evidence-20260818`。

除非需要审计差异，不要恢复它们覆盖当前正式包。

## 13. 已完成语句的关键历史结论

### 13.1 ABORT

- 官方核心语法是 optional keyword `{omitted, WORK, TRANSACTION}` × chain `{omitted, AND CHAIN, AND NO CHAIN}`；
- 当前正式包为 61 SQL；
- 旧矩阵曾存在把无关轴无条件相乘、模板未绑定的问题，已经通过 statement-specific 计划解决。

### 13.2 ALTER AGGREGATE

- 52 个 canonical values 已结算；
- 当前正式包 783 SQL；
- signature/form、branch/target state 是条件绑定，不能把所有 20 因子自由相乘；
- ordered-set、hypothetical、VARIADIC、权限、same-target、namespace、parser 边界都进入正式套件；
- 曾发现同一 `insufficient_privilege` key 在少数 case 中重复记两个值，最终规则是只给 PostgreSQL 实际首个检查失败的 canonical token，其他状态留在 derived baseline。

### 13.3 ALTER COLLATION

- 47 个 canonical values 已结算；
- 当前正式包 174 SQL；
- completion 前修复了 membership/SET option、schema CREATE actor、table-column 与 index dependency 混杂、rollback owner oracle、default collation oracle、verification label 与实际 SQL 不一致等问题；
- PostgreSQL 18 运行结果已作为完成依据。

### 13.4 ALTER CONVERSION

- 62 个 canonical values 已结算；
- 当前正式包 216 SQL；
- 条件产品覆盖 lexical shape、default status、合法 actor、权限真值、same target、lookup/parser、pg_catalog、temp/toast、DEFAULT 编码对和 rollback；
- DEFAULT conversion 移入已有同编码对的目标 schema 是成功边界，不是唯一约束失败；
- 未限定 conversion lookup 会跳过 temp namespace。

### 13.5 ALTER FUNCTION

- 85 个 canonical values 已结算（24 因子 / 85 值），外加 GRM（5 synopsis 分支、23 target actions、RESTRICT/EXTERNAL/SET-form/depends/list 轴）与 RISK（commit/rollback 事务边界），正式 ledger = 123；
- 当前正式包 123 SQL，零 delegated；
- `non_owner_with_alter` 是 expected_failure（42501）——非 owner 即使被授予 EXECUTE 也不能 ALTER FUNCTION；ledger = 25 expected_failure / 98 covered；
- signature identity 经 `argtype_specification` 与 `routine_signature_resolution_manifest` 消费，同名不同签名用稳定 identity argument oracle；
- OWNER-branch new_owner 角色必须由 superuser 在 `SET ROLE owner` 之前创建（plain LOGIN owner 无 CREATEROLE）；
- PG18.4 双跑 246 次执行，零失败/零 SQLSTATE 不匹配/零 oracle/零 cleanup/零两轮不一致。

其余已完成语句以各自 `package.json`、`validation.json` 和 `progress.json` 为准，不要仅凭本段摘要修改其状态。

## 14. 当前工作树与 Git 注意事项

Git 顶层实际在 `/Users/yuyu/PyCharmMiscProject`，当前工作目录是其中的 `pg_case_factory/` 子目录。因此 `git` 输出路径通常带 `pg_case_factory/` 前缀。

当前分支含大量用户已有或其他任务留下的未提交改动。执行下一条语句时必须：

- 先检查 `git status --short`；
- 不重置、不覆盖、不清理用户改动；
- 只暂存当前 statement 的实现、测试、计划和精确 artifacts；
- 不使用 `git reset --hard` 或破坏性 checkout；
- artifacts 默认被忽略，如需提交，只对当前 statement 目录使用 `git add -f`；
- 提交前统计 staged 文件，确认没有跨语句或无关文件。

当前 ALTER FOREIGN TABLE 相关路径在提交 `729835e` 后没有未提交变化；`ALTER FUNCTION` 相关路径在提交 `4a39451` 后没有未提交变化；工作树中的其他 dirty 状态不属于上述任一提交。

## 15. ALTER FUNCTION 完成记录 + 下一步：ALTER GROUP

`alter_function`（序号 012，ddl/function）已正式完成、提交并在循环计划打勾。下一条已由机器状态冻结为 `alter_group`（序号 013）。

### 15.1 采用的方法与账本

专用实现计划：

`docs/superpowers/plans/2026-08-19-alter-function-factor-loop-regress.md`

该语句将 GRM（5 synopsis 分支、23 target actions、RESTRICT/EXTERNAL/SET-form/depends/list 轴）+ 85 SFV canonical + RISK（commit/rollback 事务边界）编译为一义务一主用例。`alter_function.yaml` 声明 `column_type_coverage`/`table_coverage`/`target_relation_coverage` 均 `not_applicable`，故无列/表/关系 INV 扫描。最终账本：

```text
required decisions       123
local SQL programs       123
delegated handoffs         0
canonical factor rows     85 / 85
expected_failure          25
covered                   98
```

零 delegated：T5 边界（owner/schema/extension/dependency/signature）都是真实 ALTER FUNCTION 错误 → expected_failure；SUPPORT 是 fixture 依赖。`handoff_ledger.owner_statement_key` 标 `create_function`（零委托占位）。

### 15.2 生成目录与静态结果

SQL 与 schedules：

`artifacts/regress/by-factor/ddl/function/alter_function/`

其中 `ALTERFUNCTION0001.sql` 至 `ALTERFUNCTION0123.sql` + `serial_schedule` + `external_schedule`。

证据目录：

`artifacts/intermediates/remaining-statement-factor-cycle/alter_function/`

11 份 JSON：`plan`、`coverage`、`package`、`validation`、`factor-loop-plan`、`handoff`、`actual-factor-witness-report` + `runtime-run-01`、`runtime-run-02`、`runtime-two-run-comparison`、`runtime-validation`。

```text
SQL files                         123
decisions                         123
delegated                           0
canonical factor rows              85 / 85
actual primary witnesses         123 / 123
missing / duplicate / unknown       0 / 0 / 0
semantic witness mismatch             0
style validator                    PASS
runtime_status              not_run_static_sql_only
```

静态 package SHA-256：

`99a0da31efe43601351c684b2629037ad7b86a91a28824ac649f85de72b73abd`

`package.json`/`validation.json` 的 `runtime_status = not_run_static_sql_only` 是有意静态边界；runtime 结论在独立 `runtime-validation.json`，勿篡改静态 package。

### 15.3 PG18.4 双轮结果

```text
planned programs                    123
run-01 executions                   123
run-02 executions                   123
total executions                    246
missing / unexpected executions        0 / 0
execution failures                      0
SQLSTATE mismatches                     0
oracle failures                         0
cleanup failures                         0
transcript / structured mismatches   0 / 0
server_version_num                 180004
```

证据 SHA-256：

| 文件 | SHA-256 |
|---|---|
| `validation.json` | `eef6f0f42c4e47fd373a7e89f978914c9d22a304b626f2a7898af4f062cfa2a0` |
| `actual-factor-witness-report.json` | `9f352580ca5e0bcab7a3353ffa322fe68087d44e7d5709c2fa2db072d794f752` |
| `runtime-run-01.json` | `fa3b9735349f59653b65f971011a95fa3986ecac18c0f292f612b5165d534296` |
| `runtime-run-02.json` | `1321c36f4b772fd55b705aacc9100397a023be0706f023a74f9a1bd087a4fc35` |
| `runtime-two-run-comparison.json` | `44c066d6325934a692ed72aa67da96227d2b7964cb362ae2c691c76e6221ea61` |
| `runtime-validation.json` | `65fba9cac8bf3ee74898d409de6a04212a1e8a1ecb9b6250e2b771c630e87725` |

### 15.4 实现文件与提交记录

| 文件 | 作用 |
|---|---|
| `src/pg_case_factory/alter_function_regress.py` | 官方 grammar、5 synopsis 分支、PG18 outcome helper |
| `src/pg_case_factory/alter_function_factor_loop.py` | 编译 123 决定，形成 123 cases + 0 handoffs |
| `src/pg_case_factory/alter_function_factor_render.py` | 渲染完整 SQL program |
| `src/pg_case_factory/alter_function_factor_validate.py` | 从最终字节提取主见证并做守恒 |
| `src/pg_case_factory/alter_function_factor_runtime.py` | PostgreSQL 18.4 串行双跑与比较 |
| `tests/test_alter_function_factor_loop.py` | ledger、ID、baseline、disposition、守恒、grammar |
| `tests/test_alter_function_factor_render.py` | renderer、完整 program、fixture、oracle、cleanup |
| `tests/test_alter_function_factor_runtime.py` | 双跑、SQLSTATE、cleanup、确定性 |

提交记录（从计划到发布）：

```text
15a9b52 test: add alter function pg18 runtime
4a39451 test: publish alter function factor regress
```

`remaining_statement_regress.py` 在 10 个分发点镜像 `alter_foreign_table`：cached factor-plan helper、lazy plan builder、`_PLAN_BUILDERS` 条目、renderer/coverage/factor-documents/package/generate/validate dispatch，以及 `ALTER FUNCTION` SQL-header regex。

### 15.5 运行校准中解决的问题（FIX 1-8）

完整 123-case 双跑前曾发现并修复：

- FIX 1：rows-target fixture 用 `RETURNS SETOF integer`；
- FIX 2/3/4：support_fn 与 new_owner 角色删除排在 target routine 删除之后；角色删除用 `DROP OWNED BY` + `DROP ROLE`；
- FIX 5：`non_owner_with_alter` 是 expected_failure（42501）——非 owner 即使被授予 EXECUTE 也不能 ALTER FUNCTION；ledger 调整为 25 expected_failure / 98 covered；
- FIX 6：section 1 为完全幂等 pre-cleanup 超集；safety-net 用 `ON_ERROR_STOP=0`；
- FIX 7：procedure-mismatch case 的 target args 折叠为 `()`；
- FIX 8：OWNER-branch new_owner 角色由 superuser 在 `SET ROLE owner` 之前创建（plain LOGIN owner 无 CREATEROLE）。

所有修复已进入最终 SQL、单元测试与双轮运行证据。

### 15.6 下一条语句

下一条已由机器状态冻结为 `alter_group`（序号 013）。尚未研究其 grammar/coverage_scope；不得先定目标数字。续接时先读官方 `ALTER GROUP` 语法、本地 `combinations/ddl/<category>/<domain>/alter_group.yaml` 与 inventory `alter_group` 小节，编译 factor-loop ledger（GRM + SFV + RISK），再按 §16 模板逐条推进。

## 16. 每条后续语句的完成模板

每条语句完成报告至少记录：

```text
statement key
canonical factor count/value count
required decision count
local SQL count
delegated count
covered / expected-failure count
missing / duplicate / unknown / semantic mismatch
package SHA-256
PostgreSQL version
run-01 count
run-02 count
SQLSTATE/oracle/cleanup/two-run mismatch totals
runtime validation SHA-256
commit id
next statement
```

只有以下全部成立才允许勾选：

- ledger 冻结；
- 所有适用值有 disposition；
- 本地 program 与 delegated handoff 守恒；
- actual primary witness 来自最终字节；
- 编号、对象前缀、setup、oracle、cleanup 合规；
- style validator PASS；
- PostgreSQL 18.4 两轮完整执行；
- 所有 mismatch/failure 为 0；
- runtime evidence 绑定当前 package；
- 文档、progress 和提交均已落盘。

## 17. 续接时的最小验证命令

先确认当前状态：

```bash
cd /Users/yuyu/PyCharmMiscProject/pg_case_factory
git status --short
git log -1 --oneline --decorate
python3 - <<'PY'
from pathlib import Path
import json
p = Path('artifacts/intermediates/remaining-statement-factor-cycle/progress.json')
doc = json.loads(p.read_text(encoding='utf-8'))
print(doc['statements']['alter_function']['status'])
print(doc['next_pending_statement'])
PY
```

预期：

```text
completed
alter_group
```

复核 ALTER FOREIGN TABLE / ALTER FUNCTION 静态/运行证据时，不需要重新生成 SQL；先读取：

```text
artifacts/intermediates/remaining-statement-factor-cycle/alter_foreign_table/validation.json
artifacts/intermediates/remaining-statement-factor-cycle/alter_foreign_table/actual-factor-witness-report.json
artifacts/intermediates/remaining-statement-factor-cycle/alter_foreign_table/runtime-validation.json
artifacts/intermediates/remaining-statement-factor-cycle/alter_function/validation.json
artifacts/intermediates/remaining-statement-factor-cycle/alter_function/actual-factor-witness-report.json
artifacts/intermediates/remaining-statement-factor-cycle/alter_function/runtime-validation.json
```

如果正式 SQL 任一字节变化，旧 package SHA、actual witness report 和 runtime evidence 都视为失效，必须重新生成、静态验证并双跑。

## 18. 当前交付边界

截至本文档写入时：

- `ALTER FOREIGN TABLE` 与 `ALTER FUNCTION` 均已正式完成、提交并在循环计划打勾；
- 下一条是 `alter_group`；
- 尚未开始研究 `alter_group` 的 grammar/coverage_scope，更未生成正式 SQL；
- 用户要求继续按同一简化因子值循环顺序生成剩余语句；
- 每完成一条后应先通知用户检查，不得一次性把多条语句状态无证据地全部勾选。
