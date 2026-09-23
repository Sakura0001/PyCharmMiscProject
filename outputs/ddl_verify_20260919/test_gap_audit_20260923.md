# 测试遗漏点审计报告 | Test Gap Audit

> 审计时间: 2026-09-23
> 审计对象: `outputs/ddl_verify_20260919/`（纯 SQL 套件 + concurrent_dml 套件 + 全部报告文档）
> 审计基线: 分支 `codex/ddl-verify-20260919` @ `1660d3778e`
> 审计方式: 静态读取生成器/执行器源码 + 反查已生成 SQL（含 .gz）+ 交叉核对 `results/summary_aliyun.csv`、`results/failures.log`、`concurrent_dml/results/*`

---

## 0. 一句话结论

**当前"8094 用例 / 0 FAIL / 100% 通过"这个结论不成立。** 三个原因：

1. 现在仓库里的 SQL 是 18,993 个用例（9/22 重新生成），而结果 CSV 是 9/20 跑的 8,094 个 —— 报告与产物已脱节；
2. 执行器 `run_tests.py` 只匹配 `*.sql`，而 8 个大文件（含全部 VARCHAR / TEXT / VARBINARY / 分区）只以 `.sql.gz` 存在且明文版被 .gitignore 排除 —— **16,097 个用例（84.8%）现在根本跑不到，且不报错不告警**；
3. 已跑的部分里，1,600 个分区用例因生成器缺陷恒无输出、640 个分区用例是无条件通过的空断言，而"预期值 vs 实际值"的比对从未在执行器里实现。

---

## 1. 现状盘点（实测数据）

| 项 | 实测值 | 出处 |
|----|--------|------|
| 生成用例总数（当前 SQL） | **18,993** | 逐文件统计 `-- Test Case:` |
| 其中 `.sql.gz` 内（执行器跑不到） | **16,097（84.8%）** | 8 个 gz 文件 |
| 执行器实际能跑 | **2,896** | `run_tests.py` 只 glob `*.sql` |
| 已归档执行结果 | 8,094 行（9/20） | `results/summary_aliyun.csv` |
| └ PASS | 5,854 | |
| └ ERROR / NO_OUTPUT | 1,600（全部 `TC-PA*`） | 生成器缺陷，见 P0-2 |
| └ MANUAL / 空断言 | 640（全部 `TC-PA*`） | 见 P0-3 |
| 内网（增强类型）纯 SQL 执行结果 | **无**（`results/` 下无 summary_internal.csv） | 29 条转换、~2,000 用例从未跑过 |
| 并发 DML 大表矩阵 | 68 条 × **100,000 行**（声明 1,000,000） | `large_table_summary.csv` row_count 分布 |
| 5000 万行级 | **仅 1 次手工 INT INPLACE**（58,916,864 行 / 310.7s） | `aliyun_test_results.md` |
| ALTER 语句总数 | 19,021 | |
| └ 显式 `ALGORITHM=` | 19,021（100%） | 无"默认算法"用例 |
| └ 带 `LOCK=` | **0** | 纯 SQL 套件无在线性证据 |
| └ 使用 `CHANGE`（改名+改类型） | **0** | |
| 元数据断言总数 | 238 | column_comment 118 / auto_increment 40 / unsigned 20 / collation 30 / charset 30 |
| └ 断言 ALTER 后的**列类型** | **0** | 无 column_type / data_type / is_nullable / column_default |
| `SHOW CREATE TABLE` / `CHECKSUM TABLE` / `CHECK TABLE` / `FORCE INDEX` | **0 / 0 / 0 / 0** | |
| 被注释掉的"超上限负向 INSERT" | **2,623 条** | 报告声称已插入，实际未执行 |
| 分区 `SUBPARTITION` 出现次数 | **0** | "64 种分区组合"名不副实 |
| 分区文件 test_id 重复率 | 8,192 用例 / 4,096 唯一 ID（每个 ID 2 次） | instant 与 inplace 共用 ID |
| 全量跑完残留表数 | **~37,986 张**（18,993 × 2，无收尾清理） | 每用例只在开头 DROP |

