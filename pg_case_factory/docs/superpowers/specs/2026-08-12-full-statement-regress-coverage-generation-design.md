# 全语句 Regress 完整覆盖生成方法设计

## 1. 状态与决策

- 书面规格状态：`written_pending_user_review`。
- 兼容目标：PostgreSQL 18.4。
- 控制合同：`full_statement_coverage_v2`；它是对现有 coverage/regress v1 合同的显式升级，
  不是现有 `pg-case regress` 可以直接消费的别名。
- 适用范围：`statement_support_inventory.yaml` 登记的全部 183 条语句，包括既有
  DML、Cursor、DCL 和已生成的 statement-cycle 用例。
- 当前执行边界：本规格批准前停止新增或重新生成 SQL。
- 核心决策：采用“契约驱动、先计划后生成”；用例数完全由覆盖空间推导，不设置
  人为上限，不允许 pairwise、随机采样、代表值替代或按目标数量裁剪。
- 规模决策：几千、几万乃至更多 executable atoms 都是正常结果。规模只能通过稳定
  分片、断点续跑和通过守恒证明的无损装箱处理。

本规格定义的是“如何推导完整用例集合并证明没有遗漏”的唯一方法。逐语句 renderer
不得自行增加、删除、轮换或抽样因子；生成 Agent 也不得在写 SQL 时临时改变覆盖设计。
仓库在完成第 4.5 节的 v2 基础设施迁移并通过合同测试前，所有语句都不能进入
`generation_allowed`。

## 2. 问题与根因

现有仓库分别存在三类文档和产物：

1. 因子 inventory 回答“声明了哪些 statement、factor 和 value”；
2. 顺序计划回答“生成到哪条语句”；
3. 装箱设计回答“理论上如何展开和装箱”。

它们之间缺少一份生成前冻结的逐语句 coverage design。结果是部分 SQL 先生成，随后再
反推组合理由；relation/table/column/type 适用性、条件积边界、失败首因和完成门禁会随
生成过程变化。仅凭 factor-value 有 case witness 或 SQL 文件数量，不能证明覆盖完整。

本设计补齐以下缺失层：

```text
official grammar + canonical factors + canonical inventories + risks
  -> reviewed applicability
  -> exact conditional products
  -> immutable coverage atoms
  -> fixture/oracle/cleanup plans
  -> frozen mapping and bounded shards
  -> generated SQL or real harness bundles
  -> conservation validation and package evidence
```

## 3. 规范性语言与基本概念

本文中的“必须”“禁止”“只有……才……”均为 fail-closed 合同。

### 3.1 Grammar value

PostgreSQL 18.4 官方 synopsis 中一个有限、可区分的直接语法选择，包括分支、可选项的
`absent/present`、互斥关键字、列表基数、参数模式和可观察的解析边界。

### 3.2 Canonical factor-value

规范 applicability universe 中带稳定 row ID 的 statement/factor/value。全量 universe
当前为 183 statements、3,357 statement-factor pairs、9,978 factor-value rows；每次 run
必须从冻结 inventory 重算数量和语义哈希，不能把 matrix 内局部 `required_values` 当作
完整全集。

### 3.3 Inventory member

object、relation、table、column/type 或 routine signature 的规范库存成员。库存成员是否
适用由具体 statement branch 审查，不能因 matrix 没有列出而静默消失。

### 3.4 Conditional product

在明确的 axis domain 和 compatibility predicate 下，对所有合法 tuple 做完整笛卡尔积。
它不是把所有 YAML 值盲目相乘，也不是抽取代表 tuple。

### 3.5 Coverage atom

一个不可再拆的、可归因的覆盖义务。它具有单值 canonical assignments、唯一 outcome、
前置状态、唯一目标行为、确定性 oracle、后置状态、cleanup 和 execution harness。

### 3.6 Subcase、case program 与 bundle

- `subcase`：coverage atom 在可执行程序中的一对一表示；
- `case program`：承载一个或多个兼容 subcase 的 SQL 程序；
- `bundle`：共享 fixture 的物理容器，可能是一个 SQL 文件或多会话 harness 目录。

覆盖守恒以 atom/subcase 为单位，不以物理 SQL 文件数量为单位。

### 3.7 全局稳定 ID codec

所有逻辑 ID 使用同一个不可歧义 codec：先对 component array 中的字符串做 Unicode NFC，
按 RFC 8785 序列化 JSON array，再计算完整 SHA-256：

```text
logical_id(kind, components)
= <KIND> + "-" + hex(sha256(UTF8("FSCR_ID_V2\0") || JCS([kind, ...components])))
```

规范 logical ID 永远保留 64 位小写十六进制 hash，不截断、不通过 `|` 拼接，也不从 ID
反解析语义；artifact 同时保存完整 components 供审计。Kind 固定枚举包括：

```text
GRM FOB INV RISK NA INT AXI ITUP PROD PTUP STUP ATOM SUB PROGRAM BUNDLE SHARD WIT
```

现有 canonical `sfv-*` row ID 作为 source identifier 原样保存，但它的 branch/context obligation
使用 `FOB-*`。所有 ID 都包含 statement key component；global validator 建立 ID registry，发现
同 ID 不同 components 或 components 重复发出不同 ID 时立即失败。物理文件使用第 11 节的
statement-local ordinal，不用逻辑 hash 取代可读编号。

## 4. 权威文档与数据层级

### 4.1 全局生成方法设计

本文件是所有语句共用的生成算法合同：

```text
docs/superpowers/specs/2026-08-12-full-statement-regress-coverage-generation-design.md
```

`2026-08-05-statement-factor-loop-regress-bundling-design.md` 保留为前序背景和历史决策记录；
凡涉及“如何证明全量、何时允许生成、如何装箱/发布/勾选”的冲突，以本 v2 规格为准。

任何逐语句计划不得放宽本文件的守恒、适用性、归因或验证门禁。

### 4.2 全局覆盖进度计划

实现阶段应创建：

```text
docs/superpowers/plans/2026-08-12-full-statement-regress-coverage-plan.md
```

该文件只展示 183 条语句的顺序、状态、数量、阻断项和证据链接。它必须由当前证据图
确定性渲染，不允许手工修改 checkbox。

同一个 run 的全局控制证据保存为：

```text
artifacts/intermediates/full-statement-coverage-plan/<run-id>/global/
├── global-input-lock.json
├── statement-order.json
├── progress.json
├── current.json
└── global-revisions/<global-revision-id>/
    ├── selected-statement-revisions.json
    ├── handoff-ledger.json
    ├── handoff-validation.json
    ├── approvals/<statement>.json
    ├── generation-contracts/<statement>.json
    ├── global-mapping.json
    ├── global-validation.json
    └── global-package.json
```

其中 `handoff-ledger.json` 对第 7.7 节 delegated N/A 做跨语句闭环；`progress.json` 只是当前
哈希图验证结果的缓存，不是完成真相源。`global-revision-id` 使用在 global 锁内单调分配的
`gNNNN`；每个 global revision 绑定 183 条明确的 statement revision。新 statement revision、
handoff closure 或 package 选择必须创建新的 global revision，不覆盖旧全局证据。
`global-input-lock.json` 的 semantic SHA 就是 `global_input_root_sha256`；它按第 13.1 节 artifact
规则提交全部 global inputs 的相对路径、byte SHA、semantic SHA 和版本。

### 4.3 逐语句冻结计划

每条语句在生成 SQL 前必须具有：

```text
artifacts/intermediates/full-statement-coverage-plan/<run-id>/<statement>/
├── current.json
├── plan-revisions/<revision-id>/
│   ├── input-lock.json
│   ├── readiness.json
│   ├── grammar-ledger.json
│   ├── factor-ledger.json
│   ├── applicability.json
│   ├── na-ledger.json
│   ├── risk-ledger.json
│   ├── intent-axis-ledger.json
│   ├── interaction-universe.json
│   ├── products.json
│   ├── atoms.json
│   ├── fixture-plan.json
│   ├── packing-plan.json
│   ├── mapping.json
│   ├── obligation-witness-index.json
│   ├── plan-content-manifest.json
│   ├── plan-validation.json
│   └── coverage-plan.md
└── executions/<revision-id>/<global-revision-id>/
    ├── jobs.json
    ├── shards/
    ├── attempts/
    ├── reports/
    ├── regeneration-report.json
    ├── schedules/
    ├── package.json
    ├── validation.json
    └── execution-summary.md
```

JSON 是生成器消费的规范合同，`coverage-plan.md` 是这些 JSON 的确定性、完整可读视图。
二者绑定同一个 `plan_content_root_sha256`；该值是第 13.1 节定义的、截止 frozen witness
index 为止的无循环内容根。手工修改 MD 不能改变生成行为；计划审批记录必须绑定 validated
plan root、global handoff closure SHA 和 mapping SHA。任一输入漂移会使 approval 失效。路径
示例中的尖括号名称是 schema 参数；进入 approved plan 前必须解析为具体值，实际产物中残留
尖括号参数属于错误。

`run-id` 固定格式为 `fscr-pg18_4-<global-input-root-sha-prefix>`；SHA prefix 取完整小写
SHA-256 的前 16 个十六进制字符，artifact 内仍保存并验证完整 SHA，路径冲突时 fail closed。
Global input root 覆盖全部 183 条 statement 的 reference、matrix、renderer、官方来源、库存、
schema、policy 和 validator；任一非 inventory 输入变化也必须产生新 run。`revision-id` 只使用
在 statement 锁内预分配的单调 `rNNNN`，不包含参与自身内容计算的 hash。`current.json` 只保存
revision ID、plan content root、validated plan root、active global revision/approval SHA、
generation contract root 和当前 planning/runtime state。
Revision 目录一经 `local_plan_validated` 就只读；新的输入或覆盖定义创建递增 revision，不原地
覆盖。
这里的只读对象是 `plan-revisions/<revision-id>`；approval 写入 immutable global revision，
execution 状态只写到对应 `executions/<revision-id>/<global-revision-id>/`。更新 `current.json`
使用临时文件、fsync 和原子 rename。

Plan builder 先锁定并预分配 `rNNNN`，再在同一文件系统的 statement-local
`.planning/<revision-id>/` 写临时计划；完成验证后原子 rename 到最终 revision 路径。未获
`local_plan_validated` 的中断目录只能由 recovery 隔离或清理，绝不能被 `current.json`、
renderer 或全局计划引用。Revision ID、mapping path 和 object prefix 因此不存在 hash
固定点循环。

### 4.4 角色边界

- 规划 Agent：创建账本、条件积、atom 和 fixture 计划；禁止创建 regress SQL。
- 审核 Agent：只读核对官方语法、源码边界、类型适用性、乘积和失败首因。
- 生成 Agent：只能消费 approved mapping，只能写当前 shard 分配的最终文件。
- 验证 Agent：从实际字节重算 tuple、atom、mapping、SQL 和哈希守恒。
- 发布步骤：全部门禁通过后才能更新局部 package 和全局进度。

同一个 Agent 可以按顺序承担多个角色，但不能越过相应阶段门禁。

### 4.5 v2 基础设施迁移门禁

当前 `contracts.py`、matrix schema 和 `regress_generation.py` 只支持 v1 的四个 scope、
一 obligation 一 SQL、有限 job 状态和 SQL-only pg_regress schedules。实施必须先完成并测试：

1. `full_statement_coverage_v2` JSON Schema 与 Python contracts；
2. 四个既有 scope 加 selector manifests、routine/type manifests、统一 N/A ledger 和逐成员
   obligation decisions；
