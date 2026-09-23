# 修复台账 | Fix Log

> 对应审计: `test_gap_audit_20260923.md`
> 验证环境: 阿里云 RDS MySQL **8.0.36**（`ddl_test`）+ 本机社区版 MySQL 8.0.45（对照）
> 规则: **每改完一个点，先验证通过，再改下一个点**；每一步都有可复跑的验证命令与实测证据。

| 步骤 | 审计条目 | 状态 | 验证方式 |
|---|---|---|---|
| 1 | P0-1 执行器跳过 .gz | ✅ 已修复并验证 | pytest 30 + RDS 实跑 |
| 2 | P0-4 用例 ID 全局唯一 | ✅ 已修复并验证 | pytest 34+1xfail + RDS 并发实跑 |
| 3 | P0-2 / P0-3 分区分支对照与空断言 | ✅ 已修复并验证 | pytest 45 + RDS 103 例实跑 |
| 4 | P0-9 分区定义非类型感知 + P0-5 无 SUBPARTITION | ✅ 已修复并验证 | 实测探针 + pytest 52 + RDS 512 例 |
| 5 | P0-8 VC-08/VC-09/VBIN-03 超行宽上限(errno 1118) | ✅ 已修复并验证 | pytest 59 + **RDS 全量 5220/5220 PASS** |
| 6 | P0-6 超上限负向 INSERT 被注释 | ⏳ 进行中 | — |
| 7 | P0-7 + P1-1 期望值机读化 + 列类型断言 | ⏳ 待办 | — |
| 8+ | P1-2 ~ P3 | ⏳ 待办 | — |

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

---

## Step 4 — P0-9 + P0-5 分区生成器重建（类型感知 + 真 SUBPARTITION + 实测矩阵）

**问题 1（P0-9）**：`_build_single_partition()` 的分区界是硬编码整数字面量 `100/200/300`
- 对 `TINYINT`（上限 127）越界、对 `VARCHAR` 类型不符 → 实测 **errno 1654 / 1697**，建表直接失败
- RDS 抽样 103 例中 30 例中招（Step 3 的新断言把它们从"静默无输出"变成了带 errno 的可见失败）

**问题 2（P0-5）**：`_build_partition_def()` 里有自我否定的死代码，最终 `return first, True`
- 二级分区类型被完全丢弃：两个分区文件里 `SUBPARTITION` 出现 **0 次**
- `PP-33 (HASH+RANGE)` 与 `PP-37..PP-40 (HASH+*)` 生成的 SQL 逐字相同 → "64 种组合"实为 8 种 × 8 份重复

**问题 3**：`PK_COMPAT` 是猜的。实测证伪了多条：`("KEY","text")=True`、`("KEY","blob")=True`、
`("RANGE COLUMNS","decimal")=True` 全部错误（TEXT/BLOB 不能作任何分区键；DECIMAL 只能用 KEY/LINEAR KEY）。

**做法：先实测，再生成**
- 新增 `tools/probe_partition_compat.py`：按类型构造**类型正确**的分区定义，逐个 CREATE + INSERT + ALTER 探测，
  产出 `tools/partition_compat_<env>.json`（内网实例可直接复跑，得到自己的矩阵）
- 探测脚本自身也抓出两个 bug 并修正：① MySQL 的 `SUBPARTITION BY` 必须写在分区定义列表**之前**
  （写反 → 16 个组合策略全部误报 errno 1064）；② ALTER 探测原先用**同类型**（no-op），测不出真实 errno，
  改为探测真实的加宽转换
- 生成器内嵌 `PARTITION_COMPAT`（按 category 归并，附实测出处），并新增 pytest 守卫
  `test_partition_compat_matrix_matches_measured_probe` 把内嵌矩阵与探针 JSON 逐 category 对齐

**改动**
- 24 种**互不相同**的策略 = 8 种一级 + 16 种组合分区（`RANGE*/LIST* × SUB HASH/LINEAR HASH/KEY/LINEAR KEY`）
- `build_partition_clause()` 按列类型分派分区界与 LIST 取值（整数 / 字符串 / 二进制 / BIT / DECIMAL / TEXT / BLOB）
- LIST/LIST COLUMNS 没有 MAXVALUE 兜底 → PTK 分支只插入分组代表值（`partition_fit_values`），
  消除旧实现"灌边界值 → errno 1526 → 插入静默失败 → 用例退化成空表对照"的问题
- 分区键可建性新增**长度维度**：`max_bytes(target) + 4(id) ≤ 3072`
  （二分实测：latin1 VARCHAR 最大 3068、utf8mb4 最大 VARCHAR(767)，再大 1 字节即 errno 1071）
- `expected_partition_key_alter()` 按实测建立期望：分区键改类型时 INSTANT/INPLACE 多为 **1846**；
  唯一例外是 VARCHAR/VARBINARY **不跨 255 字节长度前缀边界**的扩容 → INPLACE 成功、INSTANT 仍 1845；
  `ALGORITHM=COPY` 在分区键上**可以**成功改类型（另立 COPY 对照组专项）
- 分区文件更名 `12_partition_64` → `12_partition_strategies`（"64"已不成立）
- 生成器新增 `_prune_stale_sql()`：清理本轮未产出的旧 `.sql/.sql.gz`，防止执行器跑到过期产物

