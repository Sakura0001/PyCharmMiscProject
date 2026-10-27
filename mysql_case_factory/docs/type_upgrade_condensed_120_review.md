# 120 个满帮 DDL 精简 regress 用例设计稿

> 本文件只做方案评审，不生成 SQL。每个用例都是“单个 SQL 文件可完成”的顺序用例，不依赖并发线程、外部 runner 或 session/global 变量。

## 最终口径

固定为 **120 个 SQL 用例文件**，不是 120 个逻辑用例：

```text
120 SQL files
```

每个 SQL 文件内部同时覆盖：

```text
INPLACE candidate
INSTANT candidate
direct target reference
```

也就是说每个用例文件会执行两条算法 DDL：

```sql
ALTER TABLE ... ALGORITHM=INPLACE, LOCK=NONE;
ALTER TABLE ... ALGORITHM=INSTANT;
```

并为两条算法分别做数据一致性校验。

## 单个 SQL 用例结构

每个 `TUCR-000NNN.sql` 都包含以下固定阶段：

1. **pre-cleanup**
   - 删除本用例专属的所有表、视图、触发器、函数、过程。
2. **create source candidates**
   - 创建 `tab_tucr_NNN_inplace`，使用 source type。
   - 创建 `tab_tucr_NNN_instant`，使用 source type。
3. **create direct target reference**
   - 创建 `tab_tucr_NNN_ref`，直接使用 target type。
   - 该表不执行 DDL，是数据一致性的最终对照表。
4. **seed deterministic rows**
   - 三张表插入完全相同的确定性 seed 数据。
   - 数据包含普通值、边界值、极限值、NULL 或 NOT NULL 场景。
5. **execute DDL**
   - 对 inplace candidate 执行 `ALGORITHM=INPLACE, LOCK=NONE`。
   - 对 instant candidate 执行 `ALGORITHM=INSTANT`。
6. **post-DDL DML**
   - 向三张表插入完全相同的 target-type 后置数据。
   - 执行相同的定向 UPDATE，只修改固定代表性 ID。
   - 执行相同的定向 DELETE，只删除固定代表性 ID。
   - 执行相同的固定再 INSERT。
7. **schema validation**
   - 比较 candidate 与 reference 的目标列类型。
   - 检查索引、外键、生成列、函数索引、视图、触发器等对象是否仍然存在。
8. **data validation**
   - 比较 candidate 与 reference 的行数。
   - 比较所有业务列的值。
   - 使用 `NULL`-safe 比较，避免 NULL 参与比较时误判。
   - 不输出大量业务数据。
   - 只输出差异计数和 `PASS/FAIL`。
9. **fixed result rows**
   - 每个 SQL 文件输出固定两行结果：
     - `TUCR-000NNN | INPLACE | PASS`
     - `TUCR-000NNN | INSTANT | PASS`
   - 如校验失败，对应行输出 `FAIL`。
   - 不输出 unstable 的统计信息、执行计划成本或时间。
10. **final cleanup**
    - 删除本用例创建的所有对象。

## 定向 DML 设计

所有 120 个用例都不做全表 UPDATE / DELETE。每个用例只修改固定代表性 ID：

```text
UPDATE id IN (1, 3, 5)
DELETE id IN (2, 4)
固定 reinsert
```

推荐 ID 语义：

```text
id=1  normal value
id=2  boundary value
id=3  extreme/max value
id=4  NULL/default/special semantic
id=5  collation/prefix/special representation
id=6  post-DDL inserted target value
id=7  post-DDL inserted boundary value
```

三张表执行完全相同的定向 DML：

```text
inplace candidate
instant candidate
direct target reference
```

特殊场景按语义调整：

- 外键：删除代表性 parent 行并检查 orphan；
- 唯一索引：删除后重插相同 key；
- 自增：删除后省略自增列插入；
- 生成列 / 函数索引：UPDATE 改变 base 列；
- 分区：ID 覆盖多个分区；
- 触发器 / 存储过程：DML 触发对应依赖对象。

## 数据校验设计

