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
| 6 | P0-6 超上限负向 INSERT 被注释 | ✅ 已修复并验证 | pytest 69 + **RDS 全量 5220/5220 PASS** |
| 7 | P0-7 + P1-1 期望值机读化 + 列类型断言 | ✅ 已修复并验证 | pytest 80 + 反向对照 6/6 + **RDS 全量 5228/5228 PASS** |
| 8 | 环境能力画像 + 内网 CHAR/VARCHAR 口径 | ✅ 机制已落地并验证（口径待确认） | pytest 85 + RDS 画像反向对照 |
| 9 | P1-2/P1-3/P1-4 空表 + DDL 语句形态 + 索引完整性 | ✅ 已修复并验证 | pytest 90 + RDS 200/200 + 392/392 |
| 10 | P1-5 在线 DDL 失败模式 | ✅ 已实现并验证 | RDS 43 PASS/0 FAIL/1 SKIP + 本机 S6 实测 1799 |
| 11 | P1-6 binlog/备库一致性 + 崩溃恢复 | ✅ 已实现并验证 | R1 7/7 (RDS) + C1/C2 各 14/14 (SIGKILL 真实崩溃) |
| 12 | P2 类型转换兼容矩阵（49 探针 × 4 算法） | ✅ 已实现并冻结基线 | 196/196 PASS + golden 回归 |
| 13 | P2 因子矩阵（22 因子 × 3 转换 × 3 算法）+ 会话变量专项 | ✅ 已实现并冻结基线 | 198/198 PASS + 本机 14/14 + RDS 明确 SKIP |
| 14 | P2 concurrent_dml 四项 + 凭据外置 | ✅ 已修复并验证 | RDS 实跑：4092 边界 / 70 轮 MODIFY / 4000 DDL / 延迟分位 |
| 15 | P3 工程与文档口径统一 + 凭据清理 | ✅ 已完成 | 文档 endpoint 清零 / .bak 删除 / README 重写 |

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

---

## Step 6 — P0-6 超上限负向探针真正执行

**问题**：`_build_test_case_sql` 生成的是 `-- INSERT INTO ...`（整条被注释），
全套件 **2,623 条**"超出新类型上限的值必须被拒绝"的探针从未执行；
而 `upper_limit_coverage_report.md` §3.1/§3.2 明确写着"插入 256 字符(FAIL)"、
"超上限值(预期FAIL): `REPEAT('q',16384)`"、"`0x41*65530`" —— 报告描述的验证没有发生。

**改动（生成器）**
- 新增 `build_negative_probes()`：超限值**同时**插入 t1 与对照表 t2（两表类型相同，
  因此无论 STRICT 还是非 STRICT，行为都必须完全一致），并用会话变量记录插入前后行数：
  - STRICT → 断言 `t1_added = 0 AND t2_added = 0`（超限值绝不能落库）
  - 非 STRICT → 断言 `t1_added = t2_added`（截断行为必须与对照表对称）
- 每条探针语句的 sha1 写进 `-- @expect neg_probe=<sha1>=<errno|ACCEPTED>`，
  执行器据此把"声明的期望"与"实际报错的语句"精确对上
  （65529 字节的长字面量在结果里被截断展示也不影响匹配）
- `@expect` 头统一化：`alter= build= assertions= neg_probes=`

**改动（执行器）**
- 错误记录增加 `stmt_sha1`（完整语句哈希）
- `collect_sql_assertions()` / `aggregate()` / `check_negative_probes()` 三段式：
  SQL 判定行 + runner 合成的 errno 级校验一起参与"任一 FAIL ⇒ FAIL"聚合
- `assertions=N` 只数 SQL 判定行，runner 合成断言另计（避免误判 ASSERTION_COUNT）

**过程中自查出的缺陷（已修）**
- `NEG_REJECTED` 的 `CONCAT` 里多写了一个单引号 → 语句被吞、后面的对照 SELECT 一起截断，
  543 个用例报 errno 1064。**新增静态守卫 `test_every_statement_has_balanced_quotes`**
  （每条语句单引号必须成对、括号必须配对），这类问题以后在生成阶段就会被拦住。

**验证**
```bash
python3 generate_test_sql.py     # 被注释的 INSERT: 2623 -> 0；真实探针语句 5228 条；NEG_REJECTED 断言 2492 条
python3 -m pytest selfcheck/test_runner.py -q    # 69 passed
python3 run_tests.py --env aliyun --files 01_integer_signed_instant.sql.gz 05_char_instant.sql.gz 08_varchar_inplace.sql.gz --workers 8
#   -> 707/707 PASS；断言 2458 条（SQL 1250 + runner 合成 1208），平均每用例 3.48 条
#      NEG_ERRNO 1208 PASS / NEG_REJECTED 543 PASS / PRIMARY 701 PASS / BUILD_REJECTED 6 PASS
python3 run_tests.py --env aliyun --workers 8
#   -> 5220/5220 PASS，0 FAIL / 0 ERROR / 0 MANUAL / 0 MISSING
```
STRICT 与非 STRICT 两档均有用例覆盖并全部通过。

---

## Step 7 — P0-7 期望值机读化并强制比对 + P1-1 每用例列元数据断言

**问题**
- 执行器把 `expected` 写进 CSV 却**从不比对**；解析规则互相打架，实测取值分布为
  `CREATE` 5440 / `BUILD` 640 / `FAILS` 80 / `FAIL` 8 / 空 168（从 `-- Expected: CREATE OK, ALTER FAIL ...`
  里错抓了 "CREATE"）。所以"0 FAIL"只意味着"产出了判定行的用例里数据对照没差异"。
- 全套件 238 条元数据断言只覆盖 column_comment(118) / auto_increment(40) / unsigned(20) /
  collation(30) / charset(30)，**断言 ALTER 后列类型的条数 = 0**；
  `SHOW CREATE TABLE` / `is_nullable` / `column_default` / `ordinal_position` 均为 0。

**改动**
- 每个用例头输出机读期望：`-- @expect alter=SUCCESS|FAIL errno=[...] build=... assertions=N
  alter_sha=<sha> column_type=... neg_probe=<sha>=<errno|ACCEPTED>`
- 执行器新增 `check_alter_outcome()`：按 `alter_sha` 在错误记录里定位那条 ALTER，
  声明 SUCCESS 就必须没报错、声明 FAIL 就必须报错且 errno 在声明集合内；
  一条用例可声明多个 sha（连续 ALTER 链 / 外键父子双侧）
