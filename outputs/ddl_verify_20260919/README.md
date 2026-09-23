# RDS MySQL DDL 秒级/在线修改列类型 — 验证测试套件

验证 RDS MySQL 8.0 的 **INSTANT（秒级）** 与 **INPLACE（在线）** 列类型修改能力：
功能正确性、数据一致性、元数据保持、在线性、失败模式、崩溃恢复、复制一致性。

- **权威文档**：`FIX_LOG.md`（逐步修复与验证台账）、`test_gap_audit_20260923.md`（原始审计）
- 其余 `*.md` 均为**历史留档**，顶部已标注过期点，不要直接引用其中数字

---

## 1. 当前规模与状态

| 项 | 值 |
|---|---|
| SQL 文件 | **37** 个（阿里云 17 / 内网 20） |
| 用例总数 | **10,731**（阿里云 5,822 / 内网 4,909） |
| 用例 ID | **全局唯一，重复 0**（`TC-<文件号>-<作用域>-<序号>-<算法>`） |
| 阿里云 RDS 8.0.36 全量 | **5,228 / 5,228 PASS**（0 FAIL / 0 ERROR / 0 MANUAL / 0 MISSING） |
| 断言规模 | **19,530 条**，平均 **3.74 条/用例**（SQL 11,564 + 执行器合成 7,966） |
| 静态自检 | `selfcheck/test_runner.py` **90 项 pytest** |
| 反向对照 | `selfcheck/negative_control.py` **6/6 类缺陷全部被捕获** |
| 实测 golden 基线 | 转换矩阵 196 条、因子矩阵 198 条、分区兼容 24×17、外键矩阵 66 条 |

## 2. 目录结构

```
generate_test_sql.py            SQL 生成器（表驱动，含全局唯一性/产物入库自检）
run_tests.py                    执行器 v3（pymysql 逐语句、按用例归因、并发/续跑/重试）
selfcheck/test_runner.py        90 项静态守卫（pytest）
selfcheck/negative_control.py   反向对照：故意注入 6 类缺陷，验证断言真的有牙齿
tools/probe_partition_compat.py 分区兼容矩阵探针（24 策略 × 17 类型）
tools/promote_conversion_matrix.py  把实测结果冻结为 golden 基线
tools/{conversion,factor,partition_compat,fk}_matrix_aliyun.json  实测基线
scenarios/online_ddl_failure_modes.py  MDL 阻塞 / 超时 / KILL / 并发 DDL / row log 溢出 / 外键并发
scenarios/replication_and_crash.py     binlog 记录 / 备库一致性 / SIGKILL 崩溃恢复
scenarios/session_variables.py         GIPK / sql_require_primary_key / innodb_strict_mode（需特权）
concurrent_dml/                 并发 DML + DualWrite Oracle + QPS/延迟分位 + DDL Fuzz
sql_aliyun/  sql_internal/      生成的 SQL（大文件以 .sql.gz 发布，执行器透明解压）
results/                        运行结果；results/archive/ 为带时间戳的不可覆盖证据
```

### 文件编号约定
`01–12` 阿里云基础 · `15–29` 内网基础 · `30/32/34` 阿里云专项 · `31/33/35` 内网专项 ·
`40/42` 阿里云矩阵 · `41/43` 内网矩阵。**文件号即用例 ID 的命名空间，全局唯一。**

作用域：`REG` 普通表 OFAT · `ATR` 列属性保持 · `SPE` 特殊模式 · `FK` 外键 ·
`PTK/PNK` 分区（目标列是/不是分区键）· `FRM` DDL 语句形态 · `TMG` 秒级计时 ·
`IDX` 索引完整性 · `CONV` 转换兼容矩阵 · `FCT` 因子矩阵

## 3. 如何运行