每个 candidate 都与 direct target reference 表比较：

```text
candidate row count == reference row count
candidate schema == reference schema
candidate all-column data == reference all-column data
```

数据比较使用固定 SQL 语句：

```sql
SELECT COUNT(*)
FROM candidate c
LEFT JOIN reference r ON r.id = c.id
WHERE r.id IS NULL
   OR NOT (c.col1 <=> r.col1)
   OR NOT (c.col2 <=> r.col2)
   ...
```

同时反向检查 reference 中多出的行：

```sql
SELECT COUNT(*)
FROM reference r
LEFT JOIN candidate c ON c.id = r.id
WHERE c.id IS NULL;
```

如果两个方向的差异计数都为 0，则判定数据一致。

## 输出稳定性设计

每个用例只输出固定格式的结果行：

```text
TUCR-000001	INPLACE	0	0	0	0	PASS
TUCR-000001	INSTANT	0	0	0	0	PASS
```

字段含义：

```text
case_id
algorithm
schema_diff_count
row_count_diff
candidate_missing_or_mismatch_count
reference_extra_count
result
```

因此：

- 不输出大量业务行；
- 不输出 unstable cardinality；
- 不输出 cost；
- 不输出执行时间；
- 多次执行输出一致；
- 可以直接用于流水线 `diff`。

## 算法失败处理

如果内部实现中某个算法对某条转换不支持：

- SQL 语句会返回错误；
- 结果行不会输出 `PASS`；
- 该场景判为失败或 expected reject，由流水线 stderr 和 stdout 共同判定；
- 不允许把算法失败静默当成数据校验通过。

如果产品矩阵明确要求某条转换必须失败，后续生成器可以为该用例增加
`EXPECTED_REJECT` 标记，并校验 DDL 失败后源表数据不变。但当前这份
120 用例设计默认目标是通过升级后与 direct reference 表比对数据正确性。

## 执行要求

单个 SQL 文件中包含两条 DDL。如果第一条 DDL 失败，后续语句仍应继续执行，因此内部流水线必须使用：

```bash
mysql --force
```

这样可以保证同一个文件中的 `INPLACE` 和 `INSTANT` 都被执行，并分别得到校验结果。

每个用例的对象命名都包含 case number，保证：

```text
table name 全局唯一
view name 全局唯一
trigger name 全局唯一
function name 全局唯一
procedure name 全局唯一
index 的 table.index 限定名全局唯一
```

## 120 个用例明细

下表中的“验证点”是在固定 candidate/reference 数据比对之外的重点检查项。
所有 120 个用例都会执行相同的 candidate/reference 行数、全列数据和 schema
比对；表中列出的是该用例额外关注的对象或语义。


### Integer