- 新增 `build_meta_assertion_full()`：一条判定行同时校验 **column_type / is_nullable /
  column_default 有无 / character_set_name / collation_name / extra / ordinal_position**，
  mismatch 同时给出 `actual[...]` 与 `want[...]`；铺到 REG / ATR / PTK / PNK / SPE / FK 全部用例
- 期望值的表示形式先在 RDS 上实测（`information_schema` 里 `utf8` 显示为 `utf8mb3`、
  INVISIBLE 列 `extra='INVISIBLE'`、`BINARY DEFAULT x'00'` 的 `column_default='0x'` 等），不靠猜
- 字符集/排序规则支持 `*`（不校验）标记，用于列字符集继承 `character_set_database` 的场景
  （RDS=utf8mb3 / 本机=utf8mb4，硬编码会造成环境相关的假失败）

**新断言抓出的 4 个真实问题（全部已修）**

| # | 发现 | 实测证据 | 处理 |
|---|---|---|---|
| 1 | **AUTO_INCREMENT 列的类型加宽不支持 INSTANT** | 20 例 errno **1845**；INPLACE/COPY 正常；普通列 INSTANT 正常；与 SIGNED/UNSIGNED、是 PK 还是 UNIQUE 无关 | 期望改为 FAIL(1845)。旧套件对本文件只断言 `extra LIKE '%auto_increment%'`（ALTER 成败都为真），因此把 20 个实际失败的用例报成 "40/40 PASS" |
| 2 | **外键列改类型的完整规律** | 见下表；`tools/fk_matrix_aliyun.json` 66 条组合实测 | 重写 `expected_fk_alter()`；新增 `both_fkc0` / `both_drop_fk` 两个场景 |
| 3 | 带 VIRTUAL 生成列 + 生成列索引的列，INSTANT 改类型**成功** | 旧模型判 FAIL → 对照表按旧类型建且跳过 post-ALTER 插入 → 用例恒 PASS，什么也没验证 | 期望改为 SUCCESS |
| 4 | `vcol BIGINT AS (base_col*2)` 与 `base_col=9223372036854775807` 冲突 | errno **1690** BIGINT value out of range，整条多行 INSERT 失败、3 行数据全丢 | 改用 ±2^62，仍覆盖 INT→BIGINT 加宽 |

外键列改类型实测规律（RDS 8.0.36）：

| 规则 | 实测结论 |
|---|---|
| R1 | `ALGORITHM=INSTANT` 改 fk_col **一律失败**（MySQL 强制 fk_col 有索引）：整数 → **3780**（外键兼容性校验先触发）、字符串 → **1845**、DECIMAL/BIT → **1846** |
| R2 | `ALGORITHM=INPLACE` 改 CHAR/VARCHAR/BINARY/VARBINARY 的 fk_col **一律成功**，连"只改单侧"也成功 → 改完 parent=varchar(50) 与 child=varchar(100) 能和活的外键共存，**MySQL 对这类扩容不复核外键类型兼容性**（反直觉，风险点） |
| R3 | `ALGORITHM=INPLACE` 改整数（需 rebuild）：外键在 → **3780**；只有先 `DROP FOREIGN KEY` 才成功 |
| R4 | `SET foreign_key_checks=0` **不能**绕过 3780（常见误解，实测无效） |
| R5 | 摘除外键后 INSTANT 仍失败，但 errno 从 3780 变成 **1845**（失败原因变了） |

新增 FK 场景：`both_fkc0`（固化"关外键检查无效"这个反直觉结论）、
`both_drop_fk`（唯一可行序列 DROP FK → 改两侧 → ADD FK，并断言**约束确实加回来了**，
防止"改成功"是靠永久丢约束换来的）。FK 用例 16 → 24（阿里云）/ 24 → 36（内网）。

**反向对照（证明断言不是恒过）** —— `selfcheck/negative_control.py`，故意注入 6 类缺陷跑真实实例：

| 注入的缺陷 | 必须被谁抓到 | 结果 |
|---|---|---|
| 声明 alter=FAIL，实际成功 | ALTER_OUTCOME | ✓ |
| 声明 alter=SUCCESS，实际失败(1845) | ALTER_OUTCOME + META | ✓ |
| META 期望列类型写错 | META | ✓ |
| 探针声明 ACCEPTED，实际被拒 | NEG_ERRNO | ✓ |
| 声明 assertions=2 只产出 1 条 | ASSERTION_COUNT → ERROR | ✓ |
| 对照表少一行数据 | PRIMARY | ✓ |

**验证**
```bash
python3 -m pytest selfcheck/test_runner.py -q          # 80 passed
python3 selfcheck/negative_control.py --env aliyun     # 6/6 全部捕获
python3 run_tests.py --env aliyun --workers 8          # 5228/5228 PASS，0 FAIL/ERROR/MANUAL/MISSING
```
本轮实测规模：**5,228 用例 / 19,530 条断言（3.74 条/用例，SQL 11,564 + 执行器合成 7,966）**

| 断言 | 条数 |
|---|---|
| PRIMARY（数据对照） | 4,806 |
| ALTER_OUTCOME（声明 vs 实际 + errno） | 4,806 |
| META（7 项列元数据） | 4,780 |
| NEG_ERRNO（探针 errno 级） | 3,160 |
| NEG_REJECTED（超限值不落库/两表对称） | 1,458 |
| BUILD_REJECTED（建表应被拒） | 422 |
| META_CHILD_FK / META_PARENT_FK / META_CHILD_DATA / FK_CONSTRAINT_PRESENT / META_COL_* | 98 |

ALTER 声明与实际逐条对齐：SUCCESS↔SUCCESS 3,604；FAIL↔FAIL 1,202
（errno 1846×1056、1845×138、3780×8）；N/A 422（建表即被拒，无 ALTER）。

---

## Step 8 — 环境能力画像（为内网实例的 CHAR/VARCHAR 口径差异做数据化支撑）

**背景**：内网实例与阿里云 RDS 对 CHAR/VARCHAR 改类型的支持范围不同
（口径："不支持同字节变更，只支持跨字节变更"）。旧实现把期望值硬编码在
`transition["instant"] / transition["inplace"]` 里，换实例就得改代码、且无法审阅差异。

**改动：把实例差异表达成数据**
- 新增 `ENV_PROFILES` / `resolve_expectation(transition, algorithm, env)`：
  期望值先过环境画像，再叠加因子交互调整；命中画像规则的用例会在
  `@expect` 头留下 `profile_rule=PROFILE:<env>/charvarchar=<mode>(<same|cross>桶不支持)` 标记
