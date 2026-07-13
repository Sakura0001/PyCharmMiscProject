# PostgreSQL 18.4 全量测试工厂：持久化执行账本

> 用途：这是本轮改造和复检的唯一持久化交接账本。任何后续 Codex 任务开始时，应先完整阅读本文件，再检查 Git 状态，然后从“当前阻塞点”和“未执行清单”继续。不要仅依赖聊天上下文。

## 1. 当前目标和验收口径

项目目标是把一份特性文档转换为可审计、可恢复、可逐点派遣的 PostgreSQL 18.4 兼容性测试：

1. 自研引擎上层 SQL 行为和用户可见输出以开源 PostgreSQL 18.4 为唯一 oracle。
2. 输入特性文档后，必须保存原文及 SHA-256，提取可定位需求，并生成完整测试计划。
3. 计划必须审查 PostgreSQL 18.4 的固定因子全集，而不是只列少量常见表或类型。
4. 每个可执行测试义务只能绑定一个 case manifest 和一个不可变 SQL 文件。
5. 运行时按 test point 拆成可恢复 job；主 Agent 应逐点派遣子 Agent，校验通过后再继续。
6. SQL 在 reference PostgreSQL 18.4 与 DUT 上执行，比较返回码、stdout、stderr 和 SQLSTATE；任何未解释差异都进入 finding。
7. 允许慢，但不允许用“抽样”“其余类似”“人工补充”伪装完整覆盖。
8. 用户负责观察底层日志；本项目负责上层计划发散、SQL 生成、执行证据和差异判定。

## 2. Git 与工作区状态

- Git 根目录：`/Users/yuyu/PyCharmMiscProject`
- 子项目：`/Users/yuyu/PyCharmMiscProject/pg_case_factory`
- 当前分支：`codex/pg18-feature-testing-foundation`
- 改造前基线：`223daba`（`origin/main`）
- 当前尚未提交、尚未推送。
- 修改范围应仅限 `pg_case_factory`；提交前必须再次确认父仓库没有其他待提交文件。
- 父仓库 AGENTS 规则：成功修改后必须只暂存本项目、提交并执行 `git push`；网络或认证失败必须明确报告。
- `tools/generate_project_ppt.py` 的删除是有意的：该脚本孤立、过时且含旧依赖/旧路径。
- `skills.zip` 当前是旧包；所有源码和文档稳定后必须重新生成，不要直接手工编辑 ZIP。

## 3. 已执行并确认的工作

### 3.1 PG 18.4 官方因子与清单

- [x] PostgreSQL 18.4 source inventory 已建立并通过审计：
  - SQL objects：52
  - relation kinds：10
  - concrete builtin types：85
  - array element types：79
  - pseudo types：26
  - table access methods：1
- [x] PG 16.4 与 PG 18.4 本地官方 SGML 已用于兼容性比较。
- [x] statement universe：183/183。
- [x] statement × changed-factor pairs：3357。
- [x] statement/factor value rows：9978。
- [x] synopsis changed：27；document changed：58。
- [x] 静态 ready：183；pending：0；runtime verified：0。
- [x] factor mapping 审计：mapped 40，explicitly excluded 14。
- [x] combination audit 通过；仍有 167 个明确 partial warning，属于显式迁移债务，不是静默缺口。
- [x] doctor：errors 0，warnings 559；capability 口径为 reference_only 142、renderable 41、executable 0、runtime 0。

### 3.2 基础覆盖计划

- [x] 四个强制 scope：object、relation、table、column_type。
- [x] 十二个强制 risk：syntax、operation、lifecycle、data_profile、large_value_toast、transaction、partitioning、index_constraint_trigger、privilege、maintenance、concurrency、restart_recovery。
- [x] 当前基础计划：37 axes、25 test points、3175 obligations。
- [x] 分类结果：success 2787、expected_failure 153、justified N/A 235。
- [x] executable 2940、missing 0。
- [x] obligation → case manifest → SQL 文件及 SHA-256 一一绑定；禁止复用同一个 SQL 假装多个义务。

### 3.3 特性适用性账本与 compiler

