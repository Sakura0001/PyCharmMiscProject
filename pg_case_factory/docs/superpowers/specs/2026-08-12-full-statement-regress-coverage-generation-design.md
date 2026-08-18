# 全语句 Regress 完整覆盖生成方法设计

## 1. 状态与决策

- 书面规格状态：`approved_design_pending_v2_implementation`；用户于 2026-08-17 批准方案 C
  “实际语义闭环证明”。
- 兼容目标：PostgreSQL 18.4。
- 控制合同：`full_statement_coverage_v2`；它是对现有 coverage/regress v1 合同的显式升级，
  不是现有 `pg-case regress` 可以直接消费的别名。
- 适用范围：`statement_support_inventory.yaml` 登记的全部 183 条语句，包括既有
  DML、Cursor、DCL 和已生成的 statement-cycle 用例。
- 当前执行边界：v2 基础设施、冻结 catalogs、semantic extractors 与负向合同测试全部通过前，
  禁止本全语句循环新增或重新生成正式 SQL/package。
- 核心决策：采用“契约驱动、先计划后生成”；用例数完全由覆盖空间推导，不设置
  人为上限，不允许 pairwise、随机采样、代表值替代或按目标数量裁剪。
- 规模决策：几千、几万乃至更多 executable atoms 都是正常结果。规模只能通过稳定
  分片、断点续跑和通过守恒证明的无损装箱处理。
- 非法输入决策：凡能形成实际输入并由 PostgreSQL parser、binder、权限检查或执行阶段拒绝
  的组合，都必须生成 `expected_failure`；只有目标输入在逻辑上不可构造或该 branch 确实
  不可观察的义务，才允许进入带证据的 intrinsic/delegated N/A 闭环。

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
statement-local subcase/container ordinals，不用逻辑 hash 取代可读编号。

### 3.8 计划赋值、实际赋值与三种完整性

“计划中出现因子”不等于“最终用例实现因子”。对每个 subcase `k` 必须同时保存：

```text
P(k) = approved plan 中的 context-qualified planned assignment
A(k) = 独立 extractor 从最终 SQL/harness 字节重建的 observed assignment
R(k) = RequiredSemanticAxes(statement, branch, canonical intent, semantic context)
RequiredFactorAxes(k) = R(k) 中 obligation_kind=factor 的投影
```

Axis identity 固定为：

```text
logical_id("AXI", [statement, grammar_branch_id, canonical_intent_class_id,
                   obligation_kind, factor_or_selector_id, context_id, semantic_role])
```

因此 `data_type:left_operand`、`data_type:right_operand`、目标列与辅助列、target phase 与
oracle phase 都是不同 axis/locus，不能因 factor 名称相同而合并。每次生成必须同时证明：

```text
# per-case totality
dom(A(k)) = dom(P(k)) = R(k)
forall axis in R(k): A(k)[axis] = P(k)[axis]

# suite marginal completeness
actual credited obligation IDs
= all covered and expected_failure GRM/FOB/INV/RISK obligation IDs

# suite interaction completeness
Bag(complete_interaction_projection(A(k), approved atom expected outcome/primary failure)
    for every executable subcase k)
= executable complete interaction record multiset
```

三个性质缺一不可。只证明每个 factor value 至少出现一次，不能推出独立轴的组合完整；例如
计划 `00,01,10,11`、实际 `00,00,11,11` 虽然边际值齐全，仍必须失败。`A(k)` 只能来自第
12.3 节的独立语义提取器；metadata、注释、文件名、case ID、计划 pointer 或 renderer 自报
字段不能产生 actual assignment 或 coverage credit。

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
artifacts/intermediates/full-statement-coverage-v2/<run-id>/global/
├── global-input-lock.json
├── statement-order.json
├── progress.json
├── current.json
└── global-revisions/<global-revision-id>/
    ├── selected-statement-revisions.json
    ├── handoff-ledger.json
    ├── handoff-validation.json
    ├── generation-order.json
    ├── approvals/<statement>.json
    ├── generation-contracts/<statement>.json
    ├── global-mapping.json
    └── publication-target.json
```

其中 `handoff-ledger.json` 对第 7.7 节 delegated N/A 做跨语句闭环；`progress.json` 只是当前
哈希图验证结果的缓存，不是完成真相源。`global-revision-id` 使用在 global 锁内单调分配的
`gNNNN`；每个 global revision 绑定 183 条明确的 statement revision。新 statement revision、
handoff closure 或 package 选择必须创建新的 global revision，不覆盖旧全局证据。
`global-input-lock.json` 的 semantic SHA 就是 `global_input_root_sha256`；它按第 13.1 节 artifact
规则提交全部 global inputs 的相对路径、byte SHA、semantic SHA 和版本。
`statement-order.json` 只冻结 canonical inventory order，属于 global input。由 delegated handoff
DAG 推导的顺序必须写入所选 global revision 的 `generation-order.json`，保存全部 edges、稳定
拓扑结果、inventory-ordinal tie-break 和 multiset SHA；UI 可以按 inventory order 展示，driver
只能按 generation order 领取 shard。Generation order 不参与 run-id/global-input-root，避免用
计划派生产物反向决定自己的 run 路径。
`publication-target.json` 只是绑定第 16 节唯一正式 global-validation/global-package
路径、artifact ID 和 SHA 的 current-pointer artifact，不得再保存第二份 validation/package
字节。唯一真相源在 `artifacts/regress/<run-id>/<global-revision-id>/`。
`global-mapping.json(kind=global-mapping)` 的直接 predecessors 精确为 global-input-lock、
statement-order、selected-statement-revisions 和所选 183 份 current statement `mapping.json`；其
semantic payload 从这些 mapping 独立汇总 global ordinal/path/index assignment 和多重集 SHA。
它禁止依赖 statement package、actual report、jobs、schedule、任何 publication index、
global-validation 或 global-package，因此不得通过反向边形成环。

Global control artifacts 的 direct predecessor 集合固定为：

- `selected-statement-revisions.json` 精确直接依赖 global-input-lock、statement-order，
  以及 183 条 statement 各自 current `plan-content-manifest` 和 `plan-validation`；它从
  这些当前字节重建 `(statement_key, revision_id, plan_content_root,
  validated_plan_root)` exact Bag，missing/duplicate/unexpected/stale 必须为零；
- `handoff-ledger.json` 精确直接依赖 selected revisions、所选 183 份 `na-ledger`、
  `plan-content-manifest` 和 `plan-validation`，并从 delegated N/A records 重建全部 source→owner
  edges；
- `handoff-validation.json` 精确直接依赖 global-input-lock、selected revisions、handoff
  ledger，以及所选 183 条 statement 的 grammar/factor/applicability/risk/N-A ledgers、
  obligation-witness-index、plan-content-manifest 和 plan-validation；它必须从 input-lock 绑定的
  equivalence/handoff resolvers 和当前 bytes 独立重算 owner 存在性、语义等价、无环与计划
  witness closure；
- `generation-order.json` 精确直接依赖 statement-order、selected revisions、handoff
  ledger 和 handoff-validation，只用 owner→source edges 与 inventory-ordinal tie-break 重算 exact
  183-statement topological order；
- 每个 `approvals/<statement>.json` 精确直接依赖 selected revisions、该 statement
  的 plan-content-manifest/plan-validation、global handoff-validation 和 generation-order，并明确绑定
  该 selected revision/validated root 的审批结果。

上述五类 artifact 全部禁止依赖 approval 之后的 generation contract、shard assignment/
payload/report、jobs、schedule、actual report、statement/global package 或 validation。Schema/validator
必须把 missing/extra predecessor 和任何这类反向边视为合同失败，不能只在 payload
里记一个未绑定的 plan SHA。

### 4.3 逐语句冻结计划

每条语句在生成 SQL 前必须具有：

```text
artifacts/intermediates/full-statement-coverage-v2/<run-id>/<statement>/
├── current.json
├── plan-revisions/<revision-id>/
│   ├── input-lock.json
│   ├── readiness.json
│   ├── source-universe.json
│   ├── source-consumption.json
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
    ├── normalization-policy.json
    ├── jobs.json
    ├── attempts/
    ├── reports/
    ├── published-payload-index.json
    ├── actual-factor-witness-report.json
    ├── actual-semantic-interaction-report.json
    ├── actual-handoff-validation.json
    ├── jobs-final-snapshot.json
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
2. 升级四个既有 scope、新增 `column_structure` scope，并加入 selector manifests、routine/type
   manifests、统一 N/A ledger 和逐成员 obligation decisions；
3. relation/table/column-structure/type/routine 目录之外，先实现 statement branch consumer、
   canonical target intent、PostgreSQL 18.4 check-order catalog、semantic extractor registry 与
   catalog-oracle allowlist，及其独立 join/partition/check-order/extraction/oracle-policy validators；
4. 全局 ID codec、factor branch/context obligations、intent-axis/interaction universe compiler；
5. grammar、risk、product partition、atom projection、packing、mapping、witness、approval 和
   hash-graph validators；
6. one-atom/one-subcase、multi-subcase packing 和目录式 harness mapping；
7. v2 shard lease、attempt、staging、恢复和 shard-owned 原子发布；
8. serial/parallel/external/multi-session/restart manifests、runner 和 route safety validator；
9. 两遍全局 planning/handoff closure 和 global revision/package；
10. actual factor witness 与 actual semantic interaction 两类报告、planned/observed 精确匹配、
    context-qualified per-case totality 和 suite tuple multiset validators；
11. v1 旧包只读 importer，导入结果必须带 `origin=legacy_import` 并从相同 v2 规划状态机起点
    审计；
12. CLI 的 `discover/compile-catalogs/plan-all/validate-plan/freeze-mapping/approve/generate/
    validate-artifacts/package/run/verify-global/report` 子命令；
13. 第 12.5 节全部负向合同测试，尤其是 unrelated `SELECT 42`、comment-only witness 和
    `00,00,11,11` 对角替换反例。

所有 v2 schema、canonicalization、predicate evaluator 和 runner 都必须绑定明确版本。v1 工具
不得对 v2 产物返回 PASS；v2 infrastructure contract tests 未通过时 readiness 必须失败。

### 4.6 V2 artifact schema registry 与 CLI

`full_statement_coverage_v2` 必须为下列 artifact kinds 分别注册 schema，不能用一个可接受任意
object 的宽松 envelope 代替：

```text
input-lock
current-pointer
statement-order
generation-order
progress
source-universe
source-consumption
readiness
catalog-oracle-allowlist
grammar-ledger
factor-obligation-ledger
na-ledger
risk-ledger
applicability
canonical-intents
intent-axis-ledger
interaction-products
interaction-tuples
atoms
fixture-plan
packing-plan
subcase-mapping
obligation-witness-index
plan-content-manifest
plan-validation
selected-statement-revisions
handoff-ledger
handoff-validation
approval
generation-contract
global-mapping
global-batch-manifest
selected-statement-packages
global-mapping-index
global-by-factor-manifest
global-schedule-index
global-payload-index
global-validation
global-package
shard-assignment
shard-jobs
publish-candidate
payload-manifest
published-payload-index
shard-validation-report
jobs-final-snapshot
schedule-manifest
session-profile-manifest
runner-operation-manifest
multi-session-harness
restart-external-manifest
actual-factor-witness-report
actual-semantic-interaction-report
actual-handoff-validation
semantic-validator-mutation-report
validation-report
regeneration-report
package-manifest
final-validation
run-contract
execution-manifest
runtime-profile
normalization-policy
route-result
logs-manifest
clean-state-report
cleanup-report
restore-report
cleanup-summary
restore-summary
two-run-comparison
runtime-validation
global-completion-report
```

Unknown field、missing field、unknown kind/version、错误 direct predecessor 或 v1 validator 接受
任意 v2 artifact 都是合同失败。Schema registry、每个 schema byte/semantic SHA、canonical JSON
版本和 validator SHA 必须进入 global/local input lock。

全局 YAML 目录不是 plan artifact envelope，但同样必须有独立 strict schema。其中失败检查顺序
与 route runner 目录/schema 路径固定为：

```text
skills/pg-sql-generation/references/common/pg18_statement_check_order_catalog.yaml
skills/pg-sql-generation/references/common/pg18_statement_check_order_catalog.schema.json
skills/pg-sql-generation/references/common/pg18_route_runner_registry.yaml
skills/pg-sql-generation/references/common/pg18_route_runner_registry.schema.json
```

上述文件的 raw-byte SHA、catalog semantic SHA、schema version 和 validator SHA 必须进入
global/local input lock；目录或 schema 缺失、宽松接受 unknown field，或 count/multiset SHA
不可独立重算时，readiness 失败。

用户级命令空间固定为：

```text
pg-case coverage-v2 discover
pg-case coverage-v2 compile-catalogs
pg-case coverage-v2 plan-all
pg-case coverage-v2 validate-plan
pg-case coverage-v2 freeze-mapping
pg-case coverage-v2 approve
pg-case coverage-v2 generate <statement>
pg-case coverage-v2 validate-artifacts <statement>
pg-case coverage-v2 package <statement>
pg-case coverage-v2 run <statement>
pg-case coverage-v2 verify-global
pg-case coverage-v2 report
```

`claim/complete/retry/status` 可作为同 namespace 的底层运维子命令，但不能绕过上述用户级状态
门禁。V2 实现应复用现有 discovery、engine、renderer 和 artifact store 中可证明正确的部分；
现有 V1 orchestrator 的“一 obligation 一 SQL”和 rotate-attach 规则不能作为 V2 完整性证明。

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

`failure_state` 非 null 时，它对进度渲染拥有最高优先级，不得因保留的
`planning_state=generated` 或已 validated 的部分 shards 同时渲染 `[~]`。显式 retry 必须先
重验当前输入、failed-stage 前驱和 `retryable=true`；只有在锁内成功 claim 同一
failed stage 的新 attempt 时，才能原子清除 `failure_state` 并记录 retry attempt。在此之前
仍渲染 `[ ]`；retry 再失败时必须写入新 failure record，不得留下 null 伪进行状态。

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
3. 生成 sweep 开始后严格按所选 global revision 的 `generation-order.json`；当前 statement 未
   packaged，下一条不得领取 generation shard。
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
| `ledgers_enumerated` | source universe/consumption 与 grammar/factor/applicability/N-A/risk ledgers |
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
| `statically_validated` | actual factor witness、actual semantic interaction/handoff、jobs final、regeneration、schedule 全 PASS |
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

    source_universe    = freeze_official_and_canonical_source_universe(statement)
    grammar_rows       = enumerate_official_grammar(statement)
    factor_obligations = project_canonical_factor_rows_by_branch_and_context(statement)
    applicability_rows = join_frozen_inventories_by_branch_and_role(statement)
    risk_rows          = enumerate_mandatory_and_specific_risks(statement)
    na_rows            = record_all_intrinsic_and_delegated_na_decisions(statement)

    consumers = independently_join_branch_consumer_catalog_to_all_source_rows()
    source_consumption = prove_every_source_row_and_applicable_inventory_member_has_consumers()
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
generation_order = stable_topological_sort(owner_to_source_handoff_DAG,
                                           tie_break=frozen_inventory_ordinal)
for statement in frozen_statement_order:
    approval = approve(local_validated_root, global_handoff_closure_root)