- 长度字节桶口径统一：`LEN_BUCKET_BOUNDARY = 255`，CHAR 与 VARCHAR 用同一个桶函数
  （CHAR 定长存储没有长度前缀，但字节宽度同样以 255 为界）
- 四种模式：`cross_only`（只支持跨桶）/ `same_only`（只支持同桶）/ `all` / `none`
- 命令行 `--charvarchar-mode` 可整体切换口径，**换实例不改代码**
- 当前画像：`aliyun = all`（实测 5228/5228 PASS）、`internal = cross_only`（按口径，待实测复核）

**画像对内网的影响预览**（12 条 CHAR/VARCHAR 转换）

| 转换 | 字节变化 | 桶 | 内网(cross_only) 期望 |
|---|---|---|---|
| CHAR(1)→CHAR(2) latin1 | 1→2 | same | **FAIL** |
| CHAR(63)→CHAR(64) utf8mb4 | 252→256 | cross | SUCCESS |
| CHAR(254)→CHAR(255) utf8mb4 | 1016→1020 | same | **FAIL** |
| VARCHAR(1)→(2) latin1 | 1→2 | same | **FAIL** |
| VARCHAR(254)→(255) latin1 | 254→255 | same | **FAIL** |
| VARCHAR(255)→(256) latin1 | 255→256 | cross | SUCCESS |
| VARCHAR(85)→(86) utf8mb3 | 255→258 | cross | SUCCESS |
| VARCHAR(63)→(64) utf8mb4 | 252→256 | cross | SUCCESS |
| VARCHAR(64)→(65) utf8mb4 | 256→260 | same | **FAIL** |
| VARCHAR(100)→(200) utf8mb4 | 400→800 | same | **FAIL** |
| VARCHAR(16381)→(16382) utf8mb4 | 65524→65528 | same | **FAIL** |
| VARCHAR(65527)→(65528) latin1 | 65527→65528 | same | **FAIL** |

**验证：画像反向对照（在 RDS 上故意用错画像）**

把 aliyun 环境强制切成 `cross_only`（RDS 实际两种都支持），跑 `07_varchar_instant.sql.gz`：

```
279 例 -> 119 PASS / 160 FAIL / 0 ERROR
  被判 FAIL 的 160 例全部是同桶转换（VC-01/02/06/07/08/09），
  且每例被三条独立断言同时抓到：PRIMARY(数据对照) + META(列类型) + ALTER_OUTCOME(声明vs实际)
  93 个跨桶转换用例（VC-03/04/05）保持 100% 全绿
```

这证明两件事：① 画像确实在驱动期望值；② 一旦实例真实行为与声明的画像不符，
**三条独立机制都会立刻报出来**，不会静默通过 —— 因此拿到内网实例后，
即使口径描述有偏差，第一轮跑就会把差异精确暴露出来（哪条转换、哪个算法、实际 errno 多少）。

```bash
python3 -m pytest selfcheck/test_runner.py -q     # 85 passed（新增 5 项画像守卫）
python3 generate_test_sql.py --charvarchar-mode same_only   # 可整体切换口径，不改代码
```

---

## Step 9 — P1-3 DDL 语句形态 + 秒级差分计时 + P1-4 索引完整性（含 P1-2）

**问题**
- 19,021 条 ALTER **全部**显式写 `ALGORITHM=`，`LOCK=` 出现 **0 次**、`CHANGE` 出现 **0 次**
  → "在线（不阻塞 DML）"与"秒级（用户不写 ALGORITHM 时自动走 INSTANT）"两个 PRD 核心卖点没有任何直接证据
- ALTER 之后索引/约束完全没有复验：`CHECKSUM TABLE` / `FORCE INDEX` 一致性 / 唯一约束复验 均为 0
- 472 个空表（`data_scale=S0`）用例：post 插入被跳过、t1/t2 都空 → 恒 PASS，ALTER 意外失败也无感

**新增 6 个专项文件**（文件号全局唯一，30/32/34 阿里云，31/33/35 内网）

| 文件 | 内容 | 用例数 |
|---|---|---|
| `30_ddl_forms` / `31_..._enhanced` | 4 种语句形态 × 每条转换 | 128 / 108 |
| `32_ddl_timing` / `33_..._enhanced` | 秒级差分计时（2^19 行） | 8 / 8 |
| `34_index_integrity` / `35_..._enhanced` | 索引与约束完整性 × 2 种索引 | 64 / 54 |

1. **DEFAULT**：不写 `ALGORITHM`（用户真实写法）→ 必须成功，且元数据与对照表一致
2. **LOCKNONE**：`ALGORITHM=INPLACE, LOCK=NONE` → 这是"在线不阻塞 DML"的**硬证明**；
   INPLACE 不被支持时必须以声明的 errno 失败，而不是悄悄降级
3. **CHANGE**：`CHANGE target target2 <新类型>`（改名 + 改类型）→ 额外断言 `#OLD_COL_GONE`（旧列名必须消失）
4. **COPY**：`ALGORITHM=COPY` 对照组 → 数据与元数据必须与秒级路径完全一致
5. **秒级差分计时**：同一转换、同样 524,288 行，比较"默认算法"与"强制 COPY"耗时，
   断言 `默认 × 3 < COPY` **且** `默认 < 2 秒`（双条件：只用比值不够，两边都慢也能过；只用绝对值受机器影响）
6. **索引完整性**（6 条断言）：`IDX_PRESENT`（索引仍在且列/序号正确）、
   `IDX_CONSISTENT`（`FORCE INDEX` 与 `IGNORE INDEX` 行数一致 = 索引与表物理一致）、
   `IDX_SCAN_HASH`（索引扫描 vs 全表扫描的有序 CRC 哈希一致）、
   `CRC_ORACLE`（与"用新类型全新建的对照表"逐行哈希一致）、
   `UNIQ_ENFORCED`（唯一索引仍拒绝重复值，负向探针 errno 1062）、`META`

P1-2 由 Step 7 的 META 断言覆盖：空表用例现在也断言列类型/可空性/默认值/字符集/列序，
ALTER 意外失败会被 META 判 FAIL（反向对照 NC2 已验证这条路径）。

**过程中自查出的 4 个缺陷（已修）**
1. `build_ddl_form_case` 结尾写成 `"\n".join(<字符串>)` → 把字符串**按字符炸开**，
   128 个用例生成 7.6MB 乱码。已在 `_emit` 里加"用例头数量必须等于语句块数量"强校验 +
   单用例体积哨兵，这类问题以后生成阶段就直接 `SystemExit`
