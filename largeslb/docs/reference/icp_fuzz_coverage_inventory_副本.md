# ICP Fuzz 覆盖情况与语法清单

本文档按当前源码梳理 `icp-fuzz` 可生成和可记录的覆盖维度。范围包括数据规模、数据分布、表形态、类型集合、索引集合、谓词/查询语法、profile 行为、优化器对比方式、artifact 字段和当前验证状态。

说明：

- 本文以源码 registry 和生成器逻辑为准：`src/icp_fuzz/types.py`、`src/icp_fuzz/indexes.py`、`src/icp_fuzz/generator.py`、`src/icp_fuzz/streams.py`、`src/icp_fuzz/cli.py`。
- 仓库当前没有实际运行生成的 `artifacts/coverage.json`，因此这里描述的是“当前项目可覆盖/可生成的全集”，不是某一次 MySQL 运行已经命中的覆盖率。
- 行数单位均为“行”，不是“万行”。

## 1. 总览

| 维度 | 当前覆盖 |
| --- | --- |
| 默认数据量 | `1000`、`10000`、`100000` |
| `join-fuzz` 默认数据量 | `100000`、`150000`、`200000` |
| 表形态 | 8 类：ordinary、3 类 partition、foreign key、temporary、2 类 view |
| 类型集合 | `core` 32 个，`boundary` 10 个，`all` 42 个 |
| 索引集合 | `core` 8 个，`boundary` 7 个，`all` 15 个 |
| 数据分布集合 | `core` 5 个，`all` 12 个 |
| 访问模式 | `ref`、`range` |
| histogram 模式 | `none`、`update`、`drop`、`regenerate` |
| hint 模式 | `none`、`force`、`use`、`ignore`、`random` |
| 查询执行模式 | direct、prepared |
| join/subquery 形态 | `EXISTS`、`LEFT JOIN`、`RIGHT JOIN`、`IN (SELECT ...)` |
| 优化器对比 | stock ICP：`index_condition_pushdown=off/on`；内网：`icp_cost_based=off/on` |
| 当前单测验证 | `python3 -m pytest -q`：133 passed |

## 2. 数据规模

### 2.1 默认行数档位

| 场景 | 默认值 | 说明 |
| --- | --- | --- |
| 普通 run / smoke / ci / matrix / continuous / fuzz / icp-benefit-fuzz | `1000,10000,100000` | CLI 未传 `--row-buckets` 时使用 |
| `join-fuzz` | `100000,150000,200000` | CLI/Web 在 `join-fuzz` 下自动切换 |
| 最小允许行数 | `1000` | `parse_row_buckets()` 会拒绝小于 1000 的档位 |
| DML 批大小 | `10000` | 存储过程循环执行 `INSERT ... SELECT`，每轮最多插入 10000 行 |

### 2.2 join 辅表行数

`join-fuzz` 的主表使用 row bucket。辅表行数按主表行数派生，比例轮转：

| 比例 | 含义 |
| --- | --- |
| `0.5x` | 主表行数的一半 |
| `1x` | 与主表相同 |
| `2x` | 主表两倍 |

辅表 `parent_id` 始终指向已存在父表行：

```sql
MOD(n, parent_row_count) + 1
```

## 3. 数据装载方式

当前数据装载模式固定为：

```text
stored_procedure_insert_select
```

每个表都会生成一组 SQL：

```sql
DROP PROCEDURE IF EXISTS `load_<table>`;
CREATE PROCEDURE `load_<table>`()
BEGIN
  DECLARE v_offset BIGINT DEFAULT 0;
  WHILE v_offset < <row_count> DO
    INSERT INTO `<table>` (...)
    SELECT ...
    FROM <0..9999 sequence source>
    WHERE seq.n < LEAST(10000, <row_count> - v_offset);
    SET v_offset = v_offset + 10000;
  END WHILE;
END;
CALL `load_<table>`();
DROP PROCEDURE IF EXISTS `load_<table>`;
```

复现 SQL 中 `CREATE PROCEDURE` 会用 `DELIMITER //` 包住，避免大规模数据场景把超长 literal insert 文本传到客户端。

## 4. 表形态