- [x] 新增 `src/pg_case_factory/applicability.py`。
- [x] 新增 `tools/scaffold_feature_applicability.py`。
- [x] 支持 `scaffold`、`refresh`、`validate`、`compile`。
- [x] 固定 universe 为 183/3357/9978，row ID 和 semantic SHA 稳定。
- [x] 初始 scaffold 会生成 183 个 statement review、9978 个 pending value review；`--require-complete` 必须失败。
- [x] covered row 必须带 requirement/source locator、matrix witness、outcome、route、harness（如需要）和唯一 binding。
- [x] justified exclusion 必须有双重 locator/理由；全量都是 justified exclusion 时也允许判定 complete，不能错误要求至少一个 covered。
- [x] compiler 为有 covered rows 的 statement 生成 reserved axis/test point；base plan 与 compiled plan 分离，增量追加不改变旧 binding。
- [x] external route 会生成或合并执行 harness 风险。
- [x] 9978/9978 witness 已审计通过：9968 个由 combination group 覆盖，10 个由严格 PG18 compatibility test point 覆盖。
- [x] 10 个专项点是 DELETE/INSERT/UPDATE RETURNING aliases、MERGE BY SOURCE/BY TARGET/RETURNING aliases、REFRESH MATVIEW search_path/MAINTAIN、SELECT row lock alias/MERGE CTE；不能误判为缺失，也不应重复造组合组。
- [x] `tests.test_applicability`：22 tests passed（2026-07-13 再跑，12.856s）。

### 3.4 SQL 安全与 COPY

- [x] SQL 文件在连接数据库前进行不可变快照和 SHA-256 校验。
- [x] case lock 内重读 profile/case/SQL，缩小 TOCTOU 窗口。
- [x] external-copy-ingest 只允许一个 manifest-bound SQL，必须包含直接 `COPY ... FROM STDIN;`、非空内联数据、独立 `\.`。
- [x] 拒绝外部文件、PROGRAM、`\copy`、COPY TO、out-of-band stdin、NUL、未终止 payload。
- [x] COPY 28 个 PG18 点已路由：21 个 FROM 使用 external-copy-ingest，7 个 TO 使用 basic。

### 3.5 差异比较与 SQLSTATE

- [x] reference 与 DUT 的执行结果绑定 execution profile SHA、SQL SHA 和 endpoint identity。
- [x] execution profile 要求 reference/DUT 的 expected system identifier 和 expected current user。
- [x] reference 与 DUT system identifier 必须不同，用户身份必须匹配各自 profile。
- [x] expected_failure oracle 只接受 verbose stderr 中恰好一个终止级 ERROR/FATAL/PANIC SQLSTATE；NOTICE/WARNING 不算失败终止。
- [x] 比较保留 exact transcript，要求 UTF-8，不默认丢弃尾部空白。

### 3.6 回归脚本规范模块

- [x] 新增 `src/pg_case_factory/regression_style.py`。
- [x] 新增 `tests/test_regression_style.py`。
- [x] 用户批准的 batch prefix + 连续 `<prefix><NNN>.sql`；13153 个 case 自动使用 5 位。
- [x] append-only prior mapping，旧义务不重编号；跨位宽会拒绝，避免重命名旧 SQL。
- [x] 对象前缀为 lowercase numbered prefix，并检查 PostgreSQL 63-byte identifier 限制。
- [x] Huawei header renderer/validator、严格 LF/EOF。
- [x] catalog 可观察性允许 schema-qualified 显式列 + top-level ORDER BY，拒绝不稳定/动态/需人工证明的情况。
- [x] table script 保守检查首尾清理、创建对象前缀、数据库级危险操作和动态 SQL。
- [x] 两次运行逐字节比较 returncode/stdout/stderr，包括 expected failure。
- [x] `tests.test_regression_style`：28 tests passed（2026-07-13 再跑，0.022s）。
- [ ] 该模块尚未完整接入 CLI/job transition/differential/package 门禁；见未执行清单。

### 3.7 正式运行链路（已写入但尚未全量跑绿）

