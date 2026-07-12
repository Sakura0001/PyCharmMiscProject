# 执行 PG18.4 差分回归

## 目标

把同一份确定性 SQL 分别交给 upstream PostgreSQL 18.4 与 DUT，比较 SQL/用户可见输出。任何无法解释的不一致都生成 finding 候选；存储日志与根因分析由用户完成。

## 准备

1. 在 run 外把 `assets/templates/execution_profile_template.yaml` 复制到 `work/<run-id>/execution_profile.yaml`，完成配置后和 manifest/plan 一起传给 `pg-case run init --execution-profile work/<run-id>/execution_profile.yaml`。CLI 解析后把 canonical snapshot 写入 `inputs/execution_profile.yaml`，把语义 SHA-256 写入 `run.json`。禁止在 run 内手工复制或编辑 profile。
2. profile 只允许 reference/DUT 的裸 libpq service、完全相同的裸数据库名、逐端 `expected_system_identifier` 和共同 `expected_current_user`。expected system ID 必须是在可信环境初始化时采集的不同正整数十进制字符串，expected user 必须相同、非空且无控制字符。把主机、证书和密码放在外部 libpq service 或安全凭据文件中；endpoint 出现 host/password/URI/额外字段、`persist_credentials: true` 或非 external-libpq-service 策略都会在初始化前失败。
3. profile 还固定 `compatibility_target: postgresql-18.4`、`runner.stop_on_error: true`、`comparison.mode: exact_text` 和完全为空的 normalization rules。psql executable 与正整数 timeout 也成为 run 不可变输入；变更它们必须创建新 run。
4. 为基础 runner 配置专用最小权限 role；不得拥有 superuser、CREATEDB、CREATEROLE、REPLICATION、BYPASSRLS、server-file/program roles，也不得继承或切换到具有这些能力的角色，但必须能调用 runner-owned `pg_control_system()` 身份探针。该拒绝只属于 `basic_psql`；明确授权并路由到 `external_isolated` 的 privileged case 可以使用所需权限。无论 route 为何，两个端点都必须报告 `server_version_num=180004` 和完整身份，并逐端精确命中 profile anchors；仅使用不同 service 名不是不同实例的充分证据。
5. 对两个目标使用相同 SQL 文件、数据库初始状态、locale、timezone、session 设置和 runner 参数。

## 单用例差分执行

优先使用双目标命令。它在 reference 完整执行两次、在 DUT 完整执行两次，先要求每端的 return code/stdout/stderr 逐字节确定，再完成跨端精确比较并写入 run-scoped artifacts：

```bash
pg-case run differential artifacts/runs/<run-id>/cases/sql/<case-id>.sql \
  --run-root artifacts/runs/<run-id> \
  --case-id <case-id> \
  --case-manifest artifacts/runs/<run-id>/cases/manifests/<case-id>.yaml
```

命令优先从当前 run 的 profile snapshot 读取 endpoints、psql 与 timeout，并在执行前重验固定路径、非 symlink、canonical bytes 和 `run.json` digest。profile-bound run 若附带 direct flags，它们只能与 snapshot 完全相同；任一冲突均失败。没有绑定 profile 的旧 run 仍可显式提供四个 endpoint flags，并可选 `--psql`/`--timeout`；手工放入一个未绑定 profile 不会被采用，反而会失败。

case manifest 必须位于当前 run 的 `cases/manifests/`，case ID 必须匹配，且命令中的 SQL 必须是 manifest 唯一声明的文件；执行前还会按精确 bytes 核验顶层 `sql_sha256`。本命令只执行与 obligation 一致的 `execution_profile: basic_psql`；`external_isolated` case 必须同时声明计划路由指定的 harness，由该隔离 harness 产生同一 execution/comparison artifact contract，basic 命令会在连接前拒绝。`external-copy-ingest` 的 harness 不接收单独 payload：它只能在核验 manifest 路径与 SHA 后，对两端直接执行该唯一 SQL 文件。文件本身须包含直接 `COPY ... FROM STDIN;`、下一行开始的至少一行内联 payload 和单独一行 `\.`；禁止外部 payload 文件、`PROGRAM`、`\copy`、COPY TO、pipe 或 out-of-band stdin。这样 `sql_sha256` 同时绑定命令、payload、终止符、准备、验证和清理。拿到 case 锁后、任何端点预检前，formal flow 再次加载 run execution profile 与 case manifest，要求 digest、endpoint anchors、service/database、psql、timeout、case 内容及 SQL path/SHA 未变化，并只使用锁内重载结果执行。manifest 固定 `mode: exact_text`、`oracle: upstream-postgresql-18.4`、`require_identical: true`；每个 executable obligation 只能有一个确定性 SQL。执行记录分别保存 stdout、stderr、return code、同会话 endpoint identity、SQL SHA、`execution_profile_sha256` 和耗时；comparison 也保存同一 profile digest、两端完整 transcript、hash 和 unified diff。profile-bound run 必须使用当前 digest，且 identity service/database/system_identifier/current_user 必须逐端等于 profile；legacy unprofiled run 必须显式写 `null`。job/status gate 会重新计算并拒绝任何缺失或漂移，external harness 同样适用。不要把耗时本身作为兼容性 oracle。

formal 命令固定 `ON_ERROR_STOP=1` 和 verbose errors，没有 continue-on-error 或 normalization 选项。`run execute --continue-on-error` 与 `run compare` 只是底层诊断原语，不能生成 formal compatibility pass。