---

## 2. P0 —— 阻断性问题（"已覆盖"实际没跑 / 没验证）

### P0-1 执行器静默跳过 `.sql.gz`，84.8% 用例无法执行

`run_tests.py:206` 只收集 `.sql`：

```python
sql_files = sorted([os.path.join(sql_dir, f) for f in os.listdir(sql_dir) if f.endswith('.sql')])
```

而 `.gitignore` 把 8 个文件的明文版排除了（07/08/12/17/18/21/22/29），仓库里只剩 `.gz`。后果：

- 阿里云侧跑 9 个文件而非 12 个 —— **全部 VARCHAR 用例（含新增 VC-08/VC-09 上限用例）和全部 8,192 个分区用例被跳过**；
- 内网侧跑 10 个文件而非 15 个 —— VARBINARY、TEXT、增强分区全被跳过；
- 没有任何 WARNING，汇总表看起来"正常"，只是数字变小。

**修复**：runner 同时匹配 `.sql`/`.sql.gz`（gz 走 `gzip.open` 或 `gzip -dc | mysql`）；启动前打印 manifest（文件名 + 用例数 + 内容哈希），与生成器产出的 manifest 对账，缺文件即 fail-fast。

### P0-2 分区"目标列是分区键"分支的对照 SQL 引用不存在的列 → 3,328 + 1,216 用例恒无结果

`generate_test_sql.py:1136-1156`：t1 建成 `(id, target, pad)`，t2 却用 `_build_create_table()` 建成 `(id, pad1, target, pad2)`，然后 `_build_compare_sql(test_id, t1, t2, ["id","target","pad"])` 生成 `a.pad <=> b.pad` → `ERROR 1054 Unknown column 'b.pad'`。

证据（`results/failures.log` 里唯一留存的 stderr 尾巴）：

```
ERROR 1846 (0A000) at line 366113: ALGORITHM=INPLACE is not supported. Reason: Cannot change column type INPLACE. Try ALGORITHM=COPY.
ERROR 1054 (42S22) at line 366123: Unknown column 'b.pad' in 'where clause'
```

- 当前 SQL 中该缺陷影响：`12_partition_64.sql.gz` **3,328 / 8,192**，`29_partition_64_enhanced.sql.gz` **1,216 / 6,912**；
- README 把这 1,600 个 ERROR 归因为"分区策略不支持该类型作为分区键，建表失败" —— **归因错误**，真实原因是生成器缺陷；
- 顺带：这里 ALTER 预期失败（1846），但从未被断言，失败原因是否与预期一致完全未知。

**修复**：对照列改为 `["id","target"]`，或让 t2 用与 t1 完全相同的建表语句（仅类型不同）；并追加"ALTER 必须失败且 errno ∈ {1846,1845}"的断言。

### P0-3 640 个分区用例是"无条件通过"的空断言

`generate_test_sql.py:1120-1131`（`not can_partition` 分支，空断言 SELECT 在 1127 行）：

```sql
CREATE TABLE ... PARTITION BY <first_type>(target) PARTITIONS 2;   -- 预期建表失败
ALTER TABLE ... ;                                                  -- 预期也失败
SELECT '<id>' AS test_id, 'BUILD_OR_ALTER_FAIL_EXPECTED' AS result, 'CHECK_MANUALLY' AS note;
```

最后那条 SELECT 与前面语句的成败**完全无关**，永远输出一行常量；runner 把它归为 `MANUAL`，README 计入"预期行为"。也就是说：建表到底有没有失败、失败原因是不是"该类型不能作分区键"、ALTER 有没有被正确拒绝 —— 一个都没验证。

顺带风险：`PK_COMPAT` 把 `("KEY","text")`、`("KEY","blob")`、`("KEY","bit")`、`("KEY","decimal")`、`("LINEAR KEY", ...)` 全部标为 True，但 MySQL 对 BLOB/TEXT 作分区键有明确限制；内网侧这批组合从未实跑，一旦实跑很可能大面积 CREATE 失败 —— 需要实测校正 `PK_COMPAT`，而不是靠猜。