- [x] 新增 `src/pg_case_factory/formal_run.py`。
- [x] 正式 `run init` 参数现要求 manifest、compiled plan、execution profile、complete applicability index；不能空初始化。
- [x] manifest 必须显式 `metadata.unresolved_questions: []`。
- [x] init 前验证 feature/plan/applicability feature ID、requirements、9978 完整性和 obligation binding。
- [x] 输入先完整读取/校验，随后在 runs-root flock 下写 staging，验证后 atomic rename；失败不得发布半成品 final run。
- [x] 快照包含 feature manifest/source/profile/plan/obligations、inventory、applicability index、183 reviews、ledger 和 covered matrix witnesses。
- [x] `run.json` 使用固定 formal metadata keys 和多级 SHA-256。
- [x] `status`、`transition` 已开始接入 `validate_formal_run`，防止只验证 run.json。
- [x] contracts 已开始拒绝 unknown fields，并收紧 stable ID/portable paths。
- [ ] 该分支最新全套测试仍有兼容测试未迁移；见“当前失败”。

### 3.8 Skill 打包

- [x] 9978 行 PG18 ledger 已移动到 Skill 内：`skills/pg-sql-generation/references/common/postgresql_18_4_factor_audit.tsv`。
- [x] Skill package validator 会校验引用并包含该 ledger。
- [x] 之前运行过 quick validator 和 package tests。
- [x] `skills.zip` 最终两次独立打包 byte-identical；SHA-256=`9dd850500bca735ba80d22bb2be35db04d020a830b9f2b8ab5bc32d546478e34`，402 个源文件 + manifest，archive verify 通过，账本 9979 行（含 header）。

## 4. 2026-07-13 最新复检结果

执行命令：

```bash
.venv/bin/python -m unittest discover -s tests -q
```

结果：`Ran 264 tests in 29.828s`，`FAILED (failures=1, errors=24)`。

这些失败是在 formal run 严格化尚未完成迁移时产生，不能忽略：

1. [x] 旧 `test_cli.py` / `test_execution_profile.py` helper 已迁移：正式 `run init` 始终要求 manifest/plan/profile/applicability；测试仅把 universe 计数缩为 1/1/1，仍走相同 schema、快照、原子发布和 reconciliation。
2. [x] `tests/test_jobs.py` 的 `_RunCoverageContext.applicability` 兼容已修复。
3. [x] inventory 报错断言已恢复兼容并通过。
4. [x] `contracts._require_allowed_keys` 已同时报告 missing required 与 unexpected。
5. [x] CLI 中 `return 0` 后约 200 行不可达的 legacy run-init 实现和无用 import/helper 已删除，避免两套口径继续漂移。
6. 子 Agent 在修复这些问题时触发使用额度上限，未能正常结束；其已写入的文件仍在共享工作区，已由主 Agent接管复核。

2026-07-13 追加验证：

- `tests.test_feature_contracts + tests.test_inventory + tests.test_artifact_runs`：45 tests passed（2.185s）。
- `tests.test_execution_profile + tests.test_jobs + tests.test_cli`：39 tests passed（2.016s）。
- formal differential 已有 `linted` 精确状态门禁；旧测试改为先逐态推进，不再绕过门禁。
- 第二轮全套曾只剩 1 个旧双跑次数断言；修复后全套 `Ran 268 tests in 33.087s`，`OK`。
- compileall、`git diff --check`、`UV_CACHE_DIR=/tmp/pg-case-uv-cache uv lock --check --offline` 全部通过。
- 官方 source inventory：objects 52、relkinds 10、builtins 85、arrays 79、pseudo 26、table AM 1，PASS。
- PG16.4/18.4 SGML compatibility：183/183 static ready、3357 pairs、9978 rows、27 synopsis changed、58 document changed、runtime 0，PASS。
- factor mapping：mapped 40、excluded 14，PASS。
- combination：183 matrices、381 groups，PASS；167 个 partial/deprecated warning 仍显式保留。
- doctor：ok=true、errors 0、warnings 559；reference_only 142、renderable 41。
- base plan：3175 total、2787 success、153 expected failure、235 justified N/A、2940 executable、missing 0。
- applicability pending smoke：183 statement decisions、3357 factor decisions、9978 pending；普通 validate 明确 complete=false，`--require-complete` 以 exit 2 正确拒绝。完整 compile/witness 由 22 项 applicability tests 验证，9978/9978 witness。
- build：离线隔离构建因临时 cache 缺 `setuptools>=68` 失败；`--no-build-isolation` 进一步确认环境无 setuptools。随后经最小网络权限执行标准 `uv build`，成功生成 sdist 与 wheel。