需要单独诊断目标时，可以使用底层 `pg-case run execute` 各执行一次，再用 `pg-case run compare` 比较自行构造的 transcript。底层命令不会自动从 execution JSON 提取流，也不满足 formal case manifest、outcome oracle、artifact reservation 和 evidence-chain 门禁。

## 身份与 artifact 事务边界

1. reference/DUT 在执行前分别 preflight。
2. runner 把身份 query 注入与测试 SQL **同一个 psql session** 的开头；该身份必须与 preflight 完全一致。不能用另一个连接的检查结果替代实际执行连接。
3. 两端 SQL 完成后再次 postflight；preflight、execution-session 和 postflight 任一漂移都失败。
4. reference/DUT 的有效 system identifier 必须不同，并逐端等于 immutable profile anchor；`current_user` 也必须等于共同 expected user。
5. 在任何 SQL 到达数据库前，runner 按 case ID 获取锁并预留全部 artifacts；已有完成 marker 时必须在执行前失败，除非显式 `--overwrite`。
6. 文件先写到 staging，再发布 execution/diff，最后发布 `comparisons/<case-id>.json`。该 comparison JSON 是完成 marker；没有 marker 的部分文件只表示中断，可由下一个锁持有者修复。

## 构造可比较输出

1. runner 以无歧义的长度前缀编码 return code、stdout 和 stderr，明确保留两个 stream 的边界、字节长度和最终换行。
2. formal comparison 固定 `exact_text`：仅把 CRLF/CR 统一为 LF，不删除行、不替换文本，也不忽略行尾空白或最终换行；return code、stdout、stderr 的分区边界全部参与比较。
3. formal `run differential` 不允许 drop-line、replacement 或 strip。底层 `run compare` 可以用于调查波动，但其 normalization 结果不能冒充 formal PostgreSQL compatibility oracle。

## 判定与产物

- 输出完全一致：记录 exact transcript hashes 与 `identical: true`，但还要通过 upstream outcome oracle。
- `success` case：upstream 必须 return code 0。两端同样失败、文本完全相同也必须 `passed: false`。
- `expected_failure` case：manifest 必须声明五字符 `expected_sqlstate`；upstream 必须非零退出，且 verbose stderr 必须恰有一个 `ERROR`/`FATAL`/`PANIC` 终止诊断，其 SQLSTATE 等于声明值。NOTICE/WARNING 中出现相同代码不能满足 oracle；多个终止诊断视为歧义并拒绝。之后仍要求 DUT transcript 与 upstream 完全一致。
- 输出不同或 upstream oracle 无效：comparison 为 `passed: false`，必须生成一一对应的 finding，不能静默标为已 triage。
- 将确认稳定且可复现的用例复制到 `regression/sql/`，把 comparison 保存的 upstream exact transcript 放到 `regression/expected/`。

finding 固定 `schema_version: 1`、`kind: differential_finding`，并包含 finding/test-point/obligation/case ID、非空 summary，以及 `artifacts.sql`、`reference_execution`、`dut_execution`、`comparison` 四个精确绑定；每个绑定都只有 run-relative `path` 与实际 64 位小写 SHA-256。

封装时生成一个 `regression_package` JSON：schema 1、对应 `test_point_id`、覆盖该 point 全部 case 的 `cases` 列表；每项包含 `case_id`、`regression/sql/...` 与 source SQL SHA、`regression/expected/...` 与 upstream exact transcript SHA。`packaged` evidence 必须精确等于 package JSON 加其中全部 SQL/expected 文件。

## 边界

- 当前基础 runner 只做两个目标上的顺序、单会话 psql 执行；不编排多会话、并发时序、进程重启、故障注入或集群拓扑。需要这些能力时，使用明确的 external harness，并把 readiness record、真实 probe 命令、时序和结果写回本 run。readiness gate 不独立证明 probe 真伪；没有外部 harness/操作者实际执行就不得声称对应测试已完成。
- 基础 runner 固定 `PGCLIENTENCODING=UTF8`、`LC_ALL=C` 与无颜色输出，并只向 psql 传递最小环境白名单（不传播 `PGPASSWORD`）。它的 lexer 不是数据库 server sandbox，也不能证明两端全部 GUC、locale、extension 等环境配置相同；这些必须在执行配置中预先对齐。runner 拒绝用户 SQL 中的全部 psql meta command、`COPY ... PROGRAM` 和 `COPY ... FROM STDIN` data mode；动态 SQL、过程语言、扩展、服务器函数及权限仍必须由专用非特权 role 和隔离环境控制。manifest-bound COPY STDIN 使用 `external-copy-ingest`；服务端文件、PROGRAM 或其他 privileged 分支使用另一个明确声明、隔离且授权的 external harness，不能借 COPY ingest route 绕过 payload 绑定。
- 不读取或解释存储层日志，不判断底层根因。finding 只陈述可复现的 SQL/用户可见差异。
- 不在任何 artifact 中写入真实凭据。
- 当前静态 inventory 覆盖 183 个 statement，但 `runtime_verified_statements=0`；完成真实双端执行并保留身份/执行/比较证据之前，不得提升为 runtime verified。

```yaml
structured_config:
  kind: mainflow
  skill_name: execute_differential_regression
  oracle: upstream-postgresql-18.4
  compatibility_scope: sql-and-user-visible-output
  basic_runner_scope: single-session-psql
  execution_profile_contract: assets/templates/execution_profile_template.yaml
  execution_profile_source: immutable-run-input
  formal_comparison: exact-only
  formal_stop_on_error: true
  require_case_manifest: true
  storage_root_cause_owner: user
  forbid_credential_persistence: true
```
