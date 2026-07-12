# 编排可恢复测试点任务

## 目标

为 coverage plan 中每个 test point 建立一个持久 job。主 Codex 严格一次选择一个可派发 point，为它最多分配一个子 Agent，等待该 point 生成、检查、执行、比较和封装全部通过后才选择下一个；失败后从最近成功状态恢复。

## 正式初始化前的 PG18.4 适用性闭环

基础 coverage plan 只表达已设计的特性轴，不能替代 PostgreSQL 18.4 全语句因子审查。正式 `run init` 前，主 Agent 必须亲自完成以下闭环：

1. 从固定账本 scaffold 本特性的适用性 bundle。固定全集必须精确为 183 个 statement、3,357 个 statement-factor pair、9,978 个 factor-value row。
2. 逐 statement 审查全部 9,978 行。每行只能是 `covered` 或带具体 feature/PG18 证据的 justified exclusion；不得剩余 `pending`，不得用“代表性语句/类型”批量代替审查。
3. refresh 并以 `--require-complete` 校验 index；任何计数、语义 SHA、feature ID、requirement ID、证据或 matrix witness 不一致都停止。
4. 把完整 index 编译到一个新的 compiled plan。不要覆盖 base plan，也不要让子 Agent参与或修改 applicability review、base plan 或 compiled plan。
5. 对 compiled plan 再执行完整 validate/expand，确认 `missing = 0`，然后才初始化正式 run。

参考命令：

```bash
pg-case applicability scaffold \
  --repository-root . \
  --feature-id <feature-id> \
  --output work/<run-id>/applicability

# 主 Agent逐项完成 work/<run-id>/applicability/reviews/*.yaml 后：
pg-case applicability refresh \
  work/<run-id>/applicability/feature_applicability_index.yaml \
  --repository-root .

pg-case applicability validate \
  work/<run-id>/applicability/feature_applicability_index.yaml \
  --repository-root . \
  --manifest work/<run-id>/feature_manifest.yaml \
  --require-complete

pg-case applicability compile \
  --manifest work/<run-id>/feature_manifest.yaml \
  --base-plan work/<run-id>/coverage_plan.yaml \
  --index work/<run-id>/applicability/feature_applicability_index.yaml \
  --output work/<run-id>/compiled_coverage_plan.yaml \
  --repository-root . \
  --inventory-root .

pg-case plan expand \
  work/<run-id>/compiled_coverage_plan.yaml \
  --manifest work/<run-id>/feature_manifest.yaml \
  --inventory-root . \
  --applicability-index work/<run-id>/applicability/feature_applicability_index.yaml \
  --applicability-repository-root . \
  --require-complete \
  --output work/<run-id>/coverage_obligations.json
```

## 初始化

先确保覆盖计划已通过 `--require-complete`，再执行：

```bash
pg-case run init \
  --root . \
  --run-id <run-id> \
  --manifest work/<run-id>/feature_manifest.yaml \
  --plan work/<run-id>/compiled_coverage_plan.yaml \
  --execution-profile work/<run-id>/execution_profile.yaml \
  --applicability-index work/<run-id>/applicability/feature_applicability_index.yaml \
  --inventory-root .
```

只有该 run 已经用完全相同的 manifest/compiled plan/execution profile/applicability bundle 初始化时，才对同一命令追加 `--resume`；恢复时仍须提供同一组 work-file。新 run 必须在 run 外完成全部输入后一次性初始化；不能先创建空 run，再手工复制输入或用 resume 静默挂接另一份计划/配置。profile 被规范化保存到 `inputs/execution_profile.yaml`，digest 进入 `run.json`，run 内文件不可编辑；unprofiled legacy run 也必须显式记录 `metadata.execution_profile_sha256: null`，删键不能降级绕过绑定。manifest 必须显式声明 `metadata.unresolved_questions: []`，字段缺失、类型错误或非空都会让初始化在创建 run 前失败。严格 one-job-per-test-point：一个 test point 只对应一个持久 job，但一个 job 可以管理该 point 展开的多个 obligation/case。计划、适用性结论或执行配置变更后不要复用旧 job store，应创建新 run。

## 主 Codex 自动逐点循环

主 Agent必须执行下面的闭环，不能把“请把所有测试做完”作为一个宽泛任务一次性派发：

```text
初始化/恢复正式 run
  -> next --limit 1
  -> 为返回的唯一 test point 创建至多一个 child
  -> 等待 child 交付
  -> 主 Agent逐级校验证据并 transition
  -> point 到 packaged（或明确 failed）
  -> status 重验
  -> 再次 next --limit 1
```