```bash
# 0) 配置（源码里不含任何凭据；config.ini 已被 .gitignore 排除）
cp config.example.ini config.ini      # 填 [aliyun] / [internal] / [local]
export MYSQL_PWD='<password>'         # 推荐：避免密码出现在 ps 与命令行

# 1) 生成 SQL（含全局唯一性自检 + 产物入库自检 + 过期产物清理）
python3 generate_test_sql.py
python3 generate_test_sql.py --charvarchar-mode cross_only   # 切换 CHAR/VARCHAR 支持口径

# 2) 不连库先看清单（文件/用例数/内容哈希/重复 ID）
python3 run_tests.py --env aliyun --dry-run
python3 run_tests.py --env aliyun --check-manifest results/manifest_aliyun.json

# 3) 执行（自动解压 .sql.gz；按用例切分；逐语句归因 errno）
python3 run_tests.py --env aliyun --workers 8                 # 全量，约 11 分钟
python3 run_tests.py --env aliyun --files 07_varchar_instant.sql.gz --sample 20
python3 run_tests.py --env internal --resume                  # 断点续跑

# 4) 专项场景
python3 scenarios/online_ddl_failure_modes.py --env aliyun --rows 200000
python3 scenarios/replication_and_crash.py --env aliyun --only R1
python3 scenarios/replication_and_crash.py --only C1 --crash-ddl copy_rebuild
python3 scenarios/session_variables.py --env local

# 5) 自检
python3 -m pytest selfcheck/test_runner.py -q                 # 90 passed
python3 selfcheck/negative_control.py --env aliyun            # 6/6 必须全部被捕获

# 6) 兼容矩阵：测量 -> 复核 -> 冻结 -> 回归
python3 run_tests.py --env aliyun --files 40_conversion_matrix.sql      # MEASURE 轮
python3 tools/promote_conversion_matrix.py --env aliyun                 # 冻结 golden
python3 tools/promote_conversion_matrix.py --env aliyun --kind factor
python3 generate_test_sql.py                                            # 之后按 golden 硬断言
```

## 4. 一个用例验证什么

以常规用例为例，每条用例最多产出 **7 类独立断言**，任一 FAIL 即整例 FAIL：

| 断言 | 验证内容 |
|---|---|
| `PRIMARY` | 与 Oracle 对照表逐行 NULL-safe 比对（多余行/缺失行/数据不一致分别标注） |
| `ALTER_OUTCOME` | 按 `alter_sha` 精确定位那条 ALTER，**声明 SUCCESS 就必须没报错、声明 FAIL 就必须报错且 errno 在声明集合内** |
| `META` | ALTER 后的 `column_type` / `is_nullable` / `column_default` 有无 / `character_set_name` / `collation_name` / `extra` / `ordinal_position` **7 项**，mismatch 同时给出 `actual[]` 与 `want[]` |
| `NEG_REJECTED` | 超上限值**同时**插入 t1 与对照表：STRICT 必须 0 行落库；非 STRICT 必须两表对称 |
| `NEG_ERRNO#n` | 每条负向探针按语句 sha1 对账：STRICT 必须以声明的 errno 失败，非 STRICT 必须被接受 |
| `BUILD_REJECTED` | "建表本应被拒"的负向用例真的没建出表（查 `information_schema.tables`） |
| `IDX_*` / `CRC_ORACLE` / `FK_CONSTRAINT_PRESENT` / `FAST_PATH` | 索引存在性、索引扫描 vs 全表扫描一致性、逐行 CRC 对照、外键约束是否恢复、秒级差分计时 |

执行器还会做**完整性核算**：选中的用例必须全部产出判定，否则记 `MISSING` 并以退出码 3 失败。

## 5. 环境能力画像

不同实例支持范围不同，期望值表达为**数据**而非散落的 if：

| 环境 | CHAR/VARCHAR 口径 | 依据 |
|---|---|---|
| `aliyun` | `all`（同字节桶与跨字节桶都支持） | 实测 5,228/5,228 PASS |
| `internal` | `cross_only`（**只支持跨字节桶**，同桶 INSTANT/INPLACE 均不支持） | 测试同学口径，待内网实测复核 |

"字节桶"= VARCHAR/VARBINARY 长度前缀 1 字节（≤255 字节）/ 2 字节（>255 字节）；CHAR 按字节宽度同口径。
`--charvarchar-mode {cross_only,same_only,all,none}` 可整体切换，无需改代码。
命中画像规则的用例会在 `@expect` 头留下 `profile_rule=` 标记，可追溯。