2. 计时用 8,192 行时，DDL 固定开销（约 80ms：MDL + 数据字典事务 + binlog + redo fsync）
   淹没"改元数据 vs 重建表"的差异，实测比值只有 **1.3~1.5**，断言毫无分辨力（8/8 FAIL）。
   提到 2^19 行后比值升到 **20.5~37.9**
3. `unique_values_for` 用 `("v%d" % i).ljust(width,"_")[:width]`，在 `width=1`（CHAR(1)/VARCHAR(1)）时
   对任何 i 都得到 `'v'` → 唯一索引用例只插得进 1 行，**用例"通过"了但唯一约束/索引一致性/CRC 对照
   全部退化成单行比较**。改为定宽 base62 编码
4. 二进制类型的取值生成误用了 base62（`g~z` 不是合法十六进制字符，n>15 就生成 `X'...z'` 非法字面量）；
   索引专项也没认 `minimal_table`（多一个 pad 列 → errno 1118）
5. `VARCHAR(16381)` 建整列索引必然 errno 1071 → 改为**前缀索引** `target(64)`，
   既保住覆盖，又顺带验证"前缀索引在类型变更后是否被正确重建"

**验证**
```bash
python3 -m pytest selfcheck/test_runner.py -q      # 90 passed
python3 run_tests.py --env aliyun --files 30_ddl_forms.sql.gz 32_ddl_timing.sql 34_index_integrity.sql.gz --workers 6
#   -> 200/200 PASS
python3 run_tests.py --env aliyun --files 34_index_integrity.sql.gz 30_ddl_forms.sql.gz --workers 6
#   -> 192/192 PASS
```
秒级差分实测（RDS 8.0.36，524,288 行）：

| 转换 | 默认算法 | 强制 COPY | 比值 |
|---|---|---|---|
| TINYINT→SMALLINT | 82 ms | 3,080 ms | **37.5×** |
| SMALLINT→MEDIUMINT | 94 ms | 3,118 ms | 33.2× |
| MEDIUMINT→BIGINT | 95 ms | 3,173 ms | 33.5× |
| TINYINT U→INT U | 93 ms | 3,118 ms | 33.5× |
| SMALLINT U→BIGINT U | 87 ms | 3,293 ms | **37.9×** |
| CHAR(1)→CHAR(2) | 120 ms | 3,107 ms | 25.8× |
| VARCHAR(254)→(255) | 81 ms | 1,655 ms | 20.5× |
| VARCHAR(64)→(65) | 78 ms | 1,642 ms | 21.2× |

这是套件里第一次有"秒级"的**可自动判定**证据：若服务器悄悄退化成重建表，比值会掉下来并被断言抓住。

---

## Step 10 — P1-5 在线 DDL 失败模式与中断恢复

**问题**：纯 SQL 套件无法覆盖这类场景（需要多连接、并发、计时、KILL、权限降级），
旧套件里 `innodb_online_alter_log_max_size`、MDL 阻塞、`lock_wait_timeout`、`KILL`、
并发 DDL×DDL 全部 **0 覆盖**。

**新增** `scenarios/online_ddl_failure_modes.py`（7 个场景 / 44 项检查），
只建 `s_online_*` 前缀表、跑完自动清理、每个场景有硬超时、并发与行数都有上限。

| 场景 | 验证内容 | 结果 |
|---|---|---|
| **S1** MDL 阻塞与连接堆积 | 长事务持 MDL → ALTER 排队 → **后续简单查询也被堵住**（连接池打满的真实成因） | 7/7 ✓ |
| **S2** `lock_wait_timeout` 到期 | ALTER 干净失败、不无限等待、元数据未半改、校验和不变、表可用、无 `#sql-` 残留 | 6/6 ✓ |
| **S3a** KILL 等待 MDL 中的 DDL | 确定性（不靠时序竞速）：errno 1317、类型未半改、表可用 | 7/7 ✓ |
| **S3b** KILL **重建到一半**的 DDL | 4,194,304 行表在 `copy to tmp table` 阶段被杀：errno 1317、**行数不变**、校验和不变、类型未半改、无残留、之后仍能正常 DDL | 8/8 ✓ |
| **S4** 并发 DDL × DDL | 同表两条 ALTER 竞争，都有确定结果、最终列集合确定、原数据校验和不变 | 6/6 ✓ |
| **S5** DDL vs OPTIMIZE/ANALYZE | 并发都有确定结果、表可用、无残留 | 4/4 ✓ |
| **S6** `innodb_online_alter_log_max_size` 溢出 | 需要 SUPER；RDS 上 **明确 SKIP 并给出 errno 1227**（不假装通过），本机社区版实测 **errno 1799** 且表完整 | RDS SKIP / 本机 2/2 ✓ |
| **S7** 外键父子两侧并发 ALTER | 两侧都 3780、不出现"一侧改了一侧没改"、约束状态可查、父子表都可用 | 5/5 ✓ |

**关键实测证据**
```
S1 metadata_locks: [('SHARED_UPGRADABLE','GRANTED'), ('EXCLUSIVE','PENDING'), ('SHARED_READ','GRANTED')]
S1 processlist   : state='Waiting for table metadata lock'
S1 连接堆积       : ALTER 之后发起的 SELECT COUNT(*) 同样被堵 4.0s（复现）
S3b              : killed_at=('copy to tmp table', 0) -> errno 1317，行数 4,194,304 不变
S6(本机 8.0.45)   : errno 1799 "Creating index 'idx_c2' required more than
                   'innodb_online_alter_log_max_size' bytes of modification log"
S7               : parent/child 并发 COPY 均 errno 3780（与 Step 7 的外键矩阵一致）
```

**过程中自查出的 3 个脚本缺陷（已修）**
1. 跨线程共用同一条 pymysql 连接 → `Packet sequence number wrong` 协议错乱；改为每线程独立连接
2. `information_schema` 列名大小写不固定（`TABLE_NAME` / `table_name`）→ 统一转小写
3. `table_intact()` 的写入探针写死了 `c1/c2` 列名，在外键表(`cid/fk`)上误报"表不可用"；
   父表探针还会删掉被子表引用的行触发 errno 1451（这是外键**正确生效**，不是缺陷）
   → 探针改为可注入，父表写入/删除一个未被引用的键值
4. S3 原先靠"轮询到 time>=1 再 KILL"，200k 行的 COPY 只要 1.12s，KILL 追不上导致 3 项假失败
   → 拆成 S3a（MDL 等待中 KILL，确定性）+ S3b（放大到 400 万行 + 50ms 紧轮询）；
   若 DDL 仍抢先跑完，如实报 FAIL 并给出实测耗时，不假装通过

