# PostgreSQL 18.4 全量 SQL 分批运行验证实施计划

> **执行要求：** 按 `superpowers:executing-plans` 逐任务实施；代码变更遵守 `superpowers:test-driven-development`；最终结论遵守 `superpowers:verification-before-completion`。

**目标：** 对正式范围内 855,913 个唯一 SQL 在 4 个隔离 PostgreSQL 18.4 worker 中执行两轮，形成可恢复证据并分析实际结果是否符合预期。

**架构：** manifest compiler 从 statement-cycle progress 编译唯一执行清单；runtime engine 管理隔离 worker、两轮执行和证据分级；checkpoint store 以 500 个 case 为批次只追加落盘；reporter 对 183 个语句及失败类型做守恒汇总。

---

### Task 1：冻结 manifest 与三类执行合同

**文件：**

- Create: `src/pg_case_factory/full_sql_runtime.py`
- Create: `tests/test_full_sql_runtime.py`

- [ ] 先写失败测试：正式范围计数、共享 retained package 去重、空 schedule 包仍纳入、重复 schedule 不重复执行。
- [ ] 实现 manifest record/compiler，解析 strict、compatibility、observational 三种证据等级。
- [ ] 测试 SQL SHA、expected outcome/SQLSTATE、external route 与稳定排序。
- [ ] 运行 Task 1 定向测试并提交。

### Task 2：实现单 case 两轮判定

**文件：**

- Modify: `src/pg_case_factory/full_sql_runtime.py`
- Modify: `tests/test_full_sql_runtime.py`

- [ ] 先写失败测试：strict SQLSTATE 匹配/缺失/错配、oracle false、退出码、超时、两轮 transcript/结构化差异。
- [ ] 实现 psql 输出规范化、结果记录和三类证据等级判定。
- [ ] compatibility 使用 plan 元数据；observational 不伪造精确 SQLSTATE 结论。
- [ ] 失败结果保留 stdout/stderr，成功结果只保留 digest。
- [ ] 运行 Task 2 定向测试并提交。

### Task 3：实现隔离 worker 与恢复安全

**文件：**

- Modify: `src/pg_case_factory/full_sql_runtime.py`
- Modify: `tests/test_full_sql_runtime.py`

- [ ] 先写失败测试：只允许 PG18.4、worker 路径/port 唯一、并行上限 4、超时上限、Ctrl+C 停止和 worker 重建。
- [ ] 实现 initdb/pg_ctl/createdb/bootstrap/stop 生命周期。
- [ ] 实现 crash/disconnect/cleanup 污染后的证据保存与 worker 重建。
- [ ] 保证不触碰已有 PG 实例和用户数据目录。
- [ ] 运行 Task 3 定向测试并提交。

### Task 4：实现批次账本、断点续跑与报告

**文件：**

- Modify: `src/pg_case_factory/full_sql_runtime.py`
- Modify: `src/pg_case_factory/cli.py`
- Modify: `tests/test_full_sql_runtime.py`
- Modify: CLI 对应测试文件（若已存在）

- [ ] 先写失败测试：500-case 分批、原子 checkpoint、半批重跑、SHA 漂移失效、结果计数守恒。
- [ ] 实现 JSONL 结果账本、failure transcript、checkpoint 和 summary。
- [ ] 增加 CLI：compile、calibrate、run、resume、report；参数具有保守默认值和上限。
- [ ] 运行定向测试、compileall、diff-check 并提交。

### Task 5：校准批次

- [ ] 编译真实 manifest，断言 855,913 个唯一 SQL和 183 个语句。
- [ ] 建立 4 个隔离 PostgreSQL 18.4 worker。
- [ ] 选择覆盖 183 个语句、三种证据等级、成功/失败与 external 的校准集合。
- [ ] 执行两轮，区分运行器缺陷与 SQL 偏差；只修运行器缺陷，不篡改 SQL 结果。
- [ ] 输出 `reports/calibration.json`；校准门禁通过后进入全量阶段。

### Task 6：全量分批执行

- [ ] 按稳定 manifest 顺序，以每批 500 个 case、4 worker 执行。
- [ ] 每批两轮完成后落盘 checkpoint 和摘要。
- [ ] 定期核对 completed、pending、failures、timeouts、crashes 与 ETA。
- [ ] 可恢复基础设施异常；保留真实 SQL mismatch 并继续其他 case。
- [ ] 直至 855,913 个 case 全部获得两轮记录。

### Task 7：最终守恒与分析

- [ ] 验证 case 总数 855,913、执行总数 1,711,826。
- [ ] 验证结果 SQL SHA、runner schema、PG18.4 版本和批次账本一致。
- [ ] 按 statement、证据等级、expected outcome、expected/actual SQLSTATE、失败类别汇总。
- [ ] 单列 14,718 个 observational legacy case 的判定限制。
- [ ] 运行完整相关测试和静态检查。
- [ ] 产出 `reports/final-summary.json` 和面向检查的 Markdown 总结。

---

## 运行命令（实现后冻结）

```bash
python -m pg_case_factory.cli full-sql-runtime compile \
  --output artifacts/runtime/pg18-full-sql-validation-v1

python -m pg_case_factory.cli full-sql-runtime calibrate \
  --output artifacts/runtime/pg18-full-sql-validation-v1 \
  --workers 4 --batch-size 500 --timeout-seconds 30

python -m pg_case_factory.cli full-sql-runtime run \
  --output artifacts/runtime/pg18-full-sql-validation-v1 \
  --workers 4 --batch-size 500 --timeout-seconds 30 --resume
```

实际 CLI 名称若受现有 parser 结构约束，可做等价调整，但 compile/calibrate/run/resume/report 五项能力和安全上限不可删除。
