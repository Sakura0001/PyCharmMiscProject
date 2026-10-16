# MySQL 类型升级测试进度与覆盖范围汇报

- **日期：** 2026-10-16
- **当前分支：** `codex/ddl-verify-20260919`
- **测试目标：** SQL 直连场景下的 MySQL 类型升级 / DDL 升级结果正确性、数据正确性、数据一致性
- **当前本地 oracle：** MySQL 8.0.45 `COPY`
- **内网待验证 profile：** `INPLACE`、`INSTANT`

## 1. 一页结论

当前仓库已经围绕 SQL 直连场景下的 MySQL 类型升级 / DDL 升级正确性建立 5 个独立测试批次：

```text
TUC   基础一致性批次
TUCX  交互扩展批次
TUCS  统计信息与连续升级批次
TUCP  流水线浓缩批次
TUCZ  边界与两阶段升级批次
```

当前总量：

| 指标 | 数量 |
| --- | ---: |
| 测试批次 | 5 |
| 唯一 case / scenario | 22,838 |
| Profile | 3：`COPY` / `INPLACE` / `INSTANT` |
| Case / profile 执行总量 | 68,514 |
| SQL 执行流 | 15 |
| SQL 文件 / 压缩 SQL 文件 | 2,409 |
| 项目自动化测试 | 324 passed，33 subtests passed |
| 本地 MySQL 8.0.45 COPY 验证 | 全部通过 |
| 独立产物审计 | TUCP / TUCZ 审计通过，前三批此前也完成独立审计 |
| 内网 `INPLACE` / `INSTANT` | 待内网执行，尚未形成最终通过结论 |

当前本地验证结论：

```text
TUC   8,270 / 8,270 PASS
TUCX  13,721 / 13,721 PASS
TUCS  47 / 47 PASS
TUCP  50 / 50 PASS，另有整流合并输出 + 最终清理检查 PASS
TUCZ  750 / 750 PASS，另有整流合并输出 + 最终清理检查 PASS
```

本地验证环境：

```text
MySQL 8.0.45
隔离临时实例
COPY oracle
```

## 2. 当前测试目标

当前测试聚焦以下目标：

1. **结果正确性**
   - DDL 是否按预期成功或失败。
   - 预期成功时不能误报失败。
   - 预期失败时必须原子性失败。

2. **数据正确性**
   - 升级前已有数据不能损坏。
   - 升级后新写入数据不能损坏。
   - 第二次升级后，第一次升级后写入的数据仍不能损坏。

3. **数据一致性**
   - algorithm 表与 reference 表逐行、逐列一致。
   - `COPY`、`INPLACE`、`INSTANT` 语义一致。
   - 算法间差异不能被 silently 接受。

4. **表结构一致性**
   - column type。
   - nullable。
   - default。
   - ordinal position。
   - charset / collation。
   - generated / invisible / comment / extra 等元数据。

5. **索引与约束一致性**
   - 索引定义。
   - 索引元数据。
   - 主键形态。
   - 外键约束与动作。

6. **依赖对象一致性**
   - view。
   - trigger。
   - stored function。
   - stored procedure。
   - prepared statement。

7. **统计信息一致性**
   - `mysql.innodb_table_stats`。
   - `mysql.innodb_index_stats`。
   - `information_schema.STATISTICS`。
   - `information_schema.TABLES`。
   - `information_schema.PARTITIONS`。
   - `EXPLAIN FORMAT=JSON`。

8. **异常与崩溃判定**
   - signal。
   - assertion。
   - MySQL 2013 / 2006。
   - lost connection。
   - timeout。
   - 自然 crash。

这些都统一归类为失败，不能算负向通过。

## 3. 五个批次的结构与覆盖

### 3.1 TUC：基础一致性批次

#### 基本信息

```text
BATCH_ID: 2026-10-13-type-upgrade-consistency
PREFIX:   TUC
CASES:    8,270
```

目录：

```text
mysql_case_factory/generated/type_upgrade_consistency
```