# Pass C: sequential generation; owners precede delegated sources
for statement in generation_order:
    for shard in frozen_shard_order:
        atomically_claim_one_shard()
        render_only_the_assigned_mapping_into_attempt_staging()
        validate_actual_bytes_and_all_witness_bindings()
        atomically_publish_or_mark_failed()

    regenerate_payload_in_two_empty_roots_and_compare()
    actual_handoff = validate_delegated_owner_packages_and_actual_witnesses()
    package_only_if_every_shard_and_hash_edge_is_current()
    derive_checkbox_from_the_revalidated_hash_graph()
    fail_unless_current_statement_is_packaged_before_advancing()
```

Pass A 可以在其他 local plan 上继续只读规划，以避免 delegated owner 的顺序死锁；但只要任一
statement 未 local validated，Pass B/C 都不能开始。Pass B 必须把每条 delegated edge 定向为
`owner -> source` 并稳定拓扑排序，inventory ordinal 只作为同层 tie-break；因此 source 进入
package/[x] 前，owner package 和 actual witness 已存在。Pass C 任一步失败都停在当前 statement，
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
- v2 relation/table topology、column structure、type binding context 和 routine signature catalogs；
- v2 statement branch consumer 与 canonical target-intent catalogs，以及逐语句派生的
  interaction-universe schema/compiler/validator；
- PostgreSQL 18.4 statement/branch check-order catalog、其 strict schema、目录选择 validator
  和全部 resolver implementation；
- PostgreSQL 18.4 route runner registry、其 strict schema、每类 runner implementation 和
  harness/route/container/schedule/runner crosswalk validator；
- v2 semantic extractor registry、其 strict schema、primary-target-operation/axis-value 两类记录、
  semantic locus/value decoder、structural-absence rules 和
  `semantic-validator-mutation-report.json`；
- compatibility profile；
- lifecycle、validation、naming、baseline output、catalog-oracle allowlist、route-specific safety 和
  cleanup policies；
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
- 每个 canonical statement/branch/intent triple 在 semantic extractor registry 中精确匹配一条
  enclosing primary-target-operation record，且每个 target axis/value locus 唯一归属该 operation；
- 每个 executable assignment 在固定 check-order catalog 中精确匹配一条
  statement/branch/intent profile，且目录 count/multiset SHA、profile selector 和 resolver SHA
  均可由独立 validator 重算；
- 每个 executable atom 的 harness/route/container/schedule 组合在固定 route runner registry 中
  精确匹配一个 runner class 和具体 ID/version/SHA，且未声明组合、零匹配或多匹配
  均使 readiness 失败；
- 目标语句若被 baseline output policy 禁止，已有第 9.2 节声明的窄化授权 route 和 validator，
  不存在 policy 冲突；
- 不使用 generic fallback 猜测目标 SQL。
- 第 12.5 节全部 semantic validator mutations 在预期 gate 被拒绝，报告绑定的 parser、extractor
  和 validator SHA 与当前 input lock 一致。

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

Grammar row ID 使用第 3.7 节
`logical_id("GRM", [statement, grammar_branch_id, production, value])`，
因此 production/value 即使包含分隔符也不会产生解析歧义。

`grammar-ledger.json` 每行至少包含：

```yaml
grammar_row_id: string
grammar_branch_id: string
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
    grammar_branch_id: string
    canonical_intent_class_id: string
    context_id: string
    semantic_role: string
    factor_axis_id: string
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
- 每个 canonical source row 必须至少投影出一个 `FOB` obligation；即使所有 official branches
  都不可观察，也必须投影到明确 context 并以第 7.7 节 N/A 结算，不能让 consumer join 返回
  空集后只保留 source row 外壳；
- `covered` 和 `expected_failure` 必须最终由 witness index 指向真实 atom；
- `expected_failure` 必须有具体且唯一的 primary reason；
- `justified_na` 必须引用统一 N/A ledger；
- factor alias 可以共享 atom witness，但每个 canonical row 仍独立核账；
- 相近值、规模过大、暂未实现或代表值均不是合法 N/A 理由。

Factor obligation ID 使用第 3.7 节
`logical_id("FOB", [statement, grammar_branch_id, canonical_intent_class_id, canonical_row_id, context_id,
semantic_role])`；intent/context/role 必须来自冻结 canonical-intent/branch-consumer/context
catalogs，不能由 planner 或 renderer 临时造字符串。同一 source row 在两个 canonical intent 中
消费时必须产生两个不同 FOB，分别绑定各自 AXI；不得用一个 FOB 携带多个 axis ID。独立
validator 从 9,978 source rows、canonical intents 与 branch consumer catalog 重新 join candidate
FOB multiset，并要求与 factor ledger obligations 精确相等。

守恒条件：

```text
canonical source rows = exactly frozen canonical rows
forall canonical source row: FOB projection count >= 1
derived factor obligations
= covered + expected_failure + justified_na

factor_missing   = 0
factor_duplicate = 0
factor_pending   = 0
factor_zero_consumer = 0
```

`source-consumption.json` 必须逐 source row 保存 consumer obligation IDs、count 和 multiset SHA，
每个 ID 保留 canonical intent 维度；由独立 validator 从 source universe、canonical intents 与
branch-consumer catalog 重算。同一 source row 的不同 intent consumer 不得合并、去重或共享一个
FOB ID。删除某一 source row 的全部 consumers，或只删除其中一个 intent consumer，都必须在
plan validation 失败，不能等到 SQL 生成后才发现。后置 witness index 也以这些 intent-specific
FOB ID 分别结算。

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

`applicability.json` 使用 v2 固定结构。scope ID 固定为
`object/relation/table/column_structure/column_type`，状态只取 `complete/not_applicable`；覆盖方法另用
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
  column_structure: {status: complete, coverage_mode: conditional, selector_manifest_ids: []}
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
    scope: object | relation | table | column_structure | column_type | routine_signature | type_binding
    selector_id: string
    inventory_count: nonnegative_integer
    inventory_sha256: sha256_hex
    consuming_grammar_branch_ids: []
    binding_roles: []
    context_ids: []
    compatibility_resolver: {id: string, version: string, sha256: sha256_hex}
member_decisions: []
```

每个适用 scope/manifest 都通过 `selector_manifest_ids` 引用完整 selector、count、SHA、consuming
branches、binding roles、contexts 和 compatibility resolver。`status=not_applicable` 时必须没有
executable member，但仍必须引用完整 selector/domain，并把每个 member 投影为独立 INV decision
和第 7.7 节 N/A 记录；空 selector list、一个 scope-level 总括 N/A 或只保存 count/SHA 都不能
替代逐成员义务。
`status=complete` 必须至少一个 selector manifest，且它列出的 candidate obligation 数与实际
`member_decisions` 精确相等；无成员的合法库存仍需零 count/SHA manifest，不能静默缺字段。
其中 consuming grammar branches/roles/contexts 必须与第 7.4.1 节 branch consumer catalog 的引用内容
逐字节相等；local manifest 不能重新定义或缩窄它们。

逐库存成员使用唯一 obligation ID：

```text
logical_id("INV", [statement, grammar_branch_id, scope, selector_id, member, binding_role, context_id])
```

Inventory consumption is branch-scoped rather than grammar-leaf-scoped. `grammar_branch_id` must come
from the frozen branch-consumer catalog; `grammar_row_id` is not an alias here. A branch may contain
multiple grammar rows, but a planner may not choose one row to create or suppress an inventory obligation.

因此七份类型库存中同名成员仍是不同证据义务，不会误去重。一个真实 atom 可以同时作为
多个 selector obligation 的 witness，但必须分别列出 obligation ID 和同一个可执行
witness binding；这表示同一构造同时证明多份目录事实，不要求复制 SQL。

`member_decisions[]` 固定字段为：

```yaml
obligation_id: string
statement_key: string
grammar_branch_id: string
scope: object | relation | table | column_structure | column_type | routine_signature | type_binding
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
统一 N/A ledger。库存守恒的左侧是所有 scope × selector × member × grammar branch × role × context 的 candidate
obligations，不是只计算预先判定 applicable 的成员：

```text
CandidateINV(statement)
= Bag((statement, bc.grammar_branch_id, requirement.scope, selector_id, member,
       binding_role, context_id)
      for bc in FrozenBranchConsumers(statement)
      for requirement in bc.required_binding_roles
      for selector_id in requirement.selector_ids
      for member in FrozenInventory(selector_id)
      for binding_role in requirement.binding_roles
      for context_id in requirement.context_ids)

Bag(INV coordinates projected from member_decisions)
= CandidateINV(statement)
= covered + expected_failure + justified_na

inv_missing = inv_duplicate = inv_unexpected = 0
```

每个 selector manifest 的每个冻结 member 都必须至少产生一个 branch/role/context candidate
obligation。`status=not_applicable` 使用由 branch-consumer catalog 冻结的 statement-scope
sentinel grammar branch、`binding_role=not_applicable` 和 scope context，为每个 member 产生独立
`justified_na` INV obligation；每个 obligation 拥有自己的 `na_record_id`，可以引用相同官方
evidence，但不能共享一个 source obligation ID。零 consumer 的 selector/member 是错误。
Sentinel branch ID、scope context 和 not-applicable role 必须是 branch-consumer catalog 的显式
记录并进入其 count/multiset SHA；local planner 不得临时制造 sentinel。
相同 source-consumption artifact/validator 也必须核对 grammar rows 和每个 `CandidateRISK`
obligation 均有非空消费，防止 factor 之外的源义务通过空 join 静默消失。

### 7.4 Relation 与 table 规范库存

Relation 使用：

```text
skills/pg-sql-generation/references/combinations/_shared/coverage_inventory.yaml
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
rows、relation/table/column-structure/type/routine catalogs 和 PostgreSQL 18.4 语义独立编译，按
`statement × grammar branch` 列出全部 official branches；仅当 statement 存在 inventory
not-applicable scope 时，额外允许至多一个 statement-scope `applicability_na_sentinel` branch。
Sentinel 只能承载 INV N/A，不得承载 grammar rows、FOB 或 RISK obligations：

```yaml
branch_consumer_id: string
statement_key: string
grammar_branch_id: string
grammar_branch_kind: official | applicability_na_sentinel
required_factor_value_consumers:
  - canonical_row_id: string
    factor_name: string
    canonical_intent_class_id: string
    context_id: string
    semantic_role: string
    factor_axis_id: string
required_binding_roles:
  - scope: object | relation | table | column_structure | column_type | routine_signature | type_binding
    selector_ids: [nonempty]
    binding_roles: [nonempty]
    context_ids: [nonempty]
required_statement_specific_risk_ids: []
source_evidence: [nonempty]
```

`canonical_intent_class_id` 必须逐字引用同一冻结版本的 canonical target-intent catalog；
Grammar ledger、factor obligations、INV decisions、intent-axis ledger 和 branch-consumer catalog
一律使用同一个 `grammar_branch_id` 字段并逐字节相等；`branch`、`grammar_branch` 等 local alias
不属于 v2 schema。每个 official grammar row 必须能以该字段唯一 join 到一个 official branch
consumer；sentinel branch 没有 grammar rows。
`factor_axis_id` 必须按第 3.8 节 components 从该 ID、branch、context、semantic role 和 factor
重新计算，禁止 catalog 自报不一致的 hash。同一 `factor_axis_id` 下的全部 canonical rows 构成
该 context/role/intent 轴的完整冻结 domain；catalog 不得只列 planner 准备生成的值。独立
validator 必须从 9,978 source rows、official branches、canonical intents、context/role catalogs
重新 join 出这些 consumer 和 domain，再与 local ledger 精确比较。

目录保存 statement/branch/FOB/inventory/CandidateRISK obligation 的 count 和 multiset SHA。Local
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

### 7.4.2 Semantic locus 与 extractor registry

每个可执行 grammar/factor/inventory/risk value 必须在生成前绑定独立可验证的语义位置。v2
实施必须创建并冻结：

```text
skills/pg-sql-generation/references/common/pg18_semantic_extractor_registry.yaml
skills/pg-sql-generation/references/common/pg18_semantic_extractor_registry.schema.json
```

该 strict registry 必须把“axis/value 的叶级 witness”与“包围整条 phase-8 目标操作的唯一
operation locus”分成两个不相混淆的集合。顶层至少保存 schema/catalog version、两个集合各自的
count 与 multiset SHA。Axis/value 记录最小结构为：

```yaml
record_kind: axis_value_witness
statement_key: string
grammar_branch_id: string
canonical_intent_class_id: string
axis_id: string
canonical_value_id: string
proof_kind: target_ast | target_token_stream | parser_rejection | fixture_ast | fixture_state |
            oracle_ast | transaction_state | session_profile | runner_operation |
            harness_dag | external_manifest
semantic_role: string
allowed_phase_ids: [nonempty]
semantic_locus: nonempty_json_pointer_or_selector
owner_primary_operation_locus_id: string | null
cardinality: exactly_one | absent | derived
extractor: {id: string, version: string, sha256: sha256_hex}
value_decoder: {id: string, version: string, sha256: sha256_hex}
source_evidence: [nonempty]
```

Primary target operation 记录最小结构为：

```yaml
record_kind: primary_target_operation
primary_operation_locus_id: string
statement_key: string
grammar_branch_id: string
canonical_intent_class_id: string
allowed_phase_id: 8
allowed_materialization_kinds: [nonempty]
proof_kind: target_ast | target_token_stream | parser_rejection
operation_locator_selector: nonempty_structured_selector
extractor: {id: string, version: string, sha256: sha256_hex}
source_evidence: [nonempty]
```

对 canonical target-intent catalog 的每一个
`(statement_key, grammar_branch_id, canonical_intent_class_id)` 必须精确存在一条 primary record；
missing、duplicate、wildcard 或同一 triple 由多个 selector 竞争都使 readiness 失败。独立 extractor
把该 record 应用于 actual artifact bytes 后必须返回精确一个包围完整目标 operation 的 canonical
structured locator。每条 proof kind 为 `target_ast | target_token_stream | parser_rejection` 的
axis/value 记录必须以非空 `owner_primary_operation_locus_id` 指回同一 triple 的 primary record，
并且其叶级 `semantic_locus` 必须位于该 operation locator 内；叶级 locus 不得反过来充当整条
operation locator。Fixture/oracle/harness 等非 target witness 的 owner 字段为 null。

Extractor 只能使用 frozen mapping 定位 program/subcase/phase 边界；不得读取 planned assignment、
witness credit、renderer field 或注释来决定 observed value，也不得 import renderer 或复用
renderer 的 value-selection 函数。SQL target/fixture AST、fixture state、transaction state、harness
DAG、single-session runner/schedule manifests 和 external manifest 必须分别使用适合其 proof kind
的独立 parser/state extractor。`session_profile` 与 `runner_operation` extractor 必须读取最终
runner manifest bytes，证明 phase 2 settings 和 phase 12 cleanup probe 的 operation/value；不能
从 phase projection 的 planned 字段复制。Mapping、schedule/runner manifest 及其 SHA 都是
actual reports/package 的强制前驱。
Extraction 必须先以最终 bytes 和完整 registry 做无计划过滤的 discovery pass，独立识别 actual
statement/branch、所有 observed axes、semantic roles 和 loci，再逐轴 decode value；禁止按
`P(k)` 或 `R(k)` 只运行预期 axis decoders。这样计划外 clause/axis 必须进入 `A(k)` 并触发
`unexpected_axis`，不能因 validator 没扫描而消失。
预期 parser failure 因无法产生完整 AST，必须由版本化 token stream/partial-parse extractor 证明
计划中的非法 production 已实际写入 target locus，并由 runtime validator 验证 PostgreSQL 的
observed SQLSTATE；不能因 AST 缺失把该负例降为 N/A。

`cardinality=absent` 必须由规定 target AST/state locus 的结构性零出现证明，不能用字符串未命中；
同一实际 locator 只有在冻结 alias/equivalence resolver 证明等价时，才能分别见证多个 canonical
obligations。值出现在错误 phase、辅助对象、oracle 字符串或无因果作用的位置，只能成为无信用
的 context evidence，不能满足该 axis 的 actual assignment。

### 7.4.3 PostgreSQL 18.4 失败检查顺序目录

为避免 planner 从多个合法 resolver 中自选一个并得到“自洽”首因，v2 必须在任何
interaction 编译前创建并冻结第 4.6 节指定的 check-order catalog 和 strict schema。
目录顶层精确保存 `schema_version`、`postgresql_version: "18.4"`、`catalog_version`、
`entry_count` 和 `entry_multiset_sha256`；每条 entry 的最小结构为：

```yaml
check_order_profile_id: string
statement_key: string
grammar_branch_id: string
canonical_intent_class_ids: [nonempty]
selection_predicate: nonempty_declarative_object
predicate_evaluator: {id: string, version: string, sha256: sha256_hex}
ordered_checks:
  - rank: nonnegative_integer
    check_id: string
    reachable_obligation_kinds: [GRM | FOB | INV | RISK, ...]
    condition_predicate: nonempty_declarative_object
