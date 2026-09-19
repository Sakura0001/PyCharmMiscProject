# RDS MySQL DDL 秒级/在线修改列类型 — 纯 SQL 验证测试套件

## 概述

本测试套件用于验证 RDS MySQL 8.0 的 INSTANT（秒级）和 INPLACE（在线）列类型修改功能。测试套件由 Python 生成器自动产生，覆盖所有支持的数据类型转换 × 全因子笛卡尔积（OFAT + 关键二元组）× 三种表类型（普通表 / 外键表 / 64种分区组合表）。通过 Oracle 对照表对比验证数据正确性。

## 测试环境

### 阿里云 RDS
- **实例**: `rm-uf65zzh9t461f8k64co.mysql.cn-shanghai.rds.aliyuncs.com:3306`
- **版本**: MySQL 8.0.36
- **数据库**: `ddl_test`
- **覆盖类型**: 整数（SIGNED/UNSIGNED）、CHAR、VARCHAR — INSTANT + INPLACE
- **测试结果**: ✅ **2014 用例全部通过 (100% Pass Rate)**

### 内网机器（增强类型）
- **覆盖类型**: BINARY、VARBINARY、DECIMAL、TEXT、BLOB、BIT — INSTANT + INPLACE
- **说明**: 需在内网环境执行，SQL 已生成在 `sql_internal/` 目录

## 测试结果汇总

### 阿里云 RDS（已验证）

| 文件 | 用例数 | PASS | FAIL | 耗时 |
|------|--------|------|------|------|
| 01_integer_signed_instant.sql | 290 | 290 | 0 | 307s |
| 02_integer_signed_inplace.sql | 340 | 340 | 0 | 376s |
| 03_integer_unsigned_instant.sql | 300 | 300 | 0 | 232s |
| 04_integer_unsigned_inplace.sql | 350 | 350 | 0 | 268s |
| 05_char_instant.sql | 93 | 93 | 0 | 74s |
| 06_char_inplace.sql | 108 | 108 | 0 | 75s |
| 07_varchar_instant.sql | 217 | 217 | 0 | 182s |
| 08_varchar_inplace.sql | 252 | 252 | 0 | 147s |
| 09_auto_increment_pk.sql | 40 | 40 | 0 | 15s |
| 10_special_patterns.sql | 8 | 8 | 0 | 4s |
| 11_fk_table.sql | 16 | 16 | 0 | 10s |
| **合计** | **2014** | **2014** | **0** | **1690s** |
| 12_partition_64.sql | ~3840 | 待运行 | — | — |

## 文件结构

```
outputs/ddl_verify_20260919/
├── README.md                          # 本文件
├── generate_test_sql.py               # Python SQL 生成器 (~1977行)
├── run_tests.py                       # Python 执行器 (~372行)
├── config.example.ini                 # MySQL 连接配置模板
├── risk_assessment.md                 # BIT/TEXT/BLOB 风险评估
├── expected_results.md                # 预期结果汇总
├── sql_aliyun/                        # 阿里云 RDS SQL 文件（12个文件）
│   ├── 01_integer_signed_instant.sql     # 整数SIGNED INSTANT
│   ├── 02_integer_signed_inplace.sql     # 整数SIGNED INPLACE
│   ├── 03_integer_unsigned_instant.sql   # 整数UNSIGNED INSTANT
│   ├── 04_integer_unsigned_inplace.sql   # 整数UNSIGNED INPLACE
│   ├── 05_char_instant.sql               # CHAR INSTANT
│   ├── 06_char_inplace.sql               # CHAR INPLACE
│   ├── 07_varchar_instant.sql             # VARCHAR INSTANT
│   ├── 08_varchar_inplace.sql             # VARCHAR INPLACE
│   ├── 09_auto_increment_pk.sql          # AUTO_INCREMENT主键
│   ├── 10_special_patterns.sql           # 特殊模式（连续ALTER、多列ALTER）
│   ├── 11_fk_table.sql                   # 外键表
│   └── 12_partition_64.sql              # 64种分区组合
├── sql_internal/                     # 内网增强类型 SQL 文件（15个文件）
│   ├── 15-26: BINARY/VARBINARY/DECIMAL/TEXT/BLOB/BIT 的 INSTANT+INPLACE
│   ├── 27_fk_table_enhanced.sql          # 增强类型外键表
│   ├── 28_special_patterns_enhanced.sql  # 增强类型特殊模式
│   └── 29_partition_64_enhanced.sql      # 增强类型64种分区
└── results/                          # 运行后生成
    ├── summary_aliyun.csv              # 阿里云结果汇总
    └── failures.log                    # 失败详情
```

## 类型转换矩阵（50条转换 × 2算法 = 100组合）

### 阿里云 RDS（30条转换）

