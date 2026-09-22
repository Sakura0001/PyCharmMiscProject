# 上限类型转换覆盖报告 | Upper-Limit Type Conversion Coverage Report

> 生成时间: 2026-09-22  
> Git commit: af8b2a4f65  
> 分支: codex/ddl-verify-20260919

## 1. 概述

本报告汇总了所有数据类型"转换到MySQL上限"的测试覆盖情况，包括新增的上限转换用例和已覆盖的上限转换。

## 2. 上限类型转换覆盖矩阵

### 2.1 已覆盖的上限转换（本轮无变化）

| 类型 | MySQL 上限 | 已有转换 | 状态 | 数据验证 |
|------|-----------|---------|------|---------|
| CHAR | CHAR(255) | CHAR(254)→CHAR(255) utf8mb4 | ✅ 已覆盖 | 插入254字符+255字符+256字符(FAIL) |
| BIT | BIT(64) | BIT(32)→BIT(64) | ✅ 已覆盖 | 插入32位全1+64位全1+64位最大值 |
| DECIMAL (max M, max D) | DECIMAL(65,30) | DECIMAL(64,30)→DECIMAL(65,30) | ✅ 已覆盖 | 插入64,30最大值+65,30最大值 |
| TEXT | LONGTEXT | MEDIUMTEXT→LONGTEXT | ✅ 已覆盖 | 插入16MB边界数据 |
| BLOB | LONGBLOB | MEDIUMBLOB→LONGBLOB | ✅ 已覆盖 | 插入16MB边界数据 |

### 2.2 本轮新增的上限转换

| # | ID | 源类型 | 目标类型 | 字符集 | MySQL上限说明 | INSTANT | INPLACE | minimal_table |
|---|-----|--------|---------|--------|-------------|---------|---------|---------------|
| 1 | VC-08 | VARCHAR(16382) | VARCHAR(16383) | utf8mb4 | utf8mb4字符集下VARCHAR上限(16383×4=65532字节) | ✅SUCCESS | ✅SUCCESS | ✅ 是 |
| 2 | VC-09 | VARCHAR(65528) | VARCHAR(65529) | latin1 | latin1字符集下VARCHAR上限(65529+2字节前缀+4字节INT=65535) | ✅SUCCESS | ✅SUCCESS | ✅ 是 |
| 3 | BIN-03 | BINARY(254) | BINARY(255) | — | BINARY类型MySQL上限(255) | ✅SUCCESS | ✅SUCCESS | 否 |
| 4 | VBIN-03 | VARBINARY(65528) | VARBINARY(65529) | — | VARBINARY类型MySQL上限(同VARCHAR计算) | ✅SUCCESS | ✅SUCCESS | ✅ 是 |
| 5 | DEC-07 | DECIMAL(64,0) | DECIMAL(65,0) | — | DECIMAL整数精度上限(M=65, D=0) | ✅SUCCESS | ✅SUCCESS | 否 |

### 2.3 本轮新增的DECIMAL 9位编码边界转换

DECIMAL内部存储使用9位十进制数为一组（4字节），因此M=9,18,27,36,45,54,63是存储边界。

| # | ID | 源类型 | 目标类型 | 边界说明 | INSTANT | INPLACE |
|---|-----|--------|---------|---------|---------|---------|
| 6 | DEC-08 | DECIMAL(8,2) | DECIMAL(9,2) | 1个存储单元→2个（9位边界） | ✅SUCCESS | ✅SUCCESS |
| 7 | DEC-09 | DECIMAL(9,2) | DECIMAL(10,2) | 刚过9位边界 | ✅SUCCESS | ✅SUCCESS |
| 8 | DEC-10 | DECIMAL(17,2) | DECIMAL(18,2) | 2个存储单元→3个（18位边界） | ✅SUCCESS | ✅SUCCESS |
| 9 | DEC-11 | DECIMAL(62,30) | DECIMAL(63,30) | 7个存储单元→8个（63位边界）+ 最大D | ✅SUCCESS | ✅SUCCESS |

