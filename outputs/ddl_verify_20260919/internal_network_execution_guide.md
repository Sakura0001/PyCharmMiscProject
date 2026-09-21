# RDS MySQL DDL 秒级/在线修改列类型 — 内网执行指南

> **文档日期**: 2026-09-21  
> **适用环境**: 内网增强版 MySQL 8.0（支持 DECIMAL/TEXT/BLOB/BIT 的 INPLACE/INSTANT）  
> **前置条件**: 所有功能开关默认开启（`innodb_instant_ddl_enabled=ON`, `rds_upgrade_datatype_instant_enable=ON`）

---

## 一、执行概述

### 1.1 为什么需要在内网执行

阿里云 RDS 8.0.36 上实测发现：

| 类型 | 阿里云 INSTANT | 阿里云 INPLACE | 说明 |
|------|---------------|---------------|------|
| BINARY/VARBINARY | ✅ 意外支持 | ✅ 支持 | 阿里云超出预期 |
| DECIMAL | ❌ 不支持 | ❌ 不支持 | **需内网验证** |
| TEXT/BLOB | ❌ 不支持 | ❌ 不支持 | **需内网验证** |
| BIT | ❌ 不支持 | ❌ 不支持 | **需内网验证** |

内网环境是增强版 MySQL，PRD 要求支持 DECIMAL/TEXT/BLOB/BIT 的 INPLACE rebuild 路径，因此这些类型必须在内网验证。

### 1.2 执行内容总览

| 序号 | 执行内容 | 文件/方式 | 用例数 | 预计耗时 |
|------|----------|-----------|--------|----------|
| A | SQL 验证套件（内网部分） | `sql_internal/*.sql` (15 文件) | 6,402 | 1-2 小时 |
| B | 并发 DML 测试（增强类型） | 修改 `run_concurrent_tests.py` 连接配置 | 34 | 20-30 分钟 |
| C | DECIMAL 边界专项测试 | `run_decimal_boundary_test()` | 1 组 | 2 分钟 |
| D | 大表 DML 测试（增强类型） | 修改 `run_large_table_test()` 列类型 | 1 | 30-60 分钟 |

**总计**: ~6,438 用例，预计 2-3.5 小时

---

## 二、执行前准备

### 2.1 修改连接配置

#### 方式一：修改 `run_concurrent_tests.py` 中的 `ALIYUN_CONFIG`

```python
# 文件: concurrent_dml/run_concurrent_tests.py 第 28-34 行
# 将 ALIYUN_CONFIG 修改为内网地址
ALIYUN_CONFIG = {
    'host': '<内网MySQL_IP>',        # ← 修改为内网地址
    'port': 3306,
    'user': 'root',
    'password': '<内网密码>',        # ← 修改为内网密码
    'database': 'ddl_test',
}
```

#### 方式二：修改 `config.ini`（用于 `run_tests.py` SQL 执行器）

```ini
# 文件: config.ini
[internal]
host = <内网MySQL_IP>      # ← 修改为内网地址
port = 3306
user = root
password = <内网密码>      # ← 修改为内网密码
database = ddl_test
```

### 2.2 确认功能开关

```sql
-- 在内网 MySQL 上执行，确认以下开关均为 ON
SHOW VARIABLES LIKE 'innodb_instant_ddl_enabled';
SHOW VARIABLES LIKE 'rds_upgrade_datatype_instant_enable';
SHOW VARIABLES LIKE 'innodb_inplace_alter_table_upgrade_datatype';
```

### 2.3 创建测试数据库