| 用例ID | 场景 | 类型/对象 | 数据/边界 | 依赖/索引 | 验证点 |
| --- | --- | --- | --- | --- | --- |
| TUCR-000001 | 有符号 TINYINT 扩宽 | TINYINT -> SMALLINT | MIN/MAX/0/±1/MAX-1 | 二级索引 | 列类型 + 行数据 + 索引 |
| TUCR-000002 | 有符号 SMALLINT 扩宽 | SMALLINT -> MEDIUMINT | MIN/MAX/0/±1/MAX-1 | 唯一索引 | 唯一性 + 数据一致 |
| TUCR-000003 | 有符号 MEDIUMINT 扩宽 | MEDIUMINT -> INT | MIN/MAX/0/±1/MAX-1 | 组合索引 | 组合索引顺序 + 数据 |
| TUCR-000004 | 有符号 INT 扩宽 | INT -> BIGINT | MIN/MAX/0/±1/MAX-1 | 降序索引 | 降序索引 + 查询结果 |
| TUCR-000005 | 无符号 TINYINT 扩宽 | TINYINT UNSIGNED -> SMALLINT UNSIGNED | 0/1/MAX/MAX-1 | 二级索引 | 无符号边界 + 行数据 |
| TUCR-000006 | 无符号 SMALLINT 扩宽 | SMALLINT UNSIGNED -> INT UNSIGNED | 0/1/MAX/MAX-1 | 函数索引 | 函数索引表达式 + 数据 |
| TUCR-000007 | 无符号 MEDIUMINT 扩宽 | MEDIUMINT UNSIGNED -> INT UNSIGNED | 0/1/MAX/MAX-1 | 唯一索引 | 唯一性 + 边界值 |
| TUCR-000008 | 无符号 INT 扩宽 | INT UNSIGNED -> BIGINT UNSIGNED | 0/1/MAX/MAX-1 | 二级索引 | BIGINT UNSIGNED 边界 |
| TUCR-000009 | BIGINT 同类型控制组 | BIGINT -> BIGINT | MIN/MAX/0/±1 | 二级索引 | no-op DDL 后数据不变 |
| TUCR-000010 | BIGINT UNSIGNED 同类型控制组 | BIGINT UNSIGNED -> BIGINT UNSIGNED | 0/MAX | 二级索引 | no-op DDL 后数据不变 |
| TUCR-000011 | TINYINT 扩宽 + 表达式默认值 | TINYINT -> SMALLINT | 默认值触发插入 | 表达式默认值 | 默认值保留 + 数据一致 |
| TUCR-000012 | SMALLINT 扩宽 + 注释 | SMALLINT -> INT | 普通 + 边界值 | 列注释 | 注释保留 + 类型升级 |
| TUCR-000013 | INT 扩宽 + 不可见列 | INT -> BIGINT | 普通 + 边界值 | 不可见列 | 可见性保留 + 数据一致 |
| TUCR-000014 | TINYINT 扩宽 + FIRST | TINYINT -> SMALLINT | 普通 + 边界值 | FIRST 位置 | 列位置 + 数据一致 |
| TUCR-000015 | SMALLINT 扩宽 + AFTER id | SMALLINT -> INT | 普通 + 边界值 | AFTER id 位置 | 列位置 + 数据一致 |
| TUCR-000016 | INT 扩宽 + NOT NULL 无默认值 | INT -> BIGINT | 显式插入边界值 | NOT NULL 无默认值 | 属性保留 + 插入成功 |

### Decimal

| 用例ID | 场景 | 类型/对象 | 数据/边界 | 依赖/索引 | 验证点 |
| --- | --- | --- | --- | --- | --- |
| TUCR-000017 | 最小精度扩容 | DECIMAL(1,0) -> DECIMAL(2,0) | 0/±1/±9 | 二级索引 | 精度 + 数据 |
| TUCR-000018 | 常用精度扩容 | DECIMAL(5,2) -> DECIMAL(10,2) | ±99.99/0/1.23 | 二级索引 | 精度 + scale 不变 |
| TUCR-000019 | 中精度扩容 | DECIMAL(10,2) -> DECIMAL(18,2) | ±99999999.99 | 唯一索引 | 唯一性 + 精度 |
| TUCR-000020 | 高 scale 扩容 | DECIMAL(18,6) -> DECIMAL(28,6) | 高 scale 边界 | 二级索引 | scale 保持 + 数据 |
| TUCR-000021 | 更高 scale 扩容 | DECIMAL(28,10) -> DECIMAL(38,10) | 高 scale 边界 | 组合索引 | scale 保持 + 数据 |
| TUCR-000022 | 接近最大精度 | DECIMAL(38,18) -> DECIMAL(50,18) | 接近上限值 | 二级索引 | 精度扩容 + 数据 |
| TUCR-000023 | 达到最大精度 | DECIMAL(50,30) -> DECIMAL(65,30) | MAX/MIN/0 | 二级索引 | 最大精度边界 |
| TUCR-000024 | 最大精度 no-op | DECIMAL(65,30) -> DECIMAL(65,30) | MAX/MIN/0 | 二级索引 | no-op + 数据不变 |
| TUCR-000025 | 整数 DECIMAL 扩容 | DECIMAL(10,0) -> DECIMAL(20,0) | MAX/MIN/0 | 二级索引 | scale 0 + 数据 |
| TUCR-000026 | DECIMAL/NUMERIC 互转 | DECIMAL(18,6) -> NUMERIC(19,6) | 高 scale 边界 | 二级索引 | 别名归一化 + 数据 |