| 表形态 | DDL/SQL 特征 | 备注 |
| --- | --- | --- |
| `ordinary` | `CREATE TABLE ... ENGINE=InnoDB` | 普通 InnoDB 主表 |
| `partition_range` | `PARTITION BY RANGE (id)`，分区 `p0/p1/pmax` | 查询附加 `id BETWEEN 1 AND 90000` |
| `partition_hash` | `PARTITION BY HASH (id) PARTITIONS 4` | 分区表 |
| `partition_key` | `PARTITION BY KEY (id) PARTITIONS 4` | 分区表 |
| `foreign_key` | 额外 parent 表、`FOREIGN KEY (parent_id) REFERENCES parent(id)` | 查询为 child 到 parent 的 `LEFT JOIN` |
| `temporary` | `CREATE TEMPORARY TABLE` | histogram 跳过 |
| `view_merge` | `CREATE ALGORITHM=MERGE VIEW` | 查询 view；hint 跳过；ICP plan validation 跳过 |
| `view_temptable` | `CREATE ALGORITHM=TEMPTABLE VIEW` | 查询 view；hint 跳过；ICP plan validation 跳过 |

分区兼容性：

- 分区表会跳过 spatial 类型。
- 分区表会跳过带 prefix index 的 text/blob 类型。
- 分区表会跳过 FULLTEXT、SPATIAL、functional JSON、JSON multi-valued index。

## 5. 表字段结构

### 5.1 普通 case 主表字段

普通 case 使用固定主列 `a/b/c`，三列类型通常相同；`icp-benefit-fuzz` 可让 `a/b/c` 混合不同类型。

| 字段 | 类型/生成方式 | 用途 |
| --- | --- | --- |
| `id` | `BIGINT NOT NULL AUTO_INCREMENT` | 主键、分区键 |
| `a` | 当前 TypeSpec 对应 SQL 类型 | leading/indexed column |
| `b` | 当前 TypeSpec 对应 SQL 类型 | indexed column |
| `c` | 当前 TypeSpec 对应 SQL 类型 | tail/indexed column |
| `*_jg` | JSON 类型时生成 stored generated INT 列 | JSON key 索引边界 |
| `s` | `VARCHAR(128) NULL` | LIKE 辅助谓词 |
| `nullable_col` | `INT NULL` | NULL 和返回列覆盖 |
| `payload` | `VARCHAR(255)` 或宽 payload `VARCHAR(2048)` | 回表/宽行覆盖 |
| `vbin` | `VARBINARY(32) NULL` | 辅助二进制列 |
| `d` | `DATE NULL` | 辅助日期列 |
| `ts` | `DATETIME NULL` | 辅助时间列 |
| `decv` | `DECIMAL(12,2) NULL` | 辅助 decimal 列 |
| `e` | `ENUM('alpha','beta','gamma','delta') NULL` | 辅助 enum 列 |
| `setv` | `SET('red','green','blue') NULL` | 辅助 set 列 |
| `txt` | `TEXT NULL` | 辅助 text 列 |
| `js` | `JSON NULL` | 辅助 JSON 列 |
| `vg` | virtual generated INT from `js.$.k` | virtual generated index 边界 |
| `parent_id` | `INT NULL` | foreign key/join 辅助列 |

### 5.2 fuzz case 主表字段

`fuzz` 和 `--icp-comparison` 会生成随机宽度复合索引，索引列名从 `a` 到 `h`，默认宽度范围为 `2..8`。

| 字段 | 类型/生成方式 |
| --- | --- |
| `id` | `BIGINT NOT NULL AUTO_INCREMENT` |
| `a`..`h` 中的前 N 列 | 每列从 fuzz type pool 随机选择 |
| `s` | `VARCHAR(128) NULL` |
| `nullable_col` | `INT NULL` |
| `payload` | `VARCHAR(255)` 或宽 payload `VARCHAR(2048)` |
| `vbin` | `VARBINARY(32) NULL` |
| `date_aux` | `DATE NULL` |
| `ts` | `DATETIME NULL` |
| `decv` | `DECIMAL(12,2) NULL` |
| `enum_aux` | `ENUM('alpha','beta','gamma','delta') NULL` |
| `setv` | `SET('red','green','blue') NULL` |
| `txt` | `TEXT NULL` |
| `js` | `JSON NULL` |
| `parent_id` | `INT NULL` |

### 5.3 join-fuzz 辅表字段

每个 join 辅表都有固定核心字段，并额外生成 1 到 3 个 filter columns。

| 字段 | 类型/生成方式 |
| --- | --- |
| `id` | `BIGINT NOT NULL AUTO_INCREMENT` |
| `parent_id` | `BIGINT NOT NULL` |
| `bucket` | `INT NOT NULL` |
| `marker` | `VARCHAR(32) NOT NULL` |
| `payload` | `VARCHAR(255) NOT NULL` |
| filter column | 从 `BIGINT`、`DECIMAL(12,2)`、`VARCHAR(64)`、`DATE`、`DATETIME` 中轮转 |