```sql
CREATE DATABASE IF NOT EXISTS ddl_test CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

### 2.4 确认 Python 环境

```bash
cd /Users/yuyu/PyCharmMiscProject/outputs/ddl_verify_20260919
python3 -c "import pymysql; print('pymysql OK')"
```

---

## 三、执行内容 A：SQL 验证套件（内网部分）

### 3.1 文件清单与用例数

| 序号 | 文件 | 类型 | 算法 | 用例数 | 预期结果 |
|------|------|------|------|--------|----------|
| 1 | `sql_internal/15_binary_inplace.sql` | BINARY(10)→BINARY(20), BINARY(40)→BINARY(80) | INPLACE | 68 | ✅ SUCCESS |
| 2 | `sql_internal/16_binary_instant.sql` | 同上 | INSTANT | 58 | ❌ FAIL（预期失败） |
| 3 | `sql_internal/17_varbinary_inplace.sql` | VARBINARY(20)→VARBINARY(40), VARBINARY(100)→VARBINARY(200) | INPLACE | 68 | ✅ SUCCESS |
| 4 | `sql_internal/18_varbinary_instant.sql` | 同上 | INSTANT | 58 | ❌ FAIL（预期失败） |
| 5 | `sql_internal/19_decimal_inplace.sql` | DECIMAL 多种精度扩展 | INPLACE | 204 | ✅ SUCCESS |
| 6 | `sql_internal/20_decimal_instant.sql` | 同上 | INSTANT | 174 | ❌ FAIL（预期失败） |
| 7 | `sql_internal/21_text_instant.sql` | TINYTEXT→TEXT→MEDIUMTEXT→LONGTEXT | INSTANT | 93 | ✅ SUCCESS（PRD要求） |
| 8 | `sql_internal/22_text_inplace.sql` | 同上 | INPLACE | 108 | ✅ SUCCESS |
| 9 | `sql_internal/23_blob_instant.sql` | TINYBLOB→BLOB→MEDIUMBLOB→LONGBLOB | INSTANT | 87 | ✅ SUCCESS（PRD要求） |
| 10 | `sql_internal/24_blob_inplace.sql` | 同上 | INPLACE | 102 | ✅ SUCCESS |
| 11 | `sql_internal/25_bit_instant.sql` | BIT(1)→BIT(8)→BIT(16)→BIT(32)→BIT(64) | INSTANT | 116 | ✅ SUCCESS（PRD要求） |
| 12 | `sql_internal/26_bit_inplace.sql` | 同上 | INPLACE | 136 | ✅ SUCCESS |
| 13 | `sql_internal/27_fk_table_enhanced.sql` | FK 表 BINARY/DECIMAL/TEXT/BLOB/BIT 列扩容 | INPLACE | 24 | ✅ SUCCESS（双侧）/ ❌ FAIL（单侧定长FK） |
| 14 | `sql_internal/28_special_patterns_enhanced.sql` | 连续ALTER/多列ALTER/虚拟列 | INPLACE | 4 | ✅ SUCCESS |
| 15 | `sql_internal/29_partition_64_enhanced.sql` | 64种分区策略 × 增强类型 | INPLACE/INSTANT | 5,120 | 非分区键列✅ / 分区键列❌ |

**合计**: 6,402 测试用例

### 3.2 执行命令

```bash
cd /Users/yuyu/PyCharmMiscProject/outputs/ddl_verify_20260919