```bash
python3 scenarios/online_ddl_failure_modes.py --env aliyun --rows 200000      # 43 PASS / 0 FAIL / 1 SKIP
python3 scenarios/online_ddl_failure_modes.py --env local  --rows 2000000 --only S6   # 2 PASS（实测 1799）
```

---

## Step 11 — P1-6 binlog / 备库一致性 + DDL 中途崩溃恢复

**问题**：INSTANT 类型变更本质是元数据 + 行版本操作，最需要验证的两条路径 0 覆盖：
binlog 如何记录、备库重放后是否一致；DDL 执行到一半实例崩溃后表是否可用。
这是上线后最可能造成生产事故的路径（主备表定义漂移 → 复制中断或**静默数据错误**）。

**新增** `scenarios/replication_and_crash.py`

| 检查 | 内容 | 结果 |
|---|---|---|
| **R1** binlog 记录 | 5 条代表性 ALTER（INPLACE 整数加宽 / INPLACE VARCHAR 扩容 / `INPLACE,LOCK=NONE` 建索引 / 默认算法 / COPY）逐条比对 `SHOW MASTER STATUS` 前后位置 + `SHOW BINLOG EVENTS`。**双向断言**：成功的 DDL 必须进 binlog；失败的 DDL 必须**不**进 binlog（否则备库会重放一条主库没生效的变更 → 主备漂移） | RDS 7/7 ✓ |
| **R2** 备库重放一致性 | `SHOW REPLICA STATUS` 无错误且追上、主备 `SHOW CREATE TABLE` 逐字一致、逐列 `column_type` 一致、数据 CRC 一致 | 未配置备库时**明确 SKIP** 并给出配置方法（不假装通过） |
| **C1** 崩溃在 COPY 重建途中 | 2,097,152 行表，`copy to tmp table` 阶段 SIGKILL 整个实例 → 重启 | 14/14 ✓ |
| **C2** 崩溃在 INPLACE 建索引途中 | 同规模表，`preparing for alter table`（online DDL + row log 路径）SIGKILL → 重启 | 14/14 ✓ |

崩溃恢复的 14 项断言：实例能重启（InnoDB 恢复完成）、错误日志无 InnoDB 致命错误、
列定义完整无半改、**行数与校验和与崩溃前完全一致**、`CHECK TABLE` = OK、
无 `#sql-` 残留中间表、**崩溃的索引要么完整要么完全不存在（无半成品索引）**、
恢复后仍可正常 DDL、恢复后可正常读写。

**安全边界**：崩溃恢复在 `ThrowawayInstance` 上做 —— 临时 datadir + 自动分配端口 +
独立 socket + `--initialize-insecure`，**绝不触碰任何已在运行的实例**；
退出时 SIGTERM→SIGKILL 兜底并删除 datadir。

**实测证据**
```
R1: info='use `ddl_test`; ALTER TABLE s_repl_crash MODIFY c1 BIGINT, ALGORITHM=INPLACE /* xid=6209577 */'
    -> 5/5 条 DDL 均以 Query_event 落盘（备库可重放）；binlog_format=ROW, log_bin=1
C1: state='copy to tmp table' -> SIGKILL -> 重启后 rows 2097152 不变、checksum 3351347884 不变、
    c1 仍为 int（未半改）、CHECK TABLE OK、无 #sql- 残留、之后 DDL/读写正常
C2: state='preparing for alter table' -> SIGKILL -> 同上全部通过，idx_crash 列数=0（索引完全回滚）
```

```bash
python3 scenarios/replication_and_crash.py --env aliyun --only R1        # 7 PASS
python3 scenarios/replication_and_crash.py --only C1 --crash-rows 2000000 --crash-ddl copy_rebuild
python3 scenarios/replication_and_crash.py --only C1 --crash-rows 2000000 --crash-ddl inplace_add_index
python3 scenarios/replication_and_crash.py --env aliyun --only R2 --replica-config replica.ini
```

---

## Step 12 — P2 类型转换兼容矩阵（49 探针 × 4 算法 = 196 用例/环境）

**问题**：旧套件只覆盖"加宽且被支持"的转换，负向空间与整类类型族 **0 覆盖**：
DECIMAL 只测 M 增大 D 不变、无符号↔有符号互转、无缩窄转换、无跨族转换、
无 ENUM/SET、无 FLOAT/DOUBLE、无 DATE/TIME/DATETIME/TIMESTAMP(含 fsp)、无 YEAR、
无 JSON、无 GEOMETRY、无"改类型同时改 charset/collation"。

**方法论：兼容性矩阵不靠猜期望值，而是"测量 → 冻结基线 → 回归比对"**
1. `tools/conversion_matrix_<env>.json` 不存在时，用例声明 `alter=MEASURE`，
   执行器只**记录**实测结果（不判失败），并汇总写出 `results/conversion_matrix_<env>.json`
2. 人工复核后 `python3 tools/promote_conversion_matrix.py --env aliyun` 冻结成 golden
   （`alter=INCONSISTENT` 的条目会被拒绝并要求排查）
3. 之后每次生成都按 golden 写死期望，任何行为变化都被 `ALTER_OUTCOME` 判 FAIL

覆盖的 49 个探针（每个 × default/instant/inplace/copy 四种算法）：
DECIMAL 变标度 5 个（D 增大 / D 减小 / M 减小 / M,D 同变 / D 到最大）、
符号变化 4 个（含有负数、含无符号最大值溢出）、缩窄 10 个（含有数据溢出与不溢出两档）、
跨族 9 个（INT↔DECIMAL、VARCHAR↔TEXT、CHAR↔VARCHAR、INT↔VARCHAR，含非法数据）、
ENUM/SET 4 个（末尾追加 / 成员重排 / 删除成员 / SET 追加）、
时间类型 6 个（DATETIME fsp 升降、TIMESTAMP→DATETIME、DATE→DATETIME、TIME fsp、YEAR→SMALLINT）、
FLOAT/DOUBLE 3 个、JSON 3 个（含非法 JSON）、GEOMETRY 1 个、
charset/collation 变更 4 个（latin1→utf8mb4、utf8mb4→latin1、general_ci→bin、bin→0900_ai_ci）。

**实测结论（阿里云 RDS MySQL 8.0.36，已冻结为 golden）**