**修复**：把常量 SELECT 换成真实断言，例如
`SELECT '<id>', IF(EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='<t1>'),'FAIL','PASS')`，并在建表失败时用 `GET DIAGNOSTICS` 记录 errno 落到结果里。

### P0-4 分区 test_id 重复 → 结果无法归因，且掩盖了真实的未执行数量

`12_partition_64.sql.gz`：8,192 个用例只有 4,096 个唯一 ID（instant / inplace 共用同一个 ID，如两个 `TC-PA0001`）。连锁后果：

1. CSV 里同一个 test_id 出现多行，无法区分是哪个算法的结果；
2. `parse_metadata()` 用 dict 按 ID 存元数据，后者覆盖前者 —— 所有分区用例记录的 `algorithm` 都是 inplace；
3. `seen_test_ids` 是集合，**只要两次里有一次产出了结果，就不会记 NO_OUTPUT** —— 这正是"3,328 个坏用例只体现为 1,600 个 ERROR"的原因，实际未执行数被低估约一半；
4. 对外宣称的"8094 用例"不是唯一用例数，口径不可信。

**修复**：ID 里带算法后缀（`TC-PA0001-IT` / `-IP`）；`parse_metadata` 改为按出现顺序的列表；runner 用"预期 ID 全集 − 实际产出 ID 全集"做完整性校验，缺一个就报错。

### P0-5 "64 种分区组合"实际只有 8 种，SUBPARTITION 覆盖为 0

`_build_partition_def()`（`generate_test_sql.py:1029-1055`）里有一段自我否定的死代码，最终 `return first, True` —— 二级分区类型被完全丢弃。实测两个分区文件里 `SUBPARTITION` 出现 **0 次**；`PP-33 (HASH + RANGE)` 生成的是 `PARTITION BY HASH(id) PARTITIONS 4`，与 `PP-37..PP-40 (HASH + *)` 逐字相同。

后果：① 用例数被 8 倍虚增；② 组合分区（RANGE+HASH、LIST+KEY、SUBPARTITION BY …）这一整类场景 0 覆盖；③ README / 覆盖报告里"64 种分区组合"的表述不成立；④ `_build_partition_def` 恒返回 `build_should_succeed=True`，`PK_COMPAT` 只在另一个分支生效，门控逻辑不一致。

**修复**：真正实现 `PARTITION BY <first> SUBPARTITION BY <second> SUBPARTITIONS n`（注意 MySQL 只允许 RANGE/LIST 一级 + HASH/KEY 二级），把 64 组合裁剪成合法组合并显式列出非法组合的预期建表失败；不合法的组合不要生成 8 份重复用例。

### P0-6 2,623 条"超上限负向 INSERT"被注释掉，从未执行

`generate_test_sql.py:936-938`：

```python
for v in data.get("post_fail", []):
    lines.append(f"-- Insert value exceeding new type (expected FAIL on both tables)")
    lines.append(f"-- INSERT INTO {t1} (target) VALUES ({v});")   # ← 整条被注释
```

实测各文件被注释条数：07_varchar_instant 280、08_varchar_inplace 330、19_decimal_inplace 363、20_decimal_instant 308、02_integer_signed_inplace 198 …… 合计 **2,623**。

而 `upper_limit_coverage_report.md` §3.1/§3.2 明确写着"插入 256 字符(FAIL)""超上限值(预期FAIL): `REPEAT('q', 16384)`""`0x41 * 65530`"——**报告描述的验证没有发生**。这是本次新增上限覆盖里最关键的"新类型边界必须拒绝"证据。

**修复**：把负向值真正执行，并断言错误码一致。纯 SQL 下可用"探针表 + 结果表"模式：先 `INSERT` 到 t1 与 t2，再用 `SELECT` 比较两表行数与内容是否同步；或用存储过程 `DECLARE ... HANDLER` 捕获 errno 写入结果表，断言 t1 与 t2 的 errno 完全相同（strict / 非 strict 两档都要）。

### P0-7 "预期 vs 实际"从未比对，`expected` 字段解析出的是垃圾值

