> ⚠️ **本文档的结论已过期，仅作历史留档，请勿直接引用其中的数字。**
> 唯一权威来源是 **`FIX_LOG.md`**（逐步修复与验证台账）与 **`test_gap_audit_20260923.md`**（原始审计）。
>
> 执行方式已变更，请按 `README.md` 的"如何运行"一节操作：
> - 不要再手工 `mysql < xxx.sql`：**8 个大文件只以 `.sql.gz` 存在**，直接喂给 mysql 客户端会失败；
>   用 `python3 run_tests.py --env internal`（自动解压、按用例切分、逐语句归因错误）
> - §7 "阿里云 RDS 测试结果摘要（已完成）68 项" 的口径已过期，见 `FIX_LOG.md`
> - 内网的 CHAR/VARCHAR 口径已通过**环境能力画像**表达：`ENV_PROFILES['internal'] = cross_only`
>   （同字节桶变更 INSTANT/INPLACE 均不支持，跨字节桶支持），可用 `--charvarchar-mode` 切换
>
> 当前套件规模：**37 个文件 / 10,731 个用例 / 用例 ID 全局唯一（重复 0）**；
> 阿里云 RDS MySQL 8.0.36 最近一次全量：**5,228/5,228 PASS**（19,530 条断言，0 FAIL / 0 ERROR / 0 MANUAL / 0 MISSING）。

# 内网RDS DDL秒级/在线修改列类型 测试执行指南

## 1. 测试环境要求

- 内网RDS MySQL 8.0 (支持DDL秒加能力)
- 所有功能开关默认开启
- 数据库: ddl_test (需提前创建)

## 2. 需要在内网验证的数据类型

阿里云RDS已验证通过的类型 (INSTANT+INPLACE均成功):
- 整数SIGNED: TINYINT/SMALLINT/MEDIUMINT/INT -> 更宽整数
- 整数UNSIGNED: 同上
- CHAR: 变长(同字符集)
- VARCHAR: 变长(跨pack-length边界)
- BINARY: 变长
- VARBINARY: 变长

阿里云RDS不支持，需在内网RDS验证的类型:
- DECIMAL: 精度扩展(M增大, D不变)
  - DECIMAL(10,2)->DECIMAL(12,2)
  - DECIMAL(1,0)->DECIMAL(2,0)
  - DECIMAL(1,1)->DECIMAL(2,1)
  - DECIMAL(64,30)->DECIMAL(65,30)
  - DECIMAL(18,0)->DECIMAL(20,0)
  - DECIMAL(31,30)->DECIMAL(33,30)
- TEXT: 子类型扩展
  - TINYTEXT->TEXT (跨255字节边界)
  - TEXT->MEDIUMTEXT (跨65535字节边界)
  - MEDIUMTEXT->LONGTEXT (跨16MB边界)
- BLOB: 子类型扩展
  - TINYBLOB->BLOB
  - BLOB->MEDIUMBLOB
  - MEDIUMBLOB->LONGBLOB
- BIT: 扩展
  - BIT(1)->BIT(8)
  - BIT(8)->BIT(16)
  - BIT(16)->BIT(32)
  - BIT(32)->BIT(64)

## 3. 执行命令

### 3.1 纯SQL验证套件 (基本功能验证)

```bash
cd /path/to/ddl_verify_20260919

# 生成SQL
python3 generate_test_sql.py

# 执行阿里云SQL (整数/CHAR/VARCHAR)
mysql -h <aliyun_host> -u root -p ddl_test < sql_aliyun/01_integer_signed_instant.sql

# 执行内网SQL (增强类型)
mysql -h <internal_host> -u root -p ddl_test < sql_internal/15_binary_inplace.sql
mysql -h <internal_host> -u root -p ddl_test < sql_internal/19_decimal_inplace.sql
mysql -h <internal_host> -u root -p ddl_test < sql_internal/21_text_instant.sql
mysql -h <internal_host> -u root -p ddl_test < sql_internal/23_blob_instant.sql
mysql -h <internal_host> -u root -p ddl_test < sql_internal/25_bit_instant.sql
```

### 3.2 并发DML验证套件