resolver: {id: string, version: string, sha256: sha256_hex}
source_evidence: [nonempty]
```

`canonical_intent_class_ids` 必须逐字节引用冻结 canonical target-intent catalog，
`grammar_branch_id` 必须逐字节引用 branch-consumer catalog。`ordered_checks.rank` 在一个
profile 内严格递增且唯一；目录不允许 wildcard statement/branch、自由字符串 predicate、
重复 profile ID 或未绑定 source evidence 的检查步骤。

对 canonical assignment `a`，独立 validator 必须只使用
`(statement_key, grammar_branch_id, canonical_intent_class_id, a)` 执行目录的冻结
predicate evaluator，得到：

```text
MatchingProfiles(a)
= catalog entries whose statement/branch/intent match and whose selection_predicate(a) is true

for every executable interaction: |MatchingProfiles(a)| = 1
SelectedResolver(a) = MatchingProfiles(a)[0].resolver
```

Validator 随后用 `SelectedResolver(a)` 和该 profile 的 `ordered_checks` 重算结果；不得先从
interaction/atom 读取 `check_order_resolver` 再反向查目录。Interaction/atom 中的 resolver
字段只是被验证投影：若独立计算结果为 expected failure，它必须与
`SelectedResolver(a)` 精确相等；若计算结果为 success，interaction/atom 中的
failure resolver 必须为 null，但 validator 仍必须完整执行该 catalog profile 才能得出
success，不能因自报 `expected_outcome=success` 跳过检查。匹配数为 0 或大于 1、
profile 不适用于当前 branch/intent、resolver/predicate SHA 漂移或目录 count/multiset SHA
不符，均必须在 readiness/plan validation 阶段 fail closed。

### 7.5 Column/type 七份并列库存

完整 column/type 审查统一引用：

```text
skills/pg-sql-generation/references/common/pg18_type_catalog.md
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
INSERT           = source_expression_type × target_column_type
UPDATE           = assigned_expression_type × target_column_type
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

### 7.5.1 Column structure 独立库存

“完整列结构”不能由 renderer 复制一张固定五列表自证，也不能只靠七份 type inventory
替代。v2 实施必须创建并冻结：

```text
skills/pg-sql-generation/references/common/pg18_column_structure_catalog.yaml
```

该目录至少从 PostgreSQL 18.4 grammar/catalog/source 推导以下规范维度及成员：

```text
column_count_and_position
column_name_shape
data_type_and_typmod
collation
nullability
default_state
generation_mode
identity_mode
primary_key_participation
unique_constraint
check_constraint
foreign_key_role
index_role
partition_key_role
inheritance_role
storage_and_compression
statistics_target
dependency_state
dropped_or_existing_column_state
data_profile
```

目录必须保存每个成员允许的 branch、column role、context、合法/可达失败/逻辑矛盾 tuple、
source locator、稳定顺序、count、tuple-multiset SHA 和 resolver 版本。具体值域以冻结 PG18.4
目录为准，不能把上表标题直接当作已经完成的成员枚举。

只要目标 statement 能观察一个列维度，该维度的全部 candidate obligations 都必须在对应
branch/role/context 下进入 `covered` 或 `expected_failure`，或者以第 7.7 节的严格 N/A/handoff
闭环结算。目标 SQL 能接收到列对象后再拒绝的输入是本语句的 expected failure；若列 fixture
在 setup 就无法创建、目标语句从未执行，则不得冒充本语句负例，只能由真正拒绝该定义的
statement obligation 承接。

结构库存与类型库存先按真实 column role/context join。只有 source/target、left/right、
partition-key/value 等语义独立的列或类型角色才做条件积；继承列、polymorphic binding、数组
元素→数组类型、输入→返回类型等函数依赖必须由冻结 resolver 计算。辅助列、辅助表或 oracle
字符串中偶然出现一个成员不能取得目标列结构信用。

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
grammar_branch_id: string
grammar_row_id: null | string
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

Grammar/risk N/A 使用具体 `grammar_row_id`；branch-scoped factor/inventory N/A 可令该字段为 null，
但始终必须保存由 official grammar/branch-consumer catalog 重算的 `grammar_branch_id`。N/A record
不得重新引入一个任意 grammar row 来改变 INV obligation 身份。

- `intrinsic` 表示该 member 对目标 statement/branch 确实不可观察，owner 必须为 null；
- `delegated` 表示覆盖责任转交另一条语句，必须填写全局唯一 owner obligation ID。

全局 `handoff-ledger.json` 为每个 delegated edge 冻结 source/owner statement revision、local
plan root、完整 projection、equivalence key/resolver SHA、owner disposition、owner atom 和 credited
witness。`handoff-validation.json` 必须从全部 183 个 local validated plan 重新计算 source/owner
projection，证明 equivalence key 相等、目标义务真实存在且为 covered/expected_failure，并禁止
环、禁止 owner 再次 delegated、禁止多条义务互相指向而无人执行。全局 intrinsic N/A 必须由
官方/源码证据审计，不能用另一条 N/A 自证。Handoff closure 是每个 statement approval、全局
validation 和 checkbox 的强制前驱；只检查 owner ID“存在”不算闭环。

上述 `handoff-validation.json` 只是计划闭环，不能证明 owner 的实际 SQL 已生成。每个包含
delegated N/A 的 source statement 在 package 前必须另生成不可变
`actual-handoff-validation.json`：逐 edge 绑定 owner current package SHA、owner
`actual-factor-witness-report.json` 中精确 credited obligation/value/context/role、owner actual
semantic tuple 和 source/owner equivalence resolver 结果。Owner 必须已 `[x]` 且所有 SHA 当前；
缺失、stale、context/value 不等或 owner 只有 planned witness 时 source 不得 package/打勾。
没有 delegated edge 的 statement 也必须生成通过验证的空 artifact，保存 `edge_count=0` 和冻结
empty-multiset SHA；所有 package 使用相同强制 predecessor，不允许选择性省略。

判定规则：

- 能让目标 SQL 自己拒绝的输入是 expected failure；
- 只能在 setup 阶段失败、导致目标 SQL 根本无法到达时，才可能离开本 statement 的 executable
  product；若 setup rejection 本身可执行，必须以 `delegated` 指向真正拒绝它的 statement
  expected-failure obligation，不能记作无人承接的 intrinsic N/A；
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

对 branch `b`，风险全集由独立目录确定，不能由逐语句 planner 自报：

```text
MandatoryRiskDomainV1
= exactly the 12 risk IDs listed above

SpecificRiskDomain(statement, b)
= branch_consumer(statement, b).required_statement_specific_risk_ids

MandatoryRiskDomainV1 intersect SpecificRiskDomain(statement, b) = empty

risk_domain(statement, b)
= MandatoryRiskDomainV1 ⊎ SpecificRiskDomain(statement, b)

CandidateRISK(statement)
= Bag((statement, grammar_row.grammar_row_id, risk_id)
      for grammar_row in OfficialGrammarRows(statement)
      for risk_id in risk_domain(statement, grammar_row.grammar_branch_id))

Bag((statement_key, grammar_row_id, risk_id) from risk-ledger)
= CandidateRISK(statement)

risk_missing = risk_duplicate = risk_unexpected = risk_pending = 0
```

`required_statement_specific_risk_ids` 只保存额外风险，不能重复或替换 mandatory 12 项。
独立 validator 从 official grammar rows、固定 12 项和 branch-consumer catalog 重算该 multiset，
并要求它与 ledger 的 `(grammar_row_id, risk_id)` multiset 精确相等；missing、duplicate、unexpected
均为零。因此 statement-specific risk 不能被整体省略。

`source-universe.json` 必须保存独立 `risk_source_universe` 投影：mandatory domain version、精确
12 IDs/count/multiset SHA，以及每个 official grammar branch 的 statement-specific IDs/count/SHA，
最后保存 CandidateRISK expected count/multiset SHA。Risk ledger 不能把自己的 actual count 当作
expected source universe。

```yaml
risk_source_universe:
  mandatory_domain_version: mandatory-risk-v1
  mandatory_risk_ids: [exactly_12]
  mandatory_risk_count: 12
  mandatory_risk_multiset_sha256: sha256_hex
  branch_domains:
    - grammar_branch_id: string
      statement_specific_risk_ids: []
      risk_count: nonnegative_integer
      risk_multiset_sha256: sha256_hex
  expected_obligation_count: nonnegative_integer
  expected_obligation_multiset_sha256: sha256_hex
```

`risk-ledger.json` 对 `CandidateRISK(statement)` 中每个 `grammar_row_id × risk_id` 恰有一行：

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

Risk ID 使用第 3.7 节 `logical_id("RISK", [statement, grammar_row_id, risk_id])`；RISK 不含未进入
ledger schema、也无法从独立风险全集重算的自由 `context_id`。
`covered/expected_failure` 必须在后置 witness index 中获得可执行 credited witness；N/A 引用
第 7.7 节同一 ledger。`risk-ledger.json` 必须保存 expected/actual count 和 multiset SHA，且
expected SHA 由独立 compiler 重算。它的 count/SHA 是 plan validation、approval、package
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
grammar_branch_id: string
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

每条 interaction 不能只保存语义 assignment，还必须冻结结果与失败归因：

```yaml
interaction_id: string
semantic_tuple_id: string
assignment: {}
disposition: executable | impossible | justified_na
expected_outcome: success | expected_failure | null
primary_failure_obligation_id: null | string
primary_failure_reason: null | string
expected_sqlstate: null | sqlstate5
check_order_resolver: null | {id: string, version: string, sha256: sha256_hex}
check_order_rank: null | nonnegative_integer
disposition_reason: null | string
source_evidence: []
na_record_id: null | string
```

`executable + success` 必须固定 `expected_sqlstate=00000`，且首因和 check-order resolver 都为
null，`check_order_rank=null`；`executable + expected_failure` 必须固定唯一
`primary_failure_obligation_id`、非空 `primary_failure_reason`、非 `00000` 五位 SQLSTATE、
check-order resolver 和非负 `check_order_rank`。`impossible/justified_na` 的全部执行结果/首因字段
必须为 null，并使用非空 `disposition_reason` 解释不可执行或 N/A。能到达
目标 SQL 的 expected failure 始终属于 executable。`interaction-universe.json` 分别保存
candidate/executable/impossible/N-A 的 count 和 multiset SHA，并证明三者守恒。Products 只能
无损分区 executable interactions；expected 空间来自 interaction compiler，不来自 product
planner 自报。

对每条 executable interaction，独立 validator 必须以 canonical assignment、
冻结 PostgreSQL 18.4 check-order catalog 和第 7.4.3 节的 profile selector 先唯一选出
`SelectedResolver(a)`，再使用 input-locked resolver implementation 重新执行。不得信任
interaction 自报的 `check_order_resolver`。Resolver 输出精确为：

```text
{expected_outcome, primary_failure_obligation_id, primary_failure_reason,
 expected_sqlstate, check_order_rank}
```

该输出必须逐字段等于 interaction 冻结值。重算为 success 时，必须得到
`expected_sqlstate=00000`、全部首因/rank 字段为 null，且 interaction/atom 的
failure resolver 字段为 null；重算为 expected failure 时，interaction/atom 的 resolver
必须精确等于 `SelectedResolver(a)`，primary obligation 还必须属于当前 assignment 可达的
obligation 集合，并在 GRM/FOB/INV/RISK ledger 中具有 `disposition=expected_failure`。Planner 自报
字段、仅合法的 resolver ID、同步把失败改成 success，或 interaction/atom 两侧同步篡改
都不能替代这次 assignment-driven 重算。

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
required_factor_axis_ids: []
factor_assignments:
  <axis_id>:
    canonical_row_id: string
    factor_obligation_id: string
    canonical_value: string