本地结果：

```text
8,270 / 8,270 PASS
MySQL 8.0.45
```

#### 覆盖类型族

| 类型族 | Case 数 |
| --- | ---: |
| character | 4,042 |
| decimal | 1,820 |
| binary | 1,019 |
| bit | 516 |
| integer | 873 |
| 合计 | 8,270 |

#### 覆盖类型

**整数：**

```text
TINYINT
SMALLINT
MEDIUMINT
INT
BIGINT
signed
unsigned
```

覆盖方向：

```text
正向扩宽
降宽 expected reject
signed / unsigned 转换
边界值
正负数
0
最大值 / 最小值
```

**DECIMAL / NUMERIC：**

```text
DECIMAL
NUMERIC
precision 扩宽
scale 保持不变
DECIMAL <-> NUMERIC
不同 scale
最大 precision 65
最大 scale 30
```

**字符类型：**

```text
CHAR
VARCHAR
TINYTEXT
TEXT
MEDIUMTEXT
LONGTEXT
```

长度边界包括：

```text
1
2
7
8
15
16
31
32
63
64
85
86
127
128
255
256
511
512
1023
1024
2047
2048
4095
4096
```

字符集 / collation 覆盖：

```text
ascii
latin1
utf8mb3
utf8mb4
binary / default
```

**二进制类型：**

```text
BINARY
VARBINARY
TINYBLOB
BLOB
MEDIUMBLOB
LONGBLOB
```

长度边界包括：

```text
1
2
7
8
15
16
31
32
63
64
127
128
255
256
511
512
1023
1024
2047
2048
4095
4096
```

**BIT：**

```text
BIT(1) 到 BIT(64)
宽度边界
最大值
0
最高位
全 1
```

#### 列属性覆盖

| 属性 | Case 数 |
| --- | ---: |
| nullable | 5,084 |
| not null + default | 1,079 |
| comment | 523 |
| first | 523 |
| invisible | 523 |
| expression default | 498 |
| auto_increment | 40 |

覆盖点：

```text
NULL / NOT NULL
DEFAULT
表达式 DEFAULT
COMMENT
INVISIBLE
FIRST
AUTO_INCREMENT
默认值省略
```

#### 索引覆盖

| 索引形态 | Case 数 |
| --- | ---: |
| none | 4,938 |
| secondary | 769 |
| unique | 480 |
| composite | 480 |
| descending | 480 |
| invisible index | 480 |
| prefix | 347 |
| functional | 148 |
| generated | 148 |

覆盖点：

```text
普通二级索引
唯一索引
组合索引
前缀索引
降序索引
不可见索引
函数索引
生成列索引
无索引对照
```

#### 外键覆盖

外键相关 case：

```text
99
```

覆盖：

```text
parent
child
self reference
composite
multi level
CASCADE
SET NULL
RESTRICT
NO ACTION
```

#### 依赖对象覆盖

依赖相关 case：

```text
210
```

覆盖：

```text
view
stored function read
stored procedure write
prepared statement
BEFORE INSERT trigger
AFTER INSERT trigger
BEFORE UPDATE trigger
AFTER UPDATE trigger
BEFORE DELETE trigger
AFTER DELETE trigger
```

#### 表形态覆盖

| 表形态 | Case 数 |
| --- | ---: |
| ordinary | 7,676 |
| compact | 66 |
| compressed | 66 |
| redundant | 66 |
| range partition | 66 |
| list partition | 66 |
| hash partition | 66 |
| key partition | 66 |
| instant history | 66 |
| temporary | 66 |

#### SQL mode 覆盖

覆盖：

```text
STRICT_ALL_TABLES
STRICT_TRANS_TABLES
PAD_CHAR_TO_FULL_LENGTH
ANSI_QUOTES
NO_BACKSLASH_ESCAPES
```

### 3.2 TUCX：交互扩展批次

#### 基本信息