`run_tests.py` 解析了 `expected`，但状态判定只看 SQL 输出的 result 列，`expected` 仅被写进 CSV，**没有任何比对逻辑**。且解析规则互相打架，实测 CSV 里 `expected` 的取值分布为：

| expected | 行数 | 说明 |
|---|---|---|
| `SUCCESS` | 1,758 | 正常 |
| `CREATE` | 3,840+1,600 | 从 `-- Expected: CREATE OK, ALTER FAIL ...` 里错抓了 "CREATE" |
| `BUILD` | 640 | 从 `-- Expected: BUILD FAIL ...` 里错抓了 "BUILD" |
| `FAILS` | 80 | 从 `-- Expected: ALTER FAILS (table keeps old type)` 抓取，与 `FAIL` 不统一 |
| `FAIL` | 8 | |
| `''`（空） | 168 | 完全没解析到 |

所以"0 FAIL"的准确含义是：**在产出了结果行的用例中，没有发现 t1/t2 数据不一致** —— 不等于"所有 DDL 行为符合预期"。

**修复**：生成器输出机器可读的期望（如 `-- @expected alter=FAIL errno=1846`）；runner 解析成枚举并强制比对；actual ≠ expected 一律判 FAIL，而不是只在数据不一致时才判 FAIL。

---

## 3. P1 —— 验证深度不足（跑通了也没证明关键性质）

### P1-1 全套件没有一条断言"ALTER 之后列类型确实变成了新类型"

238 条元数据断言的分布：`column_comment` 118、`extra LIKE '%auto_increment%'` 40、`column_type LIKE '%unsigned%'` 20、`collation_name` 30、`character_set_name` 30。**`column_type` 精确值 / `data_type` / `numeric_precision` / `character_maximum_length` / `is_nullable` / `column_default` 的断言数 = 0。**

Oracle 对照表能间接发现"ALTER 完全没生效"（新范围值插不进去 → 行数不一致），但发现不了"类型对了、其它属性被改坏了"：NOT NULL 丢失、DEFAULT 丢失/被改写、charset/collation 被重置、COMMENT 丢失、AUTO_INCREMENT 丢失、列顺序变化、`ROW_FORMAT` 被隐式改掉。这些恰恰是 INSTANT 元数据改动最容易出的问题。

**修复**：每个用例 ALTER 后加一条元数据断言（一次性比对 column_type / is_nullable / column_default / character_set_name / collation_name / extra / ordinal_position），再加一次 `SHOW CREATE TABLE` 快照对比 —— 除目标列类型外，其余部分必须逐字不变。

### P1-2 472 个空表（`data_scale=S0`）用例对"ALTER 意外失败"完全无感

`_build_test_case_sql` 里 `if data_scale != "S0"` 跳过全部 post 插入，且 `all_vals = []` → t1、t2 都是空表 → 对照恒 PASS。这 472 个用例目前只在验证"空表上 CREATE 成功"。

**修复**：空表用例必须依赖 P1-1 的元数据断言判定；或 ALTER 后至少补插 1 条新范围值。

### P1-3 纯 SQL 套件缺"在线性"与"默认算法"证据

19,021 条 ALTER 全部显式写 `ALGORITHM=`，`LOCK=` 出现 0 次。也就是说：

- **没有证明 INPLACE 不阻塞 DML**（`ALGORITHM=INPLACE` 仍可能拿 SHARED/EXCLUSIVE 锁）。`LOCK=NONE` 只在 `concurrent_dml/run_concurrent_tests.py:2017` 的大表路径用到；
- **没有证明"秒级"的用户真实路径**：用户不会写 `ALGORITHM=INSTANT`，只会写 `ALTER TABLE t MODIFY c BIGINT`，服务器是否自动选 INSTANT、耗时是否真的是秒级，无直接用例。

**修复**：每条转换至少补 4 个变体 —— ① 不带 ALGORITHM（断言耗时/元数据变更特征表明走了 INSTANT）；② `ALGORITHM=INPLACE, LOCK=NONE` 必须成功；③ `ALGORITHM=COPY` 作为结果对照组（三者最终数据与元数据必须完全一致）；④ `CHANGE old_name new_name <new_type>`（改名 + 改类型同时发生）。

