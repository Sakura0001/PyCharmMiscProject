# PostgreSQL 18.4 全量 SQL 分批运行验证设计

状态：`approved`

批准日期：2026-08-21

## 1. 目标与正式范围

本设计在本地隔离 PostgreSQL 18.4 上执行当前正式语句循环包，验证 SQL 的实际行为是否符合生成时冻结的预期，并形成可恢复、可审计的运行证据。

正式范围来自：

- `artifacts/intermediates/remaining-statement-factor-cycle/progress.json` 中 177 个 `completed` 包；
- 同一进度账本中 6 个 `retained_existing` 语句共享的 cursor、DCL 包；
- 按真实绝对路径去重，不按 schedule 重复累计。

冻结数量：

| 范围 | 唯一 SQL 数 |
|---|---:|
| 177 个当前语句包 | 841,195 |
| cursor 保留包 | 852 |
| DCL 保留包 | 13,866 |
| 合计 | 855,913 |
| 两轮执行次数 | 1,711,826 |

以下内容明确排除：重复的 by-factor cursor/DCL 副本、旧 DML v1/v2 包、`generated_sql`、仓库根目录散落 SQL、`work/` 工作副本和其他临时产物。

## 2. 清单规则

执行清单以 SQL 文件为真相源，schedule 只用于识别特殊执行路由，不能决定文件是否纳入。

静态审计已经确认：

- `alter_group` 3,947 个 SQL、`alter_role` 1,743 个 SQL、`drop_collation` 366 个 SQL 的 schedule 均为空；这 6,056 个 SQL 仍必须执行；
- cursor/DCL 保留包同时存在分片、串行和并行 schedule，同一文件会被多次引用；执行清单按路径去重后各执行一次；
- 6 个当前包共有 567 个 `external_schedule` 条目，必须保留特殊路由标签。

清单记录至少包含：statement、case id、SQL 相对路径、SQL SHA-256、package 类型、执行通道、预期 outcome、预期 SQLSTATE（若存在）和 external 标志。清单冻结后，运行过程中 SQL 字节变化必须使对应旧结果失效。

## 3. 三种证据等级

### 3.1 strict-contract

832,632 个 SQL 同时具备：

- `expected_outcome`；
- `expected_sqlstate`；
- `primary-target-begin/end`；
- `PGCF_TARGET_SQLSTATE` 回显；
- SQLSTATE 布尔断言；
- 清理段。

此通道严格检查：进程退出状态、超时、目标 SQLSTATE、所有布尔 oracle、清理结果、两轮结构化结果和规范化 transcript。

### 3.2 compatibility-contract

10 个当前旧格式包共 8,563 个 SQL 没有新式统一标记，但 `plan.json` 具有 case、outcome、object prefix，绝大部分 case 的 `derived_axes` 具有 expected SQLSTATE，SQL 本身具有旧式布尔 oracle。

此通道使用 plan 元数据与实际 SQL SHA 绑定，检查退出状态、超时、旧式 SQLSTATE/oracle 布尔值、清理和两轮一致性。无法恢复实际 SQLSTATE 的 case 不得提升为 strict，只能记录 `compatibility_pass` 或具体失败原因。

涉及的语句为：`abort`、`alter_aggregate`、`alter_collation`、`alter_conversion`、`alter_database`、`alter_default_privileges`、`alter_domain`、`alter_event_trigger`、`alter_extension`、`alter_foreign_data_wrapper`。

### 3.3 observational-legacy

cursor/DCL 保留包共 14,718 个 SQL 只有 `factor expected_status`，没有冻结 SQLSTATE、明确 target 边界或无歧义目标错误归因。仍执行两轮并收集退出状态、错误、布尔输出、清理可观察结果和 transcript，但结论只能是：

- `observed_as_expected`：成功格无错误且 oracle 没有失败，或失败格观察到错误；
- `observed_mismatch`：与粗粒度 expected status 冲突；
- `not_strictly_judgeable`：错误无法唯一归因到目标语句或预期 SQLSTATE 未定义。