辅表索引：

- `PRIMARY KEY (id)`
- `KEY idx_<alias>_parent (parent_id)`
- `KEY idx_<alias>_bucket (bucket, marker)`
- 每个 filter column 都有单列索引 `KEY idx_<alias>_<column> (<column>)`

## 6. 数据分布集合

### 6.1 distribution set

| set | 成员 |
| --- | --- |
| `core` | `uniform`、`low_cardinality`、`hot_key`、`null_heavy`、`mixed_random` |
| `all` | core 全部 + `high_cardinality`、`correlated`、`anti_correlated`、`stale_histogram`、`wide_payload`、`icp_benefit_high`、`icp_benefit_extreme` |

### 6.2 分布语义

| 分布 | 生成语义 |
| --- | --- |
| `uniform` | 按 `MOD(n + salt, modulus)` 均匀生成 |
| `low_cardinality` | 值域压到最多 8 个不同值 |
| `hot_key` | 约 80% 行使用同一个热点值，其余按普通规则分布 |
| `null_heavy` | nullable 列约每 4 行产生一次 NULL；随机 literal 路径约 35% NULL |
| `mixed_random` | `a/b/c` 或 fuzz 索引列分别随机选择列级分布，避免所有列完全相同 |
| `high_cardinality` | 使用 `MOD(n * 17 + salt, modulus)` 拉高基数 |
| `correlated` | 多列随同一个 `n` 正相关变化 |
| `anti_correlated` | 使用反向 modulus 生成反相关 |
| `stale_histogram` | 先生成 histogram，再把偶数 `id` 行改成 hot-key skew，制造陈旧统计 |
| `wide_payload` | payload 变宽；普通 case loader payload 约 1024 字符，DDL 可到 `VARCHAR(2048)` |
| `icp_benefit_high` | leading 列约 5% 命中目标值，tail 列约 1/1000 命中目标值 |
| `icp_benefit_extreme` | leading 列约 20% 命中目标值，tail 列约 1/10000 命中目标值 |

### 6.3 列级分布

可记录到 coverage 的列级分布：

```text
uniform
low_cardinality
hot_key
null_heavy
high_cardinality
correlated
anti_correlated
```

ICP 专项内部还会使用：

| 内部分布 | 含义 |
| --- | --- |
| `icp_leading_5pct` | leading 列每 20 行约 1 行命中目标值 4 |
| `icp_leading_20pct` | leading 列每 5 行约 1 行命中目标值 4 |
| `icp_tail_rare` | tail 列每 1000 行约 1 行命中 6，1 行命中 7 |
| `icp_tail_ultra_rare` | tail 列每 10000 行约 1 行命中 6，1 行命中 7 |
| `icp_equal_selectivity` | leading/tail 都约 5% 命中目标值 |

宽 payload 分布集合：

```text
wide_payload
icp_benefit_high
icp_benefit_extreme
```

## 7. 类型覆盖

### 7.1 谓词操作符集合

| 操作符集合 | 成员 |
| --- | --- |
| numeric ops | `=`、`<=>`、`!=`、`<>`、`>`、`>=`、`<`、`<=`、`IN`、`BETWEEN`、`IS NULL`、`IS NOT NULL` |
| string ops | `=`、`<=>`、`!=`、`<>`、`IN`、`BETWEEN`、`LIKE`、`NOT LIKE`、`IS NULL`、`IS NOT NULL` |
| boundary ops | `boundary` |

### 7.2 core 常规类型，32 个