### BIT

| 用例ID | 场景 | 类型/对象 | 数据/边界 | 依赖/索引 | 验证点 |
| --- | --- | --- | --- | --- | --- |
| TUCR-000027 | BIT(1) 扩宽 | BIT(1) -> BIT(2) | 0/1/2/3 | 二级索引 | 位值 + 数据 |
| TUCR-000028 | BIT(2) 扩宽 | BIT(2) -> BIT(4) | 0/1/2/15 | 二级索引 | 位值 + 数据 |
| TUCR-000029 | BIT(4) 扩宽 | BIT(4) -> BIT(8) | 0/1/15/255 | 二级索引 | 位边界 + 数据 |
| TUCR-000030 | BIT(8) 扩宽 | BIT(8) -> BIT(16) | 0/255/65535 | 二级索引 | 位边界 + 数据 |
| TUCR-000031 | BIT(16) 扩宽 | BIT(16) -> BIT(24) | 0/65535/16777215 | 二级索引 | 位边界 + 数据 |
| TUCR-000032 | BIT(24) 扩宽 | BIT(24) -> BIT(32) | 0/16777215/4294967295 | 二级索引 | 位边界 + 数据 |
| TUCR-000033 | BIT(32) 扩宽 | BIT(32) -> BIT(40) | 0/4294967295/2^40-1 | 二级索引 | 位边界 + 数据 |
| TUCR-000034 | BIT(40) 扩宽 | BIT(40) -> BIT(48) | 0/2^40-1/2^48-1 | 二级索引 | 位边界 + 数据 |
| TUCR-000035 | BIT(48) 扩宽 | BIT(48) -> BIT(56) | 0/2^48-1/2^56-1 | 二级索引 | 位边界 + 数据 |
| TUCR-000036 | BIT(63) 到最大宽度 | BIT(63) -> BIT(64) | 0/2^63-1/2^64-1 | 二级索引 | 最大 BIT 边界 |

### Character

| 用例ID | 场景 | 类型/对象 | 数据/边界 | 依赖/索引 | 验证点 |
| --- | --- | --- | --- | --- | --- |
| TUCR-000037 | CHAR(0) 到 CHAR(1) | CHAR(0) -> CHAR(1) | ''/'a' | 二级索引 | 零长度语义 + 空串 |
| TUCR-000038 | CHAR(1) 扩长 | CHAR(1) -> CHAR(2) | 'a'/'ab' | 二级索引 | 定长补空格语义 |
| TUCR-000039 | CHAR(10) 扩长 | CHAR(10) -> CHAR(20) | 10/20 字符 | 唯一索引 | 定长 + 唯一性 |
| TUCR-000040 | CHAR(50) 扩长 | CHAR(50) -> CHAR(100) | 50/100 字符 | 二级索引 | 长度扩展 + 数据 |
| TUCR-000041 | CHAR(100) 扩长 | CHAR(100) -> CHAR(200) | 100/200 字符 | 组合索引 | 组合索引 + 数据 |
| TUCR-000042 | CHAR(255) 跨 256 | CHAR(255) -> VARCHAR(256) | 255/256 字符 | 二级索引 | 跨 255/256 + 定长变变长 |
| TUCR-000043 | VARCHAR(0) 到 VARCHAR(1) | VARCHAR(0) -> VARCHAR(1) | ''/'a' | 二级索引 | 零长度语义 |
| TUCR-000044 | VARCHAR(1) 扩长 | VARCHAR(1) -> VARCHAR(2) | 'a'/'ab' | 唯一索引 | 变长 + 唯一性 |
| TUCR-000045 | VARCHAR(10) 扩长 | VARCHAR(10) -> VARCHAR(20) | 10/20 字符 | 二级索引 | 变长 + 数据 |
| TUCR-000046 | VARCHAR(60) 扩长 | VARCHAR(60) -> VARCHAR(100) | 60/100 字符 | 前缀索引 | 前缀索引 + 数据 |
| TUCR-000047 | VARCHAR(255) 跨 256 | VARCHAR(255) -> VARCHAR(256) | 255/256 字符 | 唯一索引 | 跨 255/256 + 唯一性 |
| TUCR-000048 | VARCHAR(512) 扩长 | VARCHAR(512) -> VARCHAR(1024) | 512/1024 字符 | 二级索引 | 大长度 + 数据 |

