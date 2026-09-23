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
| 8 | 环境能力画像 + 内网 CHAR/VARCHAR 口径 | ⏳ 进行中 | — |
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