| name | SQL 类型 | family | category | predicate ops | histogram |
| --- | --- | --- | --- | --- | --- |
| `tinyint` | `TINYINT` | integer | numeric | numeric ops | yes |
| `tinyint_unsigned` | `TINYINT UNSIGNED` | integer | numeric | numeric ops | yes |
| `smallint` | `SMALLINT` | integer | numeric | numeric ops | yes |
| `smallint_unsigned` | `SMALLINT UNSIGNED` | integer | numeric | numeric ops | yes |
| `mediumint` | `MEDIUMINT` | integer | numeric | numeric ops | yes |
| `mediumint_unsigned` | `MEDIUMINT UNSIGNED` | integer | numeric | numeric ops | yes |
| `int` | `INT` | integer | numeric | numeric ops | yes |
| `int_unsigned` | `INT UNSIGNED` | integer | numeric | numeric ops | yes |
| `bigint` | `BIGINT` | integer | numeric | numeric ops | yes |
| `bigint_unsigned` | `BIGINT UNSIGNED` | integer | numeric | numeric ops | yes |
| `decimal` | `DECIMAL(12,2)` | decimal | numeric | numeric ops | yes |
| `decimal_unsigned` | `DECIMAL(12,2) UNSIGNED` | decimal | numeric | numeric ops | yes |
| `numeric` | `NUMERIC(14,4)` | decimal | numeric | numeric ops | yes |
| `numeric_unsigned` | `NUMERIC(14,4) UNSIGNED` | decimal | numeric | numeric ops | yes |
| `float` | `FLOAT` | float | numeric | numeric ops | yes |
| `double` | `DOUBLE` | float | numeric | numeric ops | yes |
| `real` | `REAL` | float | numeric | numeric ops | yes |
| `bit_32` | `BIT(32)` | bit | numeric | numeric ops | yes |
| `bit` | `BIT(64)` | bit | numeric | numeric ops | yes |
| `date` | `DATE` | temporal | temporal | numeric ops | yes |
| `time` | `TIME` | temporal | temporal | numeric ops | yes |
| `datetime` | `DATETIME` | temporal | temporal | numeric ops | yes |
| `timestamp` | `TIMESTAMP` | temporal | temporal | numeric ops | yes |
| `year` | `YEAR` | temporal | temporal | numeric ops | yes |
| `char` | `CHAR(255)` | string | string_binary | string ops | yes |
| `char_ascii` | `CHAR(255) CHARACTER SET ascii` | string | string_binary | string ops | yes |
| `varchar` | `VARCHAR(255)` | string | string_binary | string ops | yes |
| `varchar_utf8mb4` | `VARCHAR(255) CHARACTER SET utf8mb4` | string | string_binary | string ops | yes |
| `binary` | `BINARY(255)` | binary | string_binary | string ops | yes |
| `varbinary` | `VARBINARY(255)` | binary | string_binary | string ops | yes |
| `enum` | `ENUM('alpha','beta','gamma','delta')` | enum | string_binary | string ops | yes |
| `set` | `SET('red','green','blue')` | set | string_binary | string ops | yes |

### 7.3 boundary 边界类型，10 个

| name | SQL 类型 | family | category | predicate ops | histogram | prefix | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `tinytext` | `TINYTEXT` | string | string_binary | string ops | yes | 16 | text columns require prefix indexes |
| `text` | `TEXT` | string | string_binary | string ops | yes | 16 | text columns require prefix indexes |
| `mediumtext` | `MEDIUMTEXT` | string | string_binary | string ops | yes | 16 | text columns require prefix indexes |
| `longtext` | `LONGTEXT` | string | string_binary | string ops | yes | 16 | text columns require prefix indexes |
| `tinyblob` | `TINYBLOB` | binary | string_binary | string ops | no | 16 | blob columns require prefix indexes |
| `blob` | `BLOB` | binary | string_binary | string ops | no | 16 | blob columns require prefix indexes |
| `mediumblob` | `MEDIUMBLOB` | binary | string_binary | string ops | no | 16 | blob columns require prefix indexes |
| `longblob` | `LONGBLOB` | binary | string_binary | string ops | no | 16 | blob columns require prefix indexes |
| `json_generated` | `JSON` | json | json | numeric ops | no | none | JSON participates through stored generated key columns |
| `point` | `POINT` | spatial | spatial | boundary ops | no | none | spatial indexes are not ICP BTREE candidates；`NOT NULL` |

### 7.4 all 类型集合，42 个

`all = core + boundary`，完整成员：

```text
tinyint
tinyint_unsigned
smallint
smallint_unsigned
mediumint
mediumint_unsigned
int
int_unsigned
bigint
bigint_unsigned
decimal
decimal_unsigned
numeric
numeric_unsigned
float
double
real
bit_32
bit
date
time
datetime
timestamp
year
char
char_ascii
varchar
varchar_utf8mb4
tinytext
text
mediumtext
longtext
binary
varbinary
tinyblob
blob
mediumblob
longblob
enum
set
json_generated
point
```

### 7.5 fuzz type pool

`fuzz` 随机列类型池使用 `all` 中的这些 family：

```text
integer
decimal
float
bit
temporal
string
binary
enum
set
```

