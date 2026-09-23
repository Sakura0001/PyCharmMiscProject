# 修复台账 | Fix Log

> 对应审计: `test_gap_audit_20260923.md`
> 验证环境: 阿里云 RDS MySQL **8.0.36**（`ddl_test`）+ 本机社区版 MySQL 8.0.45（对照）
> 规则: **每改完一个点，先验证通过，再改下一个点**；每一步都有可复跑的验证命令与实测证据。

| 步骤 | 审计条目 | 状态 | 验证方式 |
|---|---|---|---|
| 1 | P0-1 执行器跳过 .gz | ✅ 已修复并验证 | pytest 30 + RDS 实跑 |
| 2 | P0-4 用例 ID 全局唯一 | ✅ 已修复并验证 | pytest 34+1xfail + RDS 并发实跑 |
| 3 | P0-2 / P0-3 分区分支对照与空断言 | ✅ 已修复并验证 | pytest 45 + RDS 103 例实跑 |
| 4 | P0-9 分区定义非类型感知(errno 1654) | ⏳ 进行中 | — |
| 5 | P0-5 64 分区组合实为 8 种 / 无 SUBPARTITION | ⏳ 待办 | — |
| 6 | P0-6 超上限负向 INSERT 被注释 | ⏳ 待办 | — |
| 7 | P0-7 + P1-1 期望值机读化 + 列类型断言 | ⏳ 待办 | — |
| 8 | P0-8 VC-08/VC-09/VBIN-03 超行宽上限(errno 1118) | ⏳ 待办 | — |
| 9+ | P1-2 ~ P3 | ⏳ 待办 | — |

---

## Step 1 — P0-1 执行器静默跳过 `.sql.gz`

**问题**：`run_tests.py` 只 glob `*.sql`，而 8 个大文件（全部 VARCHAR / TEXT / VARBINARY + 两个分区文件）只以 `.sql.gz` 存在且明文版被 `.gitignore` 排除 → 16,097 / 18,993（**84.8%**）用例被静默跳过，无任何告警。

**改动**：执行器 v3 重写
- 文件发现同时匹配 `.sql` / `.sql.gz`（明文优先、去重、忽略 `.bak`），指定文件不存在时**大声报错**
- 按 `-- Test Case:` 切分用例，pymysql 逐语句执行，**errno + 具体语句按用例归因**（v2 只保留文件级 stderr 尾巴 2000 字符）
- 完整性核算：选中用例必须全部产出判定，否则记 `MISSING` 并以退出码 3 失败
- manifest：全量基线（内容哈希 / 用例数 / 唯一 ID / 重复 ID）+ 本轮 `run_manifest`，`--check-manifest` 可对账；按 `(size, mtime)` 缓存，dry-run 27s → 0.06s
- 环境快照：`VERSION()` + 25 个关键 variables 落盘
- `--workers / --retry / --resume / --case-filter / --sample / --dry-run / --sql-dir / --use-cli`
- 结果**带时间戳归档**到 `results/archive/`，永不覆盖历史证据
- 密码支持 `MYSQL_PWD` / `MYSQL_DEFAULTS_EXTRA_FILE`

**过程中自查出的两个自身缺陷（已修）**
1. `write_outputs()` 会用本轮 manifest 覆盖全量基线（dry-run 路径对、实跑路径错）→ 已分离 `manifest_<env>.json` 与 `run_manifest_<env>.json`，并加回归守卫测试。
2. 验证跑覆盖了 `results/summary_aliyun.csv`（8,094 行历史证据）→ 已从 git 恢复并归档为 `results/archive/summary_aliyun_20260920_v2runner_baseline.csv`，同时把执行器改为归档式写入。

**验证**
```bash
python3 run_tests.py --env aliyun  --dry-run   # 12 文件 / 10340 用例（修复前只能发现 9 文件 / 2148 用例）
python3 run_tests.py --env internal --dry-run   # 15 文件 / 8653 用例（修复前 10 文件 / 1351 用例）
python3 -m pytest selfcheck/test_runner.py -q   # 30 passed
python3 run_tests.py --env aliyun --files 10_special_patterns.sql           # RDS: 8/8 PASS
python3 run_tests.py --env aliyun --files 07_varchar_instant.sql.gz --sample 20
```
**实测收获**：gz 抽样立刻暴露 2 个从未执行过的新增上限用例失败 —— `TC-A0241`(VC-08) / `TC-A0261`(VC-09) **errno 1118 Row size too large**（v2 只会记成无理由的 `NO_OUTPUT`）。→ 立项 P0-8。

---

## Step 2 — P0-4 用例 ID 全局唯一化

**问题（实测）**：18,993 个用例只有 **8,500** 个唯一 ID
- 7,552 个同文件内重复：分区文件 instant / inplace 复用同一个 `TC-PA0001`
- 679 个跨文件重复：`TC-A0001` 同时是 01..08 八个文件里 **8 种完全不同的类型转换**

后果：结果无法按算法/类型归因；派生表名 `t1_a0001` 被 8 个文件共用 → 并发执行互相污染；执行器 `seen_test_ids` 是集合，两次里只要有一次出结果就不记 `NO_OUTPUT` → **3,328 个坏用例只体现为 1,600 个 ERROR，未执行数被低估一半**。