```text
BATCH_ID: 2026-10-13-type-upgrade-consistency-extension-v1
PREFIX:   TUCX
CASES:    13,721
```

目录：

```text
mysql_case_factory/generated/type_upgrade_consistency_extension_v1
```

本地结果：

```text
13,721 / 13,721 PASS
MySQL 8.0.45
```

#### 覆盖主 gap

| Gap | Case 数 |
| --- | ---: |
| GAP-DATA-BEHAVIOR | 4,116 |
| GAP-DDL-MULTI-COLUMN | 1,518 |
| GAP-FK-ACTION | 3,440 |
| GAP-INDEX-PK | 2,400 |
| GAP-QUERY-ORACLE | 2,247 |
| 合计 | 13,721 |

#### 类型族分布

| 类型族 | Case 数 |
| --- | ---: |
| character | 7,196 |
| decimal | 1,836 |
| binary | 1,615 |
| mixed | 1,518 |
| integer | 1,080 |
| bit | 476 |
| 合计 | 13,721 |

#### 数据行为覆盖

TUCX 扩展了升级后的数据行为：

```text
post-target boundary
default omission
collation equivalent
duplicate conflict
update old to new
delete reinsert
commit ledger
rollback ledger
```

具体包括：

- 升级后插入目标类型独有边界值。
- `INSERT` 省略目标列，验证 default。
- collation 等价但字节不同的值。
- unique key 冲突行为。
- 旧值更新成目标类型新值。
- 删除后重插。
- 显式事务 `COMMIT`。
- 显式事务 `ROLLBACK`。
- 提交 / 回滚后数据一致性。

#### 主键与索引覆盖

覆盖：

```text
单列主键
目标列作为第一列
目标列作为中间列
目标列作为最后一列
复合主键
主键与二级索引叠加
主键与唯一索引叠加
多个重叠索引
FORCE INDEX
唯一索引扫描
前缀索引排序
降序索引排序
EXPLAIN FORMAT=JSON
```

#### 查询 oracle 覆盖

覆盖：

```text
按 id 排序结果
按 target_col 排序结果
升序
降序
FORCE INDEX 结果一致性
reference 表与 algorithm 表查询结果一致
EXPLAIN 使用预期索引
```

#### 多列 DDL 覆盖

覆盖：

```text
两列同类型升级
三列同类型升级
五列混合类型升级
复合索引成员升级
原子性拒绝
同一 ALTER 中多列修改
```

#### 外键动作覆盖

覆盖：

```text
orphan insert
DELETE CASCADE
DELETE SET NULL
DELETE RESTRICT
DELETE NO ACTION
UPDATE CASCADE
UPDATE SET NULL
UPDATE RESTRICT
UPDATE NO ACTION
两级外键传播
```

### 3.3 TUCS：统计信息与连续升级批次

#### 基本信息

```text
BATCH_ID: 2026-10-14-type-upgrade-statistics-and-chain-v1
PREFIX:   TUCS
CASES:    47
```

目录：

```text
mysql_case_factory/generated/type_upgrade_statistics_v1
```

本地结果：

```text
47 / 47 PASS
MySQL 8.0.45
```

#### 覆盖 gap

| Gap | Case 数 |
| --- | ---: |
| GAP-STATS-PARTITION | 20 |
| GAP-STATS-INDEX | 6 |
| GAP-STATS-TABLE | 6 |
| GAP-STATS-EXPLAIN | 5 |
| GAP-STATS-INFORMATION-SCHEMA | 5 |
| GAP-CHAIN-UPGRADE | 4 |
| GAP-DUPLICATE-MODIFY | 1 |
| 合计 | 47 |

#### 统计信息接口覆盖

覆盖：

```text
mysql.innodb_table_stats
mysql.innodb_index_stats
information_schema.STATISTICS
information_schema.TABLES
information_schema.PARTITIONS
EXPLAIN FORMAT=JSON
ANALYZE TABLE
```

检查内容：