即 fuzz 随机列不会选择 `json` 和 `spatial` family。

## 8. 索引覆盖

### 8.1 core 索引，8 个

| name | key columns | family | hintable | expect ICP | 说明 |
| --- | --- | --- | --- | --- | --- |
| `idx_a_only` | `a` | btree | yes | yes | 单列普通 BTREE |
| `idx_ab_only` | `a,b` | btree | yes | yes | 双列普通 BTREE |
| `idx_a` | `a,c` | btree | yes | yes | 两列普通 BTREE |
| `idx_ab` | `a,b,c` | btree | yes | yes | 三列普通 BTREE |
| `idx_abc` | `a,b,c` | btree | yes | yes | 三列普通 BTREE，benefit 场景优先选择 |
| `idx_bac` | `b,a,c` | btree | yes | yes | alternate composite order |
| `idx_abc_desc` | `a,b DESC,c` | descending_btree | yes | yes | `b` 为 descending key part |
| `uniq_abc` | `a,b,c,id` | unique_btree | yes | yes | unique index；若 key columns 不含 `id`，DDL 追加 `id` 保证唯一 |

### 8.2 boundary 索引，7 个

| name | key columns / DDL | family | hintable | expect ICP | 说明 |
| --- | --- | --- | --- | --- | --- |
| `idx_abc_invisible` | `a,b,c INVISIBLE` | invisible_btree | no | no | invisible indexes are not optimizer candidates unless explicitly enabled |
| `idx_gc_stored` | `a_jg,c_jg` | stored_generated | yes | no | stored generated JSON key columns are tracked as ICP boundary coverage |
| `idx_vg_virtual` | `vg` | virtual_generated | yes | no | virtual generated column indexes are an ICP validation boundary |
| `idx_functional_json` | functional expression on `JSON_EXTRACT(a,'$.k')` | functional | no | no | functional indexes are an ICP validation boundary |
| `idx_json_mvi` | multi-valued expression on `JSON_EXTRACT(a,'$.tags')` | multi_valued | no | no | JSON multi-valued indexes are an ICP validation boundary |
| `fulltext_payload` | `FULLTEXT KEY (payload)` | fulltext | no | no | FULLTEXT access is outside ICP BTREE plan validation |
| `spatial_a` | `SPATIAL KEY (a)` | spatial | no | no | SPATIAL indexes are outside ICP BTREE plan validation |

### 8.3 all 索引集合，15 个

`all = core + boundary`，完整成员：

```text
idx_a_only
idx_ab_only
idx_a
idx_ab
idx_abc
idx_bac
idx_abc_desc
uniq_abc
idx_abc_invisible
idx_gc_stored
idx_vg_virtual
idx_functional_json
idx_json_mvi
fulltext_payload
spatial_a
```

### 8.4 fuzz 随机索引

`fuzz` / `--icp-comparison` 会生成随机宽度复合索引：

| 项 | 当前行为 |
| --- | --- |
| 可用列名 | `a,b,c,d,e,f,g,h` |
| 默认最大索引列数 | `8` |
| 实际宽度 | `2..max_index_columns` |
| prefix indexes | 对完整索引前缀逐级生成，例如 `idx_a_only`、`idx_ab_only`、`idx_abc_only` |
| full index | 完整宽度索引，例如 `idx_abcd` |
| index family | `random_width_btree` |

## 9. 查询与谓词覆盖

### 9.1 通用 WHERE 操作符

当前通用操作符集合：

```text
AND
OR
NOT
=
<=>
<>
!=
>
>=
<
<=
IN
NOT IN
BETWEEN
NOT BETWEEN
IS NULL
IS NOT NULL
LIKE
NOT LIKE
```

### 9.2 access pattern

| access pattern | 生成特征 |
| --- | --- |
| `ref` | leading key 使用 `=`、`<=>` 或 `IN`，tail column 叠加过滤 |
| `range` | leading key 使用 `BETWEEN`、`>= AND <=`、`>` 或 `<=`，tail column 叠加过滤 |

### 9.3 普通谓词样例集合

`PredicateGenerator.operator_samples()` 固定覆盖以下样例：