| 结论 | 证据 |
|---|---|
| **INSTANT/INPLACE 只支持 5/49 个探针**：ENUM 末尾追加、SET 末尾追加、FLOAT→FLOAT(M,D)、collation 变更（两个方向） | 其余 44 个探针 INSTANT 与 INPLACE 一律 **errno 1846** |
| **不写 ALGORITHM 时几乎全部成功**（44/49） | 说明"能改"不等于"秒级"——服务器静默回退到 COPY 重建，这正是 Step 9 计时专项量化的差异（20~38 倍） |
| **缩窄转换在数据不丢失时是成功的**（`BIGINT→INT`、`VARCHAR(255)→VARCHAR(10)`、`CHAR(255)→CHAR(254)`、`VARBINARY(40)→(20)`、`BIT(64)→BIT(32)`、`LONGTEXT→TEXT`、`LONGBLOB→BLOB`） | 审计报告里"必须不支持缩窄"的预设**是错的**；数据溢出时才失败：整数 1264、字符串 1265、`BINARY(20)→BINARY(10)` 因定长补零也 1265 |
| 有符号→无符号含负数 **1264**；无符号最大值→有符号 **1264** | 值域校验正确 |
| `VARCHAR→INT` 数据非数字 **1366**；`LONGTEXT→JSON` 非法 JSON **3140** | 语义校验正确 |
| DECIMAL 变标度：D 增大 / D 减小 / M,D 同变 / D 到最大 都只能走 default/COPY，INSTANT 与 INPLACE 均 1846 | 与"阿里云不支持 DECIMAL 改类型"一致 |

**过程中自查出的 3 个缺陷（已修）**
1. `build_meta_assertion_full` 的 `want[...]` 文本**未转义**就拼进 SQL 字符串字面量：
   ENUM/SET 的 `column_type` 本身含单引号（`enum('a','b')`）→ errno 1064，16 个用例恒 ERROR。
   普通类型没有引号，所以这个缺陷一直没暴露
2. 把带 `CHARACTER SET latin1` 的原始类型串直接喂给 `column_type_of` →
   期望值变成 `varchar(10) character set latin1`，与实测 `varchar(10)` 不符 → 66 个 META 假失败。
   新增 `strip_cs_clause()`
3. META 对**实例相关的隐式属性**写死期望：TIMESTAMP 实测为
   `nullable=NO / has_default=1 / extra='DEFAULT_GENERATED on update CURRENT_TIMESTAMP'`
   （取决于 `explicit_defaults_for_timestamp`）→ 环境相关的假失败。
   兼容矩阵改用 `check="type"` 只断言列类型（属性保持由主套件的 META 负责，那里列定义完全显式）

**验证**
```bash
python3 run_tests.py --env aliyun --files 40_conversion_matrix.sql --workers 6   # MEASURE 轮：196 条实测
python3 tools/promote_conversion_matrix.py --env aliyun                          # 冻结 golden（196 条，0 条不一致）
python3 generate_test_sql.py && python3 run_tests.py --env aliyun --files 40_conversion_matrix.sql --workers 6
#   -> 196/196 PASS（ALTER_OUTCOME 196 + PRIMARY 196 + META 196）
```
内网侧 `41_conversion_matrix_enhanced.sql` 同一套探针、golden 尚未冻结，
拿到内网实例后第一轮以 MEASURE 模式跑，复核后 promote 即可。

---

## Step 13 — P2 因子矩阵 + 需要特权的会话变量专项

**问题**：旧套件因子维度只有 10 个，且其中 **`dependencies=FOREIGN_KEY` 在
`_build_create_table` 里根本没有对应实现**（既不建外键也不加索引）—— 因子声明了但没生效，
是空壳覆盖。FULLTEXT / SPATIAL / 函数索引 / 降序索引 / 不可见索引 / 触发器 / 视图 /
STORED 生成列 / GIPK / `sql_require_primary_key` / COMPRESSED / 页压缩 / 加密表 /
非 InnoDB 引擎 / `PAD_CHAR_TO_FULL_LENGTH` 等全部 0 覆盖。

**新增** `42_factor_matrix.sql`（阿里云）/ `43_factor_matrix_enhanced.sql`（内网）：
22 个因子 × 3 条代表转换 × 3 种算法（instant / inplace / default）= **198 用例/环境**，
沿用 Step 12 的"测量 → 冻结 golden → 回归比对"机制（`tools/factor_matrix_aliyun.json`，198 条）。

**实测结论（阿里云 RDS MySQL 8.0.36，已冻结）**

| 因子 | INSTANT | INPLACE | default | 说明 |
|---|---|---|---|---|
| 函数索引 `((CONCAT(target,'')))` | ✓ | ✓ | ✓ | 表达式索引不挡秒级 |
| STORED 生成列引用目标列 + 其索引 | ✓ | ✓ | ✓ | |
| VIRTUAL 生成列 + 生成列索引 | ✓ | ✓ | ✓ | |
| 降序索引 / 不可见索引（在目标列上） | **✗ 1845** | ✓ | ✓ | 目标列上有索引即挡 INSTANT |
| 表上有 FULLTEXT（非目标列） | ✗ | **INT/CHAR ✗ 1846、VARCHAR ✓** | ✓ | 1846 原因："InnoDB presently supports one FULLTEXT index…" |
| 表上有 SPATIAL（非目标列） | ✓ | ✓ | ✓ | |
| BEFORE INSERT 触发器引用目标列 | ✓ | ✓ | ✓ | |
| 依赖目标列的视图 | ✓ | ✓ | ✓ | |
| `ROW_FORMAT=COMPRESSED` | **✗ 1845** | ✓ | ✓ | 与 PRD 的排除项一致 |
| `COMPRESSION='zlib'` 页压缩 | ✓ | ✓ | ✓ | 页压缩不影响 |
| 显式表空间 / `STATS_PERSISTENT` | ✓ | ✓ | ✓ | |
| `sql_mode` = PAD_CHAR_TO_FULL_LENGTH / TRADITIONAL / ANSI / NO_ZERO_DATE | ✓ | ✓ | ✓ | 4 档全部不改变可行性 |
| 10,000 行中等规模 / 200 列宽表 | ✓ | ✓ | ✓ | |
| `ENGINE=MyISAM` / `ENGINE=MEMORY` | **建表即失败 3161** | 同 | 同 | RDS 禁用了这两个引擎 |
| `ENCRYPTION='Y'` | **建表即失败 3185** | 同 | 同 | 无 keyring（`Can't find master key`） |

