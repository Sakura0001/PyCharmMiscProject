# 设计全量特性覆盖计划

## 目标

把 `feature_manifest.yaml` 转成可验证、可展开、无采样的 `coverage_plan.yaml`。让每一个适用 inventory 值进入覆盖义务，并证明没有静默遗漏。

## 必读输入

- `work/<run-id>/feature_manifest.yaml`（run 初始化前的受控工作副本）
- `assets/templates/coverage_plan_template.yaml`
- `references/common/compatibility_profile.yaml`
- `references/common/statement_support_inventory.yaml`
- `references/common/pg18_factor_catalog.md`
- `references/common/pg18_type_catalog.md`
- `references/combinations/_shared/coverage_inventory.yaml`
- 受影响的 `references/statements/**/*.md`
- 受影响的 `references/combinations/**/*.yaml`

若 inventory 的 PG18.4 审计状态不是 ready，不得把 PG16 基线名称当作 PG18.4 完成证明；将缺口标成待审计并阻止完整性结论。

## 设计步骤

1. 建立 `requirement -> 风险 -> 可观察结果 -> test point` 映射。每条 requirement 至少被一个 test point 引用。
2. 对每个风险逐项审视适用轴，至少检查：
   - 官方 synopsis 的全部语句分支与选项；
   - 对象、relation、table 和 partition 形态；
   - 所有适用的具体列类型、复合类型和依赖对象；
   - NULL、空值、边界值、大值、多行、重复值和数据分布；
   - 创建、读写、修改、删除、回滚、清理等生命周期阶段；
   - 事务状态、隔离级别、savepoint、prepared statement 和会话状态；
   - 权限、owner、schema、tablespace、约束、触发器、索引和分区交互；
   - 文档明确涉及的并发、重启、恢复、故障或长稳边界。
3. 对 `object`、`relation`、`table`、`column_type` 四类 scope 逐一作出决定：要么绑定完整 canonical inventory group，要么写 `not_applicable + reason`；四项缺一不可。`table` complete 时必须同时绑定 5 个正交 axis；`column_type` complete 时必须同时绑定 core profile、exact built-in、automatic array、pseudo-type、declaration alias、typmod、user-defined archetype 7 个 axis。任何一项都不能退化为自定义样本列表。
4. 为每个 axis 设置 `coverage_mode: complete`、`inventory_source`、`inventory_count` 和 `inventory_sha256`，把 inventory 的全部值按原顺序写入 `values`。canonical scope 必须引用固定的共享 inventory group。`inline:<name>` 还必须声明 `description`、`derivation`、同时包含 `feature:<requirement-id>` 与 `pg18:<official-topic>` 的 `source_locators`、`exclusion_policy`，以及 `source_derived|semantic_reviewed` 的 `review_status`；只删值并重算 hash 不能通过。不要使用“典型类型”“代表表”“抽几个分支”或隐式默认值。85 个可执行 core profile 只是 7 个类型维度之一，不能单独证明完整列类型覆盖。
5. 不要从 axis 删除“不支持”或“不经过改动层”的值。保留该值，并用 `expected_failure` 或 `justified_na` 分类；两者都必须有具体 reason。
6. 把会改变目标语义、错误类型或可观察结果的因子列为 `core_axes`。每个 test point 对其 `core_axes` 做完整笛卡尔积。
7. 因子无法与当前 point 合法组合时，拆成另一个 test point 或显式分类。不要用 pairwise、轮转挂靠或抽样代替完整 inventory。
8. 逐项记录至少 12 个 mandatory risk decision：`syntax`、`operation`、`lifecycle`、`data_profile`、`large_value_toast`、`transaction`、`partitioning`、`index_constraint_trigger`、`privilege`、`maintenance`、`concurrency`、`restart_recovery`。每项要么 `covered` 并列出 axes/test points，要么 `not_applicable` 并写具体 reason。特性暴露的 read path、MVCC snapshot、WAL/故障点、TOAST 物理存储、COPY frontend protocol data mode 或外部 provisioning 必须新增独立 risk decision。若执行需要 COPY payload ingestion、extension provisioning、LZ4、privileged role、多会话、重启或故障注入，covered risk 必须填写稳定 `execution_harness` ID；不要把 harness 名称当作已经执行的证据。
9. 为 test point 分配稳定 ID；一个 point 表达一个清晰测试意图，可以展开为多个 obligation。调度层严格建立 one-job-per-test-point；只声明真实的前置 job 依赖，并保证依赖图无环。
10. 为每个组合分类：
   - `success`：脚本应执行成功并验证 PostgreSQL 18.4 行为；
   - `expected_failure`：PostgreSQL 18.4 本身应拒绝该 SQL，且错误输出也参与差分；生成 case manifest 时必须把 upstream 五字符 SQLSTATE 写入 `comparison.expected_sqlstate`；
   - `justified_na`：组合确实不适用，但仍保留在 reconciliation 中。
11. 不确定行为不要提前归为 expected failure。先在 upstream PostgreSQL 18.4 上建立 oracle，或把计划标为未完成。formal pass 不只要求 reference/DUT 文本一致：`success` 必须让 upstream 成功；`expected_failure` 必须让 upstream 非零，并由唯一 verbose `ERROR`/`FATAL`/`PANIC` 终止诊断命中声明 SQLSTATE，NOTICE/WARNING 中的代码不算。
12. 运行契约与完整性检查；`--inventory-root` 是 canonical inventory 路径的信任根：