```sql
`a` = 4 AND `c` = 6
`a` = 4 OR `c` = 6
`a` = 4 AND NOT (`c` = 6)
`a` <=> 4 AND `c` <> 6
`a` != 4 AND `c` > 6
`a` >= 4 AND `c` < 9
`a` <= 4 AND `c` IN (1, 6, 9)
`a` BETWEEN 2 AND 4 AND `c` NOT IN (7, 8)
`a` NOT BETWEEN 8 AND 10 AND `c` IS NULL
`a` = 4 AND `c` IS NOT NULL
`a` = 4 AND `s` LIKE 'prefix%'
`a` = 4 AND `s` NOT LIKE 'skip%'
```

### 9.4 tail filter 扩展

tail column 可生成：

- 比较：`=`、`<=>`、`<>`、`!=`、`>`、`>=`、`<`、`<=`
- 集合：`IN (...)`、`NOT IN (...)`
- 范围：`BETWEEN ... AND ...`、`NOT BETWEEN ... AND ...`
- NULL：`IS NULL`、`IS NOT NULL`
- 字符串：`LIKE 'k000000%'`、`NOT LIKE 'k999999%'`
- 组合包装：`OR tail IS NULL`、`NOT (...)`、`AND s LIKE 'prefix%'`

### 9.5 ICP 专项谓词

| 参数 | 成员 | 生成行为 |
| --- | --- | --- |
| `predicate_pattern` | `random`、`ref_and_tail`、`range_and_tail` | `random` 在 ref/range 之间轮转 |
| `selectivity_profile` | `random`、`high_benefit`、`equal` | `random` 在 high_benefit/equal 之间轮转 |

具体谓词：

| 谓词形态 | SQL 形态 |
| --- | --- |
| `ref_and_tail` | leading column `= literal(4)` AND tail column `= literal(6)` |
| `range_and_tail` | leading column `BETWEEN literal(2) AND literal(40)` AND tail column `= literal(6)` |
| multi-tail 内部 helper | leading `=` AND middle `BETWEEN` AND tail `=`；当前普通 stream 未直接暴露为 CLI 参数 |

### 9.6 spatial 边界谓词

spatial 类型使用：

```sql
MBRContains(
  ST_GeomFromText('POLYGON((0 0,1000 0,1000 1000,0 1000,0 0))'),
  `a`
)
```

## 10. 查询形态

### 10.1 普通表/分区表/临时表/view

普通查询：

```sql
SELECT `payload`, `nullable_col`
FROM `<query_object>` [INDEX HINT]
WHERE (<predicate>[partition_filter])
```

`partition_range` 附加：

```sql
AND `id` BETWEEN 1 AND 90000
```

view 查询使用 view name，不加 index hint。

### 10.2 foreign key case

```sql
SELECT child.`payload`, child.`parent_id`
FROM `<child_table>` AS child [INDEX HINT]
LEFT JOIN `<parent_table>` AS parent
ON child.`parent_id` = parent.`id`
WHERE (<predicate>) AND (parent.`id` IS NULL OR parent.`id` >= 1)
```

### 10.3 fuzz probe 查询

每个 fuzz case 包含 1 条 seed query 和多条 probe query。

| 项 | 默认 |
| --- | --- |
| 普通 fuzz probe 数 | `100` |
| `join-fuzz` probe 数 | `20` |
| query execution mode | sequence 偶数 direct，奇数 prepared |
| probe term 数 | 每条 probe 1 到 4 个 term |
| connector | `AND` 或 `OR` |
| 可选包装 | term 多于 1 时，有概率 `NOT (...)` |
| cross-type literal | `NULL`、整数、负整数、decimal、字符串、date/datetime/time 字符串、hex、bit、bool、`CAST(... AS SIGNED/CHAR/DATE/DECIMAL)` |

### 10.4 join-fuzz 查询

`join-fuzz` 从 ICP benefit 主表 case 出发，再生成 2 到 4 张总表的 join 图。

| 项 | 当前行为 |
| --- | --- |
| 总表数 | `2..4`，包含 main |
| 辅表 alias | `j1`、`j2`、`j3` |
| 拓扑 | `chain` 或 `star`；两表时退化为 main -> j1 |
| join pattern | `exists`、`left_join`、`right_join`、`in_subquery` |
| plan target | `["main", base_table_name]`，继续聚焦主 ICP 表 |

join pattern 形态：

| pattern | SQL 形态 |
| --- | --- |
| `exists` | `WHERE main_predicate AND EXISTS (SELECT 1 FROM aux... WHERE join_edges AND aux_predicates)` |
| `left_join` | `FROM main LEFT JOIN aux... ON ... WHERE main_predicate AND aux_predicates` |
| `right_join` | 首个辅表 `RIGHT JOIN main`，后续辅表 `LEFT JOIN` |
| `in_subquery` | `WHERE main.id IN (SELECT first_aux.parent_id FROM aux... WHERE join_edges AND aux_predicates)` |