**改动**
- 新增 `CaseIdFactory`，ID 规则 `TC-<文件号>-<作用域>-<序号>-<IT|IP>`，作用域 `REG/ATR/SPE/FK/PTK/PNK`；同一文件跨算法轮次共享计数器
- 表名一律由 ID 派生 ⇒ 表名同样全局唯一，`--workers>1` 才安全
- `generate_all()` 改为**表驱动**（消除 27 处分散的 ID 生成点），生成结束强制自检：ID 或派生表名重复即 `SystemExit` 拒绝产出
- 用例头补 `Transition ID` / `Varied factor`
- `_write_sql_file` 按体积阈值（400KB）自动产出 `.sql` 或 `.sql.gz`，并**单一真源**维护 `.gitignore` 自动区块
- 新增 `verify_git_tracking()`：仓库根 `.gitignore` 忽略了整个 `outputs/`，产物必须 `git add -f`；未跟踪时打印告警与修复命令，杜绝"磁盘有、仓库没有"复发

**过程中自查出的缺陷（已修）**
1. `_sync_gitignore` 把**要入库的 `.gz`** 写进了忽略列表（应忽略的是解压出的明文 `.sql`）→ 已修，并清理僵尸区块（改为按 `# BEGIN/END auto-generated` 前缀匹配）。
2. 一次 patch 用 `s.index()` 定位锚点时命中了文件开头的同名标记，导致 `generate_test_sql.py` 被重复拼接（2,142 → 3,869 行、旧定义覆盖新定义）→ 已精确修复并加"每个函数只允许一处定义"的检查。

**验证**
```bash
python3 generate_test_sql.py                     # 18,993 用例 / 18,993 唯一 ID（自检通过）
python3 -m pytest selfcheck/test_runner.py -q    # 34 passed, 1 xfailed
python3 run_tests.py --env aliyun  --dry-run     # 10340 / 唯一 10340 / 重复 0
python3 run_tests.py --env internal --dry-run     # 8653 / 唯一 8653 / 重复 0
python3 run_tests.py --env aliyun --files 06_char_inplace.sql.gz --workers 4   # 108/108 PASS, 30.7s（历史串行 71s）
python3 run_tests.py --env aliyun --files 12_partition_64.sql.gz --case-filter 'TC-12-PNK-00[0-4][0-9]-' --workers 6
```
逐文件用例数与改动前**完全一致**（18,993 → 18,993），确认只改标识、未增删覆盖。

---

## Step 3 — P0-2 / P0-3 分区分支：对照表结构与空断言

**问题 1（P0-2）**：`_build_partition_test` 的"目标列是分区键"分支里，t1 建成 `(id, target, pad)`，t2 却用 `_build_create_table()` 建成 `(id, pad1, target, pad2)`，对照 SQL 写 `a.pad <=> b.pad` → **ERROR 1054 Unknown column 'b.pad'**，静态统计影响 **3,328（阿里云）+ 1,216（内网）= 4,544** 个用例恒无判定输出；README 却把它们归因为"分区策略不支持该类型作分区键、建表失败"。

**问题 2（P0-3）**：`PK_COMPAT` 判定不可分区的分支，输出的是一条**常量** SELECT（`'BUILD_OR_ALTER_FAIL_EXPECTED','CHECK_MANUALLY'`），与前面语句成败完全无关 → 640 个用例等于没有断言，却被计入"预期行为"。

**改动**
- 生成器：t2 改为 t1 的**结构克隆**（同列、同 PK、同分区定义）；新增 `column_type_of()`（映射规则已用 RDS 51 个真实样本验证：`column_type` == 类型定义小写 + 空格归一）、`build_meta_assertion()`、`build_table_absent_assertion()`
- PTK 可建表分支：数据对照 + **`#TYPE_UNCHANGED` 断言**（证明 ALTER 确实被拒、没有半生效）
- PTK 建表应被拒分支：改为 **`#BUILD_REJECTED` 真实查询 `information_schema.tables`**，表若意外建成则 FAIL 并提示"PK_COMPAT 需修正"
- 执行器：支持一个用例多条断言（`<用例ID>#<断言名>`），聚合规则"任一 FAIL ⇒ FAIL"（旧实现只看最后一行，先失败后通过会被掩盖）；新增 **`@expect assertions=N` 断言条数完整性校验**，少一条即判 ERROR
- 结果 CSV/JSONL 增加 `assertion_count` / `assertions` 列

**验证**
```bash
python3 -m pytest selfcheck/test_runner.py -q    # 45 passed（P0-2 守卫由 xfail 转真实通过）
python3 run_tests.py --env aliyun --files 12_partition_64.sql.gz --case-filter 'TC-12-PTK-' --sample 40 --workers 4
```
RDS 实测 103 例：**MANUAL 0**（修复前同类用例 100% 是空断言）、`BUILD_REJECTED` 11/11 PASS、`PRIMARY` 82 PASS、`TYPE_UNCHANGED` 62 PASS + 30 FAIL。

**新发现（立项 P0-9）**：那 30 例 `TYPE_UNCHANGED` 失败的 `actual=<missing>`，根因是建表就失败：
```
errno=1654 Partition column values of incorrect type
CREATE TABLE ... (target TINYINT, ... PRIMARY KEY (id, target))
PARTITION BY RANGE COLUMNS(target) (p0 VALUES LESS THAN (100), p1 ... (200), p2 ... (300), ...)
```
`_build_single_partition()` 的分区界是硬编码整数字面量：对 `TINYINT`（上限 127）而言 200/300 越界；对 `VARCHAR` 而言整数界类型不符。**分区定义不是类型感知的** —— 这正是 Step 3 的价值：旧套件把它藏成"静默无输出"，现在带 errno 暴露出来了。下一步（Step 4）修分区定义的类型感知，并与 P0-5（真 SUBPARTITION + 组合去重）一起做。