**新增** `scenarios/session_variables.py`：`sql_generate_invisible_primary_key` /
`sql_require_primary_key` / `innodb_strict_mode` 这三个会话变量在 RDS 上 `SET SESSION`
直接 **errno 1227**（需 SUPER / SYSTEM_VARIABLES_ADMIN / SESSION_VARIABLES_ADMIN）。
放在纯 SQL 套件里 SET 失败后用例照样往下跑 —— **因子根本没生效却报告"通过"**，
是典型的假覆盖。移到场景模块后先探权限：RDS 明确 **SKIP 3 项**，本机社区版真实执行 **14/14 PASS**：
- GIPK 开启后无主键表自动生成 `my_row_id`（`auto_increment INVISIBLE`）并建 PRIMARY KEY；
  改列类型的结果用**差分断言**（有 GIPK vs 无 GIPK 必须一致），避免把 RDS 增强特性当成通用期望
- `sql_require_primary_key=ON` 时无主键建表被拒 **3750**，有主键正常，改列类型不受影响
- `innodb_strict_mode=ON` + COMPACT + 内联约 40,800 字节 → **1118 "Row size too large (> 8126)"**；
  `OFF` 时同一张表**建成功**（降级为告警）
- **对照实测纠正**：server 级 65535 行宽上限在 `innodb_strict_mode` ON/OFF **两种模式下都报 1118**
  —— 即 `innodb_strict_mode` 管的是 InnoDB 半页(8126B)限制，**不能**绕过 server 级行宽上限

**过程中自查出的缺陷（已修）**
1. 生成器 5 处 spec 写错：函数索引误用 `CAST(... AS ... ARRAY)`（JSON multi-valued 语法，
   非 JSON 列实测 3141）；生成列引用自增列（实测 **3109**）；SPATIAL 列 NOT NULL 无默认值
   （INSERT 实测 **1364**）
2. MEASURE 模式下用"猜的期望"断言列类型 → 166 个假失败；改为占位 PASS 并注明原因，
   golden 冻结后才做真断言
3. `USABLE` 断言直接 `SELECT FROM t1`，建表失败时反而让用例记 ERROR → 去掉，
   由 `BUILD_CHECK` 承担
4. golden 里 `build=FAIL` 的因子（引擎禁用/无 keyring）原先仍发 ALTER，结果 ALTER 以
   1146"表不存在"失败，**看起来像"类型变更被拒"，实际什么都没测** → 改为只断言表没被建出来
5. **我把 `RE_FACTOR`（解析 `-- Factors:`）覆盖成了匹配 `Factor probe:`**，
   导致所有用例的 factors 元数据丢失 —— 被 pytest 的 `test_split_cases_meta_and_statements`
   当场抓住，已改名为 `RE_FACTOR_PROBE`

**验证**
```bash
python3 run_tests.py --env aliyun --files 42_factor_matrix.sql.gz --workers 6   # MEASURE: 198/198
python3 tools/promote_conversion_matrix.py --env aliyun --kind factor           # 冻结 198 条 golden
python3 generate_test_sql.py && python3 run_tests.py --env aliyun --files 42_factor_matrix.sql --workers 6
#   -> 198/198 PASS
python3 scenarios/session_variables.py --env local      # 14 PASS / 0 FAIL
python3 scenarios/session_variables.py --env aliyun     # 3 SKIP（errno 1227，如实报告）
python3 -m pytest selfcheck/test_runner.py -q           # 90 passed
```

---

## Step 14 — P2 concurrent_dml 四项修复 + 凭据外置

| # | 问题 | 修复 | 实测结果 |
|---|---|---|---|
| 1 | DDL Fuzz 1000 轮**不校验 `exec_sql` 返回值**，只判内存增长 → 1000 轮 ALTER 全失败也会给 `NO_LEAK` | 每条 DDL 都校验，统计 `ddl_ok/ddl_fail/errnos/成功率`，失败即 `verdict=DDL_FAILURES`；异常轮次记 `EXCEPTIONS` | **4000 条 DDL 全部成功、成功率 100%、内存增长 0%**（现在这个数字是被校验过的） |
| 2 | 连续 INSTANT 只做 **ADD COLUMN**、轮次 `[10,30,50]`，恰好停在边界之前；且完全没有"同一列反复 INSTANT 改类型" | 轮次扩到 `[10,30,50,63,64,65,70]` 并给出 `boundary_verdict`；新增 `run_repeated_instant_modify_test()` | **第 65 轮被拒：errno 4092**（见下）；同一列反复 MODIFY **70/70 轮全成功**、行数不变、单轮 p50=45.7ms/p95=48.1ms/max=50.0ms |
| 3 | 无 per-DML 延迟分位，只有秒级 QPS，看不到 DDL 窗口期的延迟尖刺 | `dml_framework.DualWriteOracle` 与 `run_large_table_test_single` 两条路径都加 per-worker 延迟采样（超上限抽样、内存有界），输出各相位 p50/p95/p99/max + 尖刺倍数 | 实测 pre/during/post 三相位分位齐全，`p99_spike_ratio` / `p50_spike_ratio` 可判定 |
| 4 | `LARGE_TABLE_TYPES` 声明 1,000,000 行，归档证据却是 `--quick` 的 100,000 行，而报告写"5000 万行" | 新增 `--rows-scale`；每条结果写入 `declared_rows` / `row_count` / `run_mode`；实际低于声明即 WARN 并列出条目；`--quick` 打印明确告警"不可用于宣称任何大表规模结论" | 规模口径与证据强绑定，报告无法再引用与实际不符的数字 |

**头条发现：InnoDB instant 行版本上限 = 64，第 65 次被拒**
```
add_10_cols   completed=10  ALL_INSTANT_OK
add_30_cols   completed=30  ALL_INSTANT_OK
add_50_cols   completed=50  ALL_INSTANT_OK
add_63_cols   completed=63  ALL_INSTANT_OK
add_64_cols   completed=64  ALL_INSTANT_OK
add_65_cols   completed=64  INSTANT_REJECTED_AT_65
add_70_cols   completed=64  INSTANT_REJECTED_AT_65

errno 4092: Maximum row versions reached for table ddl_test/t_perf.
            No more columns can be added or dropped instantly. Please use COPY/INPLACE.
```
旧测试只跑到 50 轮，**正好停在边界之前**，因此这个运维上很关键的限制从未被发现：
一张表累积 64 次 instant 加/删列之后，后续 instant 变更会被拒绝，必须走 COPY/INPLACE（即"秒级"能力失效）。

同时测出一个重要区分：**同一列反复 INSTANT MODIFY 类型 70 轮全部成功**，
说明 4092 的行版本上限只约束 ADD/DROP COLUMN，不约束本套件核心的 MODIFY 类型变更。