辅表 filter column 类型安全谓词：

| filter kind | 谓词 |
| --- | --- |
| integer | `alias.col BETWEEN low AND low + 50000` |
| decimal | `alias.col >= CAST(x AS DECIMAL(12,2))` |
| varchar | `alias.col LIKE '<alias>-%'` |
| date | `alias.col BETWEEN CAST('YYYY-MM-DD' AS DATE) AND CAST('YYYY-MM-DD' AS DATE)` |
| datetime | `alias.col >= CAST('YYYY-MM-DD HH:MM:SS' AS DATETIME)` |

## 11. Histogram 覆盖

| 模式 | 生成 SQL |
| --- | --- |
| `none` | 不生成 histogram SQL |
| `update` | `ANALYZE TABLE <table> UPDATE HISTOGRAM ON <columns> WITH <buckets> BUCKETS` |
| `drop` | `ANALYZE TABLE <table> DROP HISTOGRAM ON <columns>` |
| `regenerate` | 先 `DROP HISTOGRAM`，再 `UPDATE HISTOGRAM` |

候选 histogram 列：

```text
profile.index_column("a")
profile.index_column("c")
nullable_col
s
```

bucket 数：

- 75% 概率从 `8,16,32,64,128,256` 中选择。
- 25% 概率从 `1..1024` 中随机选择。

跳过规则：

- `histogram_support=False` 的类型跳过。
- temporary table 跳过。
- view 跳过。
- `stale_histogram` 如果原始模式为 `none` 或 `drop`，会强制改为 `update`，然后追加 post-histogram skew update。

## 12. Index Hint 覆盖

| hint mode | SQL |
| --- | --- |
| `none` | 不加 hint，让优化器自主选择 |
| `force` | `FORCE INDEX (<index>)` |
| `use` | `USE INDEX (<index>)` |
| `ignore` | `IGNORE INDEX (<index>)` |
| `random` | case 生成时解析成 `none/force/use/ignore` 之一 |

限制：

- 不可 hint 的索引不会生成 hint，例如 invisible、functional JSON、JSON MVI、FULLTEXT、SPATIAL。
- view 查询不生成 hint。

已有专项文档 `docs/index_hint_mode_sql_matrix.md` 覆盖了 40 个 hint SQL 生成组合，记录结果为 40/40 通过。

## 13. 优化器对比覆盖

| comparison | off mode | on mode | 用途 |
| --- | --- | --- | --- |
| `index-condition-pushdown` | `SET SESSION optimizer_switch='index_condition_pushdown=off'` | `SET SESSION optimizer_switch='index_condition_pushdown=on'` | 社区版 MySQL |
| `icp-cost-based` | `SET SESSION optimizer_switch='index_condition_pushdown=on,icp_cost_based=off'` | `SET SESSION optimizer_switch='index_condition_pushdown=on,icp_cost_based=on'` | 内网定制 MySQL |
| `auto` | 优先选择 stock ICP off/on | 优先选择 stock ICP off/on | 避免普通 MySQL 因缺少 `icp_cost_based` 失败 |

性能判定默认参数：

| 参数 | 默认值 |
| --- | --- |
| measurements | `5` |
| warmups | `1` |
| max regression ratio | `1.25` |
| min regression ms | `20.0` |
| join-fuzz max query seconds | `10.0` |

计时方式：

- 使用 `EXPLAIN ANALYZE FORMAT=TREE <SELECT>`。
- 提取 root iterator 的 `actual time`。
- prepared 模式会 `PREPARE` / `EXECUTE` 包装 `EXPLAIN ANALYZE` 语句。

## 14. Profile 覆盖

| profile | 当前代码行为 |
| --- | --- |
| `smoke` | `duration=0` 时走 `coverage_cases()`，默认 12 个 case，可用 `--max-cases` 限制 |
| `ci` | `duration=0` 时走 `coverage_cases()`，默认 96 个 case，可用 `--max-cases` 限制 |
| `matrix` | 枚举兼容组合：table shape × row bucket × access pattern × histogram mode × type spec × distribution × compatible index |
| `continuous` | 先生成最多 256 个 coverage cases，再进入 random cases；受 `duration` 控制 |
| `fuzz` | 直接持续生成 `make_fuzz_case()`；受 `duration` 或 `--max-cases` 控制 |
| `join-fuzz` | 直接持续生成 `make_join_fuzz_case()`；受 `duration` 或 `--max-cases` 控制 |
| `icp-benefit-fuzz` | 先跑 `icp_benefit_seed_cases()`，再跑 `icp_benefit_random_cases()` |