```bash
# 修改 concurrent_dml/run_concurrent_tests.py 中的 INTERNAL_CONFIG
# 然后执行:
python3 concurrent_dml/run_concurrent_tests.py --large-only --quick
```

### 3.3 大表DML验证 (5000万-1亿行)

```python
# 修改 LARGE_TABLE_TYPES 中的 row_count:
# 阿里云支持类型: 50_000_000 (5000万行)
# 增强类型(INPLACE重): 5_000_000 (500万行)

# 执行:
python3 concurrent_dml/run_concurrent_tests.py --large-only
```

## 4. 预期结果

### 内网RDS预期支持 (INSTANT + INPLACE):
| 类型 | INSTANT | INPLACE |
|------|---------|---------|
| DECIMAL扩展 | SUCCESS | SUCCESS |
| TEXT子类型扩展 | SUCCESS | SUCCESS |
| BLOB子类型扩展 | SUCCESS | SUCCESS |
| BIT扩展 | SUCCESS | SUCCESS |

### 需重点关注的边界值
| 类型 | 边界值 |
|------|--------|
| DECIMAL(64,30) | 最大精度, 34位整数+30位小数 |
| TINYTEXT->TEXT | 255字节边界 (inline->off-page) |
| TEXT->MEDIUMTEXT | 65535字节边界 |
| MEDIUMTEXT->LONGTEXT | 16MB边界 |
| BIT(1)->BIT(8) | 零填充方向风险 (b'1'应保持为1而非128) |
| BIT(8)->BIT(16) | 1字节->2字节存储变化 |

## 5. 风险点 (来自风险评估)

### BIT风险
- B1(高): 零填充方向 - BIT(1)->BIT(8)时值1应保持为1, 不应变为128
- B2(中): 存储字节数变化 - BIT(8)->BIT(16)行格式变化
- B3(中): INSTANT资格 - BIT不在原生MySQL INSTANT列表, 需验证RDS增强是否支持

### TEXT风险
- T1(高): 子类型边界 - TINYTEXT->TEXT时>255字节数据从inline迁移到off-page
- T2(高): INSTANT资格 - TEXT子类型扩展的INSTANT可能不迁移数据, 需查询旧行验证

### BLOB风险
- L1(高): Null字节完整性 - BLOB含0x00, 存储格式变化时必须保持
- L4(高): off-page迁移 - 255字节和256字节数据的存储格式变化

## 6. 大表测试参数建议

| 场景 | 行数 | DDL耗时预期 | DML线程数 |
|------|------|------------|----------|
| 阿里云支持类型(小DDL) | 5000万 | <30秒 | 8 |
| 增强类型INPLACE | 500万 | <60秒 | 8 |
| 增强类型INSTANT | 5000万 | <5秒 | 8 |

## 7. 阿里云RDS测试结果摘要 (已完成)

- 测试总数: 68
- PASS: 67 (1个TEXT-T-IP因索引前缀问题已修复)
- FAIL: 0
- 阿里云支持: INT/CHAR/VARCHAR/BINARY/VARBINARY (INSTANT+INPLACE)
- 阿里云不支持: DECIMAL/TEXT/BLOB/BIT (需内网验证)
- QPS影响: INSTANT无影响, INPLACE仅CHAR(254)->CHAR(255)有14.2%下降
- 数据正确性: 全部通过 (DualWrite Oracle对照 + NULL-safe行级对比)

## 8. 性能测试用例 (需单独执行)

以下用例在 run_concurrent_tests.py 的 Phase 1 中:
1. 表列数上限 - run_max_column_test()
2. 连续INSTANT性能 (10/30/50次) - run_consecutive_instant_test()
3. DDL Fuzz内存泄漏 (1000轮) - run_ddl_fuzz_test()
4. 连续ALTER链式升级 - run_consecutive_chain_test()
5. 多列同时升级 - run_multi_column_test()
6. 唯一键冲突优化 - run_unique_conflict_test()
7. 连续多轮DDL性能 - run_consecutive_ddl_perf_test()

执行命令:
```bash
python3 concurrent_dml/run_concurrent_tests.py  # 执行全部Phase 1-5
```