## 3. 上限数据插入验证

每个上限转换用例都执行以下数据验证流程：

### 3.1 Pre-ALTER 数据（旧类型上限）

| 类型 | 插入的上限数据 | 说明 |
|------|-------------|------|
| VARCHAR(16382) | `REPEAT('x', 16382)` = 16382字符 | 旧类型最大长度 |
| VARCHAR(65528) | `REPEAT('x', 65528)` = 65528字符 | 旧类型最大长度 |
| BINARY(254) | `0x00 * 254` + `0xFF * 254` | 全0+全FF，旧类型最大长度 |
| VARBINARY(65528) | `0x00 * 65528` + `0xFF * 65528` | 全0+全FF，旧类型最大长度 |
| DECIMAL(64,0) | `9...9`(64个9) | 旧类型最大值 |
| DECIMAL(8,2) | `999999.99` | 旧类型最大值 |
| DECIMAL(17,2) | `99999999999999999.99` | 旧类型最大值 |
| DECIMAL(62,30) | `999...9.999...9`(32+30位) | 旧类型最大值 |

### 3.2 Post-ALTER 数据（新类型上限 + 旧类型兼容）

| 类型 | 插入的新上限数据 | 插入的旧兼容数据 | 预期FAIL数据 |
|------|---------------|---------------|-------------|
| VARCHAR(16383) | `REPEAT('z', 16383)` | `REPEAT('x', 16382)` | `REPEAT('q', 16384)` |
| VARCHAR(65529) | `REPEAT('z', 65529)` | `REPEAT('x', 65528)` | `REPEAT('q', 65530)` |
| BINARY(255) | `0x00 * 255` + `0xFF * 255` | `0x00 * 254` | `0x41 * 256` |
| VARBINARY(65529) | `0x00 * 65529` + `0xFF * 65529` | `0x00 * 65528` | `0x41 * 65530` |
| DECIMAL(65,0) | `9...9`(65个9) | `9...9`(64个9) | `9...9`(70位) |
| DECIMAL(9,2) | `99999999.99` | `999999.99` | `9...9`(70位) |
| DECIMAL(18,2) | `99999999999999999.99` | `999999999999999.99` | `9...9`(70位) |
| DECIMAL(63,30) | `999...9.999...9`(33+30位) | `999...9.999...9`(32+30位) | `9...9`(70位) |

### 3.3 Oracle 对照表验证

每个用例通过 `<=>` NULL-safe 比较验证原表与对照表数据完全一致：
- 成功路径：对照表使用新类型，INSERT全部数据
- 失败路径：对照表使用旧类型，INSERT行为与原表一致（超范围值同样FAIL）

## 4. minimal_table 处理

VARCHAR(16382+)/VARCHAR(65528+)/VARBINARY(65528+) 超出行大小限制(65535字节)，无法在表中添加 pad1/pad2 列。因此使用最小化表结构：

```sql
-- 普通类型表结构（有pad列）
CREATE TABLE t1 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100),
  pad2 VARCHAR(20) DEFAULT 'pad2',
  PRIMARY KEY (id)
) ENGINE=InnoDB;

-- minimal_table 结构（仅 id + target）
CREATE TABLE t1 (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(65528),
  PRIMARY KEY (id)
) ENGINE=InnoDB;
```

minimal_table 的 OFAT 因子变化：
- `non_target_index`: 跳过（无 pad1/pad2 可索引）
- `target_position`: 仍测 FIRST / MIDDLE / LAST（但不影响列数）
- `primary_key`: 强制 CLUSTERED（COMPOSITE_PK 需要索引 target 列，但大 VARCHAR 不支持）
- 对比列: `[id, target]` 而非 `[id, pad1, target, pad2]`

## 5. 并发DML大表测试的上限覆盖

### ALIYUN_TYPES 新增（阿里云RDS验证）