> 已验证：画像与实例真实行为不符时，`PRIMARY` / `META` / `ALTER_OUTCOME` **三条独立断言会同时报出来**
> （在 RDS 上故意用错画像，160 例全部被捕获，93 例跨桶转换保持全绿）。

## 6. 主要实测结论（阿里云 RDS MySQL 8.0.36）

| 结论 | errno |
|---|---|
| AUTO_INCREMENT 列的类型加宽**不支持 INSTANT**（INPLACE/COPY 正常；普通列 INSTANT 正常） | 1845 |
| 一张表累积 **64 次** instant 加/删列后，第 65 次被拒（秒级能力失效，须 COPY/INPLACE） | **4092** |
| 同一列反复 INSTANT **MODIFY** 类型 70 轮全部成功 → 4092 只约束 ADD/DROP COLUMN | — |
| 外键列：INSTANT 一律失败（整数 3780 / 字符串 1845）；`foreign_key_checks=0` **无法**绕过 3780 | 3780/1845 |
| 外键列：INPLACE 改 CHAR/VARCHAR/BINARY/VARBINARY **一律成功，连单侧改也成功** → 父 varchar(50) 与子 varchar(100) 能和活外键共存，MySQL 不复核兼容性 | — |
| 改外键列类型的唯一可行序列：`DROP FOREIGN KEY` → 改两侧 → `ADD FOREIGN KEY` | — |
| 分区键列改类型：INSTANT/INPLACE 均拒绝，**`ALGORITHM=COPY` 可以成功** | 1846 |
| 分区键/索引列长度上限：`max_bytes(target) + 4 ≤ 3072`（latin1 VARCHAR 最大 3068、utf8mb4 最大 VARCHAR(767)） | 1071 |
| 行宽上限（`id INT` + target 两列表）：`VARCHAR(16382)` utf8mb4 / `VARCHAR(65528)` latin1 / `VARBINARY(65528)` | 1118 |
| `innodb_strict_mode` 管的是 InnoDB 半页(8126B)限制；server 级 65535 行宽上限**两种模式都报错** | 1118 |
| INSTANT/INPLACE 支持的转换只是少数：兼容矩阵 49 个探针里 **仅 5 个**（ENUM/SET 末尾追加、FLOAT(M,D)、collation 变更） | 1846 |
| 不写 `ALGORITHM` 时 44/49 探针成功 → **"能改"不等于"秒级"**，服务器静默回退 COPY（慢 20~38 倍） | — |
| 缩窄转换在数据不丢失时**是成功的**（数据溢出才失败：整数 1264 / 字符串 1265） | 1264/1265 |
| RDS 禁用 MyISAM / MEMORY 引擎；无 keyring 时 `ENCRYPTION='Y'` 建表失败 | 3161 / 3185 |
| TEXT / BLOB **不能**作任何分区键；DECIMAL 只能 KEY / LINEAR KEY；BIT 支持 14/24 种策略 | 1170/1659 |
| DDL 中途 SIGKILL（4,194,304 行 COPY 重建 / INPLACE 建索引两条路径）：行数、校验和、列类型全部一致，无 `#sql-` 残留，之后读写与 DDL 正常 | 1317 |

## 7. 安全边界

- 目标只允许 `config.ini` 里显式配置的授权测试实例；源码与文档中**不含任何真实凭据或地址**
  （文档里的实例地址已替换为 `<RDS_ENDPOINT>` 占位符）
- 崩溃恢复在 `ThrowawayInstance`（临时 datadir + 自动端口 + 独立 socket）上做，**不触碰任何在运行的实例**
- 所有场景都有硬超时、并发上限、行数上限；`SET GLOBAL` 只在具备 SUPER 的实例上尝试，否则**明确 SKIP**
- **按项目要求，测试表不做收尾清理**（用例只在自己开头 `DROP TABLE IF EXISTS` 自己的表）；
  全量跑完 `ddl_test` 里会残留约 2 万张表，需要时手工清理

> ⚠️ 历史遗留：旧版本曾在已入库的 `concurrent_dml/run_concurrent_tests.py` 里硬编码真实 RDS 口令，
> 该口令存在于 git 历史的 2 个提交中。清理工作区**不能**清除历史 —— **请轮换该口令**；
> 若仓库曾外发，还需用 `git filter-repo` 重写历史。
