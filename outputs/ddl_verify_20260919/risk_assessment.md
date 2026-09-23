> ⚠️ **本文档的结论已过期，仅作历史留档，请勿直接引用其中的数字。**
> 唯一权威来源是 **`FIX_LOG.md`**（逐步修复与验证台账）与 **`test_gap_audit_20260923.md`**（原始审计）。
>
> 本文列出的 BIT / TEXT / BLOB 风险点仍然有效，但**判定方式已改变**：
> 现在每条风险都对应可执行断言（列类型 META、负向探针 errno、索引完整性、崩溃恢复），
> 而不是靠人工评估。实测已确认的风险见 `FIX_LOG.md` 各 Step 的"实测结论"表格。
>
> 当前套件规模：**37 个文件 / 10,731 个用例 / 用例 ID 全局唯一（重复 0）**；
> 阿里云 RDS MySQL 8.0.36 最近一次全量：**5,228/5,228 PASS**（19,530 条断言，0 FAIL / 0 ERROR / 0 MANUAL / 0 MISSING）。

# BIT / TEXT / BLOB 风险评估

## BIT 风险

| # | 风险 | 级别 | 说明 | 测试覆盖 |
|---|------|------|------|----------|
| B1 | 零填充方向 | **高** | BIT(1)→BIT(8)：值1应变为b'00000001'=1。若实现左填充(MSB方向)则变为b'10000000'=128，数据全部损坏 | 插入值1，ALTER后对比应为1而非128 |
| B2 | 存储字节数变化 | 中 | BIT(8)→BIT(16)：1字节→2字节。INPLACE rebuild时行格式变化 | 插入MAX(255)，ALTER后应为65535 |
| B3 | INSTANT资格 | 中 | BIT不在原生MySQL INSTANT列表。RDS增强是否支持？若不支持但误放行，可能导致元数据与存储不一致 | INSTANT显式请求，验证FAIL或SUCCESS |
| B4 | 显示宽度变化 | 低 | b'1'→b'00000001'，值相同但显示不同。Oracle对比用数值比较避免误报 | 对比用`<=>`或CAST为UNSIGNED |
| B5 | INPLACE row_log | 中 | rebuild期间并发写入BIT新宽度值，row_log回放需正确转换 | 本轮不做并发，但数据正确性验证覆盖 |

### BIT 测试数据

- BIT(1): b'0', b'1', NULL
- BIT(8): b'00000000', b'11111111', b'10101010'
- BIT(16): b'0000000000000000', b'1111111111111111'
- BIT(32): 全0, 全1, 混合
- BIT(64): 全0, 全1

**关键验证**: 插入 b'1' (值=1)，ALTER BIT(1)→BIT(8) 后，值应仍为1，而非128。

## TEXT 风险

| # | 风险 | 级别 | 说明 | 测试覆盖 |
|---|------|------|------|----------|
| T1 | 子类型边界（inline→off-page） | **高** | TINYTEXT→TEXT：>255字节数据从inline迁移到off-page。INSTANT仅改元数据，旧数据可能仍在旧格式 | 插入255字节（inline上限）和256字节数据，ALTER后对比 |
| T2 | INSTANT资格 | **高** | TEXT子类型扩展是否真支持INSTANT？若INSTANT仅改metadata但不迁移数据，查询旧行可能出错 | INSTANT后查询全部行，与对照表对比 |
| T3 | 字符集保持 | 低 | TEXT有charset。子类型变化时charset应保持 | 创建utf8mb4 TEXT列，ALTER后检查charset |
| T4 | 前缀索引行为 | 中 | TEXT列有前缀索引时，类型扩展后索引行为是否正确 | INPLACE测试中覆盖UNIQUE_INDEX依赖 |
| T5 | 最大长度边界 | 中 | TEXT(65535)→MEDIUMTEXT：65535字节是分水岭 | 插入65535和65536字节数据 |

### TEXT 测试数据

- TINYTEXT: 空串'', 单字符, 255字节, 254字节, 256字节(FAIL for TINYTEXT), 多字节, NULL
- TEXT: 65535字节, 65534字节, 65536字节(FAIL for TEXT), 正常值
- MEDIUMTEXT→LONGTEXT: 16MB边界值

## BLOB 风险

| # | 风险 | 级别 | 说明 | 测试覆盖 |
|---|------|------|------|----------|
| L1 | Null字节完整性 | **高** | BLOB可含0x00。存储格式变化(inline→off-page)时0x00必须保持 | 插入含0x00的二进制数据，ALTER后二进制对比 |
| L2 | INSTANT资格 | **高** | 同TEXT，BLOB子类型扩展的INSTANT可能不迁移数据 | 同TEXT T2 |
| L3 | 无charset | 低 | BLOB无charset(binary)，无需保持charset | 不适用 |
| L4 | off-page迁移 | **高** | 同TEXT T1，inline→off-page存储格式变化 | 插入255字节和256字节数据 |
| L5 | 最大长度边界 | 中 | BLOB(65535)→MEDIUMBLOB：65535字节分水岭 | 插入边界值数据 |

### BLOB 测试数据

- TINYBLOB: 空, 单字节0x00, 255字节全0x00, 254字节, 256字节(FAIL), 含null字节二进制
- BLOB: 65535字节, 边界值
- MEDIUMBLOB→LONGBLOB: 16MB边界

## 共同风险

| # | 风险 | 级别 | 说明 |
|---|------|------|------|
| C1 | INSTANT失败必须干净 | **高** | INSTANT失败后表不能有部分修改。元数据、数据、索引全部保持旧状态 |
| C2 | INPLACE失败回滚 | **高** | INPLACE rebuild失败时row_log必须完全回滚，表保持旧状态 |
| C3 | 崩溃恢复 | 中 | DDL执行中实例崩溃后，表必须可正常访问（后续单独测试） |
| C4 | 主备复制 | 中 | DDL binlog格式必须正确，备库执行后结果一致（后续单独测试） |

## 验证策略

1. **数据正确性**: 通过 Oracle 对照表，使用 NULL-safe `<=>` 对比全量数据
2. **类型兼容性**: 验证 ALTER 后旧数据保持正确，新范围数据可正常插入
3. **边界覆盖**: 精确覆盖类型范围边界值（MAX, MAX-1, MAX+1, MIN, MIN+1）
4. **属性保持**: 验证 ALTER 后列属性（charset, comment, nullability等）保持正确
5. **失败安全**: 验证 ALTER 失败后表仍完全可用，数据未损坏