3. relation/table/type/routine 目录之外，先实现 statement branch consumer 与 canonical target
   intent catalogs、独立 join/partition validators；
4. 全局 ID codec、factor branch/context obligations、intent-axis/interaction universe compiler；
5. grammar、risk、product partition、atom projection、packing、mapping、witness、approval 和
   hash-graph validators；
6. one-atom/one-subcase、multi-subcase packing 和目录式 harness mapping；
7. v2 shard lease、attempt、staging、恢复和 shard-owned 原子发布；
8. serial/parallel/external/multi-session/restart manifests、runner 和 route safety validator；
9. 两遍全局 planning/handoff closure 和 global revision/package；
10. v1 旧包只读 importer，导入结果必须带 `origin=legacy_import` 并从相同 v2 规划状态机起点
    审计；
11. CLI 的 plan/validate/approve/claim/complete/retry/package/status 子命令。

所有 v2 schema、canonicalization、predicate evaluator 和 runner 都必须绑定明确版本。v1 工具
不得对 v2 产物返回 PASS；v2 infrastructure contract tests 未通过时 readiness 必须失败。

## 5. 状态机与生成权限

逐语句 `planning_state` 固定为：

```text
discovered
  -> inputs_locked
  -> readiness_passed
  -> ledgers_enumerated
  -> interaction_universe_frozen
  -> products_partitioned
  -> atoms_compiled
  -> fixtures_planned
  -> packing_frozen
  -> mapping_frozen
  -> witnesses_bound
  -> local_plan_validated
  -> global_handoff_closed
  -> plan_approved
  -> generation_allowed
  -> generating
  -> generated
  -> statically_validated
  -> packaged
```

`grammar_reconciled/factors_reconciled/applicability_reconciled/risks_reconciled` 是
`local_plan_validated` 内由 obligation witness index 证明的四个 gate result，不是会在 atom
产生前虚假完成的独立状态。`global_handoff_closed` 即使没有 delegated N/A 也必须绑定经过验证的
空 closure artifact。

控制状态拆成 `planning_state`、`failure_state`、`origin` 和 `runtime_state`。`origin` 只能是
`native_v2 | legacy_import`；旧包不是特殊完成状态，必须从 `discovered` 经过全部相同门禁。
`failure_state` 为 null 或 `{failed_stage, reason, retryable}`。事件转换固定为：

```text
input SHA drift          -> current revision stale；新 run/revision 从 discovered 开始
stage failure            -> 保留 planning_state，写 failure_state；修复后显式 retry 当前阶段
approval rejected        -> 保留 local/global validated evidence；新 revision 才能改语义内容
runtime package drift    -> runtime_state 对新 package 重置 not_run；历史记录只读
```

`runtime_state` 只能是：

```text
not_run
running
runtime_executed
runtime_verified
runtime_failed
```

进入 `running` 前必须记录当前 package SHA；之后所有 runtime 状态都绑定该 SHA。package
变化会把 runtime state 对当前 revision 的解释重置为 `not_run`，历史运行报告只读保留。

规则：

1. `generation_allowed` 之前禁止创建 SQL、`.spec` 或多会话 session 文件。
2. 全局规划 sweep 可以继续收集其他 statement 的 local plan，以解析未来 handoff owner；任一
   local failure 都会阻止 global closure 和全部 generation，不得绕过。
3. 生成 sweep 开始后严格按冻结 statement 顺序；当前 statement 未 packaged，下一条不得领取
   generation shard。
4. 修改冻结输入必须创建新 plan revision 或新 run，不能复用旧 approval。
5. `packaged` 表示静态输入包通过，不等于 PostgreSQL 运行通过。
6. `origin=legacy_import` 在 packaged 前不得显示完成；通过后与 native v2 使用同一终态。
7. `runtime_verified` 只对当前 revision/current package SHA 有效。

每条 forward edge 的最小 artifact precondition 固定如下；validator 不接受“状态字段已改”代替
证据：

| 目标状态 | 必须存在并通过的新增证据 |
|---|---|
| `inputs_locked` | local/global input locks 与完整 SHA |
| `readiness_passed` | readiness artifact、v2 infrastructure/catalog/policy gates |
| `ledgers_enumerated` | grammar/factor/applicability/N-A/risk ledgers |
| `interaction_universe_frozen` | branch consumer join、canonical intent partition、intent-axis ledger、interaction universe 守恒 |
| `products_partitioned` | product candidate/included/excluded 与 global partition 守恒 |
| `atoms_compiled` | atom projection 与 executable interaction multiset 相等 |
| `fixtures_planned` | fixture/oracle/cleanup/harness DAG 全解析 |
| `packing_frozen` | packing plan atom/subcase/container 守恒 |
| `mapping_frozen` | ID/path/shard/schedule 外键与 ordinal 全冻结 |
| `witnesses_bound` | obligation witness index，credited/context-only 分离 |
| `local_plan_validated` | plan content manifest、MD view、独立 validation 全 PASS |
| `global_handoff_closed` | selected 183 revisions、handoff ledger/validation 全 PASS |
| `plan_approved` | global-scoped approval 绑定 validated/local/global roots |
| `generation_allowed` | generation contract root 当前且 renderer/runner SHA 匹配 |
| `generated` | 全部 shard 目录原子发布或等 SHA 安全复用 |
| `statically_validated` | actual witness、jobs final、regeneration、schedule 全 PASS |
| `packaged` | package + final validation + 完整 hash graph 当前 |

### 5.1 唯一允许的全流程驱动算法

所有 statement 必须由同一个 v2 driver 执行“两遍全局规划、一遍顺序生成”。逐语句模块只
提供声明式 resolver/renderer，不能改写控制流：

```text
# Pass A: all-statement local planning; no SQL is generated
for statement in frozen_statement_order:
    lock_and_hash_all_inputs(statement)
    if not readiness_passes(statement):
        record_local_failure_and_continue_to_the_next_statement_for_dependency_discovery()
        continue

    grammar_rows       = enumerate_official_grammar(statement)
    factor_obligations = project_canonical_factor_rows_by_branch_and_context(statement)
    applicability_rows = join_frozen_inventories_by_branch_and_role(statement)
    risk_rows          = enumerate_mandatory_and_specific_risks(statement)
    na_rows            = record_all_intrinsic_and_delegated_na_decisions(statement)

    consumers = independently_join_branch_consumer_catalog_to_all_source_rows()
    canonical_intents = load_and_validate_canonical_target_intent_classes()
    intent_axes = classify_every_obligation_and_axis_inside_canonical_intents_exactly_once()
    prove_intent_partition_and_candidate_obligation_multisets()
    interactions = independently_compile_the_complete_interaction_universe(intent_axes)
    products = partition_interactions_without_loss_or_overlap(interactions)
    prove_candidate_included_excluded_multisets()

    atoms = compile_one_atom_per_executable_semantic_interaction(interactions)
    fixture_plan = compile_fixture_oracle_cleanup_and_harness_dags(atoms)
    packing_plan = map_atoms_to_subcases_and_containers_without_loss(atoms)
    mapping = freeze_ids_paths_shards_and_schedules(packing_plan)
    witness_index = bind_credited_obligations_to_atoms_subcases_and_phases()
    local_plan_report = independently_validate_current_bytes_and_conservation()

# Pass B: global N/A handoff closure and approvals
fail_if_any_local_plan_is_not_validated()
global_revision = freeze_all_183_selected_statement_roots()
handoff_closure = validate_all_delegated_edges_in_the_frozen_global_revision()
for statement in frozen_statement_order:
    approval = approve(local_validated_root, global_handoff_closure_root)

# Pass C: sequential generation; one statement must finish before the next begins
for statement in frozen_statement_order:
    for shard in frozen_shard_order:
        atomically_claim_one_shard()
        render_only_the_assigned_mapping_into_attempt_staging()
        validate_actual_bytes_and_all_witness_bindings()
        atomically_publish_or_mark_failed()

    regenerate_payload_in_two_empty_roots_and_compare()
    package_only_if_every_shard_and_hash_edge_is_current()
    derive_checkbox_from_the_revalidated_hash_graph()
    fail_unless_current_statement_is_packaged_before_advancing()
```

Pass A 可以在其他 local plan 上继续只读规划，以避免 delegated owner 的顺序死锁；但只要任一
statement 未 local validated，Pass B/C 都不能开始。Pass C 任一步失败都停在当前 statement，
不得生成下一条后把失败项手工标完成。算法的输入、枚举顺序、predicate、resolver、
canonicalization、renderer 和 validator 都必须有版本与 SHA；因此同一 approved revision
不允许因 Agent 的临时判断产生不同用例。

## 6. 输入冻结与 Readiness Gate

### 6.1 必须冻结的输入

`input-lock.json` 至少绑定路径、字节 SHA 和语义 SHA：

- PostgreSQL 18.4 官方文档 URL、版本和本地 synopsis/source locator；
- `statement_support_inventory.yaml`；
- canonical applicability universe；
- statement reference；
- matching combination matrix；
- PostgreSQL 18.4 factor、type 和 coverage inventories；
- v2 relation/table topology、type binding context 和 routine signature catalogs；
- v2 statement branch consumer、canonical target-intent 和 intent interaction catalogs；
- compatibility profile；
- lifecycle、validation、naming、baseline output、route-specific safety 和 cleanup policies；
- 对象模板；
- renderer 模块及版本；
- style validator 和 coverage validator；
- 本 coverage-plan schema 和本设计规格。

不得使用当前时间、Agent 名称、绝对临时路径等不稳定数据参与 semantic plan SHA。

### 6.2 Readiness 条件

以下条件必须全部满足：

- statement、reference 和 matrix 一一对应；
- 官方 synopsis 已固定为 PostgreSQL 18.4；
- reference/matrix 无未解析 EBNF、placeholder 或失效绑定；
- 每个 executable grammar/factor 值有确定且唯一的 renderer 路由；
- verification、cleanup 和外部 harness 能被计划表达；
- 所有规范 inventory 可读取且 count/SHA 可验证；
- official branch→required factor context/type role/selector consumer 与 canonical intent universe
  可由独立 compiler 重算；
- 目标语句若被 baseline output policy 禁止，已有第 9.2 节声明的窄化授权 route 和 validator，
  不存在 policy 冲突；
- 不使用 generic fallback 猜测目标 SQL。

Readiness 失败时只允许修复 reference、matrix、inventory 或计划基础设施，不能先生成 SQL。

## 7. 完整用例集合推导算法

### 7.1 第一步：建立官方语法账本

从官方 synopsis 和说明逐层拆解：

- statement branches；
- 每个 optional 的 `absent/present`；
- mutually exclusive alternatives；
- 列表的 zero/one/many 与有意义的多项顺序；
- 参数模式、参数名和参数类型位置；
- 名称是否允许 schema-qualified；
- 引号、保留字和 qualified target 等词法边界；
- 官方 notes 中的替代写法；
- PostgreSQL 18.4 源码中可观察的 lookup、权限检查顺序和 early return 边界。

每个直接语法叶子必须有稳定 grammar row ID。无限表达式语法不枚举无限文本，而是引用
仓库内已审计的有限语义类目录；该边界、来源和排除策略必须写入账本。

Grammar row ID 使用第 3.7 节 `logical_id("GRM", [statement, branch, production, value])`，
因此 production/value 即使包含分隔符也不会产生解析歧义。

`grammar-ledger.json` 每行至少包含：

