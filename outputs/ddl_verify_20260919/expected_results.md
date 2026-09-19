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
| BINARY变长 | **FAIL** | 不在秒级支持列表（PRD新增INPLACE但非INSTANT） |
| VARBINARY变长 | **FAIL** | 同上 |
| DECIMAL精度扩(M增D不变) | **FAIL** | 同上 |
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

## 注意事项

1. BINARY/VARBINARY/DECIMAL 的 INSTANT 预期 FAIL 基于PRD分析，但仍需测试以捕获开发遗漏
2. TEXT/BLOB/BIT 的 INSTANT SUCCESS 是PRD标注的新增能力，需重点验证
3. CORE-0416/0417的旧"拒绝"预期已被PRD"新增BINARY/VARBINARY支持"覆盖
4. COMPRESSED行格式不做（PRD排除压缩列）
5. GIPK主键不做（需特定开关）