1. 每轮只调用：

   ```bash
   pg-case run next \
     --jobs artifacts/runs/<run-id>/jobs/jobs.json \
     --limit 1
   ```

   `next` 是确定性选择器；主 Agent必须原样保留它返回的 job/test-point ID、当前状态、依赖、requirements、obligations、execution routes、允许写入目录和输入摘要。即使 CLI 支持更大的 limit，也禁止在此工作流使用；禁止自行从 plan 猜测另一个“差不多可跑”的 point。
2. 返回一个 context 时，只为该 test point 创建一个 child，并记录不可变的 `test_point_id -> child/task_id` 所有权。该 child 持有此 point 直到 `packaged` 或 `failed`；主 Agent等待它，不同时派发其他 point，也不为同一 point 创建第二个并发或替代 child。
3. 给 child 传递 `next` 的完整 context，并仅追加完成本 point 所需的最小知识：
   - feature manifest 路径与 requirement IDs；
   - compiled coverage plan、applicability snapshot、test point ID 和该 point 的 obligations；
   - 所需 statement references、combination matrices、对象模板和 common policies；
   - 本 point 的唯一可写目录、批准的 regression batch prefix 与当前 job 状态。
4. child 只写该 point 的 case/SQL/执行/比较/finding/package artifacts。禁止 child 编辑 feature source、manifest、base/compiled plan、applicability bundle、execution profile、`run.json`、`jobs.json`、共享模板、其他 point 目录，或自行新增/删除 obligation。job transition 始终由主 Agent执行。
5. 要求 child 为每个非 `justified_na` obligation 生成一个 case manifest；manifest 的 `execution_profile` 与 `execution_harness` 必须精确复制 obligation 的执行路由。`external-copy-ingest` 必须把 COPY FROM STDIN payload 直接内联到 manifest 唯一 SQL，并用独立行 `\.` 终止；不得生成第二个 payload 文件或要求 harness 另喂 stdin。`justified_na` obligation 保留在 reconciliation 中并保存 reason，不生成伪 SQL。
6. child 返回后，主 Agent读取实际文件、运行 reconciliation/lint/identity/comparison/package 校验，并按状态顺序逐级 transition。不能把 child 的完成声明当作 evidence，不能让 child 自己宣布门禁通过。
7. 只有当前 point 已到 `packaged` 且 `run status` 能重新验证全部历史 evidence，主 Agent才进入下一轮 `next --limit 1`。若 point 进入 `failed`，先修复并执行 `retry`；优先向同一 child 发送续作。原 child 不可用时由主 Agent串行接管，不创建第二个 child，并记录接管原因。
8. `next` 返回空不等于 run 成功。主 Agent必须检查 status：只有全部 job 都是 `packaged` 才完成；若存在 `failed`、未满足依赖或不可派发状态，保持 run 并解决/报告具体阻塞，不得把剩余 point 静默删除。

若当前 Codex 环境没有 subagent 能力，主 Agent直接按 `next` context 串行完成同一 point，使用完全相同的可写边界、状态门禁和证据要求；不得跳过 `next`、批量生成、声称已经派发，或降低完整性。

## Regression SQL 合同

首次派发前，主 Agent必须取得用户明确批准的稳定 batch prefix；所有 child 只能使用该 prefix，不能自行推导或变更。每个 executable case 的 SQL 必须：

- 使用连续、稳定、可追加的 `<prefix><NNN>.sql` 编号；编号宽度至少 3 位，并随本批总规模扩展。文件名与脚本内创建的对象共享同一小写编号前缀，且遵守 PostgreSQL 标识符长度限制。
- 使用固定华为文件头，完整填写 copyright、author、create at、version、description 和 FE；禁止省略 header 或以自由格式替代。
- 是可独立执行的完整脚本，包含 session 级确定性设置、前置清理、对象准备、目标操作、稳定验证和结束清理。一个文件只验证一个可归因结果。
- 在同一 reference endpoint 上完整执行两次，并在同一 DUT endpoint 上完整执行两次；成功和 expected-failure case 都必须证明各自两次的 `(returncode, stdout, stderr)` 逐字节一致。任一端 replay 不一致即失败并保留证据，不得靠删除波动行或输出归一化伪造确定性。
- 只有端内双跑确定性通过后，才做 upstream PostgreSQL 18.4 与 DUT 的 formal exact comparison；package 中的 SQL 必须保持原始 SHA，不得重新生成或改号。

## 状态门禁

按以下顺序推进，不跳级：

```text
planned -> audited -> ready -> generated -> linted
        -> executed_reference -> executed_dut -> compared
        -> triaged -> packaged
```