不得把此等级伪报为严格 SQLSTATE 验证通过。最终报告必须单列这 14,718 个 case 的证据限制。

## 4. 隔离与并行模型

运行使用 `/tmp/pgcf-postgresql-18.4-install/bin` 的 PostgreSQL 18.4 工具链，建立 4 个独立 worker：

- 每个 worker 使用独立 data directory、socket directory、port 和维护数据库；
- worker 之间不共享 catalog、角色、数据库对象或实例级参数；
- 每个 worker 内串行执行 SQL；全局最多 4 个 SQL 同时运行；
- 默认单文件超时 30 秒；运行器本身具有最大 worker 数和明确停止机制；
- 不连接或修改用户的其他 PostgreSQL 实例。

每个 case 在同一个隔离 worker 上依次执行 run-01、恢复/清理、run-02，并比较规范化结果。发生 server crash、断连或 post-clean 失败时，保存证据、重建该 worker，再继续后续 case。

## 5. 分批和恢复

默认批大小为 500 个唯一 SQL。每批流程：

1. 校验 manifest 与 SQL SHA；
2. 执行批内 run-01；
3. 执行必要清理或 worker 恢复；
4. 执行批内 run-02；
5. 比较结果并写入只追加结果账本；
6. 原子更新 checkpoint；
7. 生成批次摘要。

首个校准阶段覆盖全部 183 个语句的成功/失败代表值、全部三种证据等级和 external 路由。校准发现运行器级错误时停止进入全量阶段；发现真实 SQL 偏差时记录并继续，除非 server 不可恢复或清理污染无法隔离。

恢复时只跳过同时满足 case path、SQL SHA、runner schema version、server version 和两轮完成标记均一致的记录。半完成批次安全重跑。

## 6. 判定规则

strict case 通过必须同时满足：

- 两轮都未超时，psql 按脚本合同正常完成；
- 实际 target SQLSTATE 等于冻结 expected SQLSTATE；
- stdout 中没有失败的布尔 oracle；
- cleanup 成功，worker 可继续使用；
- 两轮规范化 stdout/stderr、SQLSTATE 和结构化投影一致。

compatibility case 使用同样的退出、oracle、清理和确定性检查，但证据等级保持 compatibility。observational case 不做不存在的精确 SQLSTATE 断言。

以下情况单独分类，不能统一记作“SQL 失败”：

- `sqlstate_mismatch`；
- `oracle_failure`；
- `unexpected_psql_error`；
- `missing_target_sqlstate`；
- `cleanup_failure`；
- `timeout`；
- `server_crash_or_disconnect`；
- `two_run_mismatch`；
- `not_strictly_judgeable`。

## 7. 证据布局

运行证据写入：

```text
artifacts/runtime/pg18-full-sql-validation-v1/
  manifest.jsonl
  run.json
  checkpoint.json
  results/
    batch-NNNNN.jsonl
  failures/
    <case-id>-run-01.stdout
    <case-id>-run-01.stderr
    ...
  reports/
    calibration.json
    statement-summary.json
    sqlstate-summary.json
    final-summary.json
```

成功 case 只保存结构化字段和 transcript SHA，避免把约 170 万次完整 stdout/stderr 重复写入磁盘；失败、超时、崩溃和两轮差异 case 保存完整 stdout/stderr。

## 8. 完成门禁

只有以下条件全部成立才能宣布本次全量运行完成：

- manifest 恰好包含 855,913 个唯一 SQL，missing/duplicate/unknown 均为 0；
- 每个 manifest case 都有两个完成的执行记录；
- 总执行次数恰好为 1,711,826；
- 每个结果绑定实际 SQL SHA 与 PostgreSQL `server_version_num=180004`；
- 所有 strict/compatibility 偏差均已分类并可定位到 SQL；
- observational legacy 的证据限制被明确统计；
- checkpoint、批次账本与最终汇总计数守恒；
- 执行器测试、静态检查和校准批次均通过。

本设计的目标是如实分析现有 SQL 是否符合预期；发现失败时保留证据，不修改或隐藏原 SQL 结果。
