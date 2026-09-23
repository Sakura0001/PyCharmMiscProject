> ⚠️ **本文档的结论已过期，仅作历史留档，请勿直接引用其中的数字。**
> 唯一权威来源是 **`FIX_LOG.md`**（逐步修复与验证台账）与 **`test_gap_audit_20260923.md`**（原始审计）。
>
> 本文的预期结果表已被**实测 golden 基线**取代：
> `tools/conversion_matrix_aliyun.json`（196 条）、`tools/factor_matrix_aliyun.json`（198 条）、
> `tools/partition_compat_aliyun.json`（24 策略 × 17 类型）、`tools/fk_matrix_aliyun.json`（66 条）。
> 期望值不再靠人写文档，而是"实测 → 冻结 → 每轮回归比对"。
>
> 当前套件规模：**37 个文件 / 10,731 个用例 / 用例 ID 全局唯一（重复 0）**；
> 阿里云 RDS MySQL 8.0.36 最近一次全量：**5,228/5,228 PASS**（19,530 条断言，0 FAIL / 0 ERROR / 0 MANUAL / 0 MISSING）。

# 预期结果汇总

## 阿里云环境 (整数 + CHAR + VARCHAR)

### INSTANT 算法

| 类型转换 | INSTANT 预期 | 说明 |
|----------|-------------|------|
| TINYINT→{SMALLINT,MEDIUMINT,INT,BIGINT} | SUCCESS | 值域包含 |
| SMALLINT→{MEDIUMINT,INT,BIGINT} | SUCCESS | 值域包含 |
| MEDIUMINT→{INT,BIGINT} | SUCCESS | 值域包含 |
| INT→BIGINT | SUCCESS | 值域包含 |
| 整数UNSIGNED同上 | SUCCESS | 值域包含 |
| CHAR变长(同字符集) | SUCCESS | 值域包含 |
| VARCHAR变长(同字符集) | SUCCESS | 值域包含，含跨pack-length边界 |

### INPLACE 算法

同上所有转换均预期 SUCCESS。

### 分区表

| 场景 | 预期 |
|------|------|
| target为分区键 | ALTER FAIL（分区键不可修改） |
| target为非分区键 | 同普通表预期 |

### 外键表

| 场景 | INSTANT | INPLACE |
|------|---------|---------|
| FK子列单侧改(INT→BIGINT) | FAIL | FAIL（类型不匹配） |
| FK父列单侧改 | FAIL | FAIL（类型不匹配） |
| FK双侧同步改 | FAIL | SUCCESS |
| 非FK列改 | SUCCESS | SUCCESS |
| FK子列单侧改(VARCHAR→VARCHAR变长) | SUCCESS | SUCCESS |
| FK子列单侧改(VARBINARY→VARBINARY变长) | FAIL | SUCCESS |

## 内网环境 (BINARY + VARBINARY + DECIMAL + TEXT + BLOB + BIT)

### INSTANT 算法

| 类型转换 | INSTANT 预期 | 说明 |
|----------|-------------|------|
| BINARY变长 | **SUCCESS** | 阿里云实测确认支持，内网同样支持 |
| VARBINARY变长 | **SUCCESS** | 阿里云实测确认支持，内网同样支持 |
| DECIMAL精度扩(M增D不变) | **SUCCESS** | 用户确认内网支持 |
| TEXT子类型扩展 | SUCCESS | PRD标注INSTANT支持 |
| BLOB子类型扩展 | SUCCESS | PRD标注INSTANT支持 |
| BIT变长 | SUCCESS | PRD标注INSTANT支持 |

### INPLACE 算法

| 类型转换 | INPLACE 预期 | 说明 |
|----------|-------------|------|
| BINARY变长 | SUCCESS | PRD新增BINARY支持 |
| VARBINARY变长 | SUCCESS | PRD新增VARBINARY支持 |
| DECIMAL精度扩(M增D不变) | SUCCESS | PRD新增DECIMAL支持 |
| TEXT子类型扩展 | SUCCESS | 值域包含 |
| BLOB子类型扩展 | SUCCESS | 值域包含 |
| BIT变长 | SUCCESS | 值域包含 |

### DECIMAL 拒绝场景（回退COPY）

| 场景 | 预期 |
|------|------|
| D(标度)变化 | FAIL/回退COPY |
| 符号变化(UNSIGNED↔SIGNED) | FAIL/回退COPY |
| AUTO_INCREMENT属性变化 | FAIL/回退COPY |

## 特殊模式预期

| 模式 | INSTANT | INPLACE |
|------|---------|---------|
| 连续ALTER(INT链式升级) | SUCCESS | SUCCESS |
| 多列同时ALTER | SUCCESS | SUCCESS |
| 虚拟生成列+函数索引 | FAIL | SUCCESS(LOCK=SHARED) |
| 显式COPY对照 | N/A | SUCCESS |

## 列属性保持预期

| 属性 | 预期 |
|------|------|
| UNSIGNED | 保持 |
| AUTO_INCREMENT | 保持 |
| COMMENT | 保持 |
| CHARACTER SET | 保持 |
| COLLATE | 保持 |

## 阿里云实测结果（2026-09-20~21）

| 类型 | INSTANT 实测 | INPLACE 实测 | 备注 |
|------|-------------|--------------|------|
| 整数(SIGNED/UNSIGNED) | ✅ SUCCESS | ✅ SUCCESS | 全部通过 |
| CHAR(latin1/utf8mb4) | ✅ SUCCESS | ✅ SUCCESS | 跨字节边界除外 |
| VARCHAR(跨pack边界) | ✅ SUCCESS | ✅ SUCCESS | 全部通过 |
| BINARY | ✅ SUCCESS(超出预期) | ✅ SUCCESS | 阿里云意外支持INSTANT |
| VARBINARY | ✅ SUCCESS(超出预期) | ✅ SUCCESS | 阿里云意外支持INSTANT |
| DECIMAL | ❌ FAIL | ❌ FAIL | 需内网验证 |
| TEXT | ❌ FAIL | ❌ FAIL | 需内网验证 |
| BLOB | ❌ FAIL | ❌ FAIL | 需内网验证 |
| BIT | ❌ FAIL | ❌ FAIL | 需内网验证 |

## 注意事项

1. BINARY/VARBINARY 的 INSTANT 在阿里云上意外成功，已更新SQL用例为成功路径
2. DECIMAL 的 INSTANT 阿里云不支持，但用户确认内网支持，SQL用例已更新为成功路径
3. TEXT/BLOB/BIT 需在内网环境验证
4. COMPRESSED行格式不做（PRD排除压缩列）
5. GIPK主键不做（需特定开关）
6. DDL Fuzz 测试已从100轮调整为1000轮