```yaml
grammar_row_id: string
branch: string
production: string
value: string
source_locator: string
disposition: covered | expected_failure | justified_na
renderer_route: string
oracle_route: string
primary_reason: null | string
expected_sqlstate: null | sqlstate5
na_record_id: null | string
```

前置账本禁止保存尚未产生的 atom/subcase ID。真实 witness 统一由 atoms 之后的
`obligation-witness-index.json` 记录，避免 successor 回填使账本 SHA 和 atom 前驱形成循环。

守恒条件：

```text
official_grammar_values
= covered + expected_failure + justified_na

grammar_missing   = 0
grammar_duplicate = 0
grammar_pending   = 0
```

可选项缺少 `absent`、列表只有单项、替代写法没有 renderer 或 failure 没有首因时，禁止进入
下一阶段。

### 7.2 第二步：建立 canonical factor 账本

逐 statement 从完整 applicability universe 读取 canonical source row，而不是只消费 matrix 内
局部 `required_values`。同一 canonical value 在不同 branch/context 下可能得到不同结果，因此
`factor-ledger.json` 分成不可变 source rows 和派生 obligations 两层：

```yaml
canonical_rows:
  - row_id: string
    factor: string
    value: string
    tier: T1 | T2 | T3 | T4 | T5 | T6
    coverage_role: string
    source_evidence: []
obligations:
  - factor_obligation_id: string
    canonical_row_id: string
    branch: string
    context_id: string
    disposition: covered | expected_failure | justified_na
    primary_reason: null | string
    expected_sqlstate: null | sqlstate5
    renderer_route: string
    oracle_route: string
    na_record_id: null | string
```

规则：

- 每个 canonical row 在 source layer 精确出现一次；当前全局基线仍是 9,978 rows；
- 每个 source row 必须按第 7.4.1 节 branch consumer catalog 声明的全部 branch/context 投影成
  `FOB` obligation，不能用一个 scalar disposition 掩盖分支差异；派生 obligation 数另行报告，
  不与 9,978 混称；
- `covered` 和 `expected_failure` 必须最终由 witness index 指向真实 atom；
- `expected_failure` 必须有具体且唯一的 primary reason；
- `justified_na` 必须引用统一 N/A ledger；
- factor alias 可以共享 atom witness，但每个 canonical row 仍独立核账；
- 相近值、规模过大、暂未实现或代表值均不是合法 N/A 理由。

Factor obligation ID 使用第 3.7 节
`logical_id("FOB", [statement, branch, canonical_row_id, context_id])`；context 必须来自冻结
branch consumer/context catalogs，不能由 planner 或 renderer 临时造字符串。独立 validator
从 9,978 source rows 与 branch consumer catalog 重新 join candidate FOB multiset，并要求与
factor ledger obligations 精确相等。

守恒条件：

```text
canonical source rows = exactly frozen canonical rows
derived factor obligations
= covered + expected_failure + justified_na

factor_missing   = 0
factor_duplicate = 0
factor_pending   = 0
```

### 7.3 第三步：逐分支审查适用性

每个 official branch 必须依次审查：

1. `object`：目标和依赖对象种类；
2. `relation`：目标或依赖行为是否随 relkind 变化；
3. `table`：持久性、分区、继承和 access method 是否可观察；
4. `column`：是否直接声明、存储、转换、比较或返回列值；
5. `routine_signature`：是否通过参数、返回、状态类型或重载解析标识 routine；
6. `type_binding`：是否有 cast、operator、aggregate 等非表列类型角色；
7. mandatory risks 和 statement-specific risks。

每项结论只能是：

- `exhaustive`：全部规范库存成员展开；
- `conditional`：在明确写出的兼容域内全部展开；
- `justified_na`：目标 SQL 不可观察该维度，并有逐分支证据。

辅助 fixture 的存在不能让本来不适用的语句取得 relation/table/column/type 覆盖信用。

`applicability.json` 使用 v2 固定结构。为兼容现有概念，四个 scope ID 仍为
`object/relation/table/column_type`，状态只取 `complete/not_applicable`；覆盖方法另用
`coverage_mode: exhaustive | conditional | not_applicable` 表示。Routine 和一般 type binding
不是伪装的 column scope，而是两个强制 manifest：

```yaml
schema_version: 2
kind: statement_applicability
statement_key: string
scope_decisions:
  object: {status: complete, coverage_mode: exhaustive, selector_manifest_ids: []}
  relation: {status: not_applicable, coverage_mode: not_applicable, selector_manifest_ids: []}
  table: {status: not_applicable, coverage_mode: not_applicable, selector_manifest_ids: []}
  column_type: {status: complete, coverage_mode: conditional, selector_manifest_ids: []}
routine_signature_manifest:
  status: complete | not_applicable
  selector_manifest_ids: []
type_binding_manifest:
  status: complete | not_applicable
  binding_roles: []
  selector_manifest_ids: []
selector_manifests:
  - selector_manifest_id: string
    scope: object | relation | table | column_type | routine_signature | type_binding
    selector_id: string
    inventory_count: nonnegative_integer
    inventory_sha256: sha256_hex
    consuming_branches: []
    binding_roles: []
    context_ids: []
    compatibility_resolver: {id: string, version: string, sha256: sha256_hex}
member_decisions: []
```

每个适用 scope/manifest 都通过 `selector_manifest_ids` 引用完整 selector、count、SHA、consuming
branches、binding roles、contexts 和 compatibility resolver。`status=not_applicable` 时必须没有
executable member，却必须拥有第 7.7 节要求的 N/A 记录；空 selector list 不能替代该记录。
`status=complete` 必须至少一个 selector manifest，且它列出的 candidate obligation 数与实际
`member_decisions` 精确相等；无成员的合法库存仍需零 count/SHA manifest，不能静默缺字段。
其中 consuming branches/roles/contexts 必须与第 7.4.1 节 branch consumer catalog 的引用内容
逐字节相等；local manifest 不能重新定义或缩窄它们。

逐库存成员使用唯一 obligation ID：

```text
logical_id("INV", [statement, selector, member, grammar_row_id, binding_role, context_id])
```

因此七份类型库存中同名成员仍是不同证据义务，不会误去重。一个真实 atom 可以同时作为
多个 selector obligation 的 witness，但必须分别列出 obligation ID 和同一个可执行
witness binding；这表示同一构造同时证明多份目录事实，不要求复制 SQL。

`member_decisions[]` 固定字段为：

```yaml
obligation_id: string
statement_key: string
grammar_row_id: string
scope: object | relation | table | column_type | routine_signature | type_binding
selector_id: string
member: string
binding_role: string
context_id: string
disposition: covered | expected_failure | justified_na
primary_reason: null | string
expected_sqlstate: null | sqlstate5
na_record_id: null | string
source_evidence: []
```

每个 obligation ID 恰有一个 decision。`covered/expected_failure` 必须有实际 atom 和 phase
binding，但该后向引用只存在 `obligation-witness-index.json`；`justified_na` 必须引用第 7.7 节
统一 N/A ledger。库存守恒的左侧是所有 selector × branch × role × context 的 candidate
obligations，不是只计算预先判定 applicable 的成员：

```text
candidate inventory obligations
= covered + expected_failure + justified_na
```

### 7.4 Relation 与 table 规范库存

Relation 使用：

```text
references/combinations/_shared/coverage_inventory.yaml
  #relation_kinds.all_pg18_relkinds
```

当前规范 relkind 库存为：

```text
relation, index, sequence, toastvalue, view, matview, composite_type,
foreign_table, partitioned_table, partitioned_index
```

Table scope 使用五个正交维度：

```text
relpersistence
partition_role
partition_strategy
inheritance_role
table_access_method_selection
```

五维只在合法域内做条件积。例如：

- `non_partitioned` 只兼容 `partition_strategy=none`；
- partition parent/leaf 必须绑定 range/list/hash；
- 普通继承和声明式分区分别建模；
- access method 只在语法和存储模型支持时适用；
- extension-provided access method 路由到 external-isolated，不得静默遗漏；
- 如果错误 relkind 能到达目标 SQL 并被目标 SQL 拒绝，它是 expected failure，不是 N/A。

五维兼容关系不得由逐语句 planner 临时编写。v2 实施必须先创建并冻结：

```text
skills/pg-sql-generation/references/common/pg18_relation_table_topology_catalog.yaml
```

该目录从 PostgreSQL 18.4 grammar/catalog/source 推导，必须包含每个合法
`relkind × five table dimensions` tuple、每个不合法 tuple 的 reason/source locator、稳定顺序、
count、tuple-multiset SHA 和 resolver version。逐语句只能在这个合法全集上继续施加自己的
branch predicate；目录缺失或 SHA 不匹配时，任何 table-applicable statement readiness 失败。

### 7.4.1 Statement branch consumer 与 canonical intent 库存

为避免 planner 先缩窄 branch/role/context 或把独立轴按值拆成多个“intent”，v2 还必须在任何
逐语句 planning 前创建并冻结两份全局目录：

```text
skills/pg-sql-generation/references/common/pg18_statement_branch_consumer_catalog.yaml
skills/pg-sql-generation/references/common/pg18_canonical_target_intent_catalog.yaml
```

`pg18_statement_branch_consumer_catalog.yaml` 由 official grammar rows、9,978 canonical source
rows、relation/table/type/routine catalogs 和 PostgreSQL 18.4 语义独立编译，按
`statement × official branch` 列出：

```yaml
branch_consumer_id: string
statement_key: string
grammar_branch_id: string
required_factor_contexts:
  - canonical_row_id: string
    context_ids: [nonempty]
required_binding_roles:
  - scope: object | relation | table | column_type | routine_signature | type_binding
    selector_ids: [nonempty]
    binding_roles: [nonempty]
    context_ids: [nonempty]
required_risk_ids: [nonempty]
source_evidence: [nonempty]
```

目录保存 statement/branch/FOB/inventory candidate obligation 的 count 和 multiset SHA。Local
planner 的 selector manifests 只能引用 branch consumer ID；独立 validator 从冻结 catalogs 重新
join 出完整左侧全集，再与 FOB/member decisions 比较。Planner 不能自报 consuming branches、
binding roles、context IDs，不能用漏掉某 branch/role/context 后得到的局部 count 自证。

`pg18_canonical_target_intent_catalog.yaml` 从 official statement branches 和目标操作语义推导
canonical intent-equivalence classes。Intent identity 只能取决于 statement、official branch、
目标 operation kind、前置事务/session/外部事件形态，以及确实改变目标行为的语义 state class；
禁止取决于本应在 intent 内交互的 factor/inventory axis value。每个 class 记录完整 source
obligations、allowed/required axes、independence relations、partition predicate constraints、count/
SHA 和 source evidence。

Global `intent-partition-validator` 先计算 canonical intent candidate multiset，再验证 local intent
ledger 是它的无损分区：

```text
canonical intent candidate multiset
= emitted canonical intent-equivalence classes

missing = duplicate = illegal_split = illegal_merge = 0
```

Core intent 的 partition predicate 不得读取 independent/conditional axis 的具体 domain value；
只有目录声明的 branch/state/harness discriminator 可以分区。若 A={a1,a2}、B={b1,b2} 独立，
把它拆成 `I1={a1,b1}`、`I2={a2,b2}` 会触发 `illegal_split`，必须在同一 canonical intent class
先合并 A/B 完整域，再生成四个 interaction。Parser、isolated negative、transaction、concurrency
等 intent 也必须来自该目录的明确 class，不能以临时 product 名称规避主积。