```bash
pg-case plan validate \
  work/<run-id>/coverage_plan.yaml \
  --manifest work/<run-id>/feature_manifest.yaml \
  --inventory-root .

pg-case plan expand \
  work/<run-id>/coverage_plan.yaml \
  --manifest work/<run-id>/feature_manifest.yaml \
  --inventory-root . \
  --require-complete \
  --output work/<run-id>/coverage_obligations.json
```

13. 只有 reconciliation 同时满足以下条件才批准派发：

```text
required = success + expected_failure + justified_na
missing = 0
```

14. 后续 inventory 变化会导致 count/hash 或 resolved values 不一致；创建新 run，不要在原 run 中静默改写已执行计划。`run init` 保存已经解析的 manifest/feature source/plan 快照、plan digest，以及 canonical execution profile 和它的 metadata digest；`--resume` 只允许完全相同的 run metadata、计划与执行配置。manifest 的 `metadata.unresolved_questions` 必须先由用户决议并清空。

15. 为执行层预先定义不可变 case/evidence 契约：每个 executable obligation 恰有一个 case manifest，每个 manifest 恰有一个 SQL 与其精确 `sql_sha256`，不同 obligation 不得复用 SQL 路径或内容。每个 obligation 还由 test-point execution routing 明确选择 `basic_psql`，或选择 `external_isolated + execution_harness`；case 必须逐项一致，basic differential 不得执行 external case。`external-copy-ingest` case 的同一个 SQL 必须是完整 psql COPY 程序：`COPY ... FROM STDIN;` 后内联至少一行 payload，并以单独一行 `\.` 结束；禁止外部 payload path、`PROGRAM`、`\copy`、pipe 或另行 stdin。job store schema v3 会对每个状态 evidence 保存 SHA 并在 status/package 重验；`generated` 必须通过完整 point-level reconciliation，不能以一个样本 SQL 代表整个 test point。

16. 对所有 `execution_harness` 制定实际 ready probe 和 event model，并把实现保存到 run 的 `jobs/harnesses/implementations/`。`jobs/harnesses/<harness-id>.json` 必须绑定 execution-profile SHA、implementation path/SHA、event model、probe、组合 fingerprint 和带时区 verified_at。gate 证明结构、计划/profile/实现绑定、自洽和不可变性，不独立证明 probe 真实性；缺少任一文件是阻塞，不是 justified N/A。

17. formal differential 固定 case-manifest-bound、stop-on-error 和 exact-only。计划中不要设计“删除波动行即可通过”的 normalization；任何用户可见不稳定性都应通过确定性 setup/SQL 设计解决，或成为 finding，而不是从 formal transcript 中抹掉。

18. manifest、plan 与 run 外的 execution profile 审批后一次性初始化 run；该命令保存解析后的原文、manifest、plan、profile、obligations 和 job store 快照。禁止初始化后手工复制 profile：

```bash
pg-case run init --root . --run-id <run-id> \
  --manifest work/<run-id>/feature_manifest.yaml \
  --plan work/<run-id>/compiled_coverage_plan.yaml \
  --execution-profile work/<run-id>/execution_profile.yaml \
  --applicability-index work/<run-id>/applicability/feature_applicability_index.yaml \
  --inventory-root .
```

仓库自带模板当前确定性展开为 3,175 个 obligation：2,787 success、153 expected failure、235 justified N/A、0 missing，共 37 个 axes、25 个 test points。模板明确覆盖 scan/read path（含 TOAST fetch）、isolation+snapshot、WAL/checkpoint/crash、TOAST storage/compression/threshold/update、relpersistence×recovery、partition×DML、table topology×operation、postgres_fdw standalone/foreign-partition interaction、schedule×concurrency，以及 PostgreSQL 18.4 COPY 的 FORCE_* 列表/通配符、ON_ERROR、REJECT_LIMIT（含 positive-bigint 最大值/overflow）和 LOG_VERBOSITY 正负边界。所有 COPY FROM obligation 都走 `external-copy-ingest` 协议 harness；COPY TO 仅在确定性 `COPY (SELECT ...) TO STDOUT` 形态下走 basic runner。需要 superuser、CREATEDB/CREATEROLE、extension files、logical-replication publisher 或 FDW 的 ObjectType/relkind assignment 必须走对应 external route；内部 subobject/relkind 通过所属对象 DDL 与 catalog observability 测试，禁止伪造不存在的独立 CREATE/DROP。缺少 external harness 是阻塞，不是 N/A。该数值用于验证模板快照和文档示例一致，不是所有特性计划的固定数量。当前 183 个 statement 已完成静态 PG18.4 目录审查，但 `runtime_verified_statements=0`，所以计划阶段不得声称已有真实双端运行证据。

## 规模处理

允许计划很大、执行很慢。通过拆分 test point、限制同时运行的 job 数、持久化状态和断点续跑控制成本；不要通过删类型、删表形态、删语句分支或 representative sampling 控制规模。

```yaml
structured_config:
  kind: mainflow
  skill_name: design_feature_coverage_plan
  input_contract: assets/templates/feature_manifest_template.yaml
  output_contract: assets/templates/coverage_plan_template.yaml
  execution_profile_contract: assets/templates/execution_profile_template.yaml
  axis_coverage_mode: complete
  sampling_allowed: false
  reconciliation: required=success+expected_failure+justified_na
  require_missing_zero: true
```
