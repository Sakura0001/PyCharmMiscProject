# pg_case_factory v0.2 项目结构

项目采用“Codex skill 知识层 + 通用 Python 控制层 + run-scoped artifacts”结构。statement 专用知识留在 skill references/matrices，不写入通用 runner。

## 根目录

```text
pg_case_factory/
├── README.md
├── PROJECT_STRUCTURE.md
├── pyproject.toml
├── docs/
├── skills/
├── src/pg_case_factory/
├── tests/
├── tools/
└── artifacts/
```

## Skill

```text
skills/pg-sql-generation/
├── SKILL.md
├── agents/openai.yaml
├── assets/
│   ├── objects/
│   └── templates/
│       ├── feature_manifest_template.yaml
│       ├── coverage_plan_template.yaml
│       ├── case_manifest_template.yaml
│       ├── execution_profile_template.yaml
│       └── lifecycle_plan_template.tsv
└── references/
    ├── mainflow/
    ├── common/
    ├── statements/
    ├── combinations/
    └── templates/
```

### `SKILL.md`

只保留触发说明、核心门禁、边界和直接导航。详细流程按需从 `references/` 加载。

### `references/mainflow/`

- `analyze_feature_document.md`：保存原文、哈希和 locator，提取 feature manifest。
- `design_feature_coverage_plan.md`：逐 requirement 建 axes/test points，并完成 reconciliation。
- `orchestrate_test_points.md`：一个持久 job/test point，按状态门禁推进。
- `execute_differential_regression.md`：执行 upstream PG18.4 与 DUT，比较输出并形成 regression evidence。
- `generate_sql_from_request.md`：根据输入类型路由完整工作流。
- `audit_lifecycle_plan.md`：审计 coverage/lifecycle 计划。
- `write_sql_program.md`：为单个 test point 生成 SQL 和 case manifests。
- `create_statement_reference.md`：按 PostgreSQL 18.4 创建 statement reference。

### `references/common/`

- `compatibility_profile.yaml`：16.4 基线到 18.4 目标的审计策略与 statement review。
- `statement_support_inventory.yaml`：statement 支持和 PG18.4 readiness inventory。
- `pg18_factor_catalog.md`、`pg18_type_catalog.md`：PG18.4 版本化 inventory 入口。
- `pg16_factor_catalog.md`、`pg16_type_catalog.md`：历史基线；不能单独证明 PG18.4 ready。
- output/factor/lifecycle/validation/naming policies：跨 statement 的公共约束。

### `references/statements/` 与 `references/combinations/`

statement references 定义语法、因子、约束、映射和渲染。combination matrices 定义可审计 required baseline；derived extensions 不能替代 required coverage。

`pg18_type_catalog.md` 将有限可执行 core profile 与 exact built-in、automatic array、pseudo-type、declaration alias、typmod、user-defined archetype 分开建账。85 个 core profile 本身不是整个 `pg_type`；complete `column_type` scope 必须绑定上述 7 个 inventory，不能只引用 core selector。

### `assets/`

`objects/` 只保存基础对象 SQL，不混入目标 statement。`templates/` 是复制后填写的输出骨架，不是示例运行结果，也不得保存真实凭据。

## Python 控制层

```text
src/pg_case_factory/
├── __main__.py
├── cli.py
├── contracts.py
├── feature_plan.py
├── inventory.py
├── coverage.py
├── jobs.py
├── artifact_store.py
├── differential.py
├── skill_packaging.py
├── audits/
├── discovery.py
├── skill_loader.py
├── renderer.py
└── engine.py
```