### Binary

| 用例ID | 场景 | 类型/对象 | 数据/边界 | 依赖/索引 | 验证点 |
| --- | --- | --- | --- | --- | --- |
| TUCR-000049 | BINARY(0) 到 BINARY(1) | BINARY(0) -> BINARY(1) | x''/x'01' | 二级索引 | 零长度 + 定长补 0x00 |
| TUCR-000050 | BINARY(1) 扩长 | BINARY(1) -> BINARY(2) | x'01'/x'0102' | 二级索引 | 定长补零语义 |
| TUCR-000051 | BINARY(10) 扩长 | BINARY(10) -> BINARY(20) | 10/20 字节 | 唯一索引 | 定长 + 唯一性 |
| TUCR-000052 | BINARY(50) 扩长 | BINARY(50) -> BINARY(100) | 50/100 字节 | 二级索引 | 长度扩展 + 数据 |
| TUCR-000053 | BINARY(100) 扩长 | BINARY(100) -> BINARY(200) | 100/200 字节 | 组合索引 | 组合索引 + 数据 |
| TUCR-000054 | BINARY(255) 跨 256 | BINARY(255) -> VARBINARY(256) | 255/256 字节 | 二级索引 | 跨 255/256 + 定长变变长 |
| TUCR-000055 | VARBINARY(0) 到 VARBINARY(1) | VARBINARY(0) -> VARBINARY(1) | x''/x'01' | 二级索引 | 零长度 + 变长 |
| TUCR-000056 | VARBINARY(1) 扩长 | VARBINARY(1) -> VARBINARY(2) | x'01'/x'0102' | 唯一索引 | 变长 + 唯一性 |
| TUCR-000057 | VARBINARY(10) 扩长 | VARBINARY(10) -> VARBINARY(20) | 10/20 字节 | 二级索引 | 变长 + 数据 |
| TUCR-000058 | VARBINARY(60) 扩长 | VARBINARY(60) -> VARBINARY(100) | 60/100 字节 | 前缀索引 | 前缀索引 + 数据 |
| TUCR-000059 | VARBINARY(255) 跨 256 | VARBINARY(255) -> VARBINARY(256) | 255/256 字节 | 唯一索引 | 跨 255/256 + 唯一性 |
| TUCR-000060 | VARBINARY(512) 扩长 | VARBINARY(512) -> VARBINARY(1024) | 512/1024 字节 | 二级索引 | 大长度 + 数据 |

### TEXT/BLOB

| 用例ID | 场景 | 类型/对象 | 数据/边界 | 依赖/索引 | 验证点 |
| --- | --- | --- | --- | --- | --- |
| TUCR-000061 | TINYTEXT 升 TEXT | TINYTEXT -> TEXT | 短/中/255 字符 | 前缀索引 | TEXT 升级 + 数据 |
| TUCR-000062 | TEXT 升 MEDIUMTEXT | TEXT -> MEDIUMTEXT | 中/长值 | 前缀索引 | TEXT 升级 + 数据 |
| TUCR-000063 | MEDIUMTEXT 升 LONGTEXT | MEDIUMTEXT -> LONGTEXT | 长值 | 前缀索引 | 最大 TEXT + 数据 |
| TUCR-000064 | TINYBLOB 升 BLOB | TINYBLOB -> BLOB | 短/中/255 字节 | 前缀索引 | BLOB 升级 + 数据 |
| TUCR-000065 | BLOB 升 MEDIUMBLOB | BLOB -> MEDIUMBLOB | 中/长值 | 前缀索引 | BLOB 升级 + 数据 |
| TUCR-000066 | MEDIUMBLOB 升 LONGBLOB | MEDIUMBLOB -> LONGBLOB | 长值 | 前缀索引 | 最大 BLOB + 数据 |
| TUCR-000067 | VARCHAR 溢出到 TEXT | VARCHAR(16307) -> TEXT | 接近行宽上限 | 前缀索引 | 跨类型 + 行宽边界 |
| TUCR-000068 | VARBINARY 溢出到 BLOB | VARBINARY(65231) -> BLOB | 接近行宽上限 | 前缀索引 | 跨类型 + 行宽边界 |