**过程中自查出的缺陷（已修）**
1. `PARTITION BY RANGE COLUMNS COLUMNS(target)` —— 关键字重复（`"%s %s"` 拼接对 `RANGE COLUMNS` 不成立），
   静态守卫 `test_no_duplicated_partition_keyword` 抓到
2. 改名后的旧产物 `12_partition_64.sql.gz` 残留在目录里，会被执行器当有效文件跑 → 加 `_prune_stale_sql`
3. TEXT/BLOB 的分区界回退成了整数字面量，使 BUILD_REJECTED 用例失败在**错误的原因**上
   （1697 而非语义正确的 1170）→ 补 text/blob 的字符串/十六进制界

**验证**
```bash
python3 tools/probe_partition_compat.py --env aliyun      # 17 类型 × 24 策略 = 408 次探测
python3 generate_test_sql.py                              # 9553 用例 / 9553 唯一 ID
python3 -m pytest selfcheck/test_runner.py -q             # 52 passed
python3 run_tests.py --env aliyun --files 12_partition_strategies.sql.gz --sample 6 --workers 8
#   -> 512/512 PASS，0 FAIL / 0 ERROR / 0 MANUAL
```
分区用例数 15,104 → **5,664**：删掉的是 8 倍完全重复，新增的是 16 种真组合分区，
**distinct 覆盖从 8 种策略提升到 24 种**。

---

## Step 5 — P0-8 上限转换超行宽 / 索引键上限

**问题**：`upper_limit_coverage_report.md` 声称 VC-08 / VC-09 / VBIN-03 "INSTANT+INPLACE ✅SUCCESS、minimal_table 是"，
但这三条从未被执行过（在 Step 1 修好 gz 之前）。实跑结果：
- `VARCHAR(16383)` utf8mb4 = 65,532 + 2 前缀 + 4(id) = **65,538 > 65,535** → errno **1118**
- `VARCHAR(65529)` / `VARBINARY(65529)` 同理 → errno **1118**
- 完整阿里云套件 5,220 例中 **216 例非 PASS，全部集中在这三条转换**（1118×200、1071×6、PRIMARY FAIL×10）

**二分实测真实上界**（`id INT AUTO_INCREMENT PRIMARY KEY + target` 两列表，RDS 8.0.36 与社区版 8.0.45 一致）：

| 类型 | 实测最大 n | 说明 |
|---|---|---|
| `VARCHAR(n)` utf8mb4 | **16382** | 16382×4 + 2 + 4 = 65534 ≤ 65535 |
| `VARCHAR(n)` latin1 | **65528** | 65528 + 2 + 4 = 65534 |
| `VARBINARY(n)` | **65528** | 同上 |
| `BINARY(n)` | 255 | 类型本身上限 |
| `CHAR(n)` utf8mb4 | 255 | 类型本身上限 |

顺带实测：`innodb_strict_mode` 在两台实例上不同（RDS=0 / 本机=1），会影响"无显式 PK"时的行宽预算
（RDS 65524 vs 本机 65532），已作为环境快照维度记录。

**改动**
- 三条上限转换改为 **16381→16382 (utf8mb4) / 65527→65528 (latin1) / 65527→65528 (VARBINARY)**；
  "再 +1" 变成真正的超上限负向探针（Step 6 落地）
- 新增**因子可行性守卫** `check_case_feasible()`：目标列 > 3072 字节且因子要求整列索引时，
  生成显式负向用例（`#BUILD_REJECTED` + `@expect build=FAIL errno=[1071]`），
  而不是像以前那样照样生成 CREATE、跑出一片 1071/1118 然后被记成 NO_OUTPUT
- `_build_column_attribute_test` 修两个缺陷：① 只有 CHARSET/COLLATE 分支带字符集，
  UNSIGNED/COMMENT 分支写裸 `VARCHAR(65528)` → 按库默认 utf8mb3 解析 → errno **1074** "max = 21845"；
  ② 完全不认 `minimal_table`，仍加 `pad VARCHAR(20)` → errno **1118**
- 分区 PTK 分支补字符集（`_partition_col_def`）：CREATE 不带而 ALTER 带 `CHARACTER SET latin1`，
  语义变成"改长度 + 改字符集" → INPLACE 被拒 1846，11 个用例的 `TYPE_AFTER_ALTER` 据此正确判 FAIL
- 期望模型修正：`minimal_table` 下 `COMPOSITE_PK` 被 `_build_create_table` **降级为 `PRIMARY KEY(id)`**，
  目标列不在任何索引里 → INSTANT 实际成功。旧模型一律判 FAIL、对照表按旧类型建 → 4 例数据不一致

**验证**
```bash
python3 generate_test_sql.py                        # 9553 用例 / 9553 唯一 ID
python3 -m pytest selfcheck/test_runner.py -q       # 59 passed
python3 run_tests.py --env aliyun --files 07_varchar_instant.sql.gz 08_varchar_inplace.sql.gz --workers 8
#   -> 603/603 PASS（修复前 120 ERROR + 20 FAIL）
python3 run_tests.py --env aliyun --workers 8
#   -> 5220/5220 PASS，0 FAIL / 0 ERROR / 0 MANUAL / 0 MISSING（10.6 分钟）
```
新增 7 项静态守卫：上限值等于实测上界、任何转换不得超 65535 行宽预算、
infeasible 组合必须走显式负向用例、minimal_table 降级不得误判、
INSTANT 期望必须认降级、ATR 用例必须认 minimal_table、字符集在所有建表点显式且与 ALTER 一致。