- `contracts.py`：加载并严格校验 feature manifest、coverage plan、test point、case manifest 与 execution profile YAML；formal profile 只接受 PG18.4、不同 libpq service、同名 database、逐端不同的 expected system ID、共同 expected current user、stop-on-error、exact 空 normalization 和外部凭据策略。formal case 固定一个 SQL、精确 `sql_sha256`、upstream PG18.4 exact oracle，expected-failure case 还绑定五字符 SQLSTATE。
- `feature_plan.py`：校验 requirement/axis/dependency 引用和 DAG，提供稳定拓扑顺序。
- `inventory.py`：在显式信任根内解析 YAML/Markdown inventory，拒绝路径逃逸，并逐值核对顺序、类型、数量和摘要。
- `coverage.py`：对 core axes 做完整笛卡尔积，生成稳定 obligation IDs；按实际 artifact root 核对 outcomes、assignments、case manifests、唯一 SQL 路径/内容和 SQL SHA。
- `jobs.py`：严格按 one-job-per-test-point 原子持久化任务，提供 dependency-aware `run next` 选择。job store schema v3 保存 evidence 路径/SHA；audited/ready/linted 使用固定 schema，后续重算 case/SQL/replay/comparison/finding/package/harness 证据。
- `artifact_store.py`：创建/恢复隔离 run，严格验证 `run.json` schema、固定 layout、metadata、目录 containment 和 symlink；重验 run-bound execution profile 的 canonical bytes 与 metadata digest，原子写入文本/JSON/YAML。
- `differential.py`：reference/DUT 各自双跑的单会话 psql runner、同会话身份探针、pre/post identity、端内逐字节确定性、formal exact-only 跨端比较、artifact 预留锁、hash 和 unified diff。
- `cli.py` / `__main__.py`：公开 `doctor`、`plan`、`run` 和 `skill` 命令。
- `audits/`：检查 statement 结构、占位符、方言、assets 与可用能力。
- `skill_packaging.py`：确定性 zip 与 archive verification。
- `discovery.py`、`skill_loader.py`、`renderer.py`、`engine.py`：保留通用对象/reference 发现和 SQL 渲染能力。

Python 层不负责自然语言理解、自动创建 Codex 子 agent、底层存储日志分析或 statement 专用生命周期推理。

## Run-scoped artifacts

`artifact_store.prepare_run()` 创建：