## 5. 复检发现但尚未完全落实的关键问题

### P0：必须在提交前完成

- [x] 将旧 CLI/execution-profile 测试迁移到正式四输入 run fixture；正式参数保持 required。
- [x] 修复 `_RunCoverageContext` 测试和 inventory 报错断言。
- [x] 修复 `_require_allowed_keys`：同时拒绝 missing 与 unexpected。
- [x] `_run_root_for_store`、status、transition、formal differential 在执行前调用 formal snapshot 重验；仍需在后续全套测试和篡改负例中持续验证。
- [x] formal differential 要求对应 job 恰好处于 `linted`，不能在 `planned` 状态直接连接 DB/写 comparison。
- [x] `audited`、`ready`、`linted` 使用固定路径和固定 schema，精确绑定 plan/feature/point/obligations；lint 重算 manifest/SQL SHA、route SQL safety、Huawei header 和 catalog observability，任意 `{safe: true}` 已有拒绝负例。
- [x] basic endpoint privilege envelope 拒绝 superuser、CREATEDB、CREATEROLE、REPLICATION、BYPASSRLS、server-file/program roles 和高权限父角色；external isolated 保留结构化记录能力。
- [x] 正式 differential 已接入 reference 两次 + DUT 两次；端内 returncode/stdout/stderr 逐字节报告写入 comparison，replay JSON/stdout/stderr 单独保存，nondeterministic evidence 无法推进 job。
- [x] regression package 验证 stable mapping SHA、连续 filename/object prefix、Huawei header/EOF、catalog observability、原 SQL SHA 和 upstream expected transcript；表脚本还会验证首尾清理和对象前缀。
- [x] 增加 deterministic `pg-case run next --jobs ... --limit 1`，按 plan 顺序和 packaged dependency 返回 point/obligations/context；failed 不自动派发。
- [x] Skill 主流程已包含 `run next` 单点循环、最多一个 child、等待门禁、无 subagent 时串行等价执行。

### P1：应尽量在本轮完成

- [ ] external harness 已绑定 harness ID、implementation path/SHA、profile SHA、event model、probe 和组合 fingerprint；仍未在 ready 阶段绑定尚未生成的 SQL SHA，也未实现通用多会话/重启 runtime timeline executor。
- [ ] 清理证明不应只依赖布尔值；用双跑和实际 transcript 验证幂等/残留对象影响。
- [ ] 稳定 case ID/path 应从 obligation + regression mapping 推导，避免 Agent 自由命名碰撞。
- [x] 已审核并修正 README、PROJECT_STRUCTURE、Skill mainflow：正式四输入、applicability compile、run next、固定 evidence、双跑、权限、harness、package schema 与实现一致。
- [x] README 已明确 `skills.zip` 是项目型 Skill：ZIP 不包含 Python engine，运行命令需要 checkout 或已安装 CLI。

### 明确不伪造完成

- [ ] 尚未连接真实 PostgreSQL 18.4 与 DUT。
- [ ] runtime verified 当前仍为 0。
- [ ] 没有实际生成并执行用户特性对应的 100+ SQL；这要等用户下一步提供真实特性文档和两个端点配置。
- [ ] 559 个 doctor warning 与 167 个 combination partial warning 仍是显式迁移债务；本轮可保证“可见且 fail-closed”，不能宣称已经全部实现为 executable。

## 6. 后续执行顺序（必须逐项更新勾选）