inventory_assignments: {}
derived_axes: {}
risk_obligation_ids: []
credited_obligation_ids: []
context_only_obligation_ids: []
expected_outcome: success | expected_failure
primary_failure_obligation_id: null | string
primary_failure_reason: null | string
check_order_resolver: null | {id: string, version: string, sha256: sha256_hex}
precheck_witness_ids: []
expected_sqlstate: sqlstate5
check_order_rank: null | nonnegative_integer
fixture_requirements: {}
pre_state: {}
target_intent: string
observable_assertion: {}
post_state: {}
cleanup_requirements: {}
execution_harness: single_session_multiphase | multi_session_barrier | restart_or_external_event
execution_route: serial_sql | parallel_sql | multi_session | external_isolated | restart_external
source_evidence: []
```

硬约束：

- assignment 容器必须是 map，键在各自 namespace 内唯一；grammar/factor/inventory assignment
  都必须绑定第 3.8 节 context-qualified `AXI-<64hex>` axis ID，并另外保存 canonical source
  row/obligation ID；不能用裸 factor 名、裸 member 或不带 context 的键折叠 left/right、
  source/target 等语义角色；
- 对该 branch 适用的每个 grammar production key 恰好一个值；互斥 grammar value 不能在同一
  atom 同时取得信用；
- 对该 branch 适用的每个 canonical factor key 恰好一个值；不适用 key 留在 ledger/N/A，
  不能被迫塞入 atom；
- `derived_axes` 同样是单值 map；一个 key 不能以 list、重复 token 或逗号拼接伪装多值；
- 多个设置形成的环境真值写入不同 axis 或 derived axes，不能让同一 factor 多值；
- 一个 expected-failure atom 只有一个 primary reason 和一个
  `primary_failure_obligation_id`；它是本 atom 唯一取得失败信用的 obligation，所有在 PostgreSQL
  检查顺序中更早的条件必须拥有实际有效的 `precheck_witness_ids`；
- success atom 必须 `expected_sqlstate=00000`，且 `primary_failure_obligation_id`、
  `primary_failure_reason`、`check_order_resolver`、`check_order_rank` 全为 null；expected-failure
  atom 必须逐字段复制 interaction 冻结的唯一首因 ID/reason、非 `00000` 五位 SQLSTATE、
  check-order resolver 和非负 rank，不能在 atom compiler 中改名或重新推导；
- disposition 为 `expected_failure` 的 obligation 只有在 atom 本身为 `expected_failure` 且它等于
  `primary_failure_obligation_id` 时才能进入 `credited_obligation_ids`；success atom 和非首因失败
  obligation 都不得取得 expected-failure 信用；
- 按 PostgreSQL 实际检查顺序归因，被更早错误遮蔽的条件不得取得覆盖信用；
- `credited_obligation_ids` 是本 atom 真正证明的 obligation；仅用于构造环境却被首因遮蔽的
  assignment 放入 `context_only_obligation_ids`，永不参与 coverage ledger 计数；失败 atom 必须
  记录首因的 check-order rank/resolver；
- 错误必须发生在目标阶段，setup 意外失败不算目标负例；
- atom 先具有 fixture、target、oracle、cleanup 和 harness，才能进入 mapping；
- 一个物理程序若覆盖多个同 factor 值，必须拆成多个独立 atom/subcase，不能靠
  `covered_values` 注释替代。
- 后置 `obligation-witness-index.json` 以 GRM/FOB/INV/RISK logical ID 为 key，把每个 credited
  obligation 绑定 atom、预期 subcase/phase、冻结 `semantic_locus_id`、`semantic_field_id`、
  extractor/value-decoder ID 和 coverage credit；context-only binding 明确标 false。
  `renderer_field` 或任意自由字符串不能替代 semantic locus。Validator 必须按第 12.3 节从实际
  SQL/harness 字节独立生成 `actual-factor-witness-report.json` 与
  `actual-semantic-interaction-report.json`，不接受注释或 renderer 自报值。

Tuple/atom 守恒不直接比较不同记录结构。规范投影函数
`atom_to_interaction_projection_v2(atom)` 必须从 atom 的 context-qualified assignments 重新
canonicalize 并推导 semantic tuple，同时投影 `expected_outcome`、`primary_failure_obligation_id`、
`primary_failure_reason`、`expected_sqlstate`、`check_order_rank` 和 check-order resolver 的
ID/version/SHA；禁止直接复制
source ITUP/STUP pointer 后宣称一致。其 resolver version/SHA 在 input lock 中冻结。
Validator 比较：

```text
FailureProjection(x)
= (expected_outcome, primary_failure_obligation_id, primary_failure_reason,
   expected_sqlstate, check_order_rank, canonical(check_order_resolver))

ExecutableInteractionProjection(i)
= (recomputed interaction_id, semantic_tuple_id, canonical assignment,
   FailureProjection(i))

AtomInteractionProjection(a)
= (recomputed interaction_id from atom assignments, recomputed semantic_tuple_id,
   canonical atom assignments, FailureProjection(a))

Bag(ExecutableInteractionProjection(i) for every executable interaction i)
= Bag(AtomInteractionProjection(a) for every atom a)
```

`precheck_witness_ids` 是 atom-only 执行证据，不进入 FailureProjection。

该等式比较的是“assignment + outcome + failure attribution”完整记录，而不只是 semantic tuple
ID。任何 expected-failure obligation 只有在 atom 自身为 `expected_failure` 且该 obligation
就是唯一 `primary_failure_obligation_id` 时才能进入 `credited_obligation_ids`；success atom 不得
给 expected-failure obligation 信用。其他同时成立但被检查顺序遮蔽的失败条件只能进入
`context_only_obligation_ids`。因此不能把非法 production 渲染出来后把 atom 偷改成 success，
也不能用同一失败给多个首因记账。

### 7.12 生成前守恒门禁

只有以下条件全部成立，状态才可进入 `generation_allowed`：

```text
official grammar ledger complete
canonical factor ledger complete
source consumption complete；zero-consumer source obligations = 0
all applicability decisions complete
all applicable type selectors reconciled
all CandidateRISK obligations reconciled
all obligations classified in intent-axis ledger

candidate interaction multiset
= executable ⊎ impossible ⊎ justified-NA interaction multisets
product included multiset = executable interaction multiset

executable tuple count  = executable atom count
atom projection multiset = executable interaction multiset
each executable semantic interaction maps to exactly one atom
duplicate canonical assignment = 0
interaction/atom outcome and primary-failure projection mismatch = 0
failure_resolver_output_mismatch = 0
primary_failure_not_in_assignment = 0
primary_failure_ledger_disposition_mismatch = 0
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

每个 assignment 必须在第 7.4.2 节 registry 为该 axis/value 指定的
`fixture/target/oracle/harness` semantic locus 中拥有机器可定位的 witness；出现在其他允许
phase 也不能自动取得信用。只在 header 或注释中出现不得取得覆盖信用。

`fixture-plan.json` 先于 packing/mapping 冻结，因此它只能按 atom 保存 key 精确为 `1..12` 的
`logical_phase_dag`：每个 phase 保存 `logical_phase_id`、`depends_on_logical_phase_ids`、
`logical_operation_ids`、`semantic_locus_ids`、`required_materialization_class` 和
`intentionally_empty_reason`；它不得保存尚未产生的 subcase/container ID、ordinal、shard、
schedule 或 payload path。DAG 必须无环、全部 phase 从入口可达，phase 8 精确包含一个 primary
target logical operation。Packing 建立 atom→subcase→container，随后 `mapping.json` 为每个
subcase 保存完整 `materialized_phase_projection`，同样具有 `1..12` 全部 key，并逐 phase 保存
`logical_phase_id`、`logical_operation_ids`、`materialization_status`、`materialization_kind`、
`container_id`、`payload_relative_path`、`artifact_id`、`operation_locator`、`semantic_locus_ids`、
`shared_materialization_id` 和 `coverage_credit`；不适用字段为 null。物化类型固定为
`header_comment | primary_sql | session_profile_operation | cleanup_probe_operation |
multi_session_operation | external_event_operation | intentionally_empty`。缺 phase、logical operation
multiset 前后 missing/duplicate/unexpected 非零、一个 logical operation 映射到多个非共享 target、
或 projection 无法无损投影回 fixture logical DAG 都使 mapping freeze 失败。共享物化只能由多个
subcase 显式引用同一 `shared_materialization_id`，不得复制 coverage credit。阶段 8 精确映射
一个 primary target operation，阶段
7、9、10、11、12 对每个 subcase 分别可定位。

装箱可以物理共享 setup 或最终 teardown，但每个 subcase 仍拥有独立 snapshot、target、result
capture、oracle、cleanup boundary 和 cleanup-oracle projection。共享 cleanup 必须位于 runner
的 unconditional-finally 路径；任一前置 subcase 失败不得跳过 cleanup，也不得让后续 subcase
取得虚假信用。普通 SQL program 必须在不依赖已有业务对象的干净数据库状态下独立重跑。

逻辑 phase 2 一律由 runner 的冻结 session profile 在载入 primary SQL 文件前施加，不内联为该
文件的 executable SQL；`materialized_phase_projection[2]` 在静态 mapping 中只绑定 expected
setting operations、planned session-profile artifact ID/path、runner identity，以及按固定
`FSCR_PLANNED_RUNNER_PAYLOAD_V2\0 || JCS({kind, semantic_payload})` 计算的 expected payload digest；
它不得绑定要到 generation contract/shard assignment 产生后才能计算的最终 artifact semantic SHA。
Observed application
result 只能进入 runtime route result，禁止写入 fixture plan、mapping 或静态 actual report。
这样表相关 primary SQL 在 header 后的第一个 executable statement 必然是 phase 3
的 `DROP TABLE IF EXISTS` pre-cleanup，满足 regress output style。若目标本身是 `SET` 等 session
语句，它属于 phase 8，不得借 phase 2 执行并取得目标信用。

为消除 regress output style 的“表脚本最后一条 executable statement 必须是
`DROP TABLE IF EXISTS`”与逻辑 phase 12 的冲突，V2 冻结唯一物理规则：primary SQL program
只物化阶段 1–11，并以 final cleanup 作为最后 executable statement；逻辑 phase 12 一律物化为
runner-owned `cleanup_probe` 结构化 operation，由 allowlisted query ID/parameters 表达，不作为
同目录第二个普通 `.sql` case。`materialized_phase_projection[12]` 同样只绑定 planned
runner-operation artifact ID/path、expected payload digest、operation policy SHA 和预期布尔结果；
runner 在 primary program 结束或异常后的 unconditional-finally 路径执行它。
实现者不得在 inline cleanup oracle 与 runner probe 之间临时选择。

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

目录查询只能使用冻结的
`skills/pg-sql-generation/references/common/catalog_oracle_allowlist_v2.yaml`，并只输出规范化布尔值
或稳定枚举。该文件必须具有独立 strict schema、schema version、稳定顺序、source locator、
count/multiset SHA 和 policy version/SHA，并进入 global/local input lock。Allowlist
至少按 statement、branch、semantic role 限定允许的 catalog、列、predicate 和投影；未进入
allowlist 的系统目录查询按 regress output policy 拒绝，renderer 不能临时放行。

禁止以 `SELECT true`、通用 `count(*)` 或仅查询对象名称代替能区分目标分支的真实 oracle。

### 8.5 Expected failure 合同

- 每个失败 subcase 只制造一个 primary reason；
- 其他权限、对象和类型条件必须配置为有效，除非它们属于被验证的检查顺序 tuple；
- 检查顺序 tuple 仍只给最先实际触发的 canonical failure value 覆盖信用；
- expected failure 不放入一个会因错误进入 aborted 状态的大事务，除非事务失败状态本身是
  目标；
- 失败后立即验证完整 snapshot 不变。

静态验证只能证明失败设计可归因；运行验证必须证明 observed target operation、observed
SQLSTATE 和 observed primary failure obligation 分别等于计划值。被更早错误遮蔽的 assignment
只能进入 `context_only_obligation_ids`，不能因为同一错误输出取得第二份失败信用。

### 8.6 Cleanup 合同

- pre-cleanup 和 final cleanup 都必须幂等；
- 按依赖 DAG 逆拓扑删除；
- RENAME/SET SCHEMA/OWNER 后按真实最终身份清理；
- 清理角色前先 RESET ROLE 并处理 owned objects；
- `CASCADE` 只有在它是计划内 cleanup factor 时使用；
- cleanup 优先不再执行同类目标 statement；确实无法避免时必须使用第 10.4 节的显式授权、
  phase 隔离和 `coverage_credit=false`；
- 表脚本满足项目 output style 对首尾清理的更严格要求。
- primary SQL program 的最后 executable statement 必须是计划内 final cleanup；cleanup oracle
  只能使用第 8.1 节冻结的 runner-owned phase-12 probe，不能追加在表 cleanup 之后。

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
event_mode: external_isolated | restart_external
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

`event_mode` 是 `restart-external-manifest` strict schema 的必填字段。独立 route resolver
必须从 approved atom execution route、event types、capabilities 和 route-safety policy 重算它：
`external_isolated` 只能使用不含 cluster/config restart 或故障恢复时序的 isolated events；
任一 restart/recovery-dependent event 必须为 `restart_external`。该 mode、mapping schedule class
和 runner registry class 必须逐字节一致，不能信任 manifest 自报。

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

阶段 1–6 只有在实际共享状态的 planned assignment projection 完全相等时才能物理共享；
“兼容但不同”必须通过显式 fixture transition 到达，不能冒充同一 fixture。每个 packed subcase
必须拥有独立的逻辑阶段 7–12 边界。Validator 必须模拟任一 subcase 在 target 前、target 中或
oracle 中失败的路径，并证明其他 subcase 不会取得虚假信用且最终 cleanup 仍可达。

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

- `subcase_local_ordinal` 与 `container_local_ordinal`；
- 明确的 `atom_id -> subcase_id -> program_id/bundle_id`；
- container 内 subcase 顺序和 SQL program/harness bundle 相对路径；
- 每个 subcase 的 `materialized_phase_projection[1..12]`，以及 phase 2/12 和多会话/外部事件
  所引用的 shard-local immutable runner manifest 相对路径；
- 对象前缀；
- shard ID；
- execution profile；
- schedule class。

Mapping 每行以 subcase 为粒度，必须保存 atom、container、shard 和 schedule 外键；同一
container 的所有 subcase 必须拥有同一 shard ID。Atom、subcase、container 和 shard ID 都按
第 3.7 节 codec 生成，物理 case label 另用可读 ordinal。外键缺失、一个 atom 多 subcase、
一个 subcase 多 container 或 container 跨 shard 都使 freeze 失败。

Atom 的 `execution_harness/execution_route`、packing container kind、mapping schedule class 和
runner manifest/runner identity 必须按下表做唯一 crosswalk；任一层不得自由选值：

| Atom harness | Atom route / schedule class | Container kind | 必需 manifest 与 runner class |
|---|---|---|---|
| `single_session_multiphase` | `serial_sql` | `sql_program` | session-profile + runner-operation / phase-aware serial SQL runner |
| `single_session_multiphase` | `parallel_sql` | `sql_program` | session-profile + runner-operation + frozen conflict set / phase-aware parallel SQL runner |
| `multi_session_barrier` | `multi_session` | `multi_session_bundle` | multi-session-harness / barrier-DAG runner |
| `restart_or_external_event` | `external_isolated` | `external_event_bundle` | restart-external-manifest with `event_mode=external_isolated` / isolated-event runner |
| `restart_or_external_event` | `restart_external` | `external_event_bundle` | restart-external-manifest with `event_mode=restart_external` / restart-restore runner |

Runner 的具体 ID/version/SHA 由 input-locked runner registry 按上述 runner class 唯一选出。
`parallel_sql` 只在冻结 conflict-set validator 证明同批 containers 无冲突时合法；否则必须为
`serial_sql`，不得随机降级。Mapping freeze 从 approved atom 和 packing plan 重算全表，
package validation 再从最终 manifests/schedule 字节反向重算，并要求
`harness_route_container_schedule_runner_mismatch=0`。例如 `multi_session_barrier +
multi_session_bundle + serial_sql` 或 restart atom 配 serial runner 都必须 fail closed。

Mapping freeze 还必须证明每个 materialized phase 无损投影回 fixture plan 的 atom-level
`logical_phase_dag`。物理 path/operation ID 只能由 packing 后的 mapping 引入，fixture plan
不得反向依赖它们。

`mapping.json` 冻结后禁止插入、删除或重排编号。覆盖变化必须生成新 revision/run。

Case ID 使用 namespaced subcase ordinal，例如 `S001-C000001`。Packing 完成后，container 按
冻结顺序连续分配 `container_local_ordinal=1..N`，物理文件/bundle 只能由 container ordinal
命名，不能使用可能因装箱产生空洞的 subcase ordinal。每条 statement 的 naming policy 必须
冻结 `filename_prefix`、`object_prefix` 和
`ordinal_width >= max(3, decimal_digits(N))`：

```text
<FILENAME_PREFIX><zero-padded-container-ordinal>.sql
<lowercase-object-prefix>_<zero-padded-container-ordinal>_<object-role>

ALTERCONVERSION00001.sql
alterconversion_00001_source_schema
alterconversion_00001_conversion
```