### 7.5 Column/type 七份并列库存

完整 column/type 审查统一引用：

```text
references/common/pg18_type_catalog.md
```

必须逐份审计以下七个 selector：

| Selector | 当前数量 | 含义 |
|---|---:|---|
| `structured_config.types` | 85 | 可执行核心类型 profile |
| `structured_config.concrete_builtin_types.values` | 85 | PG18 具体内建类型 |
| `structured_config.auto_array_types.element_types` | 79 | 自动数组元素类型 |
| `structured_config.pseudo_types.values` | 26 | pseudo types 及合法上下文 |
| `structured_config.declaration_aliases.mappings` | 16 | 声明别名和拼写 |
| `structured_config.typmod_declarations.values` | 60 | 合法/非法 typmod 边界 |
| `structured_config.user_defined_archetypes.values` | 8 | 用户定义类型原型 |

数量是当前 PG18.4 快照的可读提示；运行计划必须从冻结目录重新计算并绑定 SHA。

七份库存是 tagged union，不计算：

```text
85 × 85 × 79 × 26 × 16 × 60 × 8
```

正确方法是逐 selector 展开每个成员，并在消费它的 branch/type role 下分类为 covered、
expected failure 或 justified N/A。只有语句存在两个或多个语义独立的类型角色时，才对
各自兼容成员集合做条件积，例如：

```text
CAST             = source_type × target_type
binary operator  = left_type × right_type
aggregate lookup = compatible direct_arg_types × compatible ordered_arg_types
```

返回类型由输入/状态类型决定、分区子表继承父表列类型、polymorphic 类型由同一解析约束
绑定等情况属于函数依赖，不得伪造自由积。

类型成员的消费语境也不能由 planner 自由判断。v2 实施必须创建并冻结：

```text
skills/pg-sql-generation/references/common/pg18_type_binding_context_catalog.yaml
```

目录按 `selector+member` 记录允许的 binding contexts、constructibility
（`portable_literal/catalog_derived/expected_failure/external_fixture`）、声明能力、routine 能力、
collatable/index/coercion 能力、fixture route 和 source evidence。逐语句先选择真实 type role，
再与目录允许 context 做 join；internal/input-restricted 类型不得被伪造 portable literal，alias
和 typmod 只能在目标语法能观察其声明时消费。

### 7.6 Routine signature 独立模型

Routine signature 不得伪装成普通表列类型覆盖。适用语句至少审查：

```yaml
routine_kinds:
  - function
  - procedure
  - aggregate
  - generic_routine
forms:
  - zero_arg
  - single_arg
  - multi_arg
  - variadic
  - ordered_set
  - hypothetical_set
argument_modes:
  - omitted_default_in
  - IN
  - OUT
  - INOUT
  - VARIADIC
  - TABLE
type_roles:
  - input_arg
  - direct_arg
  - ordered_arg
  - return_type
  - state_type
overload_states:
  - unique_exact_match
  - overloaded_exact_match
  - ambiguous
  - absent
qualification_states:
  - schema_qualified
  - search_path_resolved
```

上述维度的规范库存必须由 v2 实施创建并冻结为：

```text
skills/pg-sql-generation/references/common/pg18_routine_signature_catalog.yaml
```

该目录必须包含 aggregate/function/procedure/routine 的官方 grammar forms、各 routine kind
适用的 argument modes、arity、argname、aggregate ordered/hypothetical forms、type roles、
overload 和 qualification 状态，以及完整 compatibility tuples、count/SHA 和 source locators。
例如 `ordered_set` 只属于 aggregate 兼容域，不能进入 function/procedure 自由积。目录不存在
或未通过独立 audit 时，任何 routine-signature-applicable statement readiness 失败。

ALTER/DROP/RENAME 等通过 signature 定位 routine 的语句通常必须完成身份和解析类型覆盖，
但不因此要求无关的表列数据分布覆盖。

### 7.7 Justified N/A 判据

每个 N/A 必须进入独立 `na-ledger.json`；grammar/factor/inventory/risk decision 只保存
`na_record_id`，不复制或回填 N/A 内容。记录采用 obligation-kind tagged schema：

```yaml
na_record_id: string
obligation_kind: grammar | factor | inventory | risk
source_obligation_id: string
statement_key: string
grammar_row_id: string
factor_row_id: null | string
selector_id: null | string
member: null | string
binding_role: null | string
context_id: string
na_kind: intrinsic | delegated
reason_code: string
reason: nonempty_string
target_unobservable_proof: nonempty_string
source_evidence: [nonempty]
coverage_owner_obligation_id: null | string
source_projection: object
owner_projection: null | object
equivalence_key: null | string
equivalence_resolver: null | {id: string, version: string, sha256: sha256_hex}
```

- `intrinsic` 表示该 member 对目标 statement/branch 确实不可观察，owner 必须为 null；
- `delegated` 表示覆盖责任转交另一条语句，必须填写全局唯一 owner obligation ID。

全局 `handoff-ledger.json` 为每个 delegated edge 冻结 source/owner statement revision、local
plan root、完整 projection、equivalence key/resolver SHA、owner disposition、owner atom 和 credited
witness。`handoff-validation.json` 必须从全部 183 个 local validated plan 重新计算 source/owner
projection，证明 equivalence key 相等、目标义务真实存在且为 covered/expected_failure，并禁止
环、禁止 owner 再次 delegated、禁止多条义务互相指向而无人执行。全局 intrinsic N/A 必须由
官方/源码证据审计，不能用另一条 N/A 自证。Handoff closure 是每个 statement approval、全局
validation 和 checkbox 的强制前驱；只检查 owner ID“存在”不算闭环。

判定规则：

- 能让目标 SQL 自己拒绝的输入是 expected failure；
- 只能在 setup 阶段失败、导致目标 SQL 根本无法到达时，才可能是 N/A；
- routine 参数/返回 pseudo type 必须按具体上下文逐成员决定，不能整体 N/A；
- alias 若直接进入目标语法，应 covered/expected failure；
- alias 若在 fixture 创建后已目录规范化且目标 SQL 无法观察，可 N/A 并指向声明语句族；
- typmod 若由目标 SQL 解析或影响 coercion，必须 covered/expected failure；
- user-defined enum/domain/composite/range/multirange/array 适用时必须覆盖；
- 需要外部 capability 的合法成员优先 external-isolated，不得因环境不方便直接 N/A。

以下理由一律非法：用例太多、已有代表类型、暂未实现、环境不方便、预计没有差异。

### 7.8 Mandatory risk 闭环

每个 statement branch 必须逐项决定：

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

每项必须路由到 executable atom、真实 external harness 或带证据的 justified N/A。语句
暴露的额外风险作为 statement-specific risk 增加，不能替换这 12 项。

`risk-ledger.json` 每个 `grammar_row_id × risk_id` 恰有一行：

```yaml
risk_obligation_id: string
statement_key: string
grammar_row_id: string
risk_id: string
disposition: covered | expected_failure | justified_na
execution_route: single_session_multiphase | multi_session_barrier | restart_or_external_event | null
primary_reason: null | string
expected_sqlstate: null | sqlstate5
na_record_id: null | string
source_evidence: []
```

Risk ID 使用第 3.7 节 `logical_id("RISK", [statement, grammar_row_id, risk_id, context_id])`。
`covered/expected_failure` 必须在后置 witness index 中获得可执行 credited witness；N/A 引用
第 7.7 节同一 ledger。`risk-ledger.json` 的 count/SHA 是 plan validation、approval、package
和 checkbox 的强制前驱。

### 7.9 Axis 分类

每个 axis 必须属于且只属于一种生成角色：

| 角色 | 生成方法 |
|---|---|
| independent core axis | 与同 test point 其他独立轴完整相乘 |
| conditional core axis | 在 compatibility predicate 内完整相乘 |
| derived axis | 由其他轴计算，不参与乘积 |
| alias axis | 与 canonical 语义合并，但逐 row 核账 |
| isolated negative axis | 形成单一失败原因的独立产品 |
| fixture axis | 仅在改变目标行为时进入产品 |
| verification axis | 绑定真实 oracle，不作为目标语义自由轴 |
| cleanup axis | 绑定清理合同，不放大主语义积 |
| harness axis | 路由单会话、多会话或外部事件执行模型 |

`expected_status` 必须由 tuple 条件推导，不能作为自由输入轴。signature→form、branch→target
state 等函数依赖必须写进 resolver，不能把派生值再次相乘。

仅仅让每个 factor value 至少出现一次仍可能漏掉独立交互。因此 products 不能自报“自己就是
全集”。在声明 product 前必须先生成两个独立制品：

```text
intent-axis-ledger.json
interaction-universe.json
```

`intent-axis-ledger.json` 对每个 target intent 记录：

```yaml
intent_id: string
statement_key: string
grammar_branch: string
canonical_intent_class_id: string
intent_kind: core | isolated_negative | transaction | concurrency | parser | external
source_obligation_ids: []
axes:
  - axis_id: string
    axis_key: string
    role: independent_core | conditional_core | derived | alias | isolated_negative |
          fixture | verification | cleanup | harness
    domain_source_ids: []
    domain_count: nonnegative_integer
    domain_multiset_sha256: sha256_hex
    independence_group_id: string
    resolver: null | {id: string, version: string, sha256: sha256_hex}
interaction_rules:
  - participating_axis_ids: [nonempty]
    relation: full_cross | conditional | functional_dependency | mutually_exclusive
    resolver: {id: string, version: string, sha256: sha256_hex}
    source_evidence: [nonempty]
```

Intent/axis/interaction ID 分别使用第 3.7 节 `INT/AXI/ITUP` kind，并以 statement、branch、
intent、axis/domain 或完整 interaction assignment 作为 components。

Intent ledger 必须先从第 7.4.1 节 canonical target-intent catalog 投影，保存
`canonical_intent_class_id` 并通过 intent partition 守恒；不能由 product planner先造 intent。
同一 canonical class 的 axes/domains 必须先合并，随后才允许 interaction compiler 运行。

每个 GRM/FOB/INV/RISK obligation 必须被一个或多个 intent/axis 消费，或显式属于 derived、
alias、oracle、cleanup、harness、N/A；不得未分类。每个 independence group 内的全部轴完整相乘；
group 之间也必须有明确 `full_cross/conditional/function_dependency/mutually_exclusive` 关系和
证据，不能由 planner 只选择对角线组合。

独立的 interaction compiler 只消费冻结 ledger、domain SHA 和 declarative resolvers，枚举：

```text
candidate interaction multiset
= executable semantic interactions
  ⊎ impossible interactions
  ⊎ justified-N/A interactions
```

每条 interaction 有 `ITUP` ID、完整 assignment、disposition、reason/source 或 na_record_id。
能到达目标 SQL 的 expected failure 始终属于 executable。`interaction-universe.json` 分别保存
candidate/executable/impossible/N-A 的 count 和 multiset SHA，并证明三者守恒。Products 只能
无损分区 executable interactions；expected 空间来自 interaction compiler，不来自 product
planner 自报。

### 7.10 条件笛卡尔积合同

每个 test point/product 必须记录：