```text
artifacts/runs/<run-id>/
├── run.json
├── inputs/
│   ├── feature_manifest.yaml
│   ├── <preserved-feature-document>
│   └── execution_profile.yaml
├── plans/
│   ├── inventory/
│   └── applicability/
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

- `inputs/`：原始特性文档、副本哈希、feature manifest，以及由 `run init --execution-profile <work-file>` 规范化生成的不可变 execution profile。profile 的语义 SHA-256 写入 `run.json`；禁止手工复制、增补字段或 run 内编辑。
- `plans/`：coverage plan、expanded obligations、审计记录和 inventory provenance。
- `jobs/`：schema v3 job store、固定 audits/readiness/lint sidecar，以及 external-harness verification 和 `jobs/harnesses/implementations/` 实现快照；可变的 `jobs/jobs.json` 不能充当 evidence。
- `cases/`：case manifests 和 SQL。每个 executable obligation 恰有一个 manifest，每个 manifest 恰有一个 SQL 和其精确 bytes SHA-256；跨 obligation 复用 SQL 路径或内容会被拒绝。
- `executions/`：两端 first/replay 执行 JSON 与原始 stdout/stderr；reference 固定为 upstream PostgreSQL 18.4。
- `comparisons/`：formal exact comparison、hash 和 diff；`.locks/` 在执行数据库前预留 case，comparison JSON 最后发布并作为完成 marker。
- `findings/`：`differential_finding` YAML，以 path+SHA 绑定 SQL、reference/DUT execution 和 comparison，不包含存储根因猜测。
- `regression/`：按用户批准 prefix 连续编号的 SQL、upstream exact transcript 和 `regression/packages/<point>.json`；package 绑定 mapping SHA、对象前缀、原 SQL SHA 与全部 case。

已有 run 默认不可覆盖；`--resume` 只恢复 manifest、plan、execution profile digest 与 metadata 完全相同的 run，profile-bound run 必须再次提供同一 work-file。`run.json` 始终显式保存 `metadata.execution_profile_sha256`（绑定 run 为 hash，legacy/unprofiled run 为 `null`），删键不能把绑定 run 降级。计划或执行配置变化时创建新 run。feature manifest 的 `metadata.unresolved_questions` 在分析期可非空，但正式 `run init` 要求显式存在且为 `[]`。旧根级 `generated_programs/`、`generated_sql/`、`test_plans/`、`evaluations/` 和 `intermediates/` 仅供旧 API 兼容。

coverage plan 必须恰好包含 4 个 scope decision：`object`、`relation`、`table`、`column_type`。table scope 由 5 个正交 axis 共同证明；column scope 由 7 个互补类型 inventory 共同证明；同时必须逐项记录 12 个 mandatory risk decision，并保留特性专属的额外风险。feature-local inline axis 必须提供 derivation、feature/PG18 source locators、exclusion policy 和 semantic/source review 状态。仓库 storage cross-product 基础模板当前可重复展开为 3,175 个 obligation（2,787 success、153 expected failure、235 justified N/A、0 missing；37 axes、25 test points），这是已声明 axis 的模板快照验收数字，不是所有特性的固定配额，也不能替代逐 statement/factor/value 的特性适用性账本。

`plan reconcile-cases` 必须接收 `--artifact-root`，以验证 case manifest 中的 SQL 路径确实位于当前 run 且为普通文件。`artifact_root=None` 不具备完成资格。`run transition` 的所有正常前向状态都必须提供 run-root-relative `--evidence`；转换时记录 SHA，后续转换、status 和 package 都重新核验。`generated` evidence 必须精确覆盖该 job 全部 executable obligations，不能用一份 SQL/YAML 代表整个 point；失败使用 `--error`，重试不接受 evidence。

若 risk decision 引用 `execution_harness`，`ready` evidence 必须包含 point readiness、`jobs/harnesses/<harness-id>.json` 和其 implementation 文件。record 绑定 `execution_profile_sha256`、implementation path/SHA、非空 event model、probe、组合 fingerprint 和带时区 verified_at。gate 校验计划/profile/实现绑定、自洽和不可变性；probe 是否真实运行仍由 external harness/操作者负责。

## Tools 与审计证据

- `tools/audit_factor_catalog_mapping.py`：审计 statement 到 factor catalog 的映射。
- `tools/audit_combination_matrix.py`：审计 combination matrix 的 schema、引用和 required coverage。
- `tools/audit_pg18_factor_compatibility.py`：对照官方 16.4/18.4 SGML，更新/验证逐 statement、factor、value 的 PG18.4 审计账本。
- `tools/package_skill.py`：调用确定性 skill packager。
- `skills/pg-sql-generation/references/common/postgresql_18_4_factor_audit.tsv`：逐项兼容审计产物；放在 Skill 内以保证离线归档自包含。

## 已实现与外部能力

已实现：YAML contracts、完整 coverage expansion/reconciliation、durable jobs、run layout、reference/DUT 顺序单会话 psql execution、完整 transcript comparison、静态审计和 skill packaging。formal 双目标命令必须同时提供 run 内的 `--case-manifest`；优先从当前 run 的不可变 execution profile 读取 endpoints/identity anchors/psql/timeout，无 profile 的旧 run 才要求完整 direct flags，profile-bound run 的冲突 flags 会失败。它在任何数据库调用前锁定 case/检查 collision，锁内重新加载并比对 profile digest/settings、case manifest 和 SQL path/SHA，再仅以锁内结果执行；同时强制两个端点及执行会话均为 `server_version_num=180004`、身份 pre/session/post 一致、`system_identifier` 不同、database 与 `current_user` 相同，并逐端命中 profile expected system ID/user；basic runner 固定 UTF8 client encoding。formal comparison 固定 `exact_text` 比较 return code/stdout/stderr，只统一换行编码；`success` 要求 upstream 成功，`expected_failure` 要求 upstream 非零且唯一 verbose `ERROR`/`FATAL`/`PANIC` 终止诊断 SQLSTATE 命中声明值，NOTICE/WARNING 不参与 oracle，默认并固定 stop-on-error。

由 agent 或外部 harness 完成：文档语义抽取、子 agent 调度、复杂 SQL 生成、多会话/重启/故障执行、真实环境凭据管理。基础 runner 必须使用专用非特权 role，拒绝 superuser 及 server-file/program roles，并禁止用户 SQL 中的 psql meta command、`COPY PROGRAM` 和 `COPY FROM STDIN` data mode；basic lexer 不是 server sandbox，动态 SQL、过程语言、服务器函数或其他 privileged case 必须进入隔离 external harness。`external-copy-ingest` 是更窄的例外：case 唯一 SQL 自身包含直接 COPY FROM STDIN、非空内联 payload 和独立 `\.`，其 manifest SHA 绑定全部 bytes，harness 只执行该精确文件；外部文件、PROGRAM 或另行 stdin 会在 reconciliation 被拒绝。最小权限拒绝只针对 `basic_psql`；明确授权的 external case 可以使用所需 privilege，但仍须提交完整 PG18.4 endpoint identity、不同 system ID、相同 database/current_user，以及与 immutable run profile 一致的 service/database/expected-system-ID/expected-user 和 `execution_profile_sha256`。每个 execution/comparison JSON 都显式保存该 digest（legacy 为 `null`），status/job gate 会重算。存储层日志和根因分析始终由用户负责。

当前知识库的 183 个 statement 均完成 PG18.4 静态目录审查；账本固定核对 3,357 个 statement-factor pair、9,978 条 factor-value 记录、53 个受影响 matrix、105 个必测 reference-parity point 和 132 个受影响 value binding，且 105/105 point 均显式列值。但 `runtime_verified_statements=0`；真实双端运行之前，不得把静态 ready 描述为 runtime verified，也不得把 partial/static matrix 声称为 exhaustive rendered coverage。