Run/revision/global IDs、时间和 hash 只进入版本化目录或 manifest，不进入 basename 或 SQL
对象前缀。Bundle 目录使用相同 numbered basename，内部 setup/session/verify/cleanup 文件共享
该对象前缀。物理编号在当前 statement revision 的全部 containers 上连续、无重复、无缺号；
表、视图及适用辅助对象的定义和引用必须使用当前 container prefix。有意跨 container 共享的
对象必须进入 dependency manifest。每个 SQL 文件最后一行是非空 SQL/comment，随后恰好一个
LF，不得有尾部空白行。

Naming policy 还必须冻结 PostgreSQL 18 `NAMEDATALEN-1=63` 字节限制、server encoding、quoted/
unquoted folding 规则、每类 object role 的最大 UTF-8 byte budget 和稳定缩写表。Validator 按
PostgreSQL 18 的 folding 与 multibyte-safe truncation 规则重算服务器实际保存的 identifier，并在
同一可并发 execution scope 内要求零碰撞；renderer 不得临时截断。超长 statement/object role
只能使用 approval 前冻结且可逆映射到原 role 的缩写，并把映射纳入 naming policy SHA。

顺序生成期间不预占尚未规划 statement 的全局 offset。最终
全局包按 `(statement_inventory_ordinal, container_local_ordinal)` 生成只读 global ordinal
索引，但不重命名既有文件。这样后续 statement 的新 revision 不会迫使其他 statement 重编号。

正式 payload 使用版本化统一目录，避免覆盖旧 revision：

```text
artifacts/regress/<run-id>/statement-payloads/<category>/<domain>/<statement>/<revision-id>/<global-revision-id>/
└── payload/
    └── shards/
        ├── S00001/
        │   ├── programs/
        │   ├── bundles/
        │   ├── runner-manifests/
        │   ├── payload-manifest.json
        │   ├── shard-validation-report.json
        │   └── publish-candidate.json
        └── S00002/...
```

每个 shard 独占一个最终目录，任何两个 shard 不写同一个 `sql/harness/schedules` 共享目录。
Phase 2 session profile、phase 12 cleanup probe、multi-session DAG 和 restart/external event contract
必须在 shard validation 前作为 per-container immutable files 写入该 shard 的 `runner-manifests/`，
由 payload manifest 和 mapping 绑定；它们是实际语义提取的输入，不得等 schedule 产生后才定义。
每个 container 精确具有一个 `session-profile-manifest` 和一个 `runner-operation-manifest`；允许
session operations 为空，但必须有冻结的 empty reason。两个 artifact 的 semantic payload 至少为：

```yaml
session-profile-manifest:
  container_id: string
  execution_profile_id: string
  runner: {id: string, version: string, sha256: sha256_hex}
  sessions:
    - session_id: string
      operations:
        - operation_id: string
          phase_number: 2
          setting_id: string
          parameters: object
          expected_outcome: success
          expected_sqlstate: "00000"
          semantic_locus_id: string
          coverage_credit: boolean
  intentionally_empty_reason: null | string
runner-operation-manifest:
  container_id: string
  runner: {id: string, version: string, sha256: sha256_hex}
  operations:
    - operation_id: string
      phase_number: 12
      kind: cleanup_probe
      query_id: allowlisted_string
      parameters: object
      policy: {id: string, version: string, sha256: sha256_hex}
      expected_boolean: true
      execution_condition: unconditional_finally
      semantic_locus_id: string
      coverage_credit: false
```

Observed setting application 与 cleanup boolean 只进入 runtime evidence。Profile/operation manifest
的直接 predecessors 精确为 generation contract 和 owning shard assignment；shard validation report
还直接绑定 owning payload manifest 及该 shard 的全部 profile/operation/harness manifests。
Renderer 必须从 mapping 的 planned ID/path/payload descriptor 构造这些 artifacts；validator 从最终
manifest 当前字节重算同一 fixed-domain payload digest 并要求与 mapping expected digest 相等，再
验证完整 artifact semantic SHA 和 predecessors。Mapping 不引用最终 manifest SHA，因此依赖顺序是
mapping → generation contract → runner manifest，不能反向成环。
逐 statement schedules 在全部 shard validated 后写入
`executions/<revision-id>/<global-revision-id>/schedule-staging/`，验证后一次原子 rename 为
`executions/<revision-id>/<global-revision-id>/schedules/`。最终 package 引用 shard payload 和
schedule 的相对路径/
SHA，不复制或改名。Schedule manifest 只是已验证 container/runner-manifest 的稳定顺序与 route
索引，不得新增、覆盖或重新解释 session settings、cleanup probe、barrier 或 external event。
其直接 predecessors 精确为 generation contract、mapping、jobs-final-snapshot 和全部 current
profile/operation/multi-session/external manifests；jobs-final-snapshot 本身直接绑定 mapping、全部
shard assignments、payload manifests 与 shard validation reports。
`current.json` 只提供 UI/计划视图指针，validator 永远按 package 内显式
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
statement-local subcase/container ordinals。

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

生成完成后 validator 在 staging 内验证完整 container 分配集合，先生成并 fsync
immutable `shard-validation-report.json`。该 report 的直接 predecessors 精确为
generation contract、owning shard assignment、payload manifest 及该 shard 全部 current
profile/operation/harness manifests，不依赖 jobs 或 publish marker。随后才生成并 fsync
`publish-candidate.json`，其直接 predecessors 精确为 payload manifest 和该已存在的
shard-validation-report。为保持 retry 确定性，marker 的 semantic payload 精确绑定
run、local revision、global revision、shard、assignment SHA、payload manifest SHA、validation
semantic report SHA 和预期最终相对路径，不包含 attempt、owner 或时间；这些只在 jobs
operational record。之后才把整个 staging 目录以一次同文件系统原子 rename 发布为当前
`<revision-id>/<global-revision-id>/payload/shards/<shard-id>/`，随后 fsync 父目录，并在
jobs 锁内把 report/job state 提升为
validated。目标目录在正常首次发布前必须不存在，不存在逐文件合并或半片可见状态。

若进程在 rename 成功后、report/job state 更新前崩溃，recovery 不得直接把该 job 标 failed。
它必须先检查目标目录：若存在同 assignment 的 `publish-candidate.json`，则从实际字节重新验证
完整 payload/marker/report SHA；完全一致时在 jobs 锁内执行 orphan-publish promotion，只补写
jobs/report pointer 并记录 `state=validated, recovered_orphan_publish=true`。Shard report 已在原子
rename 前写入并与整片一起发布，recovery 禁止补造或改写它。若 marker/字节不一致，
recovery 在锁内把整个目标目录原子 rename 到该 attempt 的 quarantine 路径，fsync 父目录并标
failed，随后显式 retry 才能使用原最终路径。该流程覆盖 crash-before-rename、
crash-after-rename 和 crash-after-report-before-job-state 三个窗口。

同一个 local plan revision 被新的 global revision 选中时，必须在新
`<global-revision-id>` 目录下产生、验证并发布自己的 shard payload；因 runner/payload manifests
直接绑定 global-scoped generation contract，不得把旧 global revision 的 validated job、manifest
或目录标记为 `reuse=true`。Program/bundle 普通字节可由非规范存储层去重，但每个
global revision 的正式 artifact envelope、predecessors、payload manifest 和 validation report 必须独立
生成；存储去重不得作为覆盖信用或 shard completion evidence。普通 lease 到期且目标目录不存在的
`claimed/generating/validating` 由 recovery 命令在锁内标记 failed，保存 attempt 诊断，再由
显式 retry 创建新 attempt；旧 staging 只读隔离，不能被新 attempt 复用。`validated` job 没有
retry，除非创建新 plan revision。

`jobs-final-snapshot.json` 必须从当前 jobs、mapping、published payload、shard reports 和
publish-candidate markers 的
实际字节重建，并满足：

```text
Set(snapshot.shard_id) = Set(mapping.shard_id)
forall shard: state = validated
forall shard:
  assignment_sha = recomputed assignment SHA
  published_payload_sha = recomputed payload SHA
  report_sha = recomputed report SHA
  publish_candidate_id = recomputed current marker artifact ID
  publish_candidate_sha = recomputed current marker semantic SHA
```

该 snapshot 的直接 predecessors 精确包括 mapping、全部 shard assignments、全部 current
payload manifests、shard-validation reports 和 publish-candidate markers。缺失、重复、额外、
failed、未完成 lease 或 stale SHA 任一存在时，不得创建 package。Marker 在任一
validated shard 中被删除或篡改必须使 snapshot/package/[x] 失效，不得因其被排除在
renderer determinism domain 外而忽略。

## 12. 静态验证与守恒证明

### 12.1 五级守恒

语法守恒：

```text
official grammar values
= covered + expected_failure + justified_na
missing = duplicate = pending = 0
```

因子和库存守恒：

```text
derived factor obligations + candidate inventory obligations + candidate RISK obligations
= reconciled obligations
missing = duplicate = pending = 0
```

组合守恒：

```text
candidate interaction multiset
= executable ⊎ impossible ⊎ justified-NA interaction multisets

executable complete interaction record multiset
= product included complete interaction record multiset
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

实际语义守恒：

```text
for every validated subcase k:
  dom(A(k)) = dom(P(k)) = R(k)
  A(k).grammar   = P(k).grammar
  A(k).factor    = P(k).factor
  A(k).inventory = P(k).inventory
  A(k).risk_and_harness = P(k).risk_and_harness

Bag(complete_interaction_projection(A(k), validated atom expected outcome/primary failure)
    for every validated subcase k)
= executable complete interaction record multiset

actual missing = actual duplicate = actual unexpected = 0
```

其中 `R/P/A` 使用第 3.8 节定义。`complete_interaction_projection()` 的 assignment 部分必须从
observed assignments 重新 canonicalize，结果/首因部分必须按第 7.11 节独立投影并与 interaction
record 对比；不能复制 planned ITUP/STUP ID、mapping pointer 或 renderer 输出的 tuple label。

报告必须分别给出 grammar、factor、inventory、tuple、atom、subcase、SQL file、harness
bundle 和 N/A 数量，不能用 SQL 文件数代替覆盖证明。

### 12.2 Shard 静态门禁

验证器必须重新读取实际字节并检查：

Shard gate 的实际字节包括 primary SQL/bundle 和同 shard 已发布的 session-profile、
runner-operation、multi-session、restart/external manifests；phase 2/12 与 harness 的 `A(k)` 必须
从这些 shard-owned artifacts 提取，不依赖尚未发布的 schedule。Schedule 后续只能索引已验证
内容。

- 分配文件零缺失、零额外；
- 连续编号、对象前缀、Huawei header、UTF-8/LF/EOF；
- 追踪 marker 与 mapping 一致；
- 每 subcase 的 primary target phase 精确一次；额外 target/cleanup phases 与 frozen plan
  完全一致且没有额外覆盖信用；
- 每个 subcase 的 `R(k)`、`P(k)`、`A(k)` 逐 context/role 完全相等；缺轴、多轴、错 context、
  错 semantic role、错值和计划外值全部失败；
- 声明的 expected SQLSTATE 是合法五位码并与 approved atom/mapping 一致；静态阶段不得声称
  PostgreSQL 已实际返回该 SQLSTATE，observed SQLSTATE 只由 runtime validator 结算；
- relation/table/type/signature fixture 与 mapping 一致；
- oracle、pre-cleanup、final cleanup 与计划一致；
- 无 placeholder、`pg_sleep`、未授权 shell/program escape 或不稳定输出；
- harness session/barrier/phase 与计划一致；
- external event、authorization、budget、restore 与 route-specific safety policy 一致；
- planned witness index 与独立 extractor 产生的 shard-local actual binding 多重集精确相等；值
  必须位于 registry 规定的 semantic locus，context-only binding 零 coverage credit；本阶段只把
  extractor-produced records 与其 multiset SHA 固化进 immutable shard-validation-report，不生成
  statement 级 `actual-factor-witness-report.json`；
- 本 shard 的 actual semantic assignment 与 atom expected outcome/首因投影组成的完整 interaction
  record multiset，与 mapping 分配的 interaction slice 相等；全 statement 聚合后与 executable
  interaction multiset 的比较输入同样先固化进 shard-validation-report，不在 shard gate 生成
  statement 级 `actual-semantic-interaction-report.json`；
- SQL/bundle SHA 与 shard report 绑定。

失败时不得写入 `validated`。

全部 shard 达到 `validated` 后，先按第 11.1 节原子发布 schedule manifest，再从当前 shard
payload bytes 与 shard-validation reports 重新读取并聚合生成 statement 级
`actual-factor-witness-report.json` 和 `actual-semantic-interaction-report.json`。两份报告的直接
前驱包括 schedule manifest，且只接受 current shard records；缺 shard、重复 record、局部/全局
multiset 不守恒或 schedule 漂移都会使聚合失败。只有该聚合 gate、actual handoff、jobs final、
regeneration 和后续门禁全部通过，statement 才能进入 `statically_validated`。这样 shard
validated 不反向依赖尚未产生的 schedule，证据链无环。

### 12.3 实际语义提取与双向 witness 等式

实际验证器必须独立读取最终 payload bytes；SQL 按 subcase/phase 边界使用 PostgreSQL-compatible
parser 和 psql lexer，fixture/state、single-session session-profile/runner-operation manifests、
multi-session DAG、restart/external manifest 分别按第 7.4.2 节 registry 提取。Marker 只允许
定位边界，不能提供 value 或 coverage credit。
Validator 必须从实际 target branch、冻结 branch-consumer/canonical-intent catalogs 独立重建
`R(k)`；不得用 `P(k)` 决定应运行哪些 axis extractors，否则计划漏轴仍会自证通过。
`A(k)` 则由完整 registry 对实际 bytes 的 discovery result 构造，不能以 `R(k)` 过滤 observed
axis；比较发生在两边都独立完成之后。

`actual-factor-witness-report.json` 每条记录至少包含：

```yaml
obligation_id: string
axis_id: null | string
observed_canonical_value_id: string
subcase_id: string
phase_id: string
proof_kind: string
payload_relative_path: string
payload_sha256: sha256_hex
semantic_locus: string
extractor: {id: string, version: string, sha256: sha256_hex}
value_decoder: {id: string, version: string, sha256: sha256_hex}
coverage_credit: boolean
```

`actual-semantic-interaction-report.json` 每个 subcase 至少保存 `R(k)`、`P(k)`、完整 `A(k)`、
planned/actual semantic tuple projection、实际 tuple ID、interaction/atom 两侧的
`expected_outcome`、`primary_failure_obligation_id`、`primary_failure_reason`、`expected_sqlstate`、
`check_order_rank`、check-order resolver 身份、逐字段 mismatch counters 和 payload SHA；actual tuple
ID 只能从 `A(k)` 重算，结果/首因字段只能来自已批准
interaction 与 atom 两条独立前驱，不能由 renderer 临时推导。两个报告必须满足：

两个 actual reports 的直接 predecessors 必须包括 statement input-lock、frozen mapping、
全部实际 shard payload manifests、session-profile/runner-operation manifests、multi-session/
external manifests 和 schedule manifest；validator 从这些当前字节重算 SHA 后才允许提取。
Semantic extractor registry 和 branch-consumer/canonical-intent catalogs 是 input-lock 绑定的全局
YAML 输入，不是 artifact predecessor。两个 report 的 semantic payload 必须逐一保存其
input-lock binding ID、相对路径、schema/catalog version、raw-byte SHA 和 semantic SHA；validator
必须经由当前 input-lock 读取并重算这些目录，不得把非 artifact YAML 伪装成
`predecessors` 中的 artifact ID。

```text
ExpectedCredit
= Set(GRM/FOB/INV/RISK obligations whose disposition is covered or expected_failure)