### P1-4 ALTER 之后索引 / 约束 / 表完整性没有复验

`CHECKSUM TABLE`、`CHECK TABLE ... FOR UPGRADE`、`FORCE INDEX` 一致性对比、唯一约束复验（重复值必须仍然报错）、`EXPLAIN` 确认索引仍被选中 —— 全部为 0。INPLACE rebuild 后二级索引/唯一索引/前缀索引是否正确重建，是这类改动最容易翻车的地方，而 `dependencies=SECONDARY_INDEX/UNIQUE_INDEX/COMPOSITE_PREFIX` 的用例只比对了数据行。

**修复**：对有索引依赖的用例追加三条断言：索引扫描结果 == 全表扫描结果；插入重复值必须失败且 errno 一致；`CHECKSUM TABLE t1` == `CHECKSUM TABLE t2`。

### P1-5 在线 DDL 的典型失败模式 0 覆盖

以下场景在授权测试环境里都能构造，但套件里一处都没有：

| 场景 | 为什么重要 | 现状 |
|---|---|---|
| `innodb_online_alter_log_max_size` 溢出（DB_ONLINE_LOG_TOO_BIG） | 长 INPLACE rebuild + 高写入速率下的经典失败，直接决定"在线改列类型"能否在生产大表上用 | 0 处提及 |
| 长事务 / 长查询持有 MDL，DDL 排队并阻塞其后所有连接 | 生产事故最常见的形态：一条 ALTER 把连接池打满 | 未覆盖 |
| `lock_wait_timeout` / `innodb_lock_wait_timeout` 到期 | 决定 DDL 是失败退出还是无限等待 | 未覆盖 |
| DDL 执行中 `KILL QUERY` | 表能否继续使用、元数据是否干净回滚、临时文件是否清理 | 未覆盖 |
| 并发 DDL × DDL（同表两条 ALTER / FK 父子两侧同时 ALTER） | MDL 与字典事务竞态 | 未覆盖 |
| DDL 与备份 / `OPTIMIZE` / `TRUNCATE` / `ANALYZE` 并发 | 运维窗口叠加 | 未覆盖 |

### P1-6 复制与崩溃一致性 0 覆盖（自家文档列为"后续"，但这是最高风险项）

INSTANT 类型变更本质是元数据 + 行版本操作，最需要验证的是：binlog（ROW / STATEMENT 两种格式）如何记录、备库重放后列定义与行版本是否与主库一致、DDL 中途实例崩溃（可控 SIGKILL）后表是否可用且数据一致、降级到不支持该特性的版本会怎样。

这是"秒级修改列类型"上线后最可能造成生产事故的路径（主备表定义漂移 → 复制中断或静默数据错误），建议从"后续单独测试"提到 P1。

**修复**：加一条"主库跑全量套件 → 备库逐列比对 `SHOW CREATE TABLE` + `CHECKSUM TABLE` + `SHOW REPLICA STATUS` 无错误"的对照测试；崩溃恢复用受控 SIGKILL + 重启后 `CHECK TABLE`，全程限定在一次性容器 / 测试实例内。

---

## 4. P2 —— 功能覆盖面（类型 / 因子矩阵）遗漏

### 4.1 类型转换矩阵