```text
表统计存在
索引统计存在
n_rows
clustered_index_size
sum_of_other_index_sizes
stat_name
stat_value
sample_size
分区统计覆盖每个分区
EXPLAIN 使用预期索引
统计信息非负
```

#### 分区统计覆盖

覆盖：

```text
RANGE partition
LIST partition
HASH partition
KEY partition
ordinary table 对照
```

#### 连续升级覆盖

覆盖：

```text
SMALLINT -> INT -> BIGINT
```

并且验证最终状态与直接 `SMALLINT -> BIGINT` reference 一致。

#### 负向 DDL 覆盖

覆盖：

```text
同一条 ALTER 中重复 MODIFY 同一列
```

预期：

```text
必须 reject
必须原子失败
```

### 3.4 TUCP：流水线浓缩批次

#### 基本信息

```text
BATCH_ID: 2026-10-15-type-upgrade-pipeline-v1
PREFIX:   TUCP
CASES:    50
SQL 文件: 150，COPY / INPLACE / INSTANT 各 50
```

目录：

```text
mysql_case_factory/generated/type_upgrade_pipeline_v1
```

本地结果：

```text
50 个场景 PASS
1 个 COMBINED_OUTPUT PASS
1 个 FINAL_CLEANUP PASS
合计 52 PASS
```

#### 特点

每个 SQL 文件：

```text
414 行左右
唯一表名
首尾 DROP TABLE
无 session/global 设置
确定性输出
固定 expected_output.tsv
```

#### 类型覆盖

| 类型族 | Case 数 |
| --- | ---: |
| character | 8 |
| integer | 8 |
| bit | 11 |
| decimal | 6 |
| binary | 6 |
| foreign key | 4 |
| dependency | 4 |
| statistics | 2 |
| table form | 1 |
| 合计 | 50 |

#### 索引覆盖

覆盖：

```text
secondary
unique
composite
prefix
descending
functional
primary + AUTO_INCREMENT
```

#### 表形态 / 引擎覆盖

覆盖：

```text
InnoDB
MyISAM
MEMORY
ordinary
range partition
DYNAMIC row format
COMPACT row format
```

#### 外键动作覆盖

覆盖：

```text
ON DELETE CASCADE
ON UPDATE CASCADE
ON DELETE SET NULL
NO ACTION
```

#### 依赖覆盖

覆盖：

```text
view
trigger
stored function
stored procedure
组合依赖
```

#### 统计信息覆盖

覆盖：

```text
普通表统计
索引统计
分区统计
```

#### 特殊场景

覆盖：

```text
SMALLINT -> INT -> BIGINT 连续升级
多列同时升级
```

#### 输出判定

TUCP 使用精确输出：

```text
expected_output.tsv
```

三个 profile 的期望输出完全一致。

判定：

```text
diff 为空
stderr 为空
无 |FAIL
无缺行
```

### 3.5 TUCZ：边界与两阶段升级批次

#### 基本信息

```text
BATCH_ID: 2026-10-15-type-upgrade-boundary-v1
PREFIX:   TUCZ
CASES:    750
SQL 文件: 2,250，COPY / INPLACE / INSTANT 各 750
```

目录：

```text
mysql_case_factory/generated/type_upgrade_boundary_v1
```

本地结果：

```text
750 个场景 PASS
1 个 COMBINED_OUTPUT PASS
1 个 FINAL_CLEANUP PASS
合计 752 PASS
```

#### 核心测试方式

每个 case 都是两阶段升级：

```text
1. 插入 24 行源类型数据
2. 第一次升级：source -> intermediate
3. 插入 24 行 intermediate 类型边界数据
4. 第二次升级：intermediate -> target
5. 插入 24 行 final 类型边界数据
6. 与 direct final-shape reference 表逐行逐列比较
```

这专门覆盖：

```text
升级前已有数据
第一次升级后新写入的数据
第二次升级后仍然不能损坏
```

#### 类别分布