1. [x] 共享子 Agent 均已停止；已查看并接管最新 diff，收口第一轮 formal run 测试。
2. [x] 已跑 `tests.test_feature_contracts`、`tests.test_inventory`、`tests.test_artifact_runs`、`tests.test_execution_profile`、`tests.test_jobs`、`tests.test_cli`，共 84 项通过。
3. [x] 全套 unittest：268 tests，0 failures，0 errors（33.087s）。
4. [x] 实现并测试 strict evidence schema 和 formal differential state gate。
5. [x] 实现并测试完整 basic endpoint privilege envelope。
6. [x] 集成 regression mapping/header/catalog/table audit/two-run determinism。
7. [x] 实现 `run next` 和 Skill 逐点派遣循环。
8. [x] 做文档/CLI 一致性审计并修正文档。
9. [x] 官方清单/兼容性/映射/组合/doctor 审计均 PASS，warnings 按上文显式记录。
10. [x] base plan expand、applicability pending/refusal smoke 和完整 compiler/witness tests 通过。
11. [x] Skill quick validate 通过；两次 package byte-identical，final archive verify 通过。
12. [x] `uv lock --check --offline`（临时可写 cache）、compileall、`git diff --check` 通过。
13. [x] 离线 build 失败原因已定位为 cache 缺 setuptools；经批准的标准 build 成功生成 sdist/wheel。
14. [x] 已从父仓库执行 `git status --porcelain=v1 -- . ':(exclude)pg_case_factory'`，输出为空；确认本项目外无改动。
15. [x] 只执行 `git add -- pg_case_factory`；`git diff --cached --check` 通过，缓存区外路径检查为空；staged 统计为 454 files changed、50,507 insertions、3,478 deletions。
16. [x] 已创建主实现提交 `74e8f71`（`feat(pg-case-factory): add PG18 feature test orchestration`），提交范围仅为 `pg_case_factory/`。
17. [x] 已推送到 `origin/codex/pg18-feature-testing-foundation` 并建立 tracking；沙箱内第一次尝试因 `127.0.0.1:7897` 代理不可达而失败，经批准使用本机网络和安全凭据后推送成功。

## 7. 最终验证命令清单

```bash
# Python tests
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q src tests tools

# PG 18.4 source/factor audits（官方 SGML 已位于 /tmp/pg-factor-audit）
.venv/bin/python tools/audit_pg18_source_inventories.py --help
.venv/bin/python tools/audit_pg18_factor_compatibility.py --help
.venv/bin/python tools/audit_factor_catalog_mapping.py --help
.venv/bin/python tools/audit_combination_matrix.py --help
.venv/bin/pg-case doctor --root .

# Skill
/Users/yuyu/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/pg-sql-generation
.venv/bin/pg-case skill package --skill-root skills/pg-sql-generation --output skills.zip
.venv/bin/pg-case skill verify skills.zip

# Packaging/static
uv lock --check --offline
env UV_CACHE_DIR=/tmp/pg-case-uv-cache uv build --offline --out-dir /tmp/pg-case-factory-build
git diff --check
```

运行审计工具前必须先查看各自 `--help`，按实际参数填写 PG 16.4/18.4 SGML 路径，不能盲目复制占位命令。

## 8. 更新规则

每完成一个动作，立即在本文件中：

1. 将对应 `[ ]` 改成 `[x]`；
2. 写入实际命令和结果计数；
3. 如果失败，记录完整失败类别和下一步，不要只写“环境问题”；
4. 如果实现口径变化，更新“目标和验收口径”；
5. commit/push 后写入 commit SHA、远端分支和 push 结果。

最后更新：2026-07-13（Asia/Shanghai），实现、独立验证、范围复核、主实现提交和远端推送均已完成；本文件的结果回写将作为单独收尾提交再次推送。保留给真实特性文档/真实数据库的 runtime 工作仍明确未执行。

## 9. README 对外交付说明更新（2026-07-13）

1. [x] 根据“给别人使用”的实际流程，补充 Skill + Python 控制层的双组件交付边界。
2. [x] 补充 Python、uv、psql、Codex 和双数据库环境要求。
3. [x] 补充当前 GitHub 功能分支的 clone、checkout、安装和 doctor 命令。
4. [x] 补充 `$pg-sql-generation` 最简使用提示词。
5. [x] 区分“仅生成计划和 SQL”与“连接两个数据库正式执行”两种模式。
6. [x] 补充 execution profile、libpq service、身份锚点和凭据安全要求。
7. [x] 补充 run artifacts 目录和使用者/项目职责边界。
8. [x] `git diff --check -- pg_case_factory` 通过；README 引用的 Skill ZIP、Skill 目录和 execution profile 模板均存在；父仓库项目外状态为空。
9. [ ] 创建仅限本项目的提交并推送当前 GitHub 分支。