**凭据外置（P3-4 的一部分）**
`concurrent_dml/run_concurrent_tests.py` 里硬编码了真实 RDS 地址与 root 口令，且该文件**已入库**。
改为 `_load_db_config()`：环境变量 > `config.ini` 的 `[env]` 段 > 占位符默认值，源码不留任何凭据。

> ⚠️ **安全提示**：真实 root 口令已存在于 git 历史的 2 个提交中
> （`cdf1c3a879` 初始提交、`d419023ee3`）。清理工作区**不能**清除历史，
> 必须**轮换该口令**；若仓库曾外发，还需用 `git filter-repo` 重写历史。
> 真实 endpoint 仍出现在 4 份文档里，Step 15 统一替换为占位符。

---

## Step 15 — P3 工程与文档口径统一

**改动**
1. **明文凭据清理**：4 份文档里的真实 RDS endpoint 全部替换为 `<RDS_ENDPOINT>` 占位符
   （`README.md` / `aliyun_test_results.md` / `test_coverage_report.md` /
   `concurrent_dml/test_summary_report.md`）；`FIX_LOG.md` 里的口令字面量也已脱敏。
   `config.ini` 保持 .gitignore 排除；执行器与场景模块都支持 `MYSQL_PWD` /
   `MYSQL_DEFAULTS_EXTRA_FILE`，密码不再出现在命令行与 `ps` 里。
2. **10 份历史文档加过期横幅**，逐份列出**具体的**过期点（不是笼统的"已过期"），
   并指向 `FIX_LOG.md` 作为唯一权威来源。例如：
   - `upper_limit_coverage_report.md`：VC-08/VC-09/VBIN-03 的 "✅SUCCESS" 结论错误（实测 1118）；
     §3.1/§3.2 声称插入的超上限值实际被注释；§6.1 声称的 emoji×4095/你好×5460 数据在生成器里不存在
   - `aliyun_test_results.md`：8094 用例中 1600 ERROR 是生成器缺陷而非"预期行为"、640 MANUAL 是空断言；
     `09_auto_increment_pk` 的 40/40 里有 20 个实际失败；58.9M 行只是 1 次手工验证
   - `test_coverage_report.md`：64 种分区组合实为 8 种 × 8 份重复、SUBPARTITION 为 0；
     `dependencies=FOREIGN_KEY` 因子无实现
3. **README.md 全量重写**为权威入口：当前规模、目录结构、文件编号与作用域约定、
   运行方法（含 golden 矩阵的测量→冻结→回归流程）、7 类断言的含义、环境能力画像、
   16 条主要实测结论、安全边界
4. **删除 `.bak`**：`generate_test_sql.py.bak`、`concurrent_dml/dml_framework.py.bak`
   （与正式版并存容易改错文件）
5. 生成器新增 `_prune_stale_sql()`：文件改名/减量后清理旧产物，杜绝执行器跑到过期文件

> ⚠️ **仍需人工处理的安全项**：真实 root 口令存在于 git 历史的 2 个提交
> （`cdf1c3a879` 初始提交、`d419023ee3`）。清理工作区**不能**清除历史 ——
> **请轮换该口令**；若仓库曾外发，还需 `git filter-repo` 重写历史。

---

## 最终验证（全部在阿里云 RDS MySQL 8.0.36 上实跑）

```bash
python3 -m pytest selfcheck/test_runner.py -q        # 90 passed
python3 selfcheck/negative_control.py --env aliyun   # 6/6 类注入缺陷全部被捕获
python3 run_tests.py --env aliyun --workers 8        # 5822/5822 PASS，12.6 分钟
python3 scenarios/online_ddl_failure_modes.py --env aliyun --rows 200000   # 43 PASS / 0 FAIL / 1 SKIP
python3 scenarios/replication_and_crash.py --env aliyun --only R1          # 7 PASS
python3 scenarios/replication_and_crash.py --only C1 --crash-ddl copy_rebuild       # 14 PASS
python3 scenarios/replication_and_crash.py --only C1 --crash-ddl inplace_add_index  # 14 PASS
python3 scenarios/session_variables.py --env local   # 14 PASS（RDS 上 3 SKIP，errno 1227）
```

**最终套件规模**

| 项 | 值 |
|---|---|
| SQL 文件 | 37（阿里云 17 / 内网 20） |
| 用例总数 | **10,731**（阿里云 5,822 / 内网 4,909），用例 ID 全局唯一、重复 0 |
| 阿里云全量结果 | **5,822 / 5,822 PASS**，0 FAIL / 0 ERROR / 0 MANUAL / 0 UNKNOWN / 0 MISSING |
| 断言总数 | **21,514 条**（SQL 12,949 + 执行器合成 8,565），平均 **3.70 条/用例**，**21 种**断言 |
| 证据归档 | `results/archive/summary_aliyun_20260923_183455.csv`（3.2 MB，带时间戳不可覆盖） |

**断言分布（全部 PASS）**

| 断言 | 条数 | 验证内容 |
|---|---|---|
| `ALTER_OUTCOME` | 5,373 | 声明 vs 实际的 ALTER 结果 + errno |
| `META` / `META_TYPE` | 5,347 | 列类型等 7 项元数据 |
| `PRIMARY` | 5,130 | 与 Oracle 对照表逐行 NULL-safe 比对 |
| `NEG_ERRNO#n` | 3,192 | 每条负向探针按语句 sha1 对账 errno |
| `NEG_REJECTED` | 1,458 | 超上限值不落库 / 两表对称 |
| `BUILD_REJECTED` / `BUILD_CHECK` | 620 | 建表应被拒的负向用例 |
| `IDX_PRESENT` / `IDX_CONSISTENT` / `IDX_SCAN_HASH` / `CRC_ORACLE` | 256 | 索引与约束完整性 |
| `OLD_COL_GONE` / `FK_CONSTRAINT_PRESENT` / `FAST_PATH` / `META_CHILD_*` / `META_PARENT_FK` 等 | 134 | CHANGE 改名、外键恢复、秒级差分等 |

**ALTER 声明与实际逐条对齐（5,373 条，无一条不符）**

| 声明 | 实际 | errno | 条数 |
|---|---|---|---|
| SUCCESS | SUCCESS | — | 4,053 |
| FAIL | FAIL | 1846 | 1,148 |
| FAIL | FAIL | 1845 | 148 |
| FAIL | FAIL | 3780 | 8 |
| FAIL | FAIL | 1264 / 1265 / 1366 / 3140 | 16 |
| N/A（建表即被拒，无 ALTER） | — | — | 449 |
