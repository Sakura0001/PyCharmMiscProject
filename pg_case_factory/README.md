# pg_case_factory

`pg_case_factory` v0.2 把特性文档转成可追溯、可核账、可恢复的 PostgreSQL 18.4 SQL 兼容性测试。upstream PostgreSQL 18.4 是 SQL 和用户可见输出 oracle；DUT 的任何未解释差异都应进入 finding，而不是被静默忽略。

项目由两部分组成：

- `skills/pg-sql-generation/`：指导 agent 分析文档、完整枚举因子、逐 test point 生成 SQL，并执行差分回归。
- `src/pg_case_factory/`：提供 YAML contracts、完整笛卡尔积展开、覆盖 reconciliation、持久 job 状态、run artifacts、单会话 psql 执行、文本比较、质量审计和 skill 打包。

## v0.2 工作流

```text
feature document
  -> feature_manifest.yaml（需求与原文定位）
  -> coverage_plan.yaml（完整 inventory axes）
  -> coverage_obligations.json（全量笛卡尔积与分类）
  -> one durable job / test point
  -> case manifests + deterministic SQL
  -> upstream PG18.4 execution
  -> DUT execution
  -> formal exact output comparison（不接受 normalization）
  -> findings + regression/sql + regression/expected
```

完整性门禁固定为：

```text
required = success + expected_failure + justified_na
missing = 0
```

每份计划必须恰好给出 `object`、`relation`、`table`、`column_type` 4 个 scope decision。其中 `table` 由 5 个正交 axis 共同定义：`relpersistence`、`partition_role`、`partition_strategy`、`inheritance_role`、`table_access_method_selection`；`column_type` complete 时必须同时覆盖 7 个互补 inventory：85 个可执行 core profile、85 个 exact non-pseudo built-in、79 个自动数组 element family、26 个 pseudo-type 负例、16 个声明别名、60 个 typmod 边界和 8 个用户自定义类型家族。此外必须逐项决定 12 类 mandatory risk：`syntax`、`operation`、`lifecycle`、`data_profile`、`large_value_toast`、`transaction`、`partitioning`、`index_constraint_trigger`、`privilege`、`maintenance`、`concurrency`、`restart_recovery`；特性文档揭示的 read path、MVCC、WAL/故障点、TOAST 物理策略等风险必须作为额外 risk decision 保留，不能硬塞进 12 项后丢失语义。

relation/table/column type、语法分支及其他适用 inventory 不允许使用 representative sampling。feature-local inline inventory 还必须写明推导方法、feature 与 PG18 双重来源定位、排除策略和审查状态，不能删值后只重算自签名 hash。确实不适用的值仍保留在 axis 中，并通过 `justified_na + reason` 核账；缺少 COPY protocol、privileged object administration、extension files、logical replication、postgres_fdw、LZ4、多会话或故障注入 harness 属于阻塞，不能伪装成 N/A。仓库中的 coverage plan 模板是一个可重复展开的 storage cross-product 基础包：当前固定为 3,175 个 obligation（2,787 success、153 expected failure、235 justified N/A、0 missing），覆盖 37 个 axes 和 25 个 test points。这个数字只证明模板已声明 axes 的分类闭包，不是任意特性计划的固定配额，也不自动证明 183 个 statement 的 9,978 个 factor-value 已完成特性适用性审计。

## 快速开始

安装并查看命令：

```bash
uv sync
uv run pg-case --help
```

先在 run 外完成 feature manifest、base coverage plan、execution profile 和 PG18.4 applicability bundle。`metadata.unresolved_questions` 可以在分析期间记录问题，但正式初始化前必须是空 list。Applicability 必须审完固定 183/3,357/9,978 universe、`--require-complete` 通过并 compile 成单独 plan，不能直接用 base plan 初始化：

```bash
uv run pg-case applicability validate work/<run-id>/applicability/feature_applicability_index.yaml \
  --repository-root . \
  --manifest work/<run-id>/feature_manifest.yaml \
  --require-complete

uv run pg-case applicability compile \
  --manifest work/<run-id>/feature_manifest.yaml \
  --base-plan work/<run-id>/coverage_plan.yaml \
  --index work/<run-id>/applicability/feature_applicability_index.yaml \
  --output work/<run-id>/compiled_coverage_plan.yaml \
  --repository-root . --inventory-root .

uv run pg-case run init --root . --run-id <run-id> \
  --manifest work/<run-id>/feature_manifest.yaml \
  --plan work/<run-id>/compiled_coverage_plan.yaml \
  --execution-profile work/<run-id>/execution_profile.yaml \
  --applicability-index work/<run-id>/applicability/feature_applicability_index.yaml \
  --inventory-root .
```