| 类别 | Case 数 |
| --- | ---: |
| zero_core | 512 |
| zero_cross | 112 |
| decimal_max | 64 |
| variable_max | 20 |
| variable_overflow | 10 |
| alias_normalization | 32 |
| 合计 | 750 |

#### 零长度类型覆盖

覆盖：

```text
CHAR(0)
VARCHAR(0)
BINARY(0)
VARBINARY(0)
NCHAR(0)
NVARCHAR(0)
CHARACTER(0)
CHARACTER VARYING(0)
```

其中核心四个源类型：

```text
CHAR(0)      156 个场景
VARCHAR(0)   156 个场景
BINARY(0)    156 个场景
VARBINARY(0) 156 个场景
```

覆盖链：

```text
CHAR(0)      -> CHAR(1)      -> CHAR(2)
CHAR(0)      -> VARCHAR(1)   -> VARCHAR(2)
VARCHAR(0)   -> VARCHAR(1)   -> VARCHAR(2)
VARCHAR(0)   -> CHAR(1)      -> CHAR(2)

BINARY(0)    -> BINARY(1)    -> BINARY(2)
BINARY(0)    -> VARBINARY(1) -> VARBINARY(2)
VARBINARY(0) -> VARBINARY(1) -> VARBINARY(2)
VARBINARY(0) -> BINARY(1)    -> BINARY(2)
```

跨族转换：

```text
CHAR(0)      -> BINARY(1)    -> BINARY(2)
VARCHAR(0)   -> BINARY(1)    -> BINARY(2)
BINARY(0)    -> CHAR(1)      -> CHAR(2)
VARBINARY(0) -> CHAR(1)      -> CHAR(2)
```

LOB 转换：

```text
CHAR(0)      -> VARCHAR(1)   -> TEXT
VARCHAR(0)   -> VARCHAR(1)   -> TEXT
BINARY(0)    -> VARBINARY(1) -> BLOB
VARBINARY(0) -> VARBINARY(1) -> BLOB
```

关键语义：

```text
BINARY(0) -> BINARY(1)     预期 x'00'
BINARY(0) -> VARBINARY(1)  预期 x''
CHAR(0)   -> CHAR(1)       预期 ''
CHAR(0)   -> BINARY(1)     预期 x'00'
BINARY(0) -> CHAR(1)       预期 ''
```

#### DECIMAL 最大边界

覆盖：

```text
DECIMAL(63,30) -> DECIMAL(64,30) -> DECIMAL(65,30)
NUMERIC(63,30) -> NUMERIC(64,30) -> NUMERIC(65,30)
DECIMAL(63,30) -> NUMERIC(64,30) -> NUMERIC(65,30)
NUMERIC(63,30) -> DECIMAL(64,30) -> DECIMAL(65,30)
```

覆盖：

```text
最大 precision 65
最大 scale 30
正向两阶段升级
DECIMAL <-> NUMERIC
```

#### 变长类型行大小边界

在固定表结构下覆盖：

| 类型 | 最大长度 |
| --- | ---: |
| VARCHAR utf8mb4 | 16,307 |
| VARCHAR utf8mb3 | 21,743 |
| VARCHAR latin1 | 65,231 |
| VARCHAR ascii | 65,231 |
| VARBINARY | 65,231 |

覆盖链：

```text
max-2 -> max-1 -> max
```

并覆盖溢出：

```text
VARCHAR(max-1)   -> TEXT
VARBINARY(max-1) -> BLOB
```

#### 类型别名与归一化

覆盖：

```text
BOOL
BOOLEAN
TINYINT(1)
INT(0)
INT UNSIGNED ZEROFILL
DEC
FIXED
DECIMAL
NUMERIC
BIT
BINARY
CHAR
NCHAR(0)
NVARCHAR(0)
CHARACTER(0)
CHARACTER VARYING(0)
```

#### 属性迁移覆盖

覆盖：

```text
NOT NULL DEFAULT ... -> NULL
NOT NULL DEFAULT ... -> NOT NULL DEFAULT ...
NOT NULL 无默认值
NULL
```