- `audited`：固定 `jobs/audits/<point>.json` 精确绑定 plan/feature/point/obligations，状态为 approved 且 `unresolved_items=[]`。
- `ready`：固定 `jobs/readiness/<point>.json` 精确绑定 obligations、execution profiles/harnesses 且 `blockers=[]`；所有前置 job 已 `packaged`。若 covered risk 引用 external harness，还必须提交 harness verification 及其 implementation 文件。
- `generated`：该 point 的每个 executable obligation 都有唯一 case manifest 和唯一 SQL，完整 point-level reconciliation 通过。
- `linted`：固定 `jobs/lint/<point>.json` 列全 case/obligation/manifest/SQL 及 SHA；gate 重新读取 SQL，验证 Huawei header、catalog observability 和 route-specific safety，不能用 Agent 自述替代。
- `executed_reference` / `executed_dut`：该 point 每个 case 的对应执行 JSON、原始 stdout/stderr、端点身份、SQL SHA 和 `execution_profile_sha256` 均已保存且互相一致。profile-bound run 的 identity service/database/system_identifier/current_user 必须逐端等于 profile 的 immutable endpoint anchors；legacy run 的 digest 字段必须显式为 `null`。
- `compared`：每个可执行 case 已生成可重算的 formal exact comparison，comparison 与嵌套 execution snapshot 绑定同一 run profile digest，并已计算、记录 upstream outcome/SQLSTATE oracle；oracle 无效时结果必须是 `passed: false`，随后进入 finding。
- `triaged`：差异已转成 finding 或确认一致；不得把差异静默丢弃。
- `packaged`：case、SQL、执行、比较、finding 与 regression 证据闭环。

使用 `pg-case run transition <jobs.json> <job-id> <state> --evidence <run-relative-path>` 记录正常前向转换。`--evidence` 可重复，路径必须已存在、位于当前 run 内，并落在该状态允许的目录。例如：

```bash
pg-case run transition artifacts/runs/<run-id>/jobs/jobs.json \
  TP-COLUMN-DATA-PROFILE generated \
  --evidence cases/manifests/CASE-TP-COLUMN-DATA-PROFILE-0001.yaml \
  --evidence cases/sql/TP-COLUMN-DATA-PROFILE/case_0001.sql
```

上例只有在该 point 确实只有一个 executable obligation 时才完整。多 obligation point 必须重复 `--evidence`，精确列出全部 manifest 和 SQL；不能用一个 SQL/YAML 样本推进。每个 case manifest 恰有一个 `sql_files` 项，并用顶层 `sql_sha256` 绑定精确 bytes；跨 obligation 复用路径或内容会失败。case 的 basic/external route 或 harness 与 obligation 不一致同样失败；external SQL 不交给 basic lexer/runner，而由计划风险已声明且 ready 时已登记 readiness record 的隔离 harness 执行。对 `external-copy-ingest`，reconciliation 还会逐个 SQL fail-closed 检查：至少一个直接 `COPY ... FROM STDIN;`、下一行开始的非空内联 payload、独立 `\.` 终止符、且不存在其他 psql meta command 或 COPY file/PROGRAM/TO。harness 必须对 reference/DUT 分别直接执行 manifest 所指的同一精确 SQL 文件，不能重建脚本或通过 pipe/stdin 注入 payload。`basic_psql` identity 会拒绝 superuser/server-file/program roles；`external_isolated` 可按明确授权保留所需 privilege，但仍须通过 PG18.4 identity 结构/版本、两端不同 system ID、相同 database/current_user，以及逐端 profile service/database/expected-system-ID/expected-user/digest 门禁。`executed_reference`、`executed_dut`、`compared` 也必须分别精确包含该 point 全部 case JSON。失败使用 `failed --error <具体错误>`，不能附 evidence；修复后使用 `retry` 从最近成功状态继续，retry 同样不接受 evidence。

`jobs/jobs.json` 固定为 schema v3。每个状态同时保存 evidence 的 run-relative path 与 SHA-256；下一次转换、`run status` 和最终 package 会重新读取并验证全部历史 evidence。任何文件被替换、清空或修改都会使状态检查失败。不要把可变的 `jobs/jobs.json` 本身作为 evidence；使用 `jobs/audits/<point>.json`、`jobs/readiness/<point>.json`、`jobs/lint/<point>.json` 等固定 sidecar。

## External harness ready 证据

被 plan 的 `execution_harness` 引用时，`ready` evidence 除 point readiness 外，必须精确包含每个 `jobs/harnesses/<harness-id>.json` 及其绑定 implementation 文件：

```json
{
  "schema_version": 1,
  "kind": "execution_harness_verification",
  "harness_id": "external-concurrency-harness",
  "status": "ready",
  "compatibility_target": "postgresql-18.4",
  "execution_profile_sha256": "<run-profile-sha256>",
  "implementation": {"path": "jobs/harnesses/implementations/external-concurrency-harness.py", "sha256": "<implementation-sha256>"},
  "event_model": ["provision", "execute", "collect", "cleanup"],
  "probe": {"command": "<actual isolated probe>", "result": "<stable result>"},
  "fingerprint": "<64-lowercase-hex>",
  "verified_at": "2026-07-12T00:00:00Z"
}
```