ActualCredit
= Set(extractor-produced obligation IDs whose coverage_credit is true)

ActualCredit = ExpectedCredit
ActualCredit intersect ContextOnly = empty

Bag(actual credited witness projection)
= Bag(planned credited witness projection)

Bag(actual complete interaction projection for every validated subcase)
= Bag(executable interaction tuples)

missing_credit = duplicate_binding = unplanned_credit = 0
outcome_mismatch = 0
primary_failure_obligation_mismatch = 0
primary_failure_reason_mismatch = 0
sqlstate_mismatch = 0
check_order_rank_mismatch = 0
check_order_resolver_mismatch = 0
```

上式中的 actual semantic projection 必须把从 `A(k)` 重建的 assignment 与 atom 的结果/首因
投影组合成第 7.9 节完整 interaction record。若 obligation disposition 为 `expected_failure`，
只有同时满足 atom 为 expected failure、该 obligation 是唯一 primary、SQLSTATE/resolver 与
interaction 一致，extractor 才能发出 `coverage_credit=true`；否则即使非法 token 确实存在也
不得计入 `ActualCredit`。运行阶段再把数据库实际 outcome/SQLSTATE/diagnostic locus 与该冻结
期望逐项比较，不能由静态报告冒充实际执行结果。

结构性 `absent`、权限/owner/对象状态、失败首因和多会话时序都必须由对应 proof kind 证明。
计划值只出现在错误 phase、无关辅助对象、注释或 oracle 字符串时不得匹配；失败条件被更早
错误遮蔽时只能作为 `context_only`。Shard-local assignment/witness 等式不成立时，
该 shard 不得进入 `validated`；只能在全部 shard 已 validated 且 schedule 发布后计算的
statement aggregate credit/interaction 等式不成立时，statement 不得进入
`statically_validated` 或 `packaged`，但不回退或改写已发布的 immutable validated shards。

### 12.4 确定性再生成

同一冻结计划必须在两个空目录独立生成，并满足：

```text
published_shard_payload_sha_map
= generation_A_payload_sha_map
= generation_B_payload_sha_map

published_schedule_sha_map
= generation_A_schedule_sha_map
= generation_B_schedule_sha_map
```

`ShardPayloadDeterminismDomain(shard)` 精确等于该 shard `payload-manifest.json` 中按稳定
相对路径列出的全部规范 renderer entries（programs、bundles、runner manifests）再加
`payload-manifest.json` 本身。`publish-candidate.json`、`shard-validation-report.json`、jobs、
attempt/lease 和运行日志明确不属于该域；它们由 publish/hash-graph 门禁另行验证。
Payload manifest 必须拒绝 missing/duplicate/unexpected entry，因此发布者不得通过隐式 glob
或 validator 自选 exclude pattern 改变比较域。

`published_shard_payload_sha_map` 必须按上述 domain 从正式 immutable shard bytes 重新读取，
`published_schedule_sha_map` 必须从正式 execution schedules 目录重新读取；二者都不能引用第一
次 scratch 的预期 map。这样两次 scratch 一致但正式 payload 或 schedule 不同仍会失败。

比较对象只包括 renderer 从同一个 approved mapping 生成的 payload：SQL、harness manifests
和由 mapping 派生的 schedules。Mapping 是冻结输入，不作为 renderer 输出重复比较；jobs、
attempt、lease、运行日志和 shard reports 属于执行状态，也不混入 payload determinism。

`regeneration-report.json` 绑定 plan/approval/mapping SHA、两个隔离 scratch root 的文件相对
路径→SHA map、schedule SHA 和 equality result；scratch 绝对路径不进入 semantic payload。
Package、validation 和 report 生成器分别使用第 13.1 节的 canonical semantic projection 做
确定性测试，排除 attempt、lease、heartbeat 和 wall-clock metadata。

### 12.5 Semantic validator 变异门禁

v2 readiness 前必须对 validator/extractor/parser 执行负向合同测试，并输出冻结的
`semantic-validator-mutation-report.json`。每个 mutation 都应同步重算普通 carrier SHA，保证
失败来自 semantic gate，而不只是旧哈希失效。以下变异必须全部被拒绝：

- 删除实际 target clause，但保留 metadata、marker 和 planned witness；
- 把一个实际值替换成相邻 canonical value；
- 计划 `00,01,10,11`，实际渲染 `00,00,11,11`；
- 删除一个 context-qualified axis，或交换 source/target、left/right context；
- 向 target payload 增加一个计划外但 registry 可识别的 clause/axis；
- 删除某一 canonical source row/selector member 的全部 consumers，但保留 source inventory；
- 只在注释、header、文件名或 oracle 字符串放置计划值；
- 把目标列类型/结构移到无关辅助表；
- 让同一 axis 在实际目标语义中同时出现两个互斥值；
- 用 setup 中更早错误遮蔽 primary expected failure；
- 用单会话 SQL 冒充 multi-session harness；
- 用普通 SQL/comment 冒充 restart/external event；
- 修改或删除 runner session profile 中的 phase 2 setting，但保留 planned assignment/metadata；
- 删除或替换 phase 12 cleanup probe 的 query ID/parameters，但保留 phase projection；
- 给空 coverage plan 配任意 obligation 和无关 `SELECT 42`；
- 把 parser-negative target 的非法 production 改为合法 production，但保留原 marker/metadata；
- 只翻转 atom 的 expected outcome、expected SQLSTATE、primary failure obligation/reason、
  check-order rank 或 resolver，
  但保留 assignments、payload 与普通 hashes；
- 同步篡改 interaction 与 atom 的 failure 六字段并重算普通 hashes，但保留原 assignment 和
  resolver identity；必须在独立 resolver-output recomputation gate 失败；
- 把 interaction 与 atom 的 resolver identity 同步换成目录中另一个有效但不属于当前
  statement/branch/intent 的 profile resolver，并重算普通 hashes；必须在独立
  catalog-selection gate 失败；
- 把本应由 assignment-driven resolver 判定为失败的 interaction 和 atom 同步改成
  `success/00000/null-primary/null-resolver`，保留 assignment 并重算普通 hashes；必须在
  check-order outcome recomputation gate 失败；
- 把 multi-session/restart atom 的 schedule class 或 runner identity 换成 `serial_sql`/serial runner，
  或把 serial atom 换成无 conflict-set 证据的 `parallel_sql`，并重算普通 hashes；必须在
  harness/route/container/schedule/runner crosswalk gate 失败；
- 只翻转 restart-external manifest 的 `event_mode`，或使 mode 与 event types/atom route/runner class
  不一致，并重算普通 hashes；必须在独立 route/event-mode crosswalk gate 失败；
- 让两个 container 的 primary/non-primary operations 使用相同裸 `operation_id`，随后删除其中
  一个 non-primary result，并重算普通 hashes；必须因复合 runtime operation key 的
  missing/partition 门禁失败，不得被裸 ID 过滤掉；
- 在同一个 owner container/subcase 下，让 primary `(source_A, X)` 与 non-primary
  `(source_B, X)` 共享裸 `operation_id=X`，再把 primary key 错指向 source_B 或删除任一结果并重算
  普通 hashes；必须因四元 RuntimeOperationKey 的 exact-FK/missing/partition 门禁失败，不能按
  owner + 裸 ID 合并；
- 修改 shard 后重写 `passed`/普通 hashes，但缺少 actual reports。

报告必须绑定全部 mutation fixture、预期失败 gate、实际失败 gate、validator/extractor/parser
版本和 SHA。任一 mutation 未在预期 semantic gate 失败，`full_statement_coverage_v2`
infrastructure readiness 必须失败，禁止生成正式 SQL。

## 13. 哈希证据链与防篡改

证据链固定为：

```text
input-lock
  -> readiness
  -> source universe/consumption
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
  -> immutable jobs-final snapshot
  -> schedules
  -> actual factor witness report
  -> actual semantic interaction report
  -> actual handoff validation
  -> deterministic regeneration report
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
  input-lock, readiness, source-universe, source-consumption, grammar-ledger, factor-ledger, applicability, na-ledger,
  risk-ledger, intent-axis-ledger, interaction-universe, products, atoms,
  fixture-plan, packing-plan, mapping, obligation-witness-index

validated_plan_root
  = manifest_digest("FSCR_VALIDATED_PLAN_V2",
                    [plan-content-manifest, plan-validation])

generation_contract_root
  = semantic SHA of generation-contract.json
```

`plan-content-manifest.json` 以前述 17 个 artifact 为直接 predecessors；它不包含自身。
`coverage-plan.md` 在 content root 已知后确定性渲染，`plan-validation.json` 以 content manifest
为 predecessor，并在 payload 中绑定 MD raw-byte SHA、mapping SHA、validator version/SHA、
全部 schema/守恒结果。Approval 在全局 handoff closure 和 generation order 后创建，审批对象是
`validated_plan_root + handoff-validation SHA + generation-order SHA`；它必须绑定明确审批结果。Renderer 必须同时验证
`generation_contract_root` 与当前字节重算结果相同。这样 ledger 不回填 atom、validation 不
进入自己验证的 content root、approval 不进入自己审批的 root，三类循环都被消除。
Approval artifact 存在所选 `global-revisions/<gNNNN>/approvals/<statement>.json`，不回写 local
plan revision；同一 local plan 被另一 global revision 选择时必须生成新的 global-scoped approval。

Approval 之后由控制器创建真正的 artifact envelope：

```text
global-revisions/<gNNNN>/generation-contracts/<statement>.json
```

它的直接 predecessors 精确为 plan-content-manifest、plan-validation、global-handoff-validation、
generation-order 和 approval，semantic payload 固定保存 `validated_plan_root`、handoff root、
generation-order SHA、mapping SHA、
renderer/runner/policy SHA 与 `generation_allowed=true`。它的 artifact semantic SHA 就是
`generation_contract_root`，因此 renderer/package 可以引用真实 artifact，而不是引用一个无
envelope 的裸 digest。任一 predecessor 漂移都使 contract artifact 和后继 package 失效。

Mutable `jobs.json` 只属于 operational state，不能作为 package 的规范前驱。全部 shard validated
后生成不可变 `jobs-final-snapshot.json`。在 package 前，控制器从 generation contract 和 input-locked
normalization policy catalog 生成 execution 目录唯一的 `normalization-policy.json`；其直接
predecessors 精确为 generation contract 与绑定该 policy source/version/SHA 的 statement
input-lock artifact，且不得依赖 package 或 runtime record。Package 的直接 predecessors必须包括
normalization policy、generation
contract、所有 shard payload/report/publish-candidate artifacts、`actual-factor-witness-report.json`、
`actual-semantic-interaction-report.json`、`actual-handoff-validation.json`、jobs final snapshot、
`regeneration-report.json` 和
schedule manifest。Final validation 直接依赖 package 和所有当前
payload manifest、shard-validation report 和 publish-candidate marker。Regeneration report 变化会使
package/final validation/checkbox 全部失效。

每个后继 artifact 必须精确列出所有直接 predecessors。Validator 从当前字节重算每层 SHA
和 root，不接受 artifact 内自报 hash。

### 13.2 逐语句 evidence 拓扑

逐语句静态 evidence 至少为：

```text
artifacts/intermediates/full-statement-coverage-v2/<run-id>/<statement>/
├── current.json
├── plan-revisions/<revision-id>/
│   └── <第 4.3 节的不可变计划文件>
└── executions/<revision-id>/<global-revision-id>/
    ├── jobs.json
    ├── attempts/
    ├── published-payload-index.json
    ├── reports/full-validation.json
    ├── actual-factor-witness-report.json
    ├── actual-semantic-interaction-report.json
    ├── actual-handoff-validation.json
    ├── jobs-final-snapshot.json
    ├── regeneration-report.json
    ├── schedules/
    ├── package.json
    ├── validation.json
    └── execution-summary.md
```

`published-payload-index.json` 只引用第 11.1 节正式 immutable shard 及其内部
`shard-validation-report.json`/`publish-candidate.json` 的相对路径和 SHA，并把全部 current
payload manifests、reports 和 markers 列为直接 predecessors；执行 evidence 目录不复制
payload/report/marker，也不维护第二份 `shards/`。

## 14. Package 与运行证据边界

逐 statement 静态 package 的 artifact envelope `kind` 固定为第 4.6 节注册的
`package-manifest`；其 `semantic_payload` 必须明确：

```json
{
  "package_kind": "regress_input_package",
  "package_scope": "static_input_all_routes",
  "runtime_status": "not_run",
  "expected_output_included": false,
  "execution_or_comparison_performed": false
}
```

`serial_sql/parallel_sql` 生成 pg_regress-compatible schedules，并由 V2 runner 在每个 primary
program 后执行第 8.1 节结构化 cleanup probe；`external_isolated/multi_session/
restart_external` 生成版本化 runner manifests，不伪装成 pg_regress 单文件 test。Package 分别
列出各 route 的 case/atom 数、相对路径、runner SHA 和 payload SHA，所有 route 的 atom 并集
必须等于 executable atom multiset。
Normalization policy 必须在任何执行及 package 创建前冻结在当前 statement execution 目录的
唯一 `normalization-policy.json`，并作为静态 package 的直接 predecessor；每个 RNNNN 只通过
artifact ID/SHA 引用该文件，不复制第二份 policy。`runtime-profile` 是 package 的后继，禁止
为了运行环境反向改写静态 package。

数据库运行证据独立保存，至少绑定 PostgreSQL 精确版本、build capability、初始化参数、
package SHA、harness 版本、成功数、预期失败数、非预期错误、false oracle、cleanup 结果和
日志 SHA。

不可变 runtime 证据保存为：

```text
artifacts/intermediates/full-statement-coverage-v2/<run-id>/<statement>/
└── runtime/<revision-id>/<global-revision-id>/<package-sha256>/RNNNN/
    ├── runtime-profile.json
    ├── run-01/
    │   ├── run-contract.json
    │   ├── clean-state-report.json
    │   ├── logs-manifest.json
    │   ├── route-results/
    │   ├── cleanup-reports/
    │   ├── restore-reports/
    │   └── execution-manifest.json
    ├── run-02/
    │   └── <same immutable structure as run-01>
    ├── two-run-comparison.json
    ├── cleanup-summary.json
    ├── restore-summary.json
    └── runtime-validation.json