```yaml
product_id: string
target_intent_id: string
intent: string
core_axes: []
axis_domains: {}
predicate_schema_version: 1
compatibility_predicate: {}
candidate_interaction_ids: []
candidate_tuple_count: nonnegative_integer
candidate_tuple_multiset_sha256: sha256_hex
included_tuple_count: nonnegative_integer
included_tuple_multiset_sha256: sha256_hex
excluded_tuples:
  - source_interaction_id: string
    tuple: {}
    reason_code: string
    disposition: outside_partition | covered_by_product
    destination_product_id: null | string
    destination_product_tuple_id: null | string
    source_evidence: []
excluded_tuple_count: nonnegative_integer
excluded_tuple_multiset_sha256: sha256_hex
derived_axes: {}
isolated_failure_reason: null
```

Predicate 使用版本化、无副作用的 JSON AST，不允许 Python/SQL 字符串求值。v1 只允许
`and/or/not/eq/ne/in/implies`，叶子只能是 `{axis: <declared-key>}` 或 JSON scalar/array
literal；所有 domain value 必须是字符串、整数、布尔或 null，禁止浮点。操作符按文档顺序
和严格类型求值，unknown axis、类型不匹配或未知 operator 都使 plan validation 失败。
Derived axis 只能用冻结 lookup table 或绑定版本/SHA 的 declarative resolver，不能调用
renderer 代码决定是否保留 tuple。

Interaction compiler 已经核算 grammar/function-dependency impossible 和 justified N/A；product
无权再次删除它们。每个 product 的 candidate slice 必须精确满足：

```text
candidate product tuple multiset
= included product tuple multiset ⊎ excluded product tuple multiset
```

`outside_partition` 表示该 interaction 明确由其他不重叠 slice 管理；`covered_by_product` 必须
填写目标 product 和具体 PTUP ID。所有 products 的 included emitting semantic interactions
并集必须精确等于 interaction universe 的 executable multiset，missing/duplicate 均为零。
这样 exclusion 不能成为静默删组合的出口。

Tuple 采用 inventory 声明顺序和稳定 axis key 顺序枚举。计算 tuple-multiset SHA 时使用 UTF-8
canonical JSON：对象键排序、数组保持规范库存顺序、无空白、禁止浮点和时间戳。计划中同时
保存 cardinality formula、枚举器版本和 canonicalization 版本，使 expected count/SHA 可由
独立 validator 重算，而不是信任 planner 自报值。

每个 product-local tuple 使用第 3.7 节 `PTUP` ID，component 至少含 product ID、source ITUP ID
和完整 assignment SHA。另以与 product 无关的 canonical projection 计算 `STUP` semantic tuple
ID。Projection 必须包含 statement、target intent、官方语法坐标、实际 canonical factor坐标、
具体 object/relation/type-role bindings、risk obligation、transaction/session state 和 harness；
不包含 product ID、验证/cleanup 轮转或与语义重叠的 selector evidence alias。

下列旧式可读形式只作为报告 label，不作为规范 ID：

```text
PTUP|<product-id>|<ordinal>|<assignment-sha-prefix>
```

多个产品默认必须在 semantic tuple ID 上不相交。若两个产品故意描述同一语义 tuple，只能
指定一个 emitting owner；其他本地 tuple 必须用 `covered_by_product` 指向 owner，不能再次
发射 atom。transaction/concurrency/parser 等产品若目标意图或真实状态不同，必须把该差异
纳入 semantic projection，而不是依靠 product 名称区分。validator 对所有 emitting tuples
做全局 semantic ID uniqueness 检查。

Multiset hash 由按 `(semantic_tuple_id, product_tuple_id)` 排序后的 canonical tuple records
计算并保留 occurrence count；不得用普通 set hash 丢失重复 multiplicity。

总体空间为多个互不丢失的合法产品并集：

```text
Executable tuples
= union(
    grammar branch
    × compatible object domain
    × compatible relation/table domain
    × compatible signature/type domain
    × independent state/privilege domain
  )
  + isolated negative products
  + transaction products
  + concurrency/external products
  + parser and implementation boundaries
```

最终数量只能在完整公式和兼容过滤后得出。不能预先指定“生成 N 条”，也不能因结果为
几千或几万而删减产品。

### 7.11 Atom 编译合同

每个合法 tuple 精确编译为一个 atom：

```yaml
atom_id: string
statement_key: string
product_id: string
product_tuple_id: string
semantic_tuple_id: string
target_intent_id: string
grammar_assignments: {}
factor_assignments: {}
inventory_assignments: {}
derived_axes: {}
risk_obligation_ids: []
credited_obligation_ids: []
context_only_obligation_ids: []
outcome: success | expected_failure
primary_reason: null
expected_sqlstate: "00000"
check_order_rank: null | nonnegative_integer
fixture_requirements: {}
pre_state: {}
target_intent: string
observable_assertion: {}
post_state: {}
cleanup_requirements: {}
execution_harness: single_session_multiphase
source_evidence: []
```

硬约束：

- assignment 容器必须是 map，键在各自 namespace 内唯一；inventory key 使用第 3.7 节完整
  `INV-<64hex>` obligation ID，不能用可能重名的裸 member；
- 对该 branch 适用的每个 grammar production key 恰好一个值；互斥 grammar value 不能在同一
  atom 同时取得信用；
- 对该 branch 适用的每个 canonical factor key 恰好一个值；不适用 key 留在 ledger/N/A，
  不能被迫塞入 atom；
- `derived_axes` 同样是单值 map；一个 key 不能以 list、重复 token 或逗号拼接伪装多值；
- 多个设置形成的环境真值写入不同 axis 或 derived axes，不能让同一 factor 多值；
- 一个 expected-failure atom 只有一个 primary reason；
- success atom 必须 `expected_sqlstate=00000` 且 `primary_reason=null`；expected-failure atom
  必须使用非 `00000` 的五位 SQLSTATE，并与 primary reason resolver 的结果完全一致；
- 按 PostgreSQL 实际检查顺序归因，被更早错误遮蔽的条件不得取得覆盖信用；
- `credited_obligation_ids` 是本 atom 真正证明的 obligation；仅用于构造环境却被首因遮蔽的
  assignment 放入 `context_only_obligation_ids`，永不参与 coverage ledger 计数；失败 atom 必须
  记录首因的 check-order rank/resolver；
- 错误必须发生在目标阶段，setup 意外失败不算目标负例；
- atom 先具有 fixture、target、oracle、cleanup 和 harness，才能进入 mapping；
- 一个物理程序若覆盖多个同 factor 值，必须拆成多个独立 atom/subcase，不能靠
  `covered_values` 注释替代。
- 后置 `obligation-witness-index.json` 以 GRM/FOB/INV/RISK logical ID 为 key，把每个 credited
  obligation 绑定 atom、预期 subcase/phase、renderer field 和 coverage credit；context-only
  binding 明确标 false。Validator 必须在实际 SQL/harness 中解析并形成
  `actual-witness-report.json`，不接受注释。

Tuple/atom 守恒不直接比较不同记录结构。规范投影函数
`atom_to_interaction_projection_v1(atom)` 只保留 source ITUP/STUP ID 和 interaction assignment，
其 resolver version/SHA 在 input lock 中冻结。Validator 比较：

```text
executable interaction multiset
= multiset(atom_to_interaction_projection_v1(atom) for every atom)
```

### 7.12 生成前守恒门禁

只有以下条件全部成立，状态才可进入 `generation_allowed`：

```text
official grammar ledger complete
canonical factor ledger complete
all applicability decisions complete
all applicable type selectors reconciled
all mandatory risks reconciled
all obligations classified in intent-axis ledger

candidate interaction multiset
= executable ⊎ impossible ⊎ justified-NA interaction multisets
product included multiset = executable interaction multiset

executable tuple count  = executable atom count
atom projection multiset = executable interaction multiset
each executable semantic interaction maps to exactly one atom
duplicate canonical assignment = 0
all credited obligations have witness bindings
context-only obligations receive zero coverage credit
unresolved renderer = 0
unresolved oracle = 0
unresolved cleanup = 0
unresolved harness = 0
packing conservation = exact
global handoff closure = validated
```

## 8. Fixture、SQL 与 Oracle 生成合同

### 8.1 固定 case program 阶段

以下顺序是“每个 subcase”的逻辑阶段，不等同于每个物理 program 只能出现一组。未装箱时一个
program 只有一个 subcase；装箱时允许共享阶段 1–6，然后对每个 subcase 按 mapping 顺序重复
阶段 7–10，最后执行共享或逐 subcase 的阶段 11–12：

```text
1. Huawei header 与覆盖追踪信息
2. 必需的 session settings
3. 幂等 pre-cleanup
4. schema/role/type/function 等依赖 setup
5. relation/table/column fixture
6. 确定性数据 setup
7. 目标操作前状态快照
8. 唯一目标操作
9. SQLSTATE 或目标结果捕获
10. 行为、目录和不变量 oracle
11. 反向依赖顺序 cleanup
12. cleanup oracle
```

每个 assignment 必须在 `fixture/target/oracle/harness` 中拥有机器可定位的 witness。只在
header 或注释中出现不得取得覆盖信用。

### 8.2 Relation/table/column fixture

适用时必须显式绑定：

```text
relkind, relpersistence, partition_role, partition_strategy,
inheritance_role, access_method, column type member,
NULL/default/constraint state, index/trigger/dependency state, data profile
```

每张表至少具有：

- 稳定主键；
- 正在测试的类型列；
- 可验证状态的辅助列；
- 明确的 NULL/NOT NULL；
- 适用的 DEFAULT、CHECK、UNIQUE；
- 明确列清单的确定性数据；
- 显式查询投影和 ORDER BY。

“完整列结构”表示计划声明的每个列、类型、约束和状态都真实进入 SQL，而不是所有用例
机械复制同一张固定五列表。

### 8.3 Routine 与非列类型 fixture

routine 参数、返回、状态类型、cast source/target、operator left/right 等必须绑定独立
`type_role`。类型偶然出现在辅助表中不能取得 signature/type-binding 覆盖信用；oracle
必须验证真实目录身份、重载解析和适用时的实际调用。

### 8.4 Oracle 合同

成功 atom 至少具有：

- 行为 oracle；
- 对象身份或目录 oracle；
- 不应变化字段的不变量 oracle；
- cleanup oracle。

失败 atom 至少具有：

- 精确 SQLSTATE；
- 错误发生在目标阶段的证据；
- 目标对象完整状态未变；
- session 可继续使用；
- cleanup 成功。

RENAME、OWNER、SET SCHEMA 等操作在目标前捕获身份，目标后验证 OID 是否保持、允许变化
字段、必须保持字段、`pg_depend/pg_shdepend` 变化和对象实际可用性。输出使用归一化布尔值，
禁止输出裸 OID、PID、时间、物理路径、随机数或未排序集合。

禁止以 `SELECT true`、通用 `count(*)` 或仅查询对象名称代替能区分目标分支的真实 oracle。

### 8.5 Expected failure 合同

- 每个失败 subcase 只制造一个 primary reason；
- 其他权限、对象和类型条件必须配置为有效，除非它们属于被验证的检查顺序 tuple；
- 检查顺序 tuple 仍只给最先实际触发的 canonical failure value 覆盖信用；
- expected failure 不放入一个会因错误进入 aborted 状态的大事务，除非事务失败状态本身是
  目标；
- 失败后立即验证完整 snapshot 不变。

### 8.6 Cleanup 合同

- pre-cleanup 和 final cleanup 都必须幂等；
- 按依赖 DAG 逆拓扑删除；
- RENAME/SET SCHEMA/OWNER 后按真实最终身份清理；
- 清理角色前先 RESET ROLE 并处理 owned objects；
- `CASCADE` 只有在它是计划内 cleanup factor 时使用；
- cleanup 优先不再执行同类目标 statement；确实无法避免时必须使用第 10.4 节的显式授权、
  phase 隔离和 `coverage_credit=false`；