| 缺口 | 说明 | 建议 |
|---|---|---|
| signed ↔ unsigned 互转 | `INT→INT UNSIGNED`、`INT UNSIGNED→BIGINT` 完全没有，连负向用例都没有 | 补正/负向各一组，负向断言 errno |
| 缩窄转换负向用例 | `BIGINT→INT`、`VARCHAR(255)→VARCHAR(10)`、`CHAR(255)→CHAR(254)`、`DECIMAL(12,2)→DECIMAL(10,2)`、`BIT(64)→BIT(32)`、`LONGTEXT→TEXT` | 必须显式覆盖"不支持缩窄"，否则实现悄悄支持了缩窄也发现不了 |
| 跨族转换负向用例 | `INT→DECIMAL`、`DECIMAL→BIGINT`、`VARCHAR→TEXT`、`TEXT→VARCHAR`、`CHAR→VARCHAR`、`VARCHAR→CHAR`、`INT→CHAR` | 同上 |
| **DECIMAL 标度 D 增大** | 现有 11 条 DECIMAL 转换全部 D 不变（10,2→12,2 / 64,30→65,30 / 8,2→9,2 …）。`DECIMAL(10,2)→DECIMAL(12,4)` 会压缩整数位容量，既有数据可能溢出 —— 高危路径 0 覆盖 | 补 D 增大 / D 减小 / M 与 D 同时变化三组，并灌入"整数位刚好占满"的数据 |
| 其它类型族 | FLOAT/DOUBLE、DATE/TIME/DATETIME/TIMESTAMP（含 fsp 0→3→6）、YEAR、**ENUM/SET 末尾加成员（MySQL 经典 INPLACE 场景）**、JSON、GEOMETRY、BOOLEAN | 至少各补一条"支持/不支持"的明确判定用例 |
| charset / collation 变更 | 只有 latin1 / utf8mb3 / utf8mb4 各一种固定搭配，**没有"改类型的同时改字符集或排序规则"**（`VARCHAR(10) latin1 → VARCHAR(20) utf8mb4`、`utf8mb4_general_ci → utf8mb4_0900_ai_ci`），也没有 PAD SPACE vs NO PAD 对尾空格比较语义的影响 | 这是数据正确性最容易出错的一类，建议单列一个文件 |
| ZEROFILL / 显示宽度 | 8.0 已弃用，可只做负向 | 低优先级 |

### 4.2 因子维度

| 因子 | 缺口 |
|---|---|
| row_format | 缺 COMPRESSED（PRD 排除项也应作为负向用例存在，目前只在 concurrent_dml 里）；缺 `COMPRESSION='zlib'/'lz4'` 页压缩；缺 `ENCRYPTION='Y'` |
| 索引 | 缺 FULLTEXT（会直接改变 INPLACE 可行性）、SPATIAL、函数/表达式索引、降序索引、INVISIBLE 索引 |
| 依赖对象 | 缺 trigger、view、stored routine 依赖目标列；generated column 只有 2 个 VIRTUAL 用例，缺 STORED、缺"在 generated column 上建索引" |
| 列属性 | 缺"目标列自身是 AUTO_INCREMENT 列"的类型扩展（09 文件测的是 id 主键的属性保持，不是 target）；缺 `ON UPDATE CURRENT_TIMESTAMP`；缺 SRID |
| 主键形态 | 缺 GIPK（`sql_generate_invisible_primary_key=ON`）；缺 **`sql_require_primary_key=ON` 下的 `NO_EXPLICIT_PK` 组合**（RDS 默认可能开启 → 直接建表失败，应显式覆盖而不是踩坑） |
| 引擎 / 表空间 | 缺 MyISAM / MEMORY 负向用例；缺显式表空间、共享表空间；缺 `innodb_strict_mode=OFF`（行宽超限从报错降级为警告，会改变预期） |
| sql_mode | 只有 `STRICT_TRANS_TABLES` 与 `''` 两档；缺 TRADITIONAL、NO_ZERO_DATE/NO_ZERO_IN_DATE、**PAD_CHAR_TO_FULL_LENGTH（直接影响 CHAR 语义与对照结果）**、ANSI |
| 数据规模 | 纯 SQL 套件只有 0 / 1 / 100 行，缺 1 万 / 10 万行的中规模档（大表在另一套里，且实测只跑到 100K） |

### 4.3 并发 DML 套件（自家 gap 分析的 P1~P3 仍未闭环）

