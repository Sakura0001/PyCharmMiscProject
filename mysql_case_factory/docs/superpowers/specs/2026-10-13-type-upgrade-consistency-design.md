# MySQL 类型升级一致性测试设计

## 目标

构建一个 SQL 可直接执行的 MySQL 类型升级正确性测试套件，用同一份源结构、数据和后置 DML 比较 `COPY`、`INPLACE`、`INSTANT` 三种算法的最终结果。本地使用原生 MySQL 8.0.45 和 `ALGORITHM=COPY` 验证生成器、夹具和 Oracle；内网使用同一批 case ID 快速切换为 `INPLACE` 和 `INSTANT`。

## 范围

### 保留

- 整数：`TINYINT`、`SMALLINT`、`MEDIUMINT`、`INT`、`BIGINT`，覆盖 signed/unsigned 与所有安全扩宽方向。
- 精确数：`DECIMAL(p,s)` / `NUMERIC(p,s)`，覆盖多个标度，扩精度时保持标度不变。
- 字符：`CHAR`、`VARCHAR`、`TINYTEXT`、`TEXT`、`MEDIUMTEXT`、`LONGTEXT`，覆盖长度头、字符集和排序规则。
- 二进制：`BINARY`、`VARBINARY`、`TINYBLOB`、`BLOB`、`MEDIUMBLOB`、`LONGBLOB`，覆盖长度头、补零和原始字节。
- `BIT(M)`：宽度 1 到 64，至少覆盖十多个扩宽组合。
- 列属性：NULL/NOT NULL、默认值、表达式默认值、AUTO_INCREMENT、COMMENT、INVISIBLE、列位置。
- 索引：普通、唯一、主键、复合、前缀、降序、不可见、函数、生成列索引。
- 外键：父/子、单列/复合、自引用、多级、RESTRICT/CASCADE/SET NULL/NO ACTION。
- 依赖对象：视图、六类触发器、存储函数、存储过程、PREPARE。
- 表形态：普通表、临时表、RANGE/LIST/HASH/KEY 分区、行格式、INSTANT ALTER 历史。
- SQL mode：`STRICT_ALL_TABLES`、`STRICT_TRANS_TABLES`、`PAD_CHAR_TO_FULL_LENGTH`、`ANSI_QUOTES`、`NO_BACKSLASH_ESCAPES`。

### 删除

不生成或执行以下因子：

- `FLOAT`、`DOUBLE`、`REAL`
- `DATE`、`TIME`、`DATETIME`、`TIMESTAMP`、`YEAR`
- `ENUM`、`SET`
- JSON、空间类型、向量类型
- FULLTEXT、SPATIAL、JSON 多值索引
- `time_zone` 和所有时间相关 SQL mode / 默认值 / 表达式
- 升级、降级、备份恢复、PITR、崩溃注入、资源故障、主备切换、性能、管控 API、连接断开、取消重试

非目标 canary 列只保留 `BIGINT`、`VARCHAR(64)`、`VARBINARY(64)`、`DECIMAL(20,4)`。

## 四表差分模型

每个 case 使用四张表：

- `T_old`：旧结构源表，保存升级前状态。
- `T_ref`：直接按目标结构创建的参考表。
- `T_algo`：从旧结构出发执行指定算法的表。
- 辅助表：触发器 audit、外键父子表、函数索引或生成列所需对象。

执行顺序：

1. 创建旧结构、目标参考结构和算法表。
2. 装载同一份旧范围边界数据。
3. 对 `T_algo` 执行 `ALTER ... ALGORITHM=<profile>`。
4. 比较 `T_algo` 与 `T_ref` 的结构、数据和索引结果。
5. 对 `T_ref` 与 `T_algo` 执行同一份目标范围新数据 DML。
6. 再次比较数据、结构、索引、约束和依赖对象行为。
7. 执行负向 SQL，要求失败且旧态或新态保持完整。
8. 清理所有对象。

## 预期规则

- 正向安全扩宽：本地 `COPY`、内网 `INPLACE`、内网 `INSTANT` 均断言 DDL 成功。
- 负向不支持或非法转换：三个 profile 均断言 DDL 失败且状态不变。
- 负向数据写入：断言失败且已提交状态不被破坏。
- 成功 DDL 后必须同时满足结构、数据、索引、约束、依赖对象和后置写入校验。
- 内网如果 `INPLACE` 与 `INSTANT` 结果不同，默认判 `ALGORITHM_DIFF`。
- 不因本地 COPY 结果反推算法能力；profile 的成功/失败预期来自冻结的用例矩阵。
- 任何 SQL 自然触发进程崩溃均判 `FAIL_CRASH`，不能计为负向通过。

## 产物

所有生成产物放在 `mysql_case_factory/generated/type_upgrade_consistency/`：

- `cases.jsonl`：一行一个 case，包含因子、目标结构、数据、预期和清理信息。
- `manifest.json`：生成版本、profile、case 数、覆盖摘要和 SHA-256。
- `copy_suite.sql`：本地可执行的 COPY 全量 SQL。
- `inplace_suite.sql`：内网 INPLACE 全量 SQL。
- `instant_suite.sql`：内网 INSTANT 全量 SQL。
- `coverage.tsv`：因子覆盖审计。
- `local_results.json`：本地 COPY 执行结果。
- `local_summary.md`：本地验证摘要。

生成必须确定性：相同代码和因子目录重复生成时，除时间戳字段外，case 顺序、ID 和 SQL 字节必须一致。