```

每次 run 的预执行 `run-contract` 至少保存 run ordinal、package artifact ID/SHA、PostgreSQL
version/build/init profile、runner ID/version/SHA、runtime/normalization policy SHA、baseline policy、
reset strategy、ordered container IDs、route manifest IDs 和冻结 limits。每份
`clean-state-report` 至少保存 run ordinal、baseline policy、expected/observed baseline semantic SHA、
全部 check 的 probe/value/raw-byte SHA/pass、missing/duplicate/unexpected counts、
`target_execution_started=false` 和最终 `passed`。只有 expected/observed baseline SHA 相等、全部
checks PASS 且 report 原子发布后，runner 才能开始该 run 的任何 target。Post-run
`execution-manifest` 保存 immutable result summary，并以 run-contract、clean-state、logs、全部
route/cleanup/required restore reports 为直接 predecessors；它不是 clean-state 的前驱。

`route-result` 是 per-container 的 strict artifact，但必须逐 subcase 结算，不得用“container
已启动”代替其内全部 atom 已执行。其 semantic payload 至少包含：

```yaml
run_ordinal: 1 | 2
route: serial_sql | parallel_sql | external_isolated | multi_session | restart_external
container_id: string
payload_manifest_id: string
subcase_results:
  - subcase_id: string
    atom_id: string
    target_intent_execution_count: 1
    primary_target_operation_key:
      {owner_container_id: string, owner_subcase_id: string,
       expected_source_artifact_id: string, operation_id: string}
    observed_outcome: success | expected_failure | unexpected_failure | not_executed
    observed_sqlstate: sqlstate5 | null
    diagnostic_locus: null | nonempty_structured_locator
    diagnostic_evidence_sha256: null | sha256_hex
    observed_primary_failure_obligation_id: null | string
    observed_primary_failure_reason: null | string
    observed_check_order_rank: null | nonnegative_integer
    observed_check_order_resolver: null | {id: string, version: string, sha256: sha256_hex}
    oracle_results:
      - {oracle_id: string, passed: boolean, observed_bytes_sha256: sha256_hex}
    expected_projection_match: boolean
operation_results:
  - operation_id: string
    operation_kind: session_setting | target | opponent_session | barrier | cleanup_probe |
                    cleanup_step | external_event | restart_event | restore_step
    owner_container_id: string
    owner_subcase_id: null | string
    expected_source_artifact_id: string
    observed_execution_count: nonnegative_integer
    observed_value: null | canonical_json_value
    observed_outcome: success | expected_failure | unexpected_failure | not_executed
    observed_sqlstate: sqlstate5 | null
    observed_locus: nonempty_structured_locator
    dependency_trace: []
    passed: boolean
missing_subcases: nonnegative_integer
duplicate_subcases: nonnegative_integer
unexpected_subcases: nonnegative_integer
outcome_mismatches: nonnegative_integer
sqlstate_mismatches: nonnegative_integer
diagnostic_locus_mismatches: nonnegative_integer
oracle_failures: nonnegative_integer
```

Runner 必须从 current mapping/package 重建每次 run 的预期 subcase/atom multiset，并且每次
独立满足：

```text
ExpectedContainers(run_i)
= Bag((container_id, execution_route, payload_manifest_id)
      independently joined from current mapping + schedule + package + run-contract)

Bag((rr.container_id, rr.route, rr.payload_manifest_id)
    for rr in RouteResults(run_i))
= ExpectedContainers(run_i)

Bag((rr.container_id, sr.subcase_id, sr.atom_id)
    for rr in RouteResults(run_i)
    for sr in rr.subcase_results)
= Bag((row.container_id, row.subcase_id, row.atom_id)
      for row in CurrentMapping.executable_subcase_rows)

For every executable mapping row, let p8 = row.materialized_phase_projection[8]
and f8 = the fixture-plan logical phase referenced by p8.logical_phase_id, and let
primary_record = the sole semantic-extractor-registry primary_target_operation row
keyed by the independently discovered
(statement_key, grammar_branch_id, canonical_intent_class_id):
  f8.logical_operation_ids has exactly one member
  p8.logical_operation_ids equals f8.logical_operation_ids
  p8.artifact_id and p8.payload_relative_path are non-null
  p8.operation_locator is one non-null canonical structured locator
  p8.operation_locator resolves in p8.artifact_id to exactly one operation
  primary_record.extractor applied to the actual p8 artifact bytes returns exactly
    p8.operation_locator and the same operation

primary_target_source_artifact_id(p8) = p8.artifact_id
primary_target_operation_id(p8) = the sole member of p8.logical_operation_ids
primary_target_locus(p8)
= the canonical structured locator object
  {artifact_id: p8.artifact_id,
   payload_relative_path: p8.payload_relative_path,
   operation_locator: p8.operation_locator}
  whose equality and digest projection use its JCS bytes

ExpectedPrimaryTargetOperations(run_i)
= Bag((row.container_id, row.subcase_id, row.atom_id,
       primary_target_source_artifact_id(row.materialized_phase_projection[8]),
       primary_target_operation_id(row.materialized_phase_projection[8]),
       1,
       approved_atom.expected_outcome, approved_atom.expected_sqlstate,
       primary_target_locus(row.materialized_phase_projection[8]))
      for row in CurrentMapping.executable_subcase_rows)

ObservedPrimaryTargetOperations(run_i)
= Bag((rr.container_id, sr.subcase_id, sr.atom_id,
       op.expected_source_artifact_id, op.operation_id, op.observed_execution_count,
       op.observed_outcome, op.observed_sqlstate, op.observed_locus)
      for rr in RouteResults(run_i)
      for sr in rr.subcase_results
      for op in rr.operation_results
      if RuntimeOperationKey(op) = RuntimeOperationKey(sr.primary_target_operation_key)
         and op.operation_kind = target
         and op.owner_container_id = rr.container_id
         and op.owner_subcase_id = sr.subcase_id)

ObservedPrimaryTargetOperations(run_i) = ExpectedPrimaryTargetOperations(run_i)

FrozenPhase8DependencyDAG(row)
= the exact transitive predecessor subgraph ending at fixture phase 8,
  rebuilt from row's fixture-plan logical_phase_dag and mapped operation IDs

forall op in ObservedPrimaryTargetOperationRecords(run_i):
  op.observed_execution_count = 1
  op.passed = true
  op.dependency_trace contains every vertex/edge of
    FrozenPhase8DependencyDAG(the unique owning mapping row) exactly once,
    in a valid topological order, with no extra vertex or edge

forall executable subcase in run i:
  target_intent_execution_count = primary target op.observed_execution_count = 1
  observed_outcome = approved atom.expected_outcome
  observed_sqlstate = approved atom.expected_sqlstate
  diagnostic_locus = approved target/failure locus
  observed_primary_failure_obligation_id = approved atom.primary_failure_obligation_id
  observed_primary_failure_reason = approved atom.primary_failure_reason
  observed_check_order_rank = approved atom.check_order_rank
  observed_check_order_resolver = approved atom.check_order_resolver
  every required oracle passed = true

missing_subcases = duplicate_subcases = unexpected_subcases = 0
outcome_mismatches = sqlstate_mismatches = diagnostic_locus_mismatches = oracle_failures = 0
primary_failure_obligation_mismatches = primary_failure_reason_mismatches = 0
check_order_rank_mismatches = check_order_resolver_mismatches = 0
primary_target_missing = primary_target_duplicate = primary_target_unexpected = 0
primary_target_owner_mismatch = primary_target_result_mismatch = 0
primary_target_execution_count_mismatch = 0
primary_target_pass_mismatch = primary_target_dependency_mismatch = 0
container_missing = container_duplicate = container_unexpected = 0
container_route_mismatch = container_payload_mismatch = subcase_owner_mismatch = 0
```

上面三个 `primary_target_*` helper 是规范算法，不是 renderer 可自报字段。Phase 8 的
`operation_locator` 必须由第 7.4.2 节与 actual bytes 匹配的 `target_ast | target_token_stream |
parser_rejection` primary record 独立解析；它必须与 extractor registry 为该 statement、official
branch 和 canonical intent 唯一选出的 enclosing target-operation locus 规范 JSON 相等。各
axis/value target witness 只需以 owner ID 指向该 primary record，并证明自己的叶级 locus 位于其内，
不得参与 primary record 选择。Fixture/mapping 中 phase 8 的
logical operation 为零或多于一个、locator 解析为零或多个 operation、registry locus 不一致，或
locator 只命中 comment/string decoy，都使静态验证及 runtime validation 失败。

Mapping、schedule、package 和 run-contract 对同一 container 的 route/payload 必须先独立一致，否则
`ExpectedContainers` 不得产生。每个 `subcase_results[]` 的宿主就是包含它的
`rr.container_id`；它必须与 mapping row 的 `container_id` 相等，不得把正确
subcase result 挂到错误 container/route 上取得运行信用。
`primary_target_operation_key` 必须以完整 RuntimeOperationKey 在同一 route-result 的
`operation_results[]` 中精确外键
到一条 `operation_kind=target`、owner container/subcase 相同的记录。Subcase 不保存第二份
自报的 target-key list；其他 multi-session target phases 必须从 current harness/external manifests
独立进入 `ExpectedNonPrimaryRuntimeOperations` 并逐条结算。只有冻结 phase-8 primary operation
取得该 atom 的 primary target execution 信用。Bogus key、跨 route-result 引用、错 owner/kind，或仅自报
`target_intent_execution_count=1` 都必须失败。

Observed primary failure 不得从 approved atom 复制。Runner 必须保存 PostgreSQL 原始
diagnostic/protocol bytes SHA、实际 SQLSTATE、target operation locus 和运行时 precheck/state probes，
再使用 input-locked PostgreSQL 18.4 check-order catalog 和 runtime failure classifier 独立重建
`observed_primary_failure_obligation_id/reason/rank/resolver`。Classifier 只能消费实际
diagnostic/state 和 catalog-selected profile，不得读取 atom 的 expected primary fields。Success 的四个 observed
failure 字段必须为 null；expected failure 的四个字段必须与 approved atom 逐项相等。
相同 SQLSTATE/相同 target locus 但命中了更早 check 的结果必须触发 primary/check-order
mismatch 并进入 `runtime_failed`，不得靠静态 actual report 中的 approved 投影替代。

`not_executed` 只能记录中断事实，不能在 `runtime_verified` 中通过。一个装箱 program
中途退出、跳过后续 subcase、重复执行同一 target intent，或错误发生在 setup/cleanup
而非冻结 target/failure locus，即使 container 有 logs/cleanup，也必须进入 `runtime_failed`。

运行时还必须结算全部非 primary-target 操作。每个 session-profile、runner-operation、
multi-session harness、restart/external manifest、cleanup plan 和 required restore plan 都必须为每个
operation 冻结 `operation_id`、kind、owner container/subcase、expected occurrence count、expected
canonical value/result、outcome、SQLSTATE、semantic locus 和 dependency IDs。Phase 2 setting 与 phase 12
cleanup probe 的 expected occurrence count 精确为 1；barrier/opponent/external/restart/restore 按各自冻结
DAG 保存精确次数。各 run 必须满足：

```text
ExpectedNonPrimaryRuntimeOperations(run_i)
= Bag((owner_container_id, owner_subcase_id, expected_source_artifact_id,
       operation_id, operation_kind,
       expected_occurrence_count, expected_value, expected_outcome,
       expected_sqlstate, semantic_locus, dependency_ids)
      from every current profile/runner/harness/event/cleanup/restore manifest
      where (owner_container_id, owner_subcase_id, expected_source_artifact_id, operation_id)
            not in PrimaryTargetOperationKeys(run_i))

AllObservedOperations(run_i)
= Bag(operation-result records
      from every current route-result, cleanup-report and restore-report)

ObservedPrimaryTargetOperationRecords(run_i)
= the exact operation-result records referenced by every
   subcase_result.primary_target_operation_key using full RuntimeOperationKey equality

ObservedNonPrimaryRuntimeOperations(run_i)
= Bag(op from AllObservedOperations(run_i)
      where RuntimeOperationKey(op) not in PrimaryTargetOperationKeys(run_i))

AllObservedOperations(run_i)
= ObservedPrimaryTargetOperationRecords(run_i)
   ⊎ ObservedNonPrimaryRuntimeOperations(run_i)

ObservedPrimaryTargetOperationRecords(run_i)
intersect ObservedNonPrimaryRuntimeOperations(run_i) = empty

Bag(project_identity_and_expected_fields(ObservedNonPrimaryRuntimeOperations(run_i)))
= ExpectedNonPrimaryRuntimeOperations(run_i)

forall op in ObservedNonPrimaryRuntimeOperations(run_i):
  observed_execution_count = expected_occurrence_count
  observed_value/result = expected canonical value/result
  observed_outcome = expected_outcome
  observed_sqlstate = expected_sqlstate
  observed_locus = semantic_locus
  dependency_trace satisfies the frozen DAG
  passed = true

operation_missing = operation_duplicate = operation_unexpected = 0
operation_count_mismatch = operation_value_mismatch = operation_outcome_mismatch = 0
operation_sqlstate_mismatch = operation_locus_mismatch = dependency_order_mismatch = 0
operation_partition_missing = operation_partition_duplicate = operation_partition_unexpected = 0
```

Runtime operation identity 固定为：

```text
RuntimeOperationKey(op)
= (op.owner_container_id, op.owner_subcase_id,
   op.expected_source_artifact_id, op.operation_id)
```

`PrimaryTargetOperationKeys(run_i)` 只能从 mapping phase-8 projection 的同一复合键重建。
禁止用裸 `operation_id` 做跨 container/subcase 去重、过滤或 credit；同名 operation 在不同
container、subcase 或 source artifact 中是不同运行义务，必须分别出现并结算。

Session setting 的 observed value 必须来自实际 session state probe，不得复制 manifest parameters；
cleanup probe 必须保存实际 boolean/result bytes；multi-session barrier/opponent 必须保存可验的
event trace；restart/external 与 restore 必须保存 controller 返回值、授权 event ID 和恢复后
probe。只有 primary target operation 按 atom 取得 SQL coverage credit；其他 operation 是运行闭环证据，
但任一缺失或不匹配均阻止 `runtime_verified`。

Runtime DAG 固定为：package + normalization policy → runtime profile；package + runtime profile +
normalization policy → 两个互不依赖的 run-contracts；每个 run-contract + runtime profile → 对应
clean-state；clean-state PASS 后才生成 logs/route/cleanup/restore reports；这些 records 再生成各自
post-run execution-manifest。两次的全部 records 产生 comparison 和 cleanup/restore summaries，
最后产生 runtime validation。不存在
run-01 execution result 成为 run-02 前驱的顺序耦合。

`runtime-current.json` 只保存指针；每次运行分配新 RNNNN，不覆盖历史。Runtime validation 的直接
predecessors 精确包括 current package、runtime-profile、normalization-policy、run-01/run-02
run-contracts、run-01/run-02 execution manifests、两份 clean-state reports、全部 route results/logs/cleanup/required restore
manifests、two-run-comparison、cleanup-summary 和 restore-summary。Validator 从当前字节重算每个
SHA，并要求两个 run-contracts 的 package/profile/runner/policy/container multiset 相同、run
ordinal 分别为 1/2、两份 clean-state 均在任何 target 前发布且 PASS。缺失、stale、失败或覆盖不全
只能进入 `runtime_failed`。Validator 还必须对 run-01 和 run-02 分别重算上述
container/route/payload multiset、subcase-owner/atom multiset 及全部 mismatch counters；execution manifest 或顶层 summary 的自报数量
不能代替该等式。Validator 同时必须从 current profile/runner/harness/event/
cleanup/restore manifests 和全部 route/cleanup/restore result 当前字节重算
primary/non-primary operation 的无损分区、
`ExpectedNonPrimaryRuntimeOperations/ObservedNonPrimaryRuntimeOperations` 与全部 operation mismatch
counters；只检查
container summary 或 primary target result 不足以进入 `runtime_verified`。它还必须从原始
diagnostic/state evidence 重跑 runtime failure classifier，使全部 primary/check-order mismatch counters
为零。

静态状态、运行状态分开：

```text
planning_state: statically_validated -> packaged
runtime_state: not_run -> running -> runtime_executed -> runtime_verified
                              \-----------------------> runtime_failed
               runtime_failed -> running  (new RNNNN only)