数量：

| 属性迁移 | Case 数 |
| --- | ---: |
| not_null_default_preserve | 192 |
| not_null_default_to_null | 191 |
| nullable | 191 |
| not_null_no_default | 176 |

#### 列位置覆盖

| 位置形态 | Case 数 |
| --- | ---: |
| noop_after | 232 |
| actual_after | 128 |
| first | 128 |
| none | 262 |

覆盖：

```text
无位置子句
AFTER id 的 no-op
AFTER c 的实际重排
FIRST
```

#### Row format 覆盖

| Row format | Case 数 |
| --- | ---: |
| DYNAMIC | 268 |
| COMPACT | 226 |
| COMPRESSED | 128 |
| REDUNDANT | 128 |

#### 字符集覆盖

覆盖：

```text
utf8mb4
utf8mb3
latin1
ascii
```

#### 索引模式

| 索引模式 | Case 数 |
| --- | ---: |
| none | 446 |
| add_after_first | 304 |

覆盖点：

```text
零长度源列不能直接建索引
第一次升级后同一条 ALTER 添加索引
第二次升级后索引仍正确
```

#### FK 与统计子集

覆盖：

```text
FK 子集：20 个场景
统计信息子集：47 个场景
```

## 4. 全量回归清单

已经建立强制全量回归机制。

文档：

```text
mysql_case_factory/docs/type_upgrade_full_regression.md
```

机器可读清单：

```text
mysql_case_factory/generated/type_upgrade_full_regression/inventory.tsv
```

Manifest：

```text
mysql_case_factory/generated/type_upgrade_full_regression/manifest.json
```

总量：

| 指标 | 数量 |
| --- | ---: |
| 批次 | 5 |
| case / scenario | 22,838 |
| profile | 3 |
| case/profile 执行总量 | 68,514 |
| SQL 执行流 | 15 |
| SQL artifact | 2,409 |

强制策略：

```text
5 batches x 3 profiles = 15 execution streams
```

固定顺序：

```text
TUC
TUCX
TUCS
TUCP
TUCZ
```

每个批次内：

```text
COPY
INPLACE
INSTANT
```

不允许选择性回归。漏跑任何一项，状态只能是：

```text
INCOMPLETE
```

任何 oracle 失败，状态只能是：

```text
FAIL
```

## 5. 测试 oracle 汇总

当前测试不是只看 DDL 是否返回成功，而是使用多层 oracle。

### 5.1 Reference table oracle

每个 case 通常构造：

```text
reference 表：直接按最终目标类型建表
algorithm 表：从源类型开始执行 DDL
```

然后比较：

```text
表结构
数据
索引
约束
依赖
统计信息
查询结果
```

### 5.2 Schema oracle

比较：

```text
column_name
ordinal_position
column_type
is_nullable
column_default
extra
character_set_name
collation_name
column_comment
```

### 5.3 Row data oracle

逐行比较：

```text
目标列
后续 canary 列
VARCHAR
CHAR
INT
BIGINT
DECIMAL
BLOB / TEXT
```

用于发现类似：

```text
BINARY(0) -> BINARY(1) 后列偏移错位
后续列数据损坏
INT / BIGINT 被错误解释
```

### 5.4 Index oracle

比较：

```text
index_name
non_unique
seq_in_index
column_name
collation
sub_part
packed
nullable
index_type
comment
index_comment
expression
```

### 5.5 Foreign key oracle

比较：

```text
constraint schema
constraint name
table name
referenced table
referenced column
FK action
```

并验证 FK 动作后的数据状态。

### 5.6 Dependency oracle

验证：

```text
view 查询结果
trigger 写入结果
stored function 返回值
stored procedure 写入结果
prepared statement 执行结果
```

### 5.7 Statistics oracle

验证：

```text
mysql.innodb_table_stats
mysql.innodb_index_stats
information_schema.STATISTICS
information_schema.TABLES
information_schema.PARTITIONS
EXPLAIN FORMAT=JSON
ANALYZE TABLE
```