### Zero-length

| 用例ID | 场景 | 类型/对象 | 数据/边界 | 依赖/索引 | 验证点 |
| --- | --- | --- | --- | --- | --- |
| TUCR-000069 | CHAR(0) 跨到 BINARY(1) | CHAR(0) -> BINARY(1) | '' -> x'00' | 二级索引 | 字符到二进制零长语义 |
| TUCR-000070 | BINARY(0) 跨到 CHAR(1) | BINARY(0) -> CHAR(1) | x'' -> '' | 二级索引 | 二进制到字符零长语义 |
| TUCR-000071 | VARCHAR(0) 跨到 CHAR(1) | VARCHAR(0) -> CHAR(1) | '' -> '' | 二级索引 | 变长到定长零长语义 |
| TUCR-000072 | VARBINARY(0) 跨到 BINARY(1) | VARBINARY(0) -> BINARY(1) | x'' -> x'00' | 二级索引 | 变长到定长零长语义 |
| TUCR-000073 | NCHAR(0) 到 NCHAR(1) | NCHAR(0) -> NCHAR(1) | ''/'a' | 二级索引 | NCHAR 零长度 |
| TUCR-000074 | NVARCHAR(0) 到 NVARCHAR(1) | NVARCHAR(0) -> NVARCHAR(1) | ''/'a' | 二级索引 | NVARCHAR 零长度 |
| TUCR-000075 | CHARACTER(0) 到 CHARACTER(1) | CHARACTER(0) -> CHARACTER(1) | ''/'a' | 二级索引 | 别名归一化 + 零长度 |
| TUCR-000076 | CHARACTER VARYING(0) 到 (1) | CHARACTER VARYING(0) -> CHARACTER VARYING(1) | ''/'a' | 二级索引 | 别名归一化 + 零长度 |
| TUCR-000077 | CHAR(0) 升 TEXT | CHAR(0) -> TEXT | ''/短文本 | 前缀索引 | 零长度到 TEXT |
| TUCR-000078 | BINARY(0) 升 BLOB | BINARY(0) -> BLOB | x''/短二进制 | 前缀索引 | 零长度到 BLOB |

### AutoIncrement/PK

| 用例ID | 场景 | 类型/对象 | 数据/边界 | 依赖/索引 | 验证点 |
| --- | --- | --- | --- | --- | --- |
| TUCR-000079 | TINYINT 主键自增扩宽 | TINYINT -> SMALLINT | 省略自增列插入 | PRIMARY KEY + AUTO_INCREMENT | 自增计数 + 数据 |
| TUCR-000080 | SMALLINT 主键自增扩宽 | SMALLINT -> INT | 省略自增列插入 | PRIMARY KEY + AUTO_INCREMENT | 自增计数 + 数据 |
| TUCR-000081 | MEDIUMINT 主键自增扩宽 | MEDIUMINT -> BIGINT | 省略自增列插入 | PRIMARY KEY + AUTO_INCREMENT | 自增计数 + 数据 |
| TUCR-000082 | INT 主键自增扩宽 | INT -> BIGINT | 省略自增列插入 | PRIMARY KEY + AUTO_INCREMENT | 自增计数 + 数据 |
| TUCR-000083 | BIGINT 主键自增 no-op | BIGINT -> BIGINT | 省略自增列插入 | PRIMARY KEY + AUTO_INCREMENT | no-op + 自增不回退 |
| TUCR-000084 | INT UNSIGNED 主键自增扩宽 | INT UNSIGNED -> BIGINT UNSIGNED | 省略自增列插入 | PRIMARY KEY + AUTO_INCREMENT | 无符号自增 + 数据 |