| 测试前缀 | 类型 | 旧类型 | 新类型 | INSTANT | INPLACE |
|---------|------|--------|--------|---------|---------|
| VAR-16382U4 | varchar | VARCHAR(16382) | VARCHAR(16383) | ✅ | ✅ |
| VAR-65528L | varchar | VARCHAR(65528) | VARCHAR(65529) | ✅ | ✅ |

### ENHANCED_TYPES 新增（内网RDS验证）

| 测试前缀 | 类型 | 旧类型 | 新类型 | INSTANT | INPLACE |
|---------|------|--------|--------|---------|---------|
| BIN-254 | binary | BINARY(254) | BINARY(255) | ✅ | ✅ |
| VBIN-65528 | varbinary | VARBINARY(65528) | VARBINARY(65529) | ✅ | ✅ |
| DEC-640-650 | decimal | DECIMAL(64,0) | DECIMAL(65,0) | ✅ | ✅ |
| DEC-82-92 | decimal | DECIMAL(8,2) | DECIMAL(9,2) | ✅ | ✅ |
| DEC-92-102 | decimal | DECIMAL(9,2) | DECIMAL(10,2) | ✅ | ✅ |
| DEC-172-182 | decimal | DECIMAL(17,2) | DECIMAL(18,2) | ✅ | ✅ |
| DEC-6230-6330 | decimal | DECIMAL(62,30) | DECIMAL(63,30) | ✅ | ✅ |

### LARGE_TABLE_TYPES 新增（大表并发DML，INPLACE窗口期数据一致性）

| 测试前缀 | 类型 | 旧类型→新类型 | 算法 | 行数 | 预期 |
|---------|------|-------------|------|------|------|
| BIN254-255-IP/IT | binary | BINARY(254)→BINARY(255) | INPLACE+INSTANT | 500K | SUCCESS |
| VBIN65528-65529-IP/IT | varbinary | VARBINARY(65528)→VARBINARY(65529) | INPLACE+INSTANT | 50K | SUCCESS |
| VAR16382-16383U4-IP/IT | varchar | VARCHAR(16382)→VARCHAR(16383) | INPLACE+INSTANT | 50K | SUCCESS |
| VAR65528-65529L-IP/IT | varchar | VARCHAR(65528)→VARCHAR(65529) | INPLACE+INSTANT | 50K | SUCCESS |
| DEC640-650-IP/IT | decimal | DECIMAL(64,0)→DECIMAL(65,0) | INPLACE+INSTANT | 200K | 内网 |
| DEC82-92-IP/IT | decimal | DECIMAL(8,2)→DECIMAL(9,2) | INPLACE+INSTANT | 200K | 内网 |
| DEC172-182-IP/IT | decimal | DECIMAL(17,2)→DECIMAL(18,2) | INPLACE+INSTANT | 200K | 内网 |
| DEC6230-6330-IP/IT | decimal | DECIMAL(62,30)→DECIMAL(63,30) | INPLACE+INSTANT | 200K | 内网 |

## 6. 数据多样性验证

### 6.1 VARCHAR 上限数据多样性

**utf8mb4 VARCHAR(16382)→VARCHAR(16383):**
- ASCII字符填满上限: `REPEAT('x', 16382)` / `REPEAT('z', 16383)`
- Emoji填满上限: `🎉 × 4095` (16380字节，4字节/字符)
- 3字节字符填满: `你好 × 5460` (16380字节)
- 用户特别要求的"emoji × 8000": `🎉 × 8000` = 32000字节 (在post-DDL阶段)
- 空串、单字符、NULL
- 超上限值(预期FAIL): `REPEAT('q', 16384)`

**latin1 VARCHAR(65528)→VARCHAR(65529):**
- ASCII字符填满上限: `REPEAT('x', 65528)` / `REPEAT('z', 65529)`
- 空串、单字符、NULL
- 超上限值(预期FAIL): `REPEAT('q', 65530)`

### 6.2 BINARY/VARBINARY 上限数据多样性

**BINARY(254)→BINARY(255):**
- 全0x00: `X'00' * 254` / `X'00' * 255`
- 全0xFF: `X'FF' * 254` / `X'FF' * 255`
- 混合二进制: `MIX * N + M`
- 空串（BINARY会被0x00填充）
- 超上限(预期FAIL): `X'41' * 256`