`run init` 在 staging 中完整快照 manifest、特性原文、compiled plan、obligations、execution profile、inventory、applicability index/reviews/ledger/matrix witnesses，全部复验后才原子发布 run。`--resume` 要求这组输入和全部 digest 不变。manifest 必须显式声明 `metadata.unresolved_questions: []`。使用 `run status`/`run transition` 保存进度；`run next --jobs ... --limit 1` 按计划顺序和 packaged dependency 返回下一个 point 的完整 context。CLI 不创建 Codex child，主 Agent按该 context 一次最多派一个 child；没有 subagent 能力时串行执行同一 point。

每次正常前向状态转换都必须提交已存在、位于当前 run 内且属于该状态允许目录的 `--evidence`。例如：

```bash
uv run pg-case run transition artifacts/runs/<run-id>/jobs/jobs.json \
  TP-OBJECT-LIFECYCLE audited \
  --evidence jobs/audits/TP-OBJECT-LIFECYCLE.json
```

`jobs/jobs.json` 使用 schema v3：每次转换会记录 evidence 路径及文件 SHA-256，后续转换、`run status` 和最终 `packaged` 都会重新核验，`jobs/jobs.json` 本身是可变控制状态，不能充当 evidence。`generated` 不是“有一个 SQL 就算完成”：它必须精确包含该 test point **全部 executable obligations** 的 case manifest 与 SQL，一一 reconciliation 后才可推进。reference、DUT、comparison 状态同样必须覆盖该 point 的全部 case JSON。只有 `failed --error <reason>` 和 `retry` 不接收 `--evidence`。

每个 executable obligation 对应一个 case manifest。manifest 只允许一个确定性 SQL 文件，并以顶层 `sql_sha256` 绑定其精确 UTF-8 bytes；不同 obligation 不能复用同一路径或同一 SQL 内容。obligation 与 case 还必须一致声明 `execution_profile`：普通安全单会话为 `basic_psql`；需要 COPY STDIN、特权、多会话、重启或故障控制的 case 为 `external_isolated`，并绑定该 test point 风险决策中已声明的 `execution_harness`。`external-copy-ingest` 的唯一 SQL 还必须是自包含 psql 程序：直接 `COPY ... FROM STDIN;` 后内联至少一行 payload，并用独立行 `\.` 终止；reconciliation 会拒绝空/缺失终止符、外部文件、PROGRAM、`\copy`、COPY TO 和 out-of-band stdin。外部 harness 必须在两端执行这一个 manifest-bound exact SQL，不能另喂 payload。`expected_failure` case 还必须在 `comparison.expected_sqlstate` 写 PostgreSQL 18.4 的五字符 SQLSTATE。

SQL 生成完成后，用 `plan reconcile-cases` 证明每个可执行 obligation 恰有一个 case manifest；缺失、重复、意外或 outcome 不一致都会返回非零：

```bash
uv run pg-case plan reconcile-cases artifacts/runs/<run-id>/plans/coverage_plan.yaml \
  --manifest artifacts/runs/<run-id>/inputs/feature_manifest.yaml \
  --cases artifacts/runs/<run-id>/cases/manifests \
  --artifact-root artifacts/runs/<run-id> \
  --inventory-root .
```

## 差分执行

基础 runner 会在 reference 完整执行两次、在 DUT 完整执行两次，先要求每端两次的 return code、stdout、stderr 逐字节相同，再做 reference-vs-DUT exact comparison：

```bash
uv run pg-case run differential artifacts/runs/<run-id>/cases/sql/<case-id>.sql \
  --run-root artifacts/runs/<run-id> \
  --case-id <case-id> \
  --case-manifest artifacts/runs/<run-id>/cases/manifests/<case-id>.yaml
```

formal 命令优先且默认从当前 run 的不可变 execution profile 读取 reference/DUT service、同名 database、每端 `expected_system_identifier`、相同的 `expected_current_user`、psql executable 和 timeout。两个 expected system ID 必须是不同的正整数十进制字符串，expected user 必须非空且无控制字符；这些值要在可信环境初始化时采集，不能把 service 名本身当作实例锚点。profile contract 固定 `postgresql-18.4`、两个不同的裸 libpq service、两端完全相同的裸 database 名、`stop_on_error: true`、空规则 `exact_text` normalization，以及 `external-libpq-service + persist_credentials: false`；endpoint 不能出现 host、password、URI 或其他额外字段。连接细节和凭据只存在于外部 libpq service/安全凭据文件中。拿到 case artifact 锁后、首个数据库调用前，formal 命令会重新加载 profile 和 case manifest，要求 digest、全部解析设置、case 内容及 SQL path/SHA 仍与锁外结果一致；锁内重载结果才是执行来源。