Profile 默认参数联动：

| profile | comparison | type_set | index_set | distribution_set | row_buckets | fuzz_probe_count | max_query_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 普通 profile | `index-condition-pushdown` | `core` | `core` | `core` | `1000,10000,100000` | `100` | unset |
| `icp-benefit-fuzz` | `icp-cost-based` | `all` | `all` | `all` | `1000,10000,100000` | `100` | unset |
| `join-fuzz` | `icp-cost-based` | `all` | `all` | `all` | `100000,150000,200000` | `20` | `10.0` |

## 15. Coverage Tracker 记录维度

每个 case 会向 `coverage.json` 记录以下维度：

```text
type_families
type_specs
index_specs
hint_modes
distributions
table_shapes
histogram_modes
query_shapes
join_patterns
predicate_ops
type_categories
index_families
row_buckets
column_distributions
```

其中：

- `query_shapes` 对应 access pattern：`ref`、`range`。
- `join_patterns` 仅 join-fuzz case 有值。
- `column_distributions` 记录每列最终使用的列级分布。

## 16. Artifact 与结果字段

每次 run 的主要产物：

| 文件/目录 | 内容 |
| --- | --- |
| `events.jsonl` | run/case/sql 生命周期事件 |
| `cases/<case_id>.json` | 单 case 元数据、结果摘要、路径，不内嵌完整 SQL |
| `results.jsonl` | 成功执行 case 的指标和覆盖字段 |
| `coverage.json` | 覆盖维度集合和 counts |
| `repro/<case_id>.sql` | 完整复现 SQL |
| `trace/<case_id>_on.json` / `_off.json` | optimizer trace |
| `problem_sql/<case_id>__<query_id>.sql` | 可疑且 ICP 相关的聚焦 SQL bundle |
| `failures.jsonl` | 执行错误结构化记录 |
| `errors/<case_id>.md` | 可疑/无效计划/执行错误的人类可读报告 |

`results.jsonl` / case bundle 会包含的关键 coverage 字段：

```text
case_id
table_shape
row_count
access_pattern
histogram_mode
data_type_profile
type_spec
type_family
type_category
index_spec
index_family
hint_mode
distribution
column_distributions
column_types
histogram_columns
predicate_ops
predicate_columns
expects_index_condition
available_index_specs
indexed_columns
indexed_column_types
index_width
probe_query_count
query_execution_mode
data_generation
insert_batch_size
```

join-fuzz 额外字段：

```text
join_pattern
join_table_count
join_topology
join_graph
table_row_counts
actual_table_row_counts
join_predicate_columns
```

性能/计划字段包括：

```text
comparison_mode
optimizer switch SQL
off/on EXPLAIN JSON
off/on EXPLAIN ANALYZE timing
handler deltas
chosen_key
possible_keys
access_type
rows_examined_per_scan
filtered
cost_info
index_condition
attached_condition
plan_diff
handler_read_ratio
row_ratio
cost_ratio
regression_ratio
time_saved_ms
speedup_ratio
icp_off_to_on_count
icp_plan_query_count
verdict
```

## 17. ICP Plan Validation 预期规则

`expects_index_condition=True` 的主要条件：

- index spec 本身 `icp_expected=True`。
- 类型属于 core 类型。
- 表形态不是 `view_merge` / `view_temptable`。

会跳过或标记为边界的情况：

- boundary index：invisible、generated、functional、MVI、FULLTEXT、SPATIAL 等。
- boundary type：text/blob prefix、JSON generated、spatial 等。
- view 查询。
- `range` + `enum/set` 会跳过 ICP plan validation。
- hint mode 非 none 但索引不可 hint 时，hint 会被跳过并记录 note。

## 18. 当前验证状态

最近一次本地验证命令：

```bash
python3 -m pytest -q
```

结果：

```text
133 passed in 18.45s
```

已有文档验证记录：

- `docs/frontend_full_test_report_2026-05-16.md`：UI 功能路径 9/9、SQL 生成矩阵 60/60、当时 Python 自动化测试 96/96。
- `docs/index_hint_mode_sql_matrix.md`：索引提示模式 SQL 生成组合 40/40。