### 5.8 Query oracle

验证：

```text
ORDER BY id
ORDER BY target_col
ASC / DESC
FORCE INDEX
reference 与 algorithm 查询结果一致
EXPLAIN 使用预期索引
```

### 5.9 Exact output oracle

TUCP 和 TUCZ 使用精确输出：

```text
expected_output.tsv
```

要求：

```text
stdout 完全一致
stderr 为空
无 FAIL
无缺行
```

## 6. 负向与异常覆盖

当前覆盖的负向 / 异常场景包括：

### 6.1 数据降宽或越界

覆盖：

```text
BIGINT -> INT 越界
INT -> SMALLINT 越界
目标值超出目标类型范围
expected reject
```

### 6.2 原子性 DDL

覆盖：

```text
多列 ALTER 中一列非法
整条 ALTER 必须原子失败
不能部分修改
```

### 6.3 重复 MODIFY

覆盖：

```text
同一条 ALTER 中重复 MODIFY 同一列
必须 reject
```

### 6.4 Invalid post-DDL values

覆盖：

```text
升级后插入超出目标类型范围的值
必须失败
```

### 6.5 Unique conflict 行为

TUCX 中有：

```text
480 个 duplicate_conflict case
480 个 unique_conflict query oracle case
```

本地 runner 会验证冲突插入失败。

但需要注意：

```text
当前内网 SQL suite 没有渲染 invalid_post_ddl_sql
```

因此“唯一键冲突优化”还没有完整闭环，属于当前已知待补点。

### 6.6 Crash / connection failure

统一失败分类：

```text
FAIL_CRASH
FAIL_TIMEOUT
MySQL 2013
MySQL 2006
Lost connection
Server has gone away
signal
assertion
```

不允许把自然 crash 当作负向通过。

## 7. 工程质量与可执行性覆盖

当前产物还覆盖了测试工程本身的可靠性：

### 7.1 唯一对象名

覆盖：

```text
TUCP: 110 个唯一表名
TUCZ: 1,520 个唯一表名
```

表名规则：

```text
tab_<prefix>_<case_no>_<role>
```

索引名规则：

```text
idx_<prefix>_<case_no>_<role>
uk_<prefix>_<case_no>_<role>
```

### 7.2 首尾清理

每个 SQL 文件：

```text
开始：DROP TABLE IF EXISTS
结束：DROP TABLE IF EXISTS
```

### 7.3 不依赖 session 变量

TUCP / TUCZ：

```text
不设置 SET SESSION
不设置 SET GLOBAL
```

适合直接上流水线。

### 7.4 确定性输出

TUCP / TUCZ：

```text
输出固定
expected_output.tsv 精确比对
三个 profile 期望输出一致
```

### 7.5 整流合并输出

TUCP / TUCZ 本地额外执行：

```text
所有 SQL 文件拼接成一个 stream
```

并验证：

```text
combined output 与 expected_output.tsv 完全一致
```

### 7.6 最终清理检查

执行后检查：

```text
没有遗留 tab_tucp_* 表
没有遗留 tab_tucz_* 表
没有遗留 routine
```

### 7.7 Artifact hash

TUCP / TUCZ manifest 中记录所有 SQL artifact 的 SHA-256：

```text
TUCP: 153 个 artifact hash
TUCZ: 2,253 个 artifact hash
```

审计会验证 hash。

## 8. 自动化测试状态

当前项目完整测试结果：

```text
324 passed
33 subtests passed
```

测试覆盖：

```text
生成器逻辑
确定性生成
manifest
artifact hash
case 数量
profile 数量
唯一表名
首尾清理
禁用类型
session 设置
期望输出
本地 runner
审计器
全量回归清单
文档链接
批次数完整性
SQL artifact 完整性
```

## 9. 当前明确排除的范围

本轮测试聚焦 SQL 直连类型升级，以下内容明确不纳入：