未绑定 execution profile 的旧 run 仍可完整提供 `--reference-service`、`--reference-database`、`--dut-service`、`--dut-database`，并可选 `--psql`、`--timeout`，保持直接 flags 兼容。profile-bound run 若同时给直接 flags，它们只能与不可变 profile 完全相同；任一冲突都会在连接数据库前失败。手工把 `execution_profile.yaml` 塞入未绑定 run 也会被拒绝。`run execute` 和 `run compare` 仍可作为单目标执行、手工 transcript 比较的底层原语。

formal basic 命令只接受当前 run、`execution_profile: basic_psql` 的 case manifest 和该 manifest 唯一声明的 SQL；external-isolated case 会在连接前被拒绝，必须由计划已声明、ready 时已登记 readiness record 的外部 harness 产生同一 execution/comparison artifact contract。case ID、SQL 路径与 `sql_sha256` 任一不一致也都会在连接数据库前失败；锁内读取的 immutable SQL snapshot 会在首个数据库调用前再次核对该 SHA。每个 execution JSON 和 completion-marker comparison JSON 都必须显式包含 `execution_profile_sha256`：profile-bound run 为当前 run digest，legacy/unprofiled run 为 `null`。job/status gate 会重新从 immutable run profile 计算 reference/DUT service、database、expected system ID/user 和 digest，拒绝缺字段、任一 endpoint anchor 漂移、错 digest 或嵌套 execution snapshot 不一致；external harness 也不能绕过该绑定。它固定 `ON_ERROR_STOP=1` 和 verbose error：`success` 只有 upstream return code 为 0 才有有效 oracle；`expected_failure` 必须让 upstream 非零退出，并且 stderr 中必须恰有一个 verbose `ERROR`/`FATAL`/`PANIC` 终止诊断，其 SQLSTATE 等于 manifest 声明值。NOTICE/WARNING 中出现同一代码不能满足 oracle，多个 error-looking 终止诊断也会拒绝。两端同样报错且文本相同，并不能让错误 outcome 通过。

双目标命令在执行 SQL 前、执行 SQL 的同一个 psql session 内、以及执行后都核验端点身份。reference 与 DUT 都必须报告 `server_version_num=180004`、稳定且非空的身份字段和 `system_identifier`，同会话身份必须与 preflight 相同，postflight 也不得漂移，而且两个 system identifier 必须不同；两端 database 名和 `current_user` 必须相同。仅使用不同 service 名不足以证明连接到了两套数据库。

formal comparison 固定为 `exact_text`：除把 CRLF/CR 统一为 LF 外，不删除行、不替换文本，也不忽略行尾空白或最终换行；return code、stdout 与 stderr 的长度和边界都会参与比较。formal `run differential` 不提供 normalization 开关。底层 `run compare` 的显式规则只适合诊断，不能冒充正式 PostgreSQL 兼容性结果。

基础 runner 必须使用专用最小权限数据库 role；superuser、CREATEDB、CREATEROLE、REPLICATION、BYPASSRLS、`pg_read_server_files`、`pg_write_server_files`、`pg_execute_server_program`，以及可继承/切换到具有这些能力的角色都会被拒绝。该规则只适用于 `basic_psql`；明确路由到 `external_isolated` 的 privileged case 可以按已授权 harness 使用所需权限，但 identity 仍必须完整并精确命中 immutable profile。该 role 还必须能够调用 runner-owned `pg_control_system()` 身份探针；只做最小范围授权，不要为探针授予危险能力。runner 固定 `PGCLIENTENCODING=UTF8`、`LC_ALL=C` 和无颜色输出。basic lexer 会拒绝 psql meta command、`COPY ... PROGRAM` 和 `COPY ... FROM STDIN` data mode，但它不是服务器/宿主机沙箱；动态 SQL、过程语言、扩展、文件/程序访问、多会话、重启、故障注入或集群控制必须进入隔离 external harness。

当前 basic runner 只覆盖单 psql 会话。多会话、重启、故障注入和集群拓扑需要 external harness；`ready` evidence 必须包含 point readiness、`jobs/harnesses/<harness-id>.json` 和其 `jobs/harnesses/implementations/` 文件。record 绑定 execution-profile SHA、implementation path/SHA、event model、probe 和组合 fingerprint；gate 校验结构、计划/profile/实现绑定、自洽和不可变性，但 probe 是否真实运行仍由 harness/操作者负责。

formal differential 在任何 SQL 到达数据库前为 case 获取进程锁并检查 artifact collision。执行结果先写 staging，`comparisons/<case-id>.json` 最后发布并作为完成 marker；没有 marker 的残留是可修复的未完成执行，已有 marker 的 case 只有显式 `--overwrite` 才能重跑。

## Run artifacts