### Foreign key

| 用例ID | 场景 | 类型/对象 | 数据/边界 | 依赖/索引 | 验证点 |
| --- | --- | --- | --- | --- | --- |
| TUCR-000085 | SMALLINT FK RESTRICT | SMALLINT -> INT | 父子表各 10 行 | RESTRICT 外键 | FK 元数据 + 孤儿行 |
| TUCR-000086 | SMALLINT FK NO ACTION | SMALLINT -> INT | 父子表各 10 行 | NO ACTION 外键 | FK 元数据 + 孤儿行 |
| TUCR-000087 | MEDIUMINT FK CASCADE | MEDIUMINT -> BIGINT | 父子表各 10 行 | ON DELETE CASCADE | 级联删除 + 数据 |
| TUCR-000088 | INT FK SET NULL | INT -> BIGINT | 父子表各 10 行 | ON DELETE SET NULL | SET NULL + 数据 |
| TUCR-000089 | CHAR(10) FK RESTRICT | CHAR(10) -> CHAR(20) | 父子表各 10 行 | RESTRICT 外键 | 字符 FK + 孤儿行 |
| TUCR-000090 | VARCHAR(60) FK CASCADE | VARCHAR(60) -> VARCHAR(100) | 父子表各 10 行 | ON UPDATE CASCADE | 级联更新 + 数据 |
| TUCR-000091 | BINARY(10) FK RESTRICT | BINARY(10) -> BINARY(20) | 父子表各 10 行 | RESTRICT 外键 | 定长二进制 FK + 孤儿行 |
| TUCR-000092 | VARBINARY(10) FK SET NULL | VARBINARY(10) -> VARBINARY(20) | 父子表各 10 行 | ON DELETE SET NULL | 变长二进制 FK + 数据 |

### Dependencies

| 用例ID | 场景 | 类型/对象 | 数据/边界 | 依赖/索引 | 验证点 |
| --- | --- | --- | --- | --- | --- |
| TUCR-000093 | 虚拟生成列引用 base 列 | INT -> BIGINT | 普通 + 边界值 | VIRTUAL 生成列 | 生成列值 + 数据 |
| TUCR-000094 | STORED 生成列引用 base 列 | INT -> BIGINT | 普通 + 边界值 | STORED 生成列 | 生成列值 + 数据 |
| TUCR-000095 | 函数索引引用 base 列 | VARCHAR(60) -> VARCHAR(100) | 普通 + 边界值 | 函数索引 | 函数索引查询 + 数据 |
| TUCR-000096 | 视图引用 base 列 | DECIMAL(10,2) -> DECIMAL(18,2) | 普通 + 边界值 | 视图 | 视图查询 + 数据 |
| TUCR-000097 | 触发器引用 base 列 | VARBINARY(32) -> VARBINARY(128) | 普通 + 边界值 | 触发器 | 触发器写入 + 数据 |
| TUCR-000098 | 存储函数读取 base 列 | BIT(16) -> BIT(32) | 普通 + 边界值 | 存储函数 | 函数返回 + 数据 |
| TUCR-000099 | 存储过程写 base 列 | INT -> BIGINT | 普通 + 边界值 | 存储过程 | 过程写入 + 数据 |
| TUCR-000100 | Prepared Statement 引用 base 列 | VARCHAR(32) -> VARCHAR(128) | 普通 + 边界值 | Prepared Statement | 预编译查询 + 数据 |

### Table form