| 项 | 状态 | 证据 |
|---|---|---|
| QPS 三阶段采集 | ✅ 已完成 | `large_table_detailed.json` 含 qps_summary；CSV 有 pre/during/drop_pct |
| DDL Fuzz 加 MODIFY COLUMN | ⚠️ 已加但**不校验返回值** | `run_concurrent_tests.py:616-617` 调用 `exec_sql` 后忽略 `(ok, err)`；只判内存增长 → 1000 轮 ALTER 全失败也会给出 `NO_LEAK` |
| 连续 INSTANT 次数上限 | ❌ 未覆盖边界 | `run_consecutive_instant_test` 只做 **ADD COLUMN**、轮次 `[10,30,50]`，**没有触及 InnoDB 64 个行版本 / instant 变更上限**（63/64/65），也没有"同一列反复 INSTANT 改类型 N 次" |
| 大表矩阵规模 | ❌ 与声明不符 | `LARGE_TABLE_TYPES` 声明 `1_000_000` 行，归档结果是 68 条 × **100,000** 行；新增 25 条（含全部上限类型）**无任何执行结果** |
| per-DML 延迟分位（p95/p99） | ❌ 未做 | 全仓 `percentile/p95/p99/latency` 命中 0 |
| 外键表并发 DDL+DML | ❌ 未做 | `foreign` 命中 0 |
| 分区表并发 DDL+DML | ❌ 未做 | `PARTITION` 命中 0 |
| 崩溃恢复 / 主备复制 | ❌ 未做 | `KILL` / `binlog` / `replica` 命中 0 |

---

## 5. P3 —— 工程与可复现性

1. **无收尾清理**：每个用例建 2 张表且只在用例开头 `DROP`，全量跑完在 `ddl_test` 里残留 ~37,986 张表，拖慢后续运行并可能触到实例表数量上限。建议每用例结尾 DROP，或文件末尾统一清理 + runner 提供 `--keep-tables`。
2. **无断点续跑 / 重试 / 并行**：一个文件 = 一个 mysql 进程串行灌，进程中断则其后全部记 NO_OUTPUT，且必须整文件重跑。建议按用例切分执行、失败重试（带上限）、可控并行度、单用例超时。
3. **无前置环境快照**：不记录 `SELECT VERSION()`、`innodb_strict_mode`、`sql_require_primary_key`、`sql_mode`、`innodb_online_alter_log_max_size`、字符集/时区、功能开关状态 → 结果无法与具体环境绑定复现。
4. **凭据处理**：`run_tests.py` 用 `--password=<明文>` 走命令行，在 `ps` 里可见，且 mysql 会往 stderr 打警告污染错误摘要。建议改 `--defaults-extra-file`（0600 临时文件）或 `MYSQL_PWD`。另外 `README.md` 里写了真实 RDS endpoint 并已入库，`config.ini` 里是真实 root 口令（已被 .gitignore 排除，未入库）—— 按 AGENTS.md 第 10 条，README 也应换成占位符。
5. **错误现场丢失**：stderr 只在 `file_error > 0` 时保留最后 2000 字符，1,600 个 ERROR 的真实原因只剩尾巴（幸好尾巴里就暴露了 `b.pad` 缺陷）。建议全量落盘并按用例归因。
6. **证据未版本化 / 已过期**：`results/` 在 .gitignore 里但 `summary_aliyun.csv` 已入库（历史遗留）；CSV 是 9/20 的、SQL 是 9/22 重新生成的，**文档里的 8,094 / 16,114 与当前 18,993 不一致，所有报告的结论已过期**。建议报告里带 SQL 生成时间戳 + 内容哈希，runner 输出 manifest 供对账。
7. **文档内部互相矛盾**：`large_table_test_report.md` §10 把"连续 10/30/50 次 INSTANT""DDL Fuzz 内存泄漏""表列数上限"列为未覆盖，而 `internal_execution_guide.md` §8 说这些在 Phase 1 已执行（`results/run_enhanced.log` 里确有记录）；`aliyun_test_results.md` 说 58.9M 行、`large_table_test_report.md` 说当前 100K 行。口径需要统一。
8. **`.bak` 与正式版并存**：`generate_test_sql.py.bak`、`dml_framework.py.bak` 容易改错文件，建议删除或移出仓库目录。
9. **文件编号断档**：`sql_internal` 从 15 开始，缺 13/14；README 的目录说明与实际文件不完全一致。

---

## 6. 建议修复顺序