- 表脚本满足项目 output style 对首尾清理的更严格要求。

### 8.7 禁止生成的内容

- unresolved `{placeholder}` 或 EBNF；
- `pg_sleep` 作为同步手段；
- `\!`、未被第 9.2 节窄化授权的 host program、真实凭据或任意环境路径；
- 随机数据和不稳定输出；
- comment-only concurrency/restart；
- setup 中的第二条目标操作；
- 因子 metadata 与真实 SQL 状态不一致；
- 通过复制 SQL 或无判断 filler 增加数量。

## 9. 多 SQL、多会话与外部事件

执行模型只能为：

```text
single_session_multiphase
multi_session_barrier
restart_or_external_event
```

单会话多阶段使用一个 SQL case program。

多会话 atom 必须生成一个逻辑 bundle：

```text
<CASE-ID>/
├── harness.json
├── setup.sql
├── session_a.sql
├── session_b.sql
├── verify.sql
└── cleanup.sql
```

需要更多会话时按稳定字母扩展。`harness.json` 必须冻结 session 数、阶段、barrier、执行
顺序、允许并行的步骤、lock/wait 预期、超时、唯一目标事件、oracle 和无条件 cleanup。

v2 `harness.json` 使用以下规范结构：

```yaml
schema_version: 1
harness_id: string
runner: {id: string, version: string, sha256: sha256_hex}
total_timeout_ms: positive_integer
sessions:
  - session_id: string
    role_fixture_id: string
    connection_profile_id: string
phases:
  - phase_id: string
    kind: setup | session_sql | barrier | target | verify | cleanup
    session_id: controller | string
    file: relative_path | null
    depends_on: []
    timeout_ms: positive_integer
    run_mode: foreground | asynchronous
    operation_id: string
    atom_id: string
    statement_key: string
    expected_outcome: success | expected_failure | not_applicable
    expected_sqlstate: null | sqlstate5
    coverage_credit: boolean
    join_of_phase_id: null | string
    cancel_of_phase_id: null | string
barriers:
  - barrier_id: string
    participant_phase_ids: []
    release_condition: all_arrived | controller_signal | catalog_predicate
    predicate_file: relative_path | null
    expected_boolean: true | null
target_phase_ids: [nonempty]
primary_target_phase_id: string
cleanup_phase_id: string
cleanup_policy: always
```

所有 `session_id/phase_id/operation_id` 引用必须存在且唯一。依赖图必须无环且每 phase 可达。
SQL phase 的 success/failure 与 SQLSTATE 遵守第 7.11 节；纯 barrier/join/cancel phase 使用
`not_applicable/null`，不得伪造 SQLSTATE。
Runner 通过结构化 arrive/release event 同步，禁止用
`pg_sleep`；`catalog_predicate` 只能执行计划内的稳定布尔查询，并以有界 event-loop polling
等待。Asynchronous phase 必须有后续 `join_of_phase_id` 或 `cancel_of_phase_id` 路径。任一 phase 或总超时后 runner 取消
未完成命令、执行 `cleanup_policy=always`，并产出可归因 timeout/failure report。一个 atom
仍只有一个 target intent；该 intent 所需的所有 session target phases 必须显式列出且各执行
一次，其中只有 `primary_target_phase_id` 获得该 statement atom 的目标语句覆盖信用，其他
phase 是并发前置/对手动作并单独绑定 risk witness，不能由 renderer 暗加命令。

适合 PostgreSQL isolation tester 的场景可以由计划选择 `.spec`，但生成 Agent 不得临时
改变 harness。

### 9.1 Restart/external event harness

重启、数据库级对象、实例级设置、故障恢复和外部 capability 使用独立
`external-event-harness.json`，不得塞入不含 event 的普通多会话 manifest：

```yaml
schema_version: 1
harness_id: string
atom_id: string
statement_key: string
runner: {id: string, version: string, sha256: sha256_hex}
authorization_profile_id: string
environment_profile_id: string
disposable_environment_required: true
allowed_target_hosts: [localhost_or_private_profile_ids]
capabilities: []
resource_budget:
  total_timeout_ms: positive_integer
  max_restarts: nonnegative_integer
  max_backend_terminations: nonnegative_integer
  max_disk_bytes: positive_integer
stages:
  - stage_id: string
    kind: setup_sql | probe_sql | target_sql | external_event | reconnect | verify_sql |
          restore_event | cleanup_sql
    depends_on: []
    timeout_ms: positive_integer
    operation_id: string
    file_or_event_ref: string
    expected_outcome: success | expected_failure
    expected_sqlstate: sqlstate5 | null
    coverage_credit: boolean
event_allowlist:
  - event_id: string
    event_type: cluster_restart | backend_terminate | config_reload | config_restart |
                database_create_drop_controller | capability_probe | filesystem_fault |
                network_fault | fixed_program_fixture
    parameters: {}
    stop_condition: object
    restore_operation_id: string
primary_target_operation_id: string
restore_policy: always
cleanup_policy: always
```

Event parameters 只能引用冻结 environment/fixture ID，不能接受运行时任意 host、shell 或路径。
Runner 默认只允许 localhost、私有/容器 profile；每个事件有上限、timeout、停止和 restore。
目标 statement 的 SQL coverage credit 只归 `primary_target_operation_id`；controller、恢复和
cleanup 不取得目标覆盖信用。静态阶段只能证明 manifest 完整并声明待执行，不能伪造外部
事件已经完成。

### 9.2 Route-specific safety policy

现有 output policy 是 baseline，不足以同时表示全部 183 条语句。v2 必须新增并冻结
`skills/pg-sql-generation/references/common/route_safety_policy_v2.yaml`，优先级固定为“baseline
全局禁止，v2 仅对匹配 route/operation ID 给窄化例外，未列出仍禁止”：

- `serial_sql/parallel_sql/multi_session` 继续禁止 `CREATE/DROP DATABASE`、实例持久设置、
  `COPY PROGRAM`、host shell 和不可恢复故障；
- `external_isolated/restart_external` 只能在 disposable 授权环境执行 manifest 明列的目标或
  cleanup，例如数据库 create/drop、`ALTER SYSTEM`、固定 benign PROGRAM fixture；
- `COPY PROGRAM` 只能引用 runner 提供且按 SHA 固定的测试 helper，不接受任意用户命令；
- `\!` 和 renderer 注入任意 host command 在所有 route 仍禁止；
- validator 必须逐 operation 核对 policy decision、authorization、budget、restore 和 cleanup。

这样“全语句覆盖”不会被旧 policy 静默删除，也不会把窄化授权扩展到普通 regress route。

## 10. 无损装箱

### 10.1 默认策略

默认：

```text
1 executable atom = 1 subcase = 1 execution container（SQL program 或 harness bundle）
```

不为了减少数量强行合并。只有 atoms 全量展开并通过守恒后，才允许可选装箱优化。
无论是否合并，都必须产生 `packing-plan.json`；默认计划是一对一映射，不能省略该 artifact。

`packing-plan.json` 至少包含：

```yaml
atom_to_subcase: {atom_id: subcase_id}
subcases:
  - subcase_id: string
    atom_id: string
    program_id: string
    bundle_id: null | string
    order_in_container: positive_integer
containers:
  - container_id: string
    kind: sql_program | multi_session_bundle | external_event_bundle
    ordered_subcase_ids: []
    fixture_transition_ids: []
    atom_multiset_sha256: sha256_hex
conservation:
  atom_count: nonnegative_integer
  subcase_count: nonnegative_integer
  mapped_atom_multiset_sha256: sha256_hex
```

Packing 在 mapping/sharding 前完成；一个 container 整体只属于一个 shard，不能跨 shard 切分。
v2 初版禁止 multi-session 和 external-event atoms 互相装箱，也禁止将它们与普通 SQL program
装箱；这些 route 固定一 atom/一 bundle，后续如开放必须升级 packing schema/version。

### 10.2 Fixture signature

可装箱 atom 必须拥有相同或兼容的 fixture signature，至少包含：

```text
PostgreSQL compatibility profile
execution harness and session count
role/ACL topology
object/relation/table/type topology
data profile
pre-state and post-state
transaction envelope
external capabilities
cleanup model
```

### 10.3 装箱兼容条件

必须全部满足：

- fixture signature 兼容；
- execution harness 和 transaction envelope 相同；
- subcase 间无状态污染；
- 每个 subcase 有独立 ID、目标操作和 oracle；
- 每个 subcase 前状态可由前一 post-state 确定到达；
- 任一 subcase 失败仍能单独定位和清理；
- 装箱前后 atom 多重集合完全相等。

禁止混装不同 primary failure、session 数、不可兼容事务状态、会相互改变对象身份的 atom，
以及依赖前一 subcase 成功才能 cleanup 的程序。

### 10.4 目标操作次数

每个 subcase 的目标行为必须精确执行一次。默认一 atom 一文件时，文件中目标 statement
的 `target` phase 必须精确出现一次；装箱后按 subcase marker 和 phase marker 分段计数。
Cleanup 优先使用中性命令。DROP、事务控制等语句若无法不用同类命令完成幂等清理，
`cleanup_requirements` 必须显式列出被授权的 cleanup operation、理由和
`coverage_credit=false`；validator 分别统计 target-phase 和 cleanup-phase，只有前者取得
覆盖信用。多会话对手操作同理：只能由 frozen harness 明列，若不是本 atom 的 primary target，
必须 `coverage_credit=false` 或拥有另一个独立 atom/subcase。任何未授权的同类目标语句仍是错误。

## 11. Mapping、编号与分片

### 11.1 冻结 mapping

SQL 生成前为当前 statement revision 的全部 executable atoms 分配：

- statement-local ordinal；
- 明确的 `atom_id -> subcase_id -> program_id/bundle_id`；
- container 内 subcase 顺序和 SQL program/harness bundle 相对路径；
- 对象前缀；
- shard ID；
- execution profile；
- schedule class。

Mapping 每行以 subcase 为粒度，必须保存 atom、container、shard 和 schedule 外键；同一
container 的所有 subcase 必须拥有同一 shard ID。Atom、subcase、container 和 shard ID 都按
第 3.7 节 codec 生成，物理 case label 另用可读 ordinal。外键缺失、一个 atom 多 subcase、
一个 subcase 多 container 或 container 跨 shard 都使 freeze 失败。

`mapping.json` 冻结后禁止插入、删除或重排编号。覆盖变化必须生成新 revision/run。

Case ID 使用 namespaced ordinal，例如 `S001-C000001`；文件名和对象前缀由 statement key、
revision 和 local ordinal 确定。顺序生成期间不预占尚未规划 statement 的全局 offset。最终
全局包按 `(statement_inventory_ordinal, statement_local_ordinal)` 生成只读 global ordinal
索引，但不重命名既有文件。这样后续 statement 的新 revision 不会迫使其他 statement 重编号。

正式 payload 使用版本化统一目录，避免覆盖旧 revision：

```text
artifacts/regress/by-factor/<run-id>/<category>/<domain>/<statement>/<revision-id>/
└── payload/
    └── shards/
        ├── S00001/
        │   ├── programs/
        │   ├── bundles/
        │   └── payload-manifest.json
        └── S00002/...
```