| 用例ID | 场景 | 类型/对象 | 数据/边界 | 依赖/索引 | 验证点 |
| --- | --- | --- | --- | --- | --- |
| TUCR-000101 | InnoDB DYNAMIC 行格式 | INT -> BIGINT | 普通 + 边界值 | DYNAMIC | 行格式 + 数据 |
| TUCR-000102 | InnoDB COMPACT 行格式 | VARCHAR(255) -> VARCHAR(256) | 255/256 字符 | COMPACT | 行格式 + 跨边界 |
| TUCR-000103 | InnoDB COMPRESSED 行格式 | VARBINARY(255) -> VARBINARY(256) | 255/256 字节 | COMPRESSED | 行格式 + 跨边界 |
| TUCR-000104 | InnoDB REDUNDANT 行格式 | CHAR(100) -> CHAR(200) | 100/200 字符 | REDUNDANT | 行格式 + 数据 |
| TUCR-000105 | RANGE 分区表 | INT -> BIGINT | 跨分区值 | RANGE 分区 | 分区统计 + 数据 |
| TUCR-000106 | LIST 分区表 | VARCHAR(64) -> VARCHAR(128) | 跨分区值 | LIST 分区 | 分区统计 + 数据 |
| TUCR-000107 | HASH 分区表 | SMALLINT -> INT | 跨分区值 | HASH 分区 | 分区统计 + 数据 |
| TUCR-000108 | KEY 分区表 | INT -> BIGINT | 跨分区值 | KEY 分区 | 分区统计 + 数据 |
| TUCR-000109 | MyISAM 引擎 | CHAR(16) -> CHAR(32) | 普通 + 边界值 | MyISAM | 引擎兼容 + 数据 |
| TUCR-000110 | MEMORY 引擎 | VARCHAR(63) -> VARCHAR(64) | 普通 + 边界值 | MEMORY | 引擎兼容 + 数据 |

### Chain/Stats

| 用例ID | 场景 | 类型/对象 | 数据/边界 | 依赖/索引 | 验证点 |
| --- | --- | --- | --- | --- | --- |
| TUCR-000111 | 连续升级 SMALLINT -> INT -> BIGINT | SMALLINT -> INT -> BIGINT | 普通 + 边界值 | 两步 ALTER | 最终状态 + 数据 |
| TUCR-000112 | 多列同时升级 | INT + VARCHAR + VARBINARY | 多列普通/边界值 | 一条 ALTER 多列 | 全列一致 |
| TUCR-000113 | 普通表统计信息更新 | INT -> BIGINT | 普通 + 边界值 | ANALYZE TABLE | 统计信息存在 + 非负 |
| TUCR-000114 | 索引统计信息更新 | SMALLINT -> INT | 普通 + 边界值 | 索引 + ANALYZE TABLE | 索引统计 + EXPLAIN |
| TUCR-000115 | 分区表统计信息更新 | VARCHAR(64) -> VARCHAR(128) | 跨分区值 | 分区 + ANALYZE TABLE | 分区统计 |
| TUCR-000116 | EXPLAIN 使用预期索引 | INT -> BIGINT | 普通 + 边界值 | 二级索引 | 执行计划 + 数据 |
| TUCR-000117 | 视图 + 触发器 + 函数 + 过程组合 | SMALLINT -> BIGINT | 普通 + 边界值 | 全依赖组合 | 所有依赖一致 |
| TUCR-000118 | 多列组合唯一索引 | INT + VARCHAR(60) | 多列普通/边界值 | 组合唯一索引 | 唯一性 + 数据 |
| TUCR-000119 | 多列组合前缀索引 | VARCHAR(255) + VARBINARY(255) | 多列普通/边界值 | 组合前缀索引 | 索引元数据 + 数据 |
| TUCR-000120 | 多列组合降序索引 | INT + VARCHAR(60) | 多列普通/边界值 | 组合降序索引 | 索引元数据 + 数据 |

## 备注

1. 上述 120 个用例覆盖了当前仓库中最核心的表级、列级、类型级、边界、依赖和算法因子。
2. 并发类场景（如 DDL 期间唯一键冲突、主键并发插入）和性能类场景（大表 300 秒扫描）不能通过单个 SQL 文件完成，因此不包含在这 120 个用例里。
3. 若你确认这份 120 个用例的设计，我下一步会生成对应的 SQL 文件、expected output 和审计报告。
