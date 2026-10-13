# 类型升级一致性测试实施计划

## Task 1：因子目录与 case 生成器

1. 新增 `src/mysql_case_factory/type_upgrade_consistency.py`。
2. 定义类型转换、数据、属性、索引、外键、依赖对象、表形态和 SQL mode 因子。
3. 生成唯一 case ID、`expected_outcome`、四表夹具、正向/负向后置 SQL 和清理 SQL。
4. 支持生成 `copy`、`inplace`、`instant` 三个 profile 的 SQL。
5. 新增 `tools/generate_type_upgrade_cases.py`，输出 `cases.jsonl`、三个 suite SQL、manifest 和 coverage。
6. 先写测试并确认失败，再实现：禁止类型清单、BIT 组合数、整数全方向、DECIMAL 标度、字符/二进制边界、唯一 ID、确定性输出、profile 算法替换。

验收：

- 所有禁止类型和索引不出现在 case JSON 与 SQL 中。
- 整数覆盖所有 rank 提升方向及 signed/unsigned 安全组合。
- `BIT` 至少 10 个扩宽组合，实际目标不少于 20。
- `DECIMAL` 至少覆盖 5 个标度并保持标度不变。
- 字符与二进制覆盖 255/256、utf8mb3 85/86、utf8mb4 63/64 等长度头。
- 重复生成的内容哈希一致。

## Task 2：本地 COPY 执行器与结果 Oracle

1. 新增 `tools/run_type_upgrade_copy.py`。
2. 使用本机 `/opt/homebrew/opt/mysql@8.0/bin/mysqld` 启动隔离实例：独立 data dir、socket、port 0、无网络监听。
3. 使用 root socket 连接，不写入凭据，不修改全局配置。
4. 逐 case 执行旧结构、目标参考结构和算法表。
5. 正向 case：DDL 必须成功，结构、旧数据、目标范围新数据、索引和依赖行为必须与参考表一致。
6. 负向 case：DDL 或非法 DML 必须失败，状态必须保持完整。
7. 输出逐 case 结果、失败原因、SQLSTATE/errno、耗时和汇总 JSON。
8. 提供 `--limit`、`--case-id`、`--keep-server`、`--results`、`--summary` 等有界参数。
9. Ctrl+C 或失败时停止受影响批次并清理服务器。

验收：

- 本地 MySQL 8.0.45 可启动并执行全量 COPY case。
- 每个 case 都有 `PASS`、`FAIL_*` 或 `BLOCKED_*` 结果。
- 结果 JSON 与 case ID 一一对应，无缺失、无重复。
- 服务器进程和临时目录最终被清理。

## Task 3：生成全量产物并本地验证

1. 生成 `copy_suite.sql`、`inplace_suite.sql`、`instant_suite.sql`。
2. 运行全量本地 COPY 验证，不允许只抽样替代全量。
3. 保存 `local_results.json` 和 `local_summary.md`。
4. 覆盖审计必须证明保留因子均有至少一个 case，删除因子无 case。
5. 如果发现生成器或夹具问题，先写失败测试再修复，之后全量重跑。
6. 产物纳入 git 跟踪，避免依赖被 ignore 的 `artifacts/` 目录。

验收：

- 全量 COPY case 均 PASS。
- manifest、coverage、suite SQL、cases JSON 和结果文件互相一致。
- 内网 profile SQL 中所有正向 case 的算法分别为 `INPLACE` / `INSTANT`，case ID 与 COPY 完全一致。

## Task 4：文档、测试与子代理复审

1. 更新 `mysql_case_factory/README.md`，说明本地验证和内网切换方法。
2. 新增设计文档、使用说明、结果摘要。
3. 运行项目全量测试。
4. 使用子代理独立复审：
   - 因子范围是否符合用户裁剪要求。
   - 类型覆盖是否遗漏 SMALLINT/INT/BIGINT、CHAR/VARCHAR、DECIMAL、BIT。
   - 禁止类型是否完全清除。
   - 生成 SQL 是否可直接执行。
   - COPY 本地结果是否全量且均 PASS。
   - 内网 profile 是否可一键切换。
5. 根据复审意见修复并重跑测试与全量验证。

验收：

- `pytest -q` 全部通过。
- 子代理复审结论为通过且无未处理阻塞项。
- 变更包含代码、测试、文档和生成产物。

## Task 5：提交并推送

1. 检查 git status，确认无临时环境、凭据或无关文件。
2. 分批提交文档、代码、测试和生成产物。
3. 推送 `codex/type-upgrade-consistency` 到 `origin`。
4. 输出分支、commit、验证命令和结果摘要。

验收：

- 分支已推送到 GitHub。
- 推送前全量测试和本地 COPY 验证均通过。
- 提交信息清晰，未包含本机敏感路径之外的凭据或私有数据。