```text
FLOAT / DOUBLE / REAL
DATE / TIME / DATETIME / TIMESTAMP / YEAR
ENUM / SET
JSON
空间类型
向量类型
FULLTEXT
SPATIAL
JSON multi-value index
time_zone
备份 / PITR
crash injection
资源故障注入
HA switchover
控制面 API
连接丢失重试 / cancel
并发 DDL / DML
```

这些不是当前批次的目标范围。

## 10. 当前已知待补点

### 10.1 内网 `INPLACE` / `INSTANT` 尚未执行

当前本地全部使用 `COPY` 作为 oracle。

内网还需要执行：

```text
TUCP INPLACE
TUCP INSTANT
TUCZ INPLACE
TUCZ INSTANT
TUC / TUCX / TUCS INPLACE
TUC / TUCX / TUCS INSTANT
```

在内网结果出来前，不能宣称全量回归 PASS。

### 10.2 唯一键冲突优化未完整闭环

已有：

```text
unique index
duplicate conflict case 元数据
本地 runner 冲突插入
```

但缺少：

```text
内网 SQL suite 中的冲突插入渲染
DDL-time unique conflict
精确 ERROR 1062 断言
BINARY(0) -> BINARY(1) + ADD UNIQUE
collation 转换导致 DDL-time 冲突
```

建议后续单独增加 `TUCU` 批次。

### 10.3 TUCZ 不是全因子完整笛卡尔积

TUCZ 是边界矩阵，不是：

```text
所有类型
x 所有属性
x 所有位置
x 所有 row format
x 所有索引
x 所有 FK
x 所有统计
```

的完整笛卡尔积。

它是针对已发现缺口的定向边界补充。

### 10.4 统计信息参数尚未全量覆盖

当前覆盖持久化表 / 索引 / 分区统计和 EXPLAIN。

尚未完整覆盖：

```text
UPDATE HISTOGRAM
COLUMN_STATISTICS
innodb_stats_persistent
innodb_stats_auto_recalc
innodb_stats_persistent_sample_pages
innodb_stats_transient_sample_pages
innodb_stats_method
innodb_stats_on_metadata
```

## 11. 建议汇报口径

可以直接使用下面这段话：

> 当前已经围绕 SQL 直连类型升级建立 5 个独立测试批次，共 22,838 个测试场景，覆盖 COPY、INPLACE、INSTANT 三种算法，理论执行量为 68,514 次 case/profile 执行，涉及 2,409 个 SQL artifact。覆盖范围包括整数、DECIMAL、字符、二进制、BIT、零长度类型、最大精度、最大行长度、索引、主键、外键、视图、触发器、存储函数、存储过程、prepared statement、分区、row format、多列 ALTER、连续升级、统计信息、EXPLAIN、事务提交回滚、默认值、collation、查询 oracle 和负向原子性场景。当前本地 MySQL 8.0.45 COPY oracle 已全部通过，项目自动化测试 324 项通过，TUCP 和 TUCZ 的独立产物审计也全部通过。内网 INPLACE 和 INSTANT 尚待按全量回归清单执行，执行完成后才能给出最终上线结论。

## 12. 当前关键产物位置

全量回归文档：

```text
mysql_case_factory/docs/type_upgrade_full_regression.md
```

全量回归清单：

```text
mysql_case_factory/generated/type_upgrade_full_regression/inventory.tsv
```

全量回归 manifest：

```text
mysql_case_factory/generated/type_upgrade_full_regression/manifest.json
```

TUC：

```text
mysql_case_factory/generated/type_upgrade_consistency
```

TUCX：

```text
mysql_case_factory/generated/type_upgrade_consistency_extension_v1
```

TUCS：

```text
mysql_case_factory/generated/type_upgrade_statistics_v1
```

TUCP：

```text
mysql_case_factory/generated/type_upgrade_pipeline_v1
```

TUCZ：

```text
mysql_case_factory/generated/type_upgrade_boundary_v1
```

当前分支：

```text
codex/ddl-verify-20260919
```