```

`running` 前置条件是 `planning_state=packaged` 且 runtime record 绑定 current package SHA；
`runtime_verified` 还必须证明所有 executable atom 在两次 run 中都各精确执行一次，
且 outcome/SQLSTATE/diagnostic locus/oracle/cleanup 对该 SHA 逐项通过。外部
capability 缺失不能删除 atom，只能保留对应 execution profile 为待执行。

对同一 current package 的 runtime retry 只允许 `runtime_failed -> running`。控制器先在 runtime
锁内分配新的 RNNNN，历史失败 RNNNN 保持只读；然后必须使用 allowlisted recovery/
restore 流程并发布新 record 的 run-01 `clean-state-report`，证明当前环境与冻结
baseline 完全相等且 `target_execution_started=false`。只有该 clean-state PASS 后，才能原子把
`runtime-current.json` 指向新 RNNNN 并把 statement `runtime_state` 改为 `running`。恢复或
clean-state 失败时保持 `runtime_failed`，不得重用旧 record、不得在旧 RNNNN 中续写，
也不得靠将 package 状态重置为 `not_run` 规避恢复门禁。

### 14.1 运行时双执行确定性

第 12.4 节只证明 renderer 的字节确定性，不证明 SQL 在数据库中的行为确定性。每个 execution
container 必须针对同一个 current package SHA、PostgreSQL profile、runner SHA 和预先冻结的
normalization policy，从两个独立干净状态执行两次；第一次为 expected failure 或返回非零时
仍必须执行第二次。

每次执行前生成 clean-state report，执行后生成 cleanup report；restart/external route 还必须
生成 restore report。对每个 container 必须满足：

```text
normalized_stdout_run1 = normalized_stdout_run2
normalized_stderr_run1 = normalized_stderr_run2
exit_status_run1 = exit_status_run2
structured_route_result_run1 = structured_route_result_run2
```

上式的 structured route result 指冻结比较投影，不是两份 artifact envelope 原文。

```text
ComparableRouteResult(rr)
= canonical projection of container_id, route, ordered subcase results,
  ordered operation results, observed outcome/SQLSTATE/locus/oracles,
  dependency traces and mismatch counters
  excluding run_ordinal, artifact/predecessor IDs, runtime record ID,
  timestamps, attempt/lease/worker identity and absolute paths

ComparableRouteResult(route_result_run1)
= ComparableRouteResult(route_result_run2)
```

原始 route-result artifacts 仍分别保存 `run_ordinal=1/2`、完整 envelope 和各自 SHA。
Normalization/comparison policy 必须在 package 前冻结上述 projection 字段和排除字段；
不得为了让两次相等在运行后临时删除语义结果。

原始 stdout/stderr/log 仍完整保存并绑定 SHA。Normalization policy 必须在执行前冻结并绑定
package，禁止根据结果临时增加忽略规则，也不得删除 target SQLSTATE、oracle、timeout、cleanup
或 restore 结果。两份 execution manifest 各自直接绑定对应 run-contract、clean-state、logs、
route、cleanup 和 required restore artifacts；runtime validation 再按第 14 节的精确 predecessor 集合直接绑定两次
全部 evidence，不能只依赖一份顶层 summary 隐式承接 clean-state。

只有全部 executable containers 两次执行、成功/预期失败 oracle、cleanup/restore 和比较均通过，
runtime state 才能进入 `runtime_verified`。Restore 或 cleanup 任一失败都必须进入
`runtime_failed`；下次运行前先证明环境恢复到冻结 baseline。

## 15. 全局计划与自动勾选

全局计划由证据确定性渲染。状态符号：

```text
[ ] `failure_state != null`，或 discovered/planning/stale（origin=legacy_import 也相同）
[~] `failure_state = null` 且 generated/statically_validated 或部分 shard validated
[x] packaged 且完整哈希图复验通过
[R] runtime_verified、two-run determinism/cleanup/restore 全 PASS，且运行报告绑定 current package SHA
```

渲染优先级固定为：`failure_state != null` 先输出 `[ ]`；否则 current package
已 runtime verified 输出 `[R]`；否则 packaged 输出 `[x]`；否则生成中/已生成/部分
validated 输出 `[~]`；其余输出 `[ ]`。`runtime_state=runtime_failed` 不改写已通过的
静态 `[x]`，而在独立 runtime 状态列显示失败；它只阻止 `[R]`。

每次渲染 `[R]` 都必须从当前不可变字节重验第 14 节完整 runtime DAG，包括两份 clean-state；
不得只相信 `runtime-current.json`、summary 字段或缓存状态。任一 current predecessor 漂移立即撤销
`[R]`，历史 runtime record 仍只读保留。

逐语句只有同时满足以下条件才能 `[x]`：

```text
readiness_passed
source_consumption_reconciled
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
actual_factor_witness_validation_passed
actual_semantic_interaction_validation_passed
actual_handoff_validation_passed
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
global actual credited obligations = global covered + expected_failure obligations
global actual complete interaction record multiset = global executable interaction record multiset
all delegated edges have current owner package and actual witness validation
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
├── mapping-index.json
├── by-factor/
│   └── <sql-purpose>/<factor-directory>/<statement>/manifest.json
├── schedules/index.json
├── payload-index.json
├── validation.json
└── package.json
```

上述每个 JSON 都是第 4.6/13.1 节的 strict artifact envelope，kind 分别为
`global-batch-manifest`、`selected-statement-packages`、`global-mapping-index`、
`global-by-factor-manifest`、`global-schedule-index`、`global-payload-index`、
`global-validation` 和 `global-package`。`validation.json` 和 `package.json` 是唯一规范
global-validation/global-package 字节；第 4.2 节 global control 目录只以
`publication-target.json(kind=current-pointer)` 引用它们，不存在第二份真相源。

对所选 global revision，独立 validator 先从冻结 183 statement inventory、
`selected-statement-revisions.json` 和每条 statement current execution bytes 重建：

```text
ExpectedStatementEvidence
= Bag((statement_key, statement_revision_id, global_revision_id,
       statement_package_artifact_id, statement_package_sha,
       final_validation_artifact_id, final_validation_sha,
       actual_factor_report_id, actual_factor_report_sha,
       actual_interaction_report_id, actual_interaction_report_sha,
       actual_handoff_validation_id, actual_handoff_validation_sha,
       jobs_final_snapshot_id, jobs_final_snapshot_sha,
       schedule_manifest_id, schedule_manifest_sha)
      for every one of the exact 183 selected statements)

Bag(selected-statement-packages.records) = ExpectedStatementEvidence
statement_missing = statement_duplicate = statement_unexpected = statement_stale = 0
```

`selected-statement-packages.json` 的直接 predecessors 精确为 selected-statement-revisions
和上述每条 record 引用的全部 current artifacts；不允许只绑定一个自报 package list。
`batch.json` 直接绑定 global-input-lock、selected revisions、generation order 和 handoff
validation。`mapping-index.json` 直接绑定 global-mapping 和 183 份 current statement
mapping；`payload-index.json` 直接绑定 183 份 published-payload-index 及其全部 current
shard payload manifests、shard-validation reports 和 publish-candidate markers；`schedules/index.json`
直接绑定 183 份 current schedule manifests。

每个 `by-factor/.../manifest.json` 的 purpose/factor/statement key 必须来自冻结 inventory
和 global mapping。它的直接 predecessors 精确为 global-mapping、所属 statement
package/published-payload-index/schedule manifest；全部 by-factor manifests 的 path/key 多重集必须与
独立从 inventory+mapping 重算的 expected directory assignment multiset 相等，
`factor_manifest_missing/duplicate/unexpected=0`。这些 index 只引用第 11.1 节 immutable
statement shard/schedule 相对路径和 SHA，不复制 SQL/harness。

`validation.json(kind=global-validation)` 的直接 predecessors **精确**为：global-input-lock、
selected-statement-revisions、handoff-validation、generation-order、global-mapping，
`ExpectedStatementEvidence` 中全部 current statement artifacts，以及 batch、selected packages、
mapping index、全部 by-factor manifests、schedule index 和 payload index。Validator 必须从这些当前
字节重算 183 statement multiset、全局 obligation/atom/interaction/actual-credit Bags、handoff closure
和所有 missing/duplicate/unexpected counters，不得信任 selected list 或 validation payload 自报数量。

`package.json(kind=global-package)` 的直接 predecessors 精确为 global-validation 以及
global-validation 前述的全部 direct predecessor 集合；其 semantic payload 保存 exact 183
statement evidence multiset/count/SHA、全局 obligations/interactions multiset SHA 和所有 publication index
artifact IDs/SHA。缺任一 statement 的 package、final validation、actual reports、jobs 或 schedule，
或任一发布 index 字节漂移，都使 global-validation/global-package 失效。Runner 只消费
该 immutable global package/index；全局目录中不存在 SQL/harness 复制品。Global revision
一经发布只读；任何 statement revision/package 变化创建新 gNNNN 和新全局路径。

全局发布必须先在同一文件系统的
`artifacts/regress/<run-id>/.publishing/<global-revision-id>/` 写入完整树，从当前字节复验
全部 manifests、global-validation 和 global-package，然后 fsync 文件/目录并以一次目录
rename 原子发布到 `<global-revision-id>/`；最终目录必须事先不存在，禁止逐文件
合并或覆盖。Rename 返回后必须立即 fsync 目标父目录
`artifacts/regress/<run-id>/`，确保最终目录项已持久化；只有父目录 fsync 成功并重读正式
package/validation 通过后，才能以临时文件 + fsync +
atomic rename 创建 `publication-target.json(kind=current-pointer)`；其直接 predecessors 精确为
global-validation 和 global-package。崩溃后若最终目录存在，recovery 必须重读完整树；
字节/哈希完全一致才能补发 pointer，否则整目录 quarantine 并 fail closed。
若 `publication-target.json` 已存在但最终目录缺失、不完整或 SHA 不符，validator 必须将
该 pointer/global revision 判定为 corrupt，立即撤销 `[x]`/运行资格并 fail closed；禁止仅凭 pointer
自报 SHA 重建或信任目录。修复必须从 current 183 statement evidence 重新生成新 gNNNN，
保留受损 revision/pointer 作为只读诊断证据。

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
5. canonical factor/source universe、逐 row consumer 投影、zero-consumer 门禁和守恒；
6. object/relation/table/column/signature/type 适用性；
7. mandatory 12 与全部 statement-specific CandidateRISK obligations，missing/duplicate/unexpected/pending 均为零；
8. 每个 product 的 axes、公式、predicate、排除 tuple 和 tuple SHA；
9. atom 数量，以及 expected outcome、primary failure obligation/reason、SQLSTATE、check-order rank/resolver；
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
3. canonical 9,978 source rows 按 statement 完整核账，每 row 至少一个 branch/context/role FOB
   consumer，zero-consumer 为零；
4. candidate relation/table/column-structure/type obligations 每成员/branch/role/context 恰有一个
   disposition；
5. 七份 type inventory 被逐份审计，未被错误做成七维自由积；
6. branch consumer 独立 join 重建全部 FOB/INV 左侧，canonical intent partition 对角拆分检测为零；
7. intent-axis ledger 覆盖全部义务，interaction universe 不是由 products 自报；
8. 每个 product 的 candidate = included ⊎ excluded，所有 included 无损分区 executable
   interaction multiset；
9. 每个 executable interaction 精确产生一个 atom，assignment、expected outcome、SQLSTATE、
   primary failure obligation/reason、check-order rank/resolver 的 atom projection 与 universe 完全相等；
   每个 expected failure 的 resolver 必须由冻结 catalog 按 statement/branch/intent/assignment
   唯一选出并重算，不能由 interaction/atom 自报；
10. grammar/factor/derived assignment 每键单值，expected failure 每 atom 一个首因；success
    atom 不得给 expected-failure obligation 信用；
11. credited/context-only obligation 分离，实际 witness report 零伪信用；
12. 每个 atom 有真实 fixture、target、oracle、cleanup 和 harness；
13. 多会话/重启义务不再以注释或普通单会话 probe 冒充；
14. 装箱前后 atom 多重集合守恒，container 不跨 shard；
15. shard 可中断、重试、整目录原子发布且不改变编号；
16. 两个空目录与正式发布目录的 payload SHA maps 三方相等，两个空目录与正式 schedule 的
    schedule SHA maps 三方相等；
17. delegated N/A 同时通过 183 条 local plan 的计划 handoff closure，以及 owner-first generation
    order 下绑定 current owner package/actual witness 的 actual handoff validation；
18. route safety policy 能覆盖受限语句且不扩大普通 route 权限；
19. 历史 SQL 或 regeneration evidence 漂移会自动撤销完成状态；
20. 几千或几万用例不会触发抽样、轮转或代表值降级；
21. 静态 package 与 runtime evidence 明确分离；
22. 每个 subcase 的 actual axis domain 与 `RequiredSemanticAxes` 相等，actual assignment 与 planned
    assignment 逐 context/role 相等；
23. actual assignment 加 validated atom expected outcome/首因 reason/rank 的完整 interaction record 多重集，与
    executable interaction record 多重集相等；
24. actual credited obligation 集合与 covered/expected_failure obligation 集合双向相等；
25. 第 12.5 节全部 mutation 在预期 semantic gate 被拒绝；
26. 当前 package 的全部 executable subcases/atoms 在两次 run 中各精确出现一次，
    outcome/SQLSTATE/diagnostic locus/observed primary failure/reason/rank/resolver/oracle 逐项与
    approved atom 相等；全部 session setting、
    cleanup probe、barrier/opponent、external/restart、cleanup/restore operations 的 actual Bag 也必须
    与 current manifests 精确相等，并且全部 execution containers 通过第 14.1 节运行时
    双执行确定性后，才允许显示 `[R]`；
27. 只有全部静态门禁通过的语句能在全局 MD 中显示 `[x]`。

## 20. 明确禁止的旧做法

- SQL 先生成，plan/coverage evidence 后补；
- 只按 matrix 的局部 required values 宣称全因子覆盖；
- 只看每个 factor value 是否被某个 case ID 引用；
- 只证明边际 factor values 出现，未证明 actual interaction tuple 多重集；
- 从 planned assignment、comment 或 renderer 自报字段复制 actual assignment；
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

1. 完整性由 grammar、factor、inventory、tuple、atom、mapping 与 actual semantic assignment
   五级守恒证明。
2. 用例数是覆盖推导结果，不是输入指标。
3. 全笛卡尔积只用于彼此独立且兼容的语义轴；其他关系必须显式建模。
4. 类型七目录逐份穷举，只有独立 type roles 做条件积。
5. 计划和 mapping 先冻结并验证，approval 绑定二者后 renderer 才执行。
6. 默认一 atom 一 execution container；装箱只能在 atom 完整后无损进行。
7. 每个 subcase 目标操作精确一次，失败首因唯一，oracle 可区分。
8. 多会话和外部事件使用真实 harness，不伪造运行。
9. 分片解决规模和恢复问题，不通过删覆盖解决。
10. checkbox 是当前哈希证据图的派生结果，不是人工声明。