`fingerprint` 必须等于 `event_model`、`execution_profile_sha256`、`implementation`、`probe` 组成的对象按 UTF-8、key 排序、紧凑 JSON 序列化后的 SHA-256；implementation SHA 还必须等于 run 内实际文件。它不是任意占位 64 位字符串。

`probe` 必须是非空 object，`verified_at` 必须带时区。此 gate 校验 record 结构、计划绑定、自洽和后续不可变性，但不独立证明 probe 真执行过；外部 harness/操作者负责 probe 真实性和运行验证。plan 中写了 harness 名称或提交 record，都不等于已产生真实运行证据。

## Triage 与 package 证据

任何 `passed: false`（包括输出不同或 upstream oracle 无效）的 case 都必须恰好有一个 finding。finding 的 `artifacts` 必须只包含以下四个绑定，每个都同时提供 run-relative `path` 与文件实际 `sha256`：

```yaml
schema_version: 1
kind: differential_finding
finding_id: FINDING-<case-id>
test_point_id: <test-point-id>
obligation_id: <obligation-id>
case_id: <case-id>
summary: <SQL/user-visible difference>
artifacts:
  sql: {path: cases/sql/<case-id>.sql, sha256: <64-lowercase-hex>}
  reference_execution: {path: executions/reference/<case-id>.json, sha256: <64-lowercase-hex>}
  dut_execution: {path: executions/dut/<case-id>.json, sha256: <64-lowercase-hex>}
  comparison: {path: comparisons/<case-id>.json, sha256: <64-lowercase-hex>}
```

`triaged` evidence 精确包含该 point 的全部 comparison JSON 和所有必需 finding。`packaged` evidence 精确包含一个 `regression_package` JSON 及其列出的所有文件：

```json
{
  "schema_version": 1,
  "kind": "regression_package",
  "test_point_id": "<test-point-id>",
  "batch_prefix": "<user-approved-prefix>",
  "number_width": 3,
  "mapping_sha256": "<stable-mapping-sha256>",
  "cases": [{
    "case_id": "<case-id>",
    "obligation_id": "<obligation-id>",
    "case_ordinal": 1,
    "object_prefix": "<lower-prefix>_001_",
    "sql_file": "regression/sql/<prefix>001.sql",
    "sql_sha256": "<source-case-sql-sha256>",
    "expected_file": "regression/expected/<prefix>001.out",
    "expected_sha256": "<upstream-exact-transcript-sha256>"
  }]
}
```

package 必须列全该 point 的所有 case；regression SQL 必须与 source case SQL SHA 相同，expected 文件必须等于 comparison 保存的 upstream exact transcript。最后一个 job 进入 `packaged` 时还会执行全 run case reconciliation。

## 完整性门禁

- 重新核对 executable obligations 与 case manifests 一一对应。
- 使用下列命令生成机器可读门禁；`--artifact-root` 必填，用于证明 manifest 引用的 SQL 是当前 run 内真实存在的普通文件，不完整时命令返回非零：

```bash
pg-case plan reconcile-cases artifacts/runs/<run-id>/plans/coverage_plan.yaml \
  --cases artifacts/runs/<run-id>/cases/manifests \
  --artifact-root artifacts/runs/<run-id> \
  --manifest artifacts/runs/<run-id>/inputs/feature_manifest.yaml \
  --inventory-root .
```
- 拒绝缺 case、意外 case、obligation ID 不匹配或 outcome 不一致。
- 拒绝缺少 `--artifact-root`、SQL SHA 不一致、跨 obligation 重用 SQL 路径/内容，以及只生成部分 executable obligations。
- 不因某个子 agent 超时而删除 test point；保留失败状态并重试。
- 先完成依赖 job，再推进 dependent job。

## 当前自动化边界

CLI 持久化 job、校验状态转换、提供执行/比较原语，并由 `run next --limit 1` 返回确定性的单 point 派发 context；CLI 本身不创建 Codex child。主 Codex 必须在具备 subagent 工具时按本页循环创建/等待 child，在不具备时串行执行同一 context。两种模式都由主 Agent独占共享输入和状态转换。

当前 statement inventory 的 `runtime_verified_statements=0`。job 只有在相应 SQL、两端 execution JSON、comparison/finding 等真实证据已经落盘后才能推进；静态审查、agent 自述或空 evidence 都不能替代运行时验证。

```yaml
structured_config:
  kind: mainflow
  skill_name: orchestrate_test_points
  job_granularity: one_job_per_test_point
  resumable: true
  require_case_reconciliation: true
  deterministic_selector: pg-case run next --limit 1
  max_in_flight_test_points: 1
  max_child_agents_per_test_point: 1
  auto_dispatch_available: codex-orchestrated
```