**VARBINARY(65528)→VARBINARY(65529):**
- 全0x00: `0x0000...00` (65528字节) / (65529字节)
- 全0xFF: `0xFFFF...FF` (65528字节) / (65529字节)
- 混合二进制
- 空串、NULL
- 超上限(预期FAIL): `0x4141...41` (65530字节)

### 6.3 DECIMAL 上限和边界数据多样性

**DECIMAL(64,0)→DECIMAL(65,0):**
- 旧最大值: `9...9` (64位)
- 新最大值: `9...9` (65位)
- 0, 1, -1
- 超上限(预期FAIL): `9...9` (70位)

**DECIMAL(8,2)→DECIMAL(9,2) (9位边界):**
- 旧最大值: `999999.99` (8位精度)
- 新最大值: `99999999.99` (9位精度，跨存储边界)
- 最小步长: `0.01`
- MAX-1, MIN+1
- 正常值: `1.23`, `-1.23`

## 7. 文件清单

### 纯SQL测试文件

| 文件 | 新增上限用例 | 大小 |
|------|------------|------|
| sql_aliyun/07_varchar_instant.sql.gz | VC-08, VC-09 INSTANT | ~400KB (gz) |
| sql_aliyun/08_varchar_inplace.sql.gz | VC-08, VC-09 INPLACE | ~500KB (gz) |
| sql_internal/15_binary_inplace.sql | BIN-03 INPLACE | ~630KB |
| sql_internal/16_binary_instant.sql | BIN-03 INSTANT | ~530KB |
| sql_internal/17_varbinary_inplace.sql.gz | VBIN-03 INPLACE | ~150KB (gz) |
| sql_internal/18_varbinary_instant.sql.gz | VBIN-03 INSTANT | ~130KB (gz) |
| sql_internal/19_decimal_inplace.sql | DEC-07~11 INPLACE | ~1.2MB |
| sql_internal/20_decimal_instant.sql | DEC-07~11 INSTANT | ~1.0MB |
| sql_aliyun/12_partition_64.sql.gz | 64分区×VC-08,VC-09 | ~1.5MB (gz) |
| sql_internal/29_partition_64_enhanced.sql.gz | 64分区×BIN-03,VBIN-03,DEC-07~11 | ~1.7MB (gz) |

### Python 测试框架文件

| 文件 | 修改内容 |
|------|---------|
| generate_test_sql.py | +9 transitions, minimal_table支持, 对比列修复 |
| concurrent_dml/run_concurrent_tests.py | +2 ALIYUN_TYPES, +7 ENHANCED_TYPES, +16 LARGE_TABLE_TYPES |
| concurrent_dml/data_generator.py | DECIMAL_9BIT_TRANSITIONS扩展 |

## 8. 总结

| 维度 | 之前 | 本轮后 | 变化 |
|------|------|--------|------|
| 类型转换总数 | 50 | 59 | +9 |
| ALIYUN_TYPES | 13 | 15 | +2 |
| ENHANCED_TYPES | 20 | 27 | +7 |
| LARGE_TABLE_TYPES | 77 | 93 | +16 |
| 上限覆盖类型 | 5/8 | 8/8 | +3 (VARCHAR, BINARY, VARBINARY) |
| DECIMAL 9位边界 | 1 | 5 | +4 |

**所有8种支持扩展的数据类型均已覆盖到MySQL上限：**
1. ✅ CHAR → CHAR(255) 
2. ✅ VARCHAR → VARCHAR(16383) utf8mb4 / VARCHAR(65529) latin1
3. ✅ BIT → BIT(64)
4. ✅ BINARY → BINARY(255)
5. ✅ VARBINARY → VARBINARY(65529)
6. ✅ DECIMAL → DECIMAL(65,30) / DECIMAL(65,0) + 9位边界
7. ✅ TEXT → LONGTEXT
8. ✅ BLOB → LONGBLOB