每个 shard 独占一个最终目录，任何两个 shard 不写同一个 `sql/harness/schedules` 共享目录。
逐 statement schedules 在全部 shard validated 后写入
`executions/<revision-id>/<global-revision-id>/schedule-staging/`，验证后一次原子 rename 为
`executions/<revision-id>/<global-revision-id>/schedules/`。最终 package 引用 shard payload 和
schedule 的相对路径/
SHA，不复制或改名。`current.json` 只提供 UI/计划视图指针，validator 永远按 package 内显式
revision 路径读取。

Schedule class 是固定枚举：

```text
serial_sql
parallel_sql
external_isolated
multi_session
restart_external
```

每类绑定 v2 runner ID/version/SHA；`parallel_sql` 还必须绑定互斥资源集合并由 scheduler
证明批内无冲突。未知 class 或缺 runner 使 plan validation 失败。

### 11.2 分片

大规模只通过有界 shard 控制。`mapping.json.shard_policy` 必须冻结
`max_case_programs_per_shard`；v2 默认值精确为 500，但可在 approval 前显式修改并参与 plan
SHA。它不是覆盖上限。单个 test point 可以按规范 tuple 顺序拆成多个 shard，仍保持
statement-local ordinal。

Shard 状态：

```text
planned -> claimed -> generating -> validating -> validated
               \          \             \-> failed
                \----------\----------------> failed
failed -> planned（显式 retry，attempt + 1）
```

默认一次只领取一个 shard。生成 Agent 只能写当前 shard 的已分配文件；shard 未 validated
前不得领取下一片。重试沿用原 mapping、编号和前缀。

`jobs.json` 每个 shard 至少记录 immutable assignment SHA、state、attempt、claimed_by、
lease_expires_at、last_heartbeat、staging_relative_path、published_payload_sha 和 report SHA。
Claim 必须通过文件锁或 compare-and-swap 原子完成；同一 shard 同一 attempt 只有一个 owner。
Runner 在 lease 的三分之一周期内 heartbeat，lease 长度和 heartbeat interval 固定在
execution policy 并绑定 SHA。

每个 attempt 只写：

```text
executions/<revision-id>/<global-revision-id>/attempts/<shard-id>/A<attempt>/staging/
```

生成完成后 validator 在 staging 内验证完整 container 分配集合，并先写入、fsync
`publish-candidate.json`。为保持 retry/global reuse 确定性，marker 的 semantic payload 精确绑定
run、local revision、shard、assignment SHA、payload manifest SHA、validation semantic report
SHA 和预期最终相对路径，不包含 global revision、attempt、owner 或时间；这些只在 jobs
operational record。之后才把整个 staging 目录以一次同文件系统原子 rename 发布为该 shard 独占的
`payload/shards/<shard-id>/`，随后 fsync 父目录，并在 jobs 锁内把 report/job state 提升为
validated。目标目录在正常首次发布前必须不存在，不存在逐文件合并或半片可见状态。

若进程在 rename 成功后、report/job state 更新前崩溃，recovery 不得直接把该 job 标 failed。
它必须先检查目标目录：若存在同 assignment 的 `publish-candidate.json`，则从实际字节重新验证
完整 payload/marker/report SHA；完全一致时在 jobs 锁内执行 orphan-publish promotion，补写
immutable report 并记录 `state=validated, recovered_orphan_publish=true`。若 marker/字节不一致，
recovery 在锁内把整个目标目录原子 rename 到该 attempt 的 quarantine 路径，fsync 父目录并标
failed，随后显式 retry 才能使用原最终路径。该流程覆盖 crash-before-rename、
crash-after-rename 和 crash-after-report-before-job-state 三个窗口。

同一个 local plan revision 被新的 global revision 复用时，若目标 shard 已存在，只能从实际
字节重算 manifest 并证明与 mapping/expected payload SHA 完全相同后记录
`state=validated, reuse=true`；`reused_validated_payload` 不是额外状态，`all_shards_validated`
仍只接受 `state=validated`。禁止覆盖。普通 lease 到期且目标目录不存在的
`claimed/generating/validating` 由 recovery 命令在锁内标记 failed，保存 attempt 诊断，再由
显式 retry 创建新 attempt；旧 staging 只读隔离，不能被新 attempt 复用。`validated` job 没有
retry，除非创建新 plan revision。

## 12. 静态验证与守恒证明

### 12.1 四级守恒

语法守恒：

```text
official grammar values
= covered + expected_failure + justified_na
missing = duplicate = pending = 0
```

因子和库存守恒：

```text
derived factor obligations + candidate inventory obligations + mandatory risks
= reconciled obligations
missing = duplicate = pending = 0
```

组合守恒：

```text
candidate interaction multiset
= executable ⊎ impossible ⊎ justified-NA interaction multisets

executable interaction multiset
= product included semantic multiset
= atom_to_interaction projection multiset
```

装箱守恒：

```text
executable atom multiset
= packing-plan atom multiset
= mapped subcase atom projection multiset
= validated subcase multiset
missing = duplicate = unexpected = 0
```

报告必须分别给出 grammar、factor、inventory、tuple、atom、subcase、SQL file、harness
bundle 和 N/A 数量，不能用 SQL 文件数代替覆盖证明。

### 12.2 Shard 静态门禁

验证器必须重新读取实际字节并检查：

- 分配文件零缺失、零额外；
- 连续编号、对象前缀、Huawei header、UTF-8/LF/EOF；
- 追踪 marker 与 mapping 一致；
- 每 subcase 的 primary target phase 精确一次；额外 target/cleanup phases 与 frozen plan
  完全一致且没有额外覆盖信用；
- factor assignment 每键单值；
- SQLSTATE 与计划一致；
- relation/table/type/signature fixture 与 mapping 一致；
- oracle、pre-cleanup、final cleanup 与计划一致；
- 无 placeholder、`pg_sleep`、未授权 shell/program escape 或不稳定输出；
- harness session/barrier/phase 与计划一致；
- external event、authorization、budget、restore 与 route-specific safety policy 一致；
- planned witness index 的每个 credited binding 在实际 target/fixture/oracle/harness 字节中存在，
  context-only binding 零 coverage credit，并生成 immutable `actual-witness-report.json`；
- SQL/bundle SHA 与 shard report 绑定。

失败时不得写入 `validated`。

### 12.3 确定性再生成

同一冻结计划必须在两个空目录独立生成，并满足：

```text
generation_A_sha_map = generation_B_sha_map
```

比较对象只包括 renderer 从同一个 approved mapping 生成的 payload：SQL、harness manifests
和由 mapping 派生的 schedules。Mapping 是冻结输入，不作为 renderer 输出重复比较；jobs、
attempt、lease、运行日志和 shard reports 属于执行状态，也不混入 payload determinism。

`regeneration-report.json` 绑定 plan/approval/mapping SHA、两个隔离 scratch root 的文件相对
路径→SHA map、schedule SHA 和 equality result；scratch 绝对路径不进入 semantic payload。
Package、validation 和 report 生成器分别使用第 13.1 节的 canonical semantic projection 做
确定性测试，排除 attempt、lease、heartbeat 和 wall-clock metadata。

## 13. 哈希证据链与防篡改

证据链固定为：

```text
input-lock
  -> readiness
  -> grammar/factor/applicability/N-A/risk ledgers
  -> intent-axis ledger
  -> interaction universe
  -> products
  -> atoms
  -> fixture plan
  -> packing plan
  -> frozen mapping
  -> obligation witness index
  -> plan-content manifest and readable plan view
  -> plan validation
  -> global handoff validation
  -> approval / generation contract
  -> immutable shard assignments
  -> shard payload manifests and reports
  -> actual witness report
  -> immutable jobs-final snapshot
  -> deterministic regeneration report
  -> schedules
  -> package
  -> final validation
  -> selected-statement/global validation/package/progress
```

每次读取历史完成项和每次渲染全局 MD 都必须从当前文件重新验证完整哈希图。不能只相信
`progress.json.status`。validated SQL、mapping 或 report 改变后，旧 package 和 checkbox
立即失效；不得原地重写证据后仍沿用旧 approval。

### 13.1 Artifact envelope 与 semantic hash

每个规范 JSON artifact 必须具有：

```yaml
schema_version: integer
kind: string
artifact_id: string
predecessors:
  artifact_id: sha256_hex
semantic_payload: object
semantic_sha256: sha256_hex
operational_metadata: null | object
```

`semantic_sha256` 精确定义为：

```text
SHA256(UTF8("FSCR_ARTIFACT_V2\0") ||
       JCS({schema_version, kind, artifact_id, predecessors, semantic_payload}))
```

JCS 是 RFC 8785 JSON Canonicalization Scheme；禁止 NaN/Infinity，计划数据禁止浮点。
`predecessors` 的 key 是直接前驱 artifact ID、value 是从当前字节重算的完整 semantic SHA。
显示时间、绝对路径、claimed_by、attempt、lease 和 heartbeat 只能进入非规范
`operational_metadata`，不得进入 semantic payload，也不得影响 semantic SHA。

本规格不再使用未定义叶序/奇数叶规则的 Merkle tree。凡需汇总多个 artifact，统一使用：

```text
manifest_digest(domain, artifacts)
= SHA256(UTF8(domain + "\0") ||
         JCS(sort_by_artifact_id([
           {artifact_id, semantic_sha256}, ...
         ])))
```

排序按 artifact ID 的 UTF-8 byte order，record 恰好只有上述两个字段，重复 artifact ID 或同 ID
不同 SHA 直接失败。Domain 是本节明列的固定 ASCII 字符串，不得由调用方自定义。

哈希根按以下无循环顺序计算：

```text
plan_content_root = semantic SHA of plan-content-manifest.json
  whose sorted artifact list is exactly:
  input-lock, readiness, grammar-ledger, factor-ledger, applicability, na-ledger,
  risk-ledger, intent-axis-ledger, interaction-universe, products, atoms,
  fixture-plan, packing-plan, mapping, obligation-witness-index

validated_plan_root
  = manifest_digest("FSCR_VALIDATED_PLAN_V2",
                    [plan-content-manifest, plan-validation])

generation_contract_root
  = semantic SHA of generation-contract.json
```

`plan-content-manifest.json` 以前述 15 个 artifact 为直接 predecessors；它不包含自身。
`coverage-plan.md` 在 content root 已知后确定性渲染，`plan-validation.json` 以 content manifest
为 predecessor，并在 payload 中绑定 MD raw-byte SHA、mapping SHA、validator version/SHA、
全部 schema/守恒结果。Approval 在全局 handoff closure 后创建，审批对象是
`validated_plan_root + handoff-validation SHA`；它必须绑定明确审批结果。Renderer 必须同时验证
`generation_contract_root` 与当前字节重算结果相同。这样 ledger 不回填 atom、validation 不
进入自己验证的 content root、approval 不进入自己审批的 root，三类循环都被消除。
Approval artifact 存在所选 `global-revisions/<gNNNN>/approvals/<statement>.json`，不回写 local
plan revision；同一 local plan 被另一 global revision 选择时必须生成新的 global-scoped approval。

Approval 之后由控制器创建真正的 artifact envelope：

```text
global-revisions/<gNNNN>/generation-contracts/<statement>.json
```

它的直接 predecessors 精确为 plan-content-manifest、plan-validation、global-handoff-validation
和 approval，semantic payload 固定保存 `validated_plan_root`、handoff root、mapping SHA、
renderer/runner/policy SHA 与 `generation_allowed=true`。它的 artifact semantic SHA 就是
`generation_contract_root`，因此 renderer/package 可以引用真实 artifact，而不是引用一个无
envelope 的裸 digest。任一 predecessor 漂移都使 contract artifact 和后继 package 失效。