| 类别 | 转换数 | INSTANT | INPLACE |
|------|--------|---------|---------|
| 整数 SIGNED | 10 | ✅ | ✅ |
| 整数 UNSIGNED | 10 | ✅ | ✅ |
| CHAR | 3 | ✅ | ✅ |
| VARCHAR | 7 | ✅ | ✅ |

### 内网增强类型（20条转换）

| 类别 | 转换数 | INSTANT | INPLACE |
|------|--------|---------|---------|
| BINARY | 2 | ❌预期FAIL | ✅ |
| VARBINARY | 2 | ❌预期FAIL | ✅ |
| DECIMAL | 6 | ❌预期FAIL | ✅ |
| TEXT | 3 | ✅ | ✅ |
| BLOB | 3 | ✅ | ✅ |
| BIT | 4 | ✅ | ✅ |

## 因子覆盖

| 因子 | 变化值 | 说明 |
|------|--------|------|
| row_format | DYNAMIC/COMPACT/REDUNDANT | 行格式 |
| primary_key | CLUSTERED/COMPOSITE_PK/NO_EXPLICIT_PK | 主键类型 |
| non_target_index | NONE/ONE_SECONDARY/MULTIPLE/UNIQUE/COMPOSITE_PREFIX | 非目标列索引 |
| target_position | FIRST/MIDDLE/LAST | 目标列位置 |
| target_attributes | NULL/NOT_NULL/CONSTANT_DEFAULT/NULL_DEFAULT/NOT_NULL_DEFAULT/INVISIBLE | 列属性 |
| data_scale | 0/1/100 | 数据规模 |
| data_distribution | TYPE_BOUNDARIES/UNIFORM/MONOTONIC | 数据分布 |
| null_ratio | ZERO/SINGLE/TEN_PERCENT/ALL | NULL比例 |
| dependencies | NONE/SECONDARY_INDEX/UNIQUE_INDEX/FOREIGN_KEY/CHECK | 依赖关系 |
| sql_mode | STRICT/非严格 | SQL模式 |

## Oracle 对照表验证逻辑

### 成功路径（ALTER 成功）
1. 创建原表（旧类型）→ 插入旧类型范围数据
2. 执行 ALTER（成功）→ 插入新类型范围 + 旧类型范围数据
3. 创建对照表（新类型）→ 插入相同数据
4. 使用 `<=>`（NULL-safe比较）对比原表和对照表

### 失败路径（ALTER 预期失败）
1. 创建原表（旧类型）→ 插入旧类型范围数据
2. 执行 ALTER（预期FAIL）→ 表保持旧类型
3. 插入新类型范围数据（部分INSERT失败）+ 旧类型范围数据
4. 创建对照表（旧类型）→ 插入相同数据
5. 对比原表和对照表（应完全一致）

## 使用方法

### 1. 配置连接
```bash
cp config.example.ini config.ini
# 编辑 config.ini 填入实际的数据库连接信息
```

### 2. 重新生成 SQL（可选）
```bash
python3 generate_test_sql.py
```

### 3. 执行测试
```bash
# 阿里云环境
python3 run_tests.py --env aliyun

# 内网环境
python3 run_tests.py --env internal

# 指定文件
python3 run_tests.py --env aliyun --files 01_integer_signed_instant.sql 02_integer_signed_inplace.sql

# 两个环境都跑
python3 run_tests.py --env both
```

### 4. 查看结果
```bash
cat results/summary_aliyun.csv
cat results/failures.log  # 如果有失败的话
```

## 关键发现

### CHECK 约束行为是类型相关的

在 Aliyun RDS MySQL 8.0.36 上验证发现：
- **CHAR/VARCHAR** 类型变更 + CHECK约束：ALTER 成功（INPLACE/INSTANT均可）
- **整数类型** 变更 + CHECK约束：ALTER 失败（ERROR 1845）

这说明 MySQL 对 CHECK 约束的处理依赖于列类型变更的方式，而非约束本身。

### UTF8 字符集在 information_schema 中的表示

MySQL 8.0 在 `information_schema.columns` 中将 `utf8` 存储为 `utf8mb3`，`utf8_bin` 存储为 `utf8mb3_bin`。测试中需要使用正确的名称进行验证。

### UNSIGNED 属性检查大小写敏感性

`information_schema.columns.column_type` 的 LIKE 比较是大小写敏感的，`column_type LIKE '%UNSIGNED%'` 不匹配 `smallint unsigned`。需使用小写 `%unsigned%`。

## 预计总用例数

- 阿里云: ~5,854 用例（11个常规文件 + 1个分区文件）
- 内网: ~10,260 用例（14个常规文件 + 1个分区文件）
- **总计**: ~16,114 用例，约 15-20 万条 SQL 语句