新流程不清空整个 `artifacts/`。每次运行使用隔离目录：

```text
artifacts/runs/<run-id>/
├── run.json
├── inputs/
│   ├── feature_manifest.yaml
│   ├── <preserved-feature-document>
│   └── execution_profile.yaml
├── plans/
├── jobs/
├── cases/
│   ├── manifests/
│   └── sql/
├── executions/
│   ├── reference/
│   └── dut/
├── comparisons/
├── findings/
└── regression/
    ├── sql/
    └── expected/
```

差异必须以如下 finding 绑定原 SQL、两端 execution JSON 和 comparison JSON；四个 artifact 都同时记录 run-relative path 与实际 SHA-256：

```yaml
schema_version: 1
kind: differential_finding
finding_id: FINDING-<case-id>
test_point_id: <test-point-id>
obligation_id: <obligation-id>
case_id: <case-id>
summary: <observable difference>
artifacts:
  sql: {path: cases/sql/<case-id>.sql, sha256: <64-lowercase-hex>}
  reference_execution: {path: executions/reference/<case-id>.json, sha256: <64-lowercase-hex>}
  dut_execution: {path: executions/dut/<case-id>.json, sha256: <64-lowercase-hex>}
  comparison: {path: comparisons/<case-id>.json, sha256: <64-lowercase-hex>}
```

`packaged` evidence 必须精确包含一个 package JSON 以及其中列出的全部 regression SQL/expected 文件。每个 expected 文件必须等于 comparison 中保存的 upstream exact transcript：

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

external harness readiness record 还必须绑定当前 run 的 `execution_profile_sha256`、implementation path/SHA 和非空 event model；fingerprint 覆盖 implementation、event model、profile SHA 与 probe。该结构门禁不是独立 attestation；外部 harness/操作者仍须对 probe 的真实性负责。

旧版 `generated_sql/`、`test_plans/` 等根级目录仅为兼容旧调用保留，不是 v0.2 新 run 的默认位置。

## Skill 与知识库

- [SKILL.md](skills/pg-sql-generation/SKILL.md)：轻量入口和流程导航。
- `references/mainflow/`：特性分析、覆盖设计、job 编排、SQL 生成和差分回归。
- `references/common/`：PG18.4 compatibility profile、factor/type inventories 与公共规则。
- `references/statements/`：statement 语法、因子、约束和渲染信息。
- `references/combinations/`：可审计 baseline 组合矩阵。
- `assets/objects/`：纯基础对象模板。
- `assets/templates/`：feature/coverage/case/execution contracts 的可复制模板。

PG16 factor/type catalogs 作为历史基线保留；PG18.4 factor readiness 由 compatibility profile、PG18 inventory 和逐项审计账本决定。`pg18_type_catalog.md` 把 85 个有限可执行 core profile 与 source-derived concrete、automatic-array、pseudo-type、alias、typmod、user-defined inventories 分开保存。单独的 85 个 profile 不是整个 `pg_type`；只有 complete `column_type` scope 同时绑定全部 7 个维度时，才允许声明模板定义下的完整类型覆盖。

当前 183 个 statement 的 PG18.4 静态目录审查已经完成：账本包含 3,357 个 statement-factor pair 和 9,978 条 statement-factor-value 记录；其中 53 个受版本差异影响的 matrix 被拆成 105 个必测 reference-parity point，105/105 均显式绑定受影响值，共 132 个 factor-value binding。`runtime_verified_statements` 仍为 **0**，组合矩阵也没有把 partial/static declaration 冒充为已验证的 exhaustive、rendered 或 runtime coverage。因此仓库可以声称静态 ready，不能声称任何 statement 已在真实 upstream/DUT 双端完成运行时验证；只有真实执行证据回写后才能提升该等级。

## 质量与发布

```bash
uv run pg-case doctor --root .
uv run python -m unittest discover -s tests -v

uv run pg-case skill package \
  --skill-root skills/pg-sql-generation \
  --output skills.zip
uv run pg-case skill verify skills.zip
```

`doctor` 检查 statement/reference 结构、占位符、SQL 方言、对象 assets 和能力降级。skill 打包使用确定性归档与校验 manifest。`skills.zip` 自包含 Skill 文档、模板和 9,978 行账本，但不内嵌 Python engine；执行 `pg-case` 命令需要当前项目 checkout 或已安装的 `pg-case-factory`。

## 职责边界

- 项目负责：测试计划、完整覆盖核账、SQL、两端执行记录、输出差分和 regression evidence。
- 用户负责：存储层日志观察、底层根因分析和最终缺陷归属。
- agent 负责：读取特性文档并编排现有原语；当前 Python 包不提供通用自然语言文档解析器，也不承诺已连接真实数据库。

详细目录与模块职责见 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)。