| 顺序 | 动作 | 价值 | 工作量 |
|---|---|---|---|
| 1 | P0-1 runner 支持 `.sql.gz` + manifest 对账 | 让 84.8% 的用例重新可执行 | 小（~60 行） |
| 2 | P0-4 分区 test_id 加算法后缀 + runner 完整性校验 | 结果可归因，未执行数不再被掩盖 | 小（~40 行） |
| 3 | P0-2 / P0-3 修分区两个分支的对照与断言 | 让 4,544 + 640 个分区用例真正产出判定 | 中（~150 行） |
| 4 | P0-7 + P1-1 期望值机读化 + 每用例补元数据断言 | "0 FAIL" 才真正等于"符合预期" | 中（~200 行） |
| 5 | P0-6 负向超上限 INSERT 真正执行 + errno 断言 | 补齐报告已宣称的边界拒绝证据 | 中（~120 行） |
| 6 | P0-5 分区组合去重 + 真 SUBPARTITION | 消除 8 倍虚增，补上组合分区 | 中（~150 行） |
| 7 | P1-3 / P1-4 补 LOCK=NONE、默认算法、CHANGE、索引与 CHECKSUM 复验 | 证明"在线"与"改后表仍健康" | 中 |
| 8 | P1-5 / P1-6 在线 DDL 失败模式 + 主备/崩溃一致性 | 覆盖最高生产风险 | 大 |
| 9 | P2 类型与因子矩阵补全（DECIMAL 变标度、缩窄/跨族负向、charset 变更、ENUM/SET、时间类型、FULLTEXT、PAD_CHAR_TO_FULL_LENGTH…） | 功能覆盖面 | 大 |
| 10 | P3 清理 / 续跑 / 环境快照 / 凭据 / 文档口径 | 可持续运行与可复现 | 中 |

修完 1~6 之后必须**重新全量跑一遍**（阿里云 + 内网），再更新 README 与各覆盖报告；在此之前，现有报告里的通过率数字不应对外引用。

---

## 7. 快速自查命令

```bash
cd outputs/ddl_verify_20260919

# 1) 执行器实际会跑哪些文件（对照 gz 列表即可看到被跳过的）
python3 -c "import os;[print(d, sorted(f for f in os.listdir(d) if f.endswith('.sql'))) for d in ('sql_aliyun','sql_internal')]"

# 2) 当前用例总数 vs 报告里的 8094
python3 - <<'EOF'
import os,gzip
t=0
for d in ('sql_aliyun','sql_internal'):
    for f in sorted(os.listdir(d)):
        p=os.path.join(d,f)
        op=gzip.open if f.endswith('.gz') else open
        if not (f.endswith('.sql') or f.endswith('.gz')): continue
        with op(p,'rt',errors='replace') as fh:
            n=sum(1 for l in fh if l.startswith('-- Test Case:'))
        t+=n; print(f'{p:46s} {n}')
print('TOTAL', t)
EOF

# 3) 分区对照 SQL 缺陷（b.pad 不存在）
gzcat sql_aliyun/12_partition_64.sql.gz | grep -c 'a.pad <=> b.pad'

# 4) 分区 test_id 重复
gzcat sql_aliyun/12_partition_64.sql.gz | grep '^-- Test Case:' | sort | uniq -d | wc -l

# 5) SUBPARTITION 覆盖
gzcat sql_aliyun/12_partition_64.sql.gz sql_internal/29_partition_64_enhanced.sql.gz | grep -c SUBPARTITION

# 6) 被注释掉的负向 INSERT
grep -c '^-- INSERT INTO' sql_aliyun/*.sql sql_internal/*.sql

# 7) LOCK= / CHANGE / 默认算法 / SHOW CREATE TABLE / CHECKSUM TABLE
grep -ho 'LOCK=[A-Z]*\|CHANGE \|SHOW CREATE TABLE\|CHECKSUM TABLE' sql_aliyun/*.sql sql_internal/*.sql | sort | uniq -c

# 8) 已归档结果里 ERROR / MANUAL 的归因
python3 -c "
import csv,collections
r=list(csv.DictReader(open('results/summary_aliyun.csv')))
print(collections.Counter((x['status'],x['expected']) for x in r))"
```