# 使用 run_tests.py 执行所有内网 SQL 文件
python3 run_tests.py --env internal --dir sql_internal --output results/summary_internal.csv
```

或逐文件执行（便于调试）：

```bash
# 逐文件执行（每个文件独立，可并行或按需执行）
for f in sql_internal/*.sql; do
    echo "=== Executing $f ==="
    mysql -h<内网IP> -P3306 -uroot -p<密码> ddl_test --force < "$f" 2>&1 | tee -a results/internal_run.log
    echo "=== Done $f ==="
done
```

### 3.3 预期结果矩阵

| 类型 | INSTANT 预期 | INPLACE 预期 | 特殊说明 |
|------|-------------|-------------|----------|
| **BINARY** | ❌ FAIL | ✅ SUCCESS | INSTANT 预期不支持，INPLACE rebuild 支持 |
| **VARBINARY** | ❌ FAIL | ✅ SUCCESS | 同 BINARY |
| **DECIMAL** | ❌ FAIL | ✅ SUCCESS | D(标度)不变，仅 M(精度)增大 |
| **TEXT** | ✅ SUCCESS | ✅ SUCCESS | PRD 明确要求支持，跨子类型边界 (255→65535→16M) |
| **BLOB** | ✅ SUCCESS | ✅ SUCCESS | 同 TEXT，二进制版本 |
| **BIT** | ✅ SUCCESS | ✅ SUCCESS | PRD 明确要求支持，零填充方向风险重点关注 |

### 3.4 重点关注项

#### BINARY/VARBINARY
- INSTANT 预期 FAIL（不在秒级支持列表），但需测试以确认内网是否也意外支持
- INPLACE 预期 SUCCESS
- **FK 单侧拓宽**: 定长 BINARY FK 列单侧拓宽预期 FAIL（PRD规定拒绝）

#### DECIMAL
- 精度扩展: M 增大, D 不变 → ✅
- 标度变化: D 变化 → ❌ FAIL（PRD规定拒绝）
- 9 位编码边界: DECIMAL(9,2)→DECIMAL(10,2), DECIMAL(18,2)→DECIMAL(19,2), DECIMAL(38,2)→DECIMAL(39,2)
- 最大 M: DECIMAL(64,30)→DECIMAL(65,30)

#### TEXT/BLOB（高风险）
- **T1 风险**: TINYTEXT→TEXT 时 >255 字节数据从 inline 迁移到 off-page。INSTANT 仅改元数据，需验证旧数据查询正确
- **T2 风险**: TEXT 子类型扩展 INSTANT 是否真支持？若 INSTANT 仅改 metadata 但不迁移数据，查询旧行可能出错
- **L1/L4 风险**: BLOB 含 0x00 字节，存储格式变化时完整性必须保持
- **边界值**: 255/256/8101/8192/16000/32000/60000/65535/65536 字节全覆盖

#### BIT（高风险）
- **B1 风险（高）**: BIT(1)→BIT(8) 零填充方向。值 1 应变为 b'00000001'=1，若左填充(MSB方向)则变为 b'10000000'=128，数据全部损坏
  - 验证方法：插入值 1，ALTER 后查询应为 1 而非 128
- **B2 风险**: BIT(8)→BIT(16) 存储字节数变化（1→2字节），INPLACE rebuild 行格式变化
- **B3 风险**: BIT 是否在 INSTANT 列表中？若不支持但误放行，可能导致元数据与存储不一致

### 3.5 分区表特殊说明

`29_partition_64_enhanced.sql` 包含 5,120 用例，覆盖：

- 8 种一级分区 × 8 种二级分区 = 64 种策略组合
- 每种策略 × 每条类型转换 × 2 种情况（target 为分区键 / 非分区键）
- **分区键兼容性矩阵**：

| 策略 | 整数 | CHAR/VARCHAR | BINARY/VARBINARY | TEXT/BLOB | BIT | DECIMAL |
|------|------|-------------|-----------------|-----------|-----|---------|
| RANGE | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| RANGE COLS | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| LIST | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| LIST COLS | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| HASH | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| LIN HASH | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| KEY | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| LIN KEY | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

- target 为分区键列：预期 ALTER FAIL（PRD规定"不支持修改分区键包含的列"）
- 不支持该类型作为分区键的策略：建表即 FAIL，记录为 BUILD_FAIL
- target 为非分区键列：预期 SUCCESS

---

## 四、执行内容 B：并发 DML 测试（增强类型）

### 4.1 需要执行的测试用例（34 条）

以下是阿里云上 DDL 失败（预期 SUCCESS 但实际 FAIL）的用例，需在内网重新执行：

| 序号 | 测试 ID | 类型 | 算法 | 源类型 | 目标类型 | 阿里云结果 | 内网预期 |
|------|---------|------|------|--------|----------|-----------|----------|
| 1 | CD-DEC-102-INPLACE | DECIMAL | INPLACE | DECIMAL(10,2) | DECIMAL(12,2) | ❌ FAIL | ✅ SUCCESS |
| 2 | CD-DEC-180-INPLACE | DECIMAL | INPLACE | DECIMAL(18,0) | DECIMAL(20,0) | ❌ FAIL | ✅ SUCCESS |
| 3 | CD-DEC-6430-INPLACE | DECIMAL | INPLACE | DECIMAL(64,30) | DECIMAL(65,30) | ❌ FAIL | ✅ SUCCESS |
| 4 | CD-TEXT-T2T-INPLACE | TEXT | INPLACE | TINYTEXT | TEXT | ❌ FAIL | ✅ SUCCESS |
| 5 | CD-TEXT-T2T-INSTANT | TEXT | INSTANT | TINYTEXT | TEXT | ❌ FAIL | ✅ SUCCESS |
| 6 | CD-TEXT-T2M-INPLACE | TEXT | INPLACE | TEXT | MEDIUMTEXT | ❌ FAIL | ✅ SUCCESS |
| 7 | CD-TEXT-T2M-INSTANT | TEXT | INSTANT | TEXT | MEDIUMTEXT | (未完成) | ✅ SUCCESS |
| 8 | CD-TEXT-M2L-INPLACE | TEXT | INPLACE | MEDIUMTEXT | LONGTEXT | ❌ FAIL | ✅ SUCCESS |
| 9 | CD-TEXT-M2L-INSTANT | TEXT | INSTANT | MEDIUMTEXT | LONGTEXT | ❌ FAIL | ✅ SUCCESS |
| 10 | CD-BLOB-T2B-INPLACE | BLOB | INPLACE | TINYBLOB | BLOB | ❌ FAIL | ✅ SUCCESS |
| 11 | CD-BLOB-T2B-INSTANT | BLOB | INSTANT | TINYBLOB | BLOB | ❌ FAIL | ✅ SUCCESS |
| 12 | CD-BLOB-B2M-INPLACE | BLOB | INPLACE | BLOB | MEDIUMBLOB | ❌ FAIL | ✅ SUCCESS |
| 13 | CD-BLOB-B2M-INSTANT | BLOB | INSTANT | BLOB | MEDIUMBLOB | ❌ FAIL | ✅ SUCCESS |
| 14 | CD-BLOB-M2L-INPLACE | BLOB | INPLACE | MEDIUMBLOB | LONGBLOB | (未完成) | ✅ SUCCESS |
| 15 | CD-BLOB-M2L-INSTANT | BLOB | INSTANT | MEDIUMBLOB | LONGBLOB | ❌ FAIL | ✅ SUCCESS |
| 16 | CD-BIT-1to8-INPLACE | BIT | INPLACE | BIT(1) | BIT(8) | ❌ FAIL | ✅ SUCCESS |
| 17 | CD-BIT-1to8-INSTANT | BIT | INSTANT | BIT(1) | BIT(8) | ❌ FAIL | ✅ SUCCESS |
| 18 | CD-BIT-8to16-INPLACE | BIT | INPLACE | BIT(8) | BIT(16) | ❌ FAIL | ✅ SUCCESS |
| 19 | CD-BIT-8to16-INSTANT | BIT | INSTANT | BIT(8) | BIT(16) | ❌ FAIL | ✅ SUCCESS |
| 20 | CD-BIT-16to32-INPLACE | BIT | INPLACE | BIT(16) | BIT(32) | (未完成) | ✅ SUCCESS |
| 21 | CD-BIT-16to32-INSTANT | BIT | INSTANT | BIT(16) | BIT(32) | ❌ FAIL | ✅ SUCCESS |
| 22 | CD-BIT-32to64-INPLACE | BIT | INPLACE | BIT(32) | BIT(64) | ❌ FAIL | ✅ SUCCESS |
| 23 | CD-BIT-32to64-INSTANT | BIT | INSTANT | BIT(32) | BIT(64) | ❌ FAIL | ✅ SUCCESS |

以下是 BINARY/VARBINARY 的 INSTANT 测试（阿里云意外支持，内网需确认）：

| 序号 | 测试 ID | 类型 | 算法 | 源类型 | 目标类型 | 阿里云结果 | 内网预期 |
|------|---------|------|------|--------|----------|-----------|----------|
| 24 | CD-BIN-10-INPLACE | BINARY | INPLACE | BINARY(10) | BINARY(20) | ✅ SUCCESS | ✅ SUCCESS |
| 25 | CD-BIN-10-INSTANT | BINARY | INSTANT | BINARY(10) | BINARY(20) | ✅ (意外) | ❌ FAIL 或 ✅ |
| 26 | CD-BIN-40-INPLACE | BINARY | INPLACE | BINARY(40) | BINARY(80) | ✅ SUCCESS | ✅ SUCCESS |
| 27 | CD-BIN-40-INSTANT | BINARY | INSTANT | BINARY(40) | BINARY(80) | ✅ (意外) | ❌ FAIL 或 ✅ |
| 28 | CD-VBIN-20-INPLACE | VARBINARY | INPLACE | VARBINARY(20) | VARBINARY(40) | ✅ SUCCESS | ✅ SUCCESS |
| 29 | CD-VBIN-20-INSTANT | VARBINARY | INSTANT | VARBINARY(20) | VARBINARY(40) | ✅ (意外) | ❌ FAIL 或 ✅ |
| 30 | CD-VBIN-100-INPLACE | VARBINARY | INPLACE | VARBINARY(100) | VARBINARY(200) | ✅ SUCCESS | ✅ SUCCESS |
| 31 | CD-VBIN-100-INSTANT | VARBINARY | INSTANT | VARBINARY(100) | VARBINARY(200) | ✅ (意外) | ❌ FAIL 或 ✅ |

以下是 DECIMAL INSTANT 测试（预期 FAIL，确认内网行为一致）：

| 序号 | 测试 ID | 类型 | 算法 | 源类型 | 目标类型 | 阿里云结果 | 内网预期 |
|------|---------|------|------|--------|----------|-----------|----------|
| 32 | CD-DEC-102-INSTANT | DECIMAL | INSTANT | DECIMAL(10,2) | DECIMAL(12,2) | ❌ FAIL_EXPECTED | ❌ FAIL |
| 33 | CD-DEC-180-INSTANT | DECIMAL | INSTANT | DECIMAL(18,0) | DECIMAL(20,0) | ❌ FAIL_EXPECTED | ❌ FAIL |
| 34 | CD-DEC-6430-INSTANT | DECIMAL | INSTANT | DECIMAL(64,30) | DECIMAL(65,30) | ❌ FAIL_EXPECTED | ❌ FAIL |

### 4.2 执行命令

修改 `run_concurrent_tests.py` 中的 `ALIYUN_CONFIG` 为内网地址后：

```bash
cd /Users/yuyu/PyCharmMiscProject/outputs/ddl_verify_20260919/concurrent_dml

# 执行全部 89 个测试（含增强类型在内网上的结果）
python3 -u run_concurrent_tests.py 2>&1 | tee results/run_internal.log
```

或仅执行增强类型部分（如需跳过已验证的 INT/CHAR/VARCHAR）：

```bash
# 可选：注释掉 main() 中 Phase 2 的 ALIYUN_TYPES 部分，仅保留 ENHANCED_TYPES
# 然后执行
python3 -u run_concurrent_tests.py 2>&1 | tee results/run_internal_enhanced.log
```

### 4.3 预期结果

| 类型 | INSTANT | INPLACE | 并发 DML 一致性 |
|------|---------|---------|----------------|
| BINARY | ❌ FAIL（或 ✅ 如果内网也支持） | ✅ SUCCESS | ✅ PASS |
| VARBINARY | ❌ FAIL（或 ✅） | ✅ SUCCESS | ✅ PASS |
| DECIMAL | ❌ FAIL | ✅ SUCCESS | ✅ PASS |
| TEXT | ✅ SUCCESS | ✅ SUCCESS | ✅ PASS |
| BLOB | ✅ SUCCESS | ✅ SUCCESS | ✅ PASS |
| BIT | ✅ SUCCESS | ✅ SUCCESS | ✅ PASS |

---

## 五、执行内容 C：DECIMAL 边界专项测试

### 5.1 测试内容

`run_concurrent_tests.py` 中的 `run_decimal_boundary_test()` 函数测试 DECIMAL 9 位编码边界：

| 转换 | 说明 | 预期 |
|------|------|------|
| DECIMAL(9,2) → DECIMAL(10,2) | 跨 9 位编码边界 | INPLACE ✅ |
| DECIMAL(18,2) → DECIMAL(19,2) | 跨 18 位编码边界 | INPLACE ✅ |
| DECIMAL(38,2) → DECIMAL(39,2) | 跨 38 位编码边界 | INPLACE ✅ |

### 5.2 执行说明

此测试已包含在 `run_concurrent_tests.py` 的 Phase 1 中（测试 ID: `DECIMAL_BOUNDARY`）。在内网执行时，这些测试预期从 FAIL 变为 SUCCESS。

---

## 六、执行内容 D：大表 DML 测试（增强类型）

### 6.1 测试方案

在内网大表上使用增强类型进行 INPLACE DDL + 并发 DML 测试：

| 类型 | DDL 操作 | 数据量 | 预期 DDL | 预期 DML |
|------|----------|--------|---------|---------|
| DECIMAL | `ALTER TABLE t MODIFY c1 DECIMAL(12,2), ALGORITHM=INPLACE` | 5000万+ | ✅ | ✅ |
| TEXT | `ALTER TABLE t MODIFY c1 TEXT, ALGORITHM=INPLACE` | 5000万+ | ✅ | ✅ |
| BLOB | `ALTER TABLE t MODIFY c1 BLOB, ALGORITHM=INPLACE` | 5000万+ | ✅ | ✅ |
| BIT | `ALTER TABLE t MODIFY c1 BIT(8), ALGORITHM=INPLACE` | 5000万+ | ✅ | ✅ |

### 6.2 修改方法

修改 `run_concurrent_tests.py` 中的 `run_large_table_test()` 函数：

```python
# 修改建表语句中的列类型
exec_sql(conn, 'CREATE TABLE t_large (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, c1 DECIMAL(10,2), c2 VARCHAR(50), KEY idx_c1(c1)) ROW_FORMAT=DYNAMIC')
exec_sql(conn, 'CREATE TABLE t_large_oracle (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, c1 DECIMAL(12,2), c2 VARCHAR(50), KEY idx_c1(c1)) ROW_FORMAT=DYNAMIC')

# 修改 ALTER 语句
exec_sql(conn, 'ALTER TABLE t_large MODIFY c1 DECIMAL(12,2), ALGORITHM=INPLACE')

# 修改 DML worker 中的值生成逻辑以适配 DECIMAL 类型
```

### 6.3 重点关注

- **TEXT/BLOB 大表**: 大量 TEXT/BLOB 数据可能导致行溢出到 off-page，INPLACE rebuild 期间 off-page 数据迁移正确性
- **BIT 大表**: BIT 类型 INPLACE rebuild 期间零填充方向在大数据量下的正确性
- **DECIMAL 大表**: DECIMAL 编码变化在大数据量下的正确性

---

## 七、执行步骤总结

### 7.1 完整执行流程

```bash
# ====== 步骤 1: 配置修改 ======
cd /Users/yuyu/PyCharmMiscProject/outputs/ddl_verify_20260919

# 修改 concurrent_dml/run_concurrent_tests.py 中的 ALIYUN_CONFIG
# 修改 config.ini 中的 [internal] 配置

# ====== 步骤 2: 确认环境 ======
python3 -c "
import pymysql
c = pymysql.connect(host='<内网IP>', port=3306, user='root', password='<密码>', database='ddl_test')
cur = c.cursor()
cur.execute('SELECT VERSION()')
print('MySQL版本:', cur.fetchone())
cur.execute(\"SHOW VARIABLES LIKE 'innodb_instant_ddl_enabled'\")
print('INSTANT开关:', cur.fetchone())
cur.execute(\"SHOW VARIABLES LIKE 'rds_upgrade_datatype_instant_enable'\")
print('类型升级开关:', cur.fetchone())
c.close()
"

# ====== 步骤 3: 执行 SQL 验证套件 ======
python3 run_tests.py --env internal --dir sql_internal --output results/summary_internal.csv 2>&1 | tee results/internal_sql_run.log

# ====== 步骤 4: 执行并发 DML 测试 ======
cd concurrent_dml
python3 -u run_concurrent_tests.py 2>&1 | tee results/run_internal.log

# ====== 步骤 5: 检查结果 ======
# 检查 SQL 验证结果
cat ../results/summary_internal.csv | head -20
echo "---"
# 检查并发 DML 结果
cat results/concurrent_summary.csv | head -20

# ====== 步骤 6: 对比阿里云结果 ======
# DECIMAL/TEXT/BLOB/BIT 的 INPLACE 应从 FAIL 变为 SUCCESS
# BINARY/VARBINARY 的 INSTANT 需确认是否与阿里云一致
```

### 7.2 预期差异（阿里云 vs 内网）

| 类型 | 算法 | 阿里云 | 内网预期 | 变化 |
|------|------|--------|---------|------|
| DECIMAL | INPLACE | ❌ FAIL | ✅ SUCCESS | 🔄 需验证 |
| TEXT | INPLACE | ❌ FAIL | ✅ SUCCESS | 🔄 需验证 |
| TEXT | INSTANT | ❌ FAIL | ✅ SUCCESS | 🔄 需验证 |
| BLOB | INPLACE | ❌ FAIL | ✅ SUCCESS | 🔄 需验证 |
| BLOB | INSTANT | ❌ FAIL | ✅ SUCCESS | 🔄 需验证 |
| BIT | INPLACE | ❌ FAIL | ✅ SUCCESS | 🔄 需验证 |
| BIT | INSTANT | ❌ FAIL | ✅ SUCCESS | 🔄 需验证 |
| BINARY | INSTANT | ✅ (意外) | ❌ 或 ✅ | ❓ 需确认 |
| VARBINARY | INSTANT | ✅ (意外) | ❌ 或 ✅ | ❓ 需确认 |

---

## 八、结果检查清单

### 8.1 SQL 验证套件

执行后检查 `results/summary_internal.csv`：

- [ ] BINARY INPLACE: 68 用例全 PASS
- [ ] BINARY INSTANT: 58 用例全 FAIL（预期失败，表状态保持）
- [ ] VARBINARY INPLACE: 68 用例全 PASS
- [ ] VARBINARY INSTANT: 58 用例全 FAIL（预期失败）
- [ ] DECIMAL INPLACE: 204 用例全 PASS
- [ ] DECIMAL INSTANT: 174 用例全 FAIL（预期失败）
- [ ] TEXT INSTANT: 93 用例全 PASS（PRD要求支持）
- [ ] TEXT INPLACE: 108 用例全 PASS
- [ ] BLOB INSTANT: 87 用例全 PASS（PRD要求支持）
- [ ] BLOB INPLACE: 102 用例全 PASS
- [ ] BIT INSTANT: 116 用例全 PASS（PRD要求支持）
- [ ] BIT INPLACE: 136 用例全 PASS
- [ ] FK 表增强: 24 用例符合预期（双侧✅/单侧定长FK❌）
- [ ] 特殊模式增强: 4 用例全 PASS
- [ ] 分区表增强: 5,120 用例符合预期（非分区键✅/分区键❌/不支持类型建表❌）

### 8.2 并发 DML 测试

执行后检查 `concurrent_dml/results/concurrent_summary.csv`：

- [ ] DECIMAL INPLACE: DDL SUCCESS + 验证 PASS
- [ ] TEXT INPLACE: DDL SUCCESS + 验证 PASS
- [ ] TEXT INSTANT: DDL SUCCESS + 验证 PASS
- [ ] BLOB INPLACE: DDL SUCCESS + 验证 PASS
- [ ] BLOB INSTANT: DDL SUCCESS + 验证 PASS
- [ ] BIT INPLACE: DDL SUCCESS + 验证 PASS
- [ ] BIT INSTANT: DDL SUCCESS + 验证 PASS
- [ ] BIT(1)→BIT(8) 零填充方向: 值1 ALTER后仍为1（非128）
- [ ] TEXT TINYTEXT→TEXT: >255字节数据 inline→off-page 迁移正确
- [ ] BLOB TINYBLOB→BLOB: 0x00 字节完整性保持

### 8.3 性能测试

- [ ] DECIMAL 边界: DDL 成功
- [ ] 大表 DECIMAL/TEXT/BLOB/BIT INPLACE: DDL 成功 + DML 不中断 + CHECKSUM 一致

---

## 九、文件清单

### 9.1 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `concurrent_dml/run_concurrent_tests.py` | `ALIYUN_CONFIG` 改为内网地址 |
| `config.ini` | `[internal]` 配置改为内网地址 |

### 9.2 需要执行的文件

| 文件 | 说明 |
|------|------|
| `sql_internal/*.sql` (15 文件) | 纯 SQL 测试用例，通过 `run_tests.py` 或 `mysql` CLI 执行 |
| `concurrent_dml/run_concurrent_tests.py` | Python 并发 DML 测试框架 |
| `run_tests.py` | SQL 执行器 |

### 9.3 结果输出文件

| 文件 | 说明 |
|------|------|
| `results/summary_internal.csv` | SQL 验证结果汇总 |
| `results/internal_sql_run.log` | SQL 执行日志 |
| `concurrent_dml/results/concurrent_summary.csv` | 并发 DML 结果汇总（覆盖阿里云版本） |
| `concurrent_dml/results/concurrent_detailed.json` | 并发 DML 详细结果 |
| `concurrent_dml/results/run_internal.log` | 并发 DML 执行日志 |

---

## 十、风险评估与注意事项

### 10.1 BIT 零填充方向（最高风险）

**风险**: BIT(1)→BIT(8) 时，值 1 应变为 b'00000001'（右侧填充，值仍为1）。若实现错误为左填充(MSB方向)，值变为 b'10000000'=128，导致全部数据损坏。

**验证方法**：
1. 建表 `CREATE TABLE t (id INT PK, c1 BIT(1))`
2. 插入 `INSERT INTO t VALUES (1, 1)` — 值为 b'1'
3. `ALTER TABLE t MODIFY c1 BIT(8), ALGORITHM=INPLACE`
4. `SELECT c1 FROM t WHERE id=1` — 应返回 1（非 128）
5. 创建对照表 `CREATE TABLE t2 (id INT PK, c1 BIT(8))`
6. `INSERT INTO t2 VALUES (1, 1)`
7. `SELECT t.c1 <=> t2.c1` — 应为 1（一致）

### 10.2 TEXT/BLOB inline→off-page 迁移

**风险**: TINYTEXT→TEXT 时，>255 字节数据从 inline 存储迁移到 off-page。INSTANT 仅改元数据，可能不迁移数据，导致查询旧行出错。

**验证方法**：
1. 建表插入 254 字节 + 255 字节 + 256 字节(FAIL for TINYTEXT) 数据
2. ALTER TINYTEXT→TEXT
3. ALTER 后插入 256 字节数据（新类型可容纳）
4. 创建对照表（TEXT 类型），插入相同数据
5. 对比原表和对照表数据是否一致

### 10.3 BLOB Null 字节完整性

**风险**: BLOB 含 0x00 字节，存储格式变化时 0x00 必须保持。

**验证方法**：
1. 插入含 0x00 的二进制数据
2. ALTER TINYBLOB→BLOB
3. 用 `<=>` 对比原表和对照表

### 10.4 INSTANT 失败必须干净

**风险**: INSTANT 失败后表不能有部分修改，元数据、数据、索引全部保持旧状态。

**验证方法**：所有 INSTANT 预期 FAIL 的用例，FAIL 后继续插入旧类型范围数据，与对照表对比。

### 10.5 分区表 64 种策略 × 全类型

**风险**: 分区表组合量大（5,120 用例），执行时间长。

**建议**：可分批执行，先执行 KEY/LIN KEY 策略（支持所有类型），再执行其他策略。

---

## 十一、执行后操作

### 11.1 结果对比

将内网结果与阿里云结果对比，生成差异报告：

```bash
# 对比 SQL 验证结果
python3 -c "
import csv
aliyun = {r['test_id']: r for r in csv.DictReader(open('results/summary_aliyun.csv'))}
internal = {r['test_id']: r for r in csv.DictReader(open('results/summary_internal.csv'))}
for tid in sorted(set(aliyun) & set(internal)):
    if aliyun[tid]['result'] != internal[tid]['result']:
        print(f'DIFF {tid}: aliyun={aliyun[tid][\"result\"]} vs internal={internal[tid][\"result\"]}')
"
```

### 11.2 提交结果到 GitHub

```bash
cd /Users/yuyu/PyCharmMiscProject
git add -f outputs/ddl_verify_20260919/results/summary_internal.csv
git add -f outputs/ddl_verify_20260919/results/internal_sql_run.log
git add -f outputs/ddl_verify_20260919/concurrent_dml/results/
git commit -m "test: 内网增强类型验证结果 (DECIMAL/TEXT/BLOB/BIT INPLACE+INSTANT)"
git push origin codex/ddl-verify-20260919
```

### 11.3 更新总结报告

更新 `concurrent_dml/test_summary_report.md` 中的内网验证结果。

---

*文档生成时间: 2026-09-21*
*测试套件版本: v2.0*