Mutable `jobs.json` 只属于 operational state，不能作为 package 的规范前驱。全部 shard validated
后生成不可变 `jobs-final-snapshot.json`；package 的直接 predecessors 必须包括 generation
contract、所有 shard payload/report manifests、`actual-witness-report.json`、jobs final snapshot、
`regeneration-report.json` 和 schedule manifest。Final validation 直接依赖 package 和所有当前
payload manifest。Regeneration report 变化会使 package/final validation/checkbox 全部失效。

每个后继 artifact 必须精确列出所有直接 predecessors。Validator 从当前字节重算每层 SHA
和 root，不接受 artifact 内自报 hash。

### 13.2 逐语句 evidence 拓扑

逐语句静态 evidence 至少为：

```text
artifacts/intermediates/full-statement-coverage-plan/<run-id>/<statement>/
├── current.json
├── plan-revisions/<revision-id>/
│   └── <第 4.3 节的不可变计划文件>
└── executions/<revision-id>/<global-revision-id>/
    ├── jobs.json
    ├── shards/
    ├── attempts/
    ├── reports/S00001.json
    ├── reports/full-validation.json
    ├── actual-witness-report.json
    ├── jobs-final-snapshot.json
    ├── regeneration-report.json
    ├── schedules/
    ├── package.json
    ├── validation.json
    └── execution-summary.md
```

## 14. Package 与运行证据边界

静态 package 必须明确：

```json
{
  "kind": "regress_input_package",
  "runtime_status": "not_run_static_sql_only",
  "expected_output_included": false,
  "execution_or_comparison_performed": false
}
```

`serial_sql/parallel_sql` 生成 pg_regress schedules；`external_isolated/multi_session/
restart_external` 生成版本化 runner manifests，不伪装成 pg_regress 单文件 test。Package 分别
列出各 route 的 case/atom 数、相对路径、runner SHA 和 payload SHA，所有 route 的 atom 并集
必须等于 executable atom multiset。

数据库运行证据独立保存，至少绑定 PostgreSQL 精确版本、build capability、初始化参数、
package SHA、harness 版本、成功数、预期失败数、非预期错误、false oracle、cleanup 结果和
日志 SHA。

不可变 runtime 证据保存为：

```text
artifacts/intermediates/full-statement-coverage-plan/<run-id>/<statement>/
└── runtime/<revision-id>/<global-revision-id>/<package-sha256>/RNNNN/
    ├── execution-manifest.json
    ├── route-results/
    ├── logs-manifest.json
    ├── cleanup-report.json
    └── runtime-validation.json
```

`runtime-current.json` 只保存指针；每次运行分配新 RNNNN，不覆盖历史。Runtime validation 的
predecessors 必须包含精确 package artifact 和所有 route/log/cleanup manifests。

静态状态、运行状态分开：

```text
planning_state: statically_validated -> packaged
runtime_state: not_run -> running -> runtime_executed -> runtime_verified
                              \-----------------------> runtime_failed
```

`running` 前置条件是 `planning_state=packaged` 且 runtime record 绑定 current package SHA；
`runtime_verified` 还必须证明所有已执行 atom、oracle 和 cleanup 对该 SHA 通过。外部
capability 缺失不能删除 atom，只能保留对应 execution profile 为待执行。

## 15. 全局计划与自动勾选

全局计划由证据确定性渲染。状态符号：

```text
[ ] discovered/planning/stale/failed（origin=legacy_import 也相同）
[~] generated 或部分 shard validated
[x] packaged 且完整哈希图复验通过
[R] runtime_verified 且运行报告绑定 current package SHA
```

逐语句只有同时满足以下条件才能 `[x]`：

```text
readiness_passed
grammar_reconciled
factors_reconciled
applicability_reconciled
risks_reconciled
interaction_universe_frozen
products_partitioned_without_loss
atoms_reconciled
packing_conservation_passed
mapping_frozen
obligation_witness_index_validated
local_plan_validation_passed
global_handoff_closure_validated
plan_approved
all_shards_validated
actual_witness_validation_passed
deterministic_regeneration_passed
package_validation_passed
hash_graph_current
```

既有 DML、Cursor、DCL、ABORT、ALTER AGGREGATE、ALTER COLLATION 和其他旧包统一从
`origin=legacy_import, planning_state=discovered` 开始。只有补齐/导入所有 v2 账本并通过同一
状态机到 `packaged` 后才能显示 `[x]`；不存在跳过门禁的 `legacy_audited` 终态。SQL 数量、
旧 package 标记或一次性测试通过不能替代该审计。

## 16. 全局完成条件

选定 global revision 的 183 条语句都达到 `packaged` 后，才能生成该 revision 的唯一全局包：

```text
global grammar/factor/inventory obligations reconciled
global executable atom multiset mapped exactly once
all statement packages current
all jobs validated
global missing = 0
global duplicate = 0
global unexpected = 0
```

任一 statement 为 stale、failed、partial 或未 packaged，都禁止生成最终完成包。

全局包采用唯一的 manifest-only 拓扑，不复制 statement shard 中的 SQL/harness，也不再声明
含义冲突的第二份 `sql/` 或 `harness/`：

```text
artifacts/regress/<run-id>/<global-revision-id>/
├── batch.json
├── selected-statement-packages.json
├── global-mapping.json
├── schedules/
├── payload-index.json
├── validation.json
└── package.json
```

`payload-index.json` 逐项引用第 11.1 节 immutable statement shard/schedule 相对路径和 SHA。
Runner 只消费该 index；全局目录中不存在复制品。Global revision 一经发布只读；任何 statement
revision/package 变化创建新 gNNNN，并生成新全局路径。

## 17. 失败、恢复与变更管理

- Readiness 失败：修复输入资产，重新锁定；禁止 renderer workaround。
- Product 不守恒：修正 axis role、compatibility predicate 或 exclusion evidence。
- Atom 不守恒：修正编译器，不得复制或删除 atom 使数量相等。
- SQL 静态失败：保留 attempt 诊断；修 renderer/reference/policy 后因输入 SHA 变化创建新
  run/revision，禁止手工修改 frozen mapping 对应的正式文件。
- 输入漂移：新建 plan revision/run，旧 evidence 只读保留。
- 运行 capability 缺失：保持 static package，通过 execution profile 延后运行。
- 运行非预期错误：保留 SQL、日志和 package SHA，修复必须进入新 revision。

任何恢复操作都不能修改已冻结 mapping 中其他 shard 的编号或覆盖归属。

## 18. 每条语句 coverage-plan.md 的固定章节

逐语句可读计划必须完整显示：

1. identity、状态、兼容版本和 plan SHA；
2. 冻结输入路径与 SHA；
3. readiness 结果；
4. 官方语法账本和守恒；
5. canonical factor 账本和守恒；
6. object/relation/table/column/signature/type 适用性；
7. 12 类 mandatory risk；
8. 每个 product 的 axes、公式、predicate、排除 tuple 和 tuple SHA；
9. atom 数量、outcome 和 failure disposition；
10. fixture DAG、完整表列结构、角色/ACL、数据和 transaction/session；
11. target、oracle、cleanup 和 harness 设计；
12. atom→subcase→file mapping；
13. shard、schedule 和预计物理文件数量；
14. 全部门禁、阻断项、`plan_content_root` 和待验证/待审批对象；MD 禁止显示尚未产生的
    `validated_plan_root` 或 approval；
15. 预期 execution evidence 路径和所需 predecessor SHA。

MD 不得省略大列表后只写“同上”或“其余类似”。可以链接同目录规范 JSON，但必须显示
总数、守恒、哈希和每个异常/排除理由。

`coverage-plan.md` 在 content root 后、plan validation 前生成并绑定 raw-byte SHA；因此它只
显示 content root，不显示由其 SHA 间接决定的 validated root。Plan validation、validated root、
approval、实际文件、report、package 和 validation SHA 显示在
`executions/<revision-id>/<global-revision-id>/execution-summary.md` 以及全局进度视图中，避免
修改计划破坏 root。

## 19. 验收标准

本设计实现后必须证明：

1. 生成器在 approved plan 缺失时拒绝写 SQL；
2. 官方语法 optional、互斥项和列表基数零 missing；
3. canonical 9,978 source rows 按 statement 完整核账，所有 branch/context FOB obligations 另行
   完整核账；
4. candidate relation/table/type obligations 每成员/branch/role/context 恰有一个 disposition；
5. 七份 type inventory 被逐份审计，未被错误做成七维自由积；
6. branch consumer 独立 join 重建全部 FOB/INV 左侧，canonical intent partition 对角拆分检测为零；
7. intent-axis ledger 覆盖全部义务，interaction universe 不是由 products 自报；
8. 每个 product 的 candidate = included ⊎ excluded，所有 included 无损分区 executable
   interaction multiset；
9. 每个 executable interaction 精确产生一个 atom，atom projection 与 universe 相等；
10. grammar/factor/derived assignment 每键单值，expected failure 每 atom 一个首因；
11. credited/context-only obligation 分离，实际 witness report 零伪信用；
12. 每个 atom 有真实 fixture、target、oracle、cleanup 和 harness；
13. 多会话/重启义务不再以注释或普通单会话 probe 冒充；
14. 装箱前后 atom 多重集合守恒，container 不跨 shard；
15. shard 可中断、重试、整目录原子发布且不改变编号；
16. 两个空目录的确定性再生成 SHA map 相同；
17. delegated N/A 通过 183 条 local plan 的语义等价 handoff closure；
18. route safety policy 能覆盖受限语句且不扩大普通 route 权限；
19. 历史 SQL 或 regeneration evidence 漂移会自动撤销完成状态；
20. 几千或几万用例不会触发抽样、轮转或代表值降级；
21. 静态 package 与 runtime evidence 明确分离；
22. 只有全部门禁通过的语句能在全局 MD 中显示 `[x]`。

## 20. 明确禁止的旧做法

- SQL 先生成，plan/coverage evidence 后补；
- 只按 matrix 的局部 required values 宣称全因子覆盖；
- 只看每个 factor value 是否被某个 case ID 引用；
- 一个 case 的同一 factor 同时记多个 canonical value；
- expected status 与失败条件自由相乘；
- 把 helper table 当成全表/全类型覆盖；
- 以固定 `text/integer` 代表所有适用类型；
- 以 pairwise、轮转、随机或样本控制规模；
- 用注释冒充多会话、重启或外部事件；
- validator 只检查“至少有一条目标语句”；
- 已生成目录存在就手工勾选完成；
- 修改已验证 SQL 后仍复用旧 validation/package 状态。

## 21. 设计决策摘要

1. 完整性由 grammar、factor、inventory、tuple、atom 和 mapping 多级守恒证明。
2. 用例数是覆盖推导结果，不是输入指标。
3. 全笛卡尔积只用于彼此独立且兼容的语义轴；其他关系必须显式建模。
4. 类型七目录逐份穷举，只有独立 type roles 做条件积。
5. 计划和 mapping 先冻结并验证，approval 绑定二者后 renderer 才执行。
6. 默认一 atom 一 execution container；装箱只能在 atom 完整后无损进行。
7. 每个 subcase 目标操作精确一次，失败首因唯一，oracle 可区分。
8. 多会话和外部事件使用真实 harness，不伪造运行。
9. 分片解决规模和恢复问题，不通过删覆盖解决。
10. checkbox 是当前哈希证据图的派生结果，不是人工声明。
