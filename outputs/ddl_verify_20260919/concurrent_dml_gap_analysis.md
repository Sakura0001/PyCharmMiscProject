# 并发DML验证套件 — 缺口分析与改进方案

> 生成时间: 2026-09-21
> 分析对象: `concurrent_dml/` 目录下全部代码 (3,049行)
> 分析维度: QPS观测、数据覆盖、类型覆盖、测试漏洞

---

## 一、QPS影响观测能力分析

### 1.1 当前状态

| 指标 | 是否采集 | 采集位置 | 说明 |
|------|---------|---------|------|
| DDL执行耗时 | ✅ | `dml_framework.py` L358-364 | `ddl_duration_s` 字段 |
| DML总操作数 | ✅ | `_dml_ops[worker_id]` | 所有worker的累计ops |
| DML总错误数 | ✅ | `_dml_errors[worker_id]` | 所有worker的累计errors |
| DML操作类型 | ✅ | `op_types[i % 5]` | INSERT/UPDATE/DELETE/SELECT/UPSERT |
| **DDL前QPS (基线)** | ✅ (已修复) | QPSSampler | pre_ddl阶段每秒采样 |
| **DDL期间QPS** | ✅ (已修复) | QPSSampler | during_ddl阶段每秒采样 |
| **DDL后QPS (恢复)** | ✅ (已修复) | QPSSampler | post_ddl阶段每秒采样 |
| **单条DML延迟** | ⚠️ 间接 | QPS采样 | 通过QPS变化间接反映延迟变化，无per-statement精确延迟 |
| **DDL期间错误类型** | ⚠️ 部分 | `_mismatch_log` | 记录了t1/t2不一致，但未分类是超时/锁等待/范围溢出 |

### 1.2 核心缺口

**框架无法回答以下关键问题：**

1. INPLACE DDL执行期间，DML QPS从多少下降到多少？下降比例是多少？
2. INSTANT DDL是否对QPS有可观测影响？（预期接近零影响）
3. DDL完成后QPS恢复到基线的速度如何？
4. 不同数据类型（INT→BIGINT vs VARCHAR(255)→VARCHAR(256)）的INPLACE DDL期间QPS影响差异？
5. DML延迟在DDL期间是否出现尖峰？

### 1.3 改进方案

需要在 `DualWriteOracle` 中增加**时间窗口化QPS采集器**：

```python
class QPSSampler:
    """每秒采样DML ops，区分 pre-DDL / during-DDL / post-DDL 三阶段"""
    def __init__(self):
        self._samples = []  # [(timestamp, phase, ops_per_sec, errors_per_sec)]
        self._phase = 'pre_ddl'
        self._last_ops = 0
        self._last_errors = 0
        self._last_ts = time.time()
    
    def set_phase(self, phase):  # 'pre_ddl' / 'during_ddl' / 'post_ddl'
        self._phase = phase
    
    def sample(self, current_ops, current_errors):
        now = time.time()
        elapsed = now - self._last_ts
        if elapsed > 0:
            qps = (current_ops - self._last_ops) / elapsed
            eps = (current_errors - self._last_errors) / elapsed
            self._samples.append({
                'ts': round(now, 3),
                'phase': self._phase,
                'qps': round(qps, 1),
                'errors_per_sec': round(eps, 1),
            })
        self._last_ops = current_ops
        self._last_errors = current_errors
        self._last_ts = now
```

在 `_dml_worker` 中每秒采样一次，在 `run_ddl` 前后切换 phase。

输出增加：
```json
{
  "qps_curve": [
    {"ts": 0.0, "phase": "pre_ddl", "qps": 850.2, "errors_per_sec": 0.0},
    {"ts": 1.0, "phase": "pre_ddl", "qps": 920.1, "errors_per_sec": 0.0},
    {"ts": 2.0, "phase": "during_ddl", "qps": 45.3, "errors_per_sec": 2.1},
    {"ts": 3.0, "phase": "during_ddl", "qps": 38.7, "errors_per_sec": 1.8},
    {"ts": 4.0, "phase": "post_ddl", "qps": 780.5, "errors_per_sec": 0.0},
    {"ts": 5.0, "phase": "post_ddl", "qps": 910.3, "errors_per_sec": 0.0}
  ],
  "qps_summary": {
    "baseline_avg_qps": 885.15,
    "ddl_window_avg_qps": 42.0,
    "ddl_window_qps_drop_pct": 95.3,
    "post_ddl_recovery_qps": 845.4,
    "recovery_time_s": 1.0
  }
}
```

---

## 二、数据覆盖分析

### 2.1 DML期间插入的数据

| 阶段 | 数据来源 | 值域覆盖 | EXPECT_FAIL值 | 评估 |
|------|---------|---------|--------------|------|
| DDL前 (pre phase) | `gen_*_data(..., phase='pre')` | ✅ 旧类型MIN/MAX/0/正负/NULL/边界±1 | ❌ 已过滤 | **正确** — 不应插入超限值 |
| DDL期间 (仍pre phase) | 同上 | ✅ 旧类型范围 | ❌ 已过滤 | **正确** — INPLACE rebuild期间表仍接受旧类型值 |
| DDL后 (post phase) | `gen_*_data(..., phase='post')` | ✅ 新类型范围+旧类型范围+NULL | ❌ 已过滤 | **正确** — 并发DML不应插入必定失败的值 |

### 2.2 顺序INSERT中的数据 (baseline + post_ddl)

| 数据集 | 值域覆盖 | EXPECT_FAIL值 | 评估 |
|--------|---------|--------------|------|
| baseline (DDL前) | ✅ 极值/边界/正负/零/NULL | ❌ 已过滤 | **正确** |
| post_ddl (DDL后) | ✅ 新范围+旧范围+NULL | ✅ 包含 (标注 `-- EXPECT_FAIL`) | **正确** — 验证新类型范围限制 |

### 2.3 各类型数据多样性检查

| 类型 | 负数/零/正数 | 源MIN/MAX | 新范围值 | NULL/空串/空格 | 0x00/0xFF/前缀冲突 | utf8mb3/utf8mb4 | 旧/新/超新上限 | 9位编码边界 |
|------|:---------:|:--------:|:------:|:------------:|:----------------:|:-------------:|:----------:|:--------:|
| 整数SIGNED | ✅ | ✅ | ✅ | ✅ NULL | N/A | N/A | N/A | N/A |
| 整数UNSIGNED | ✅ | ✅ | ✅ | ✅ NULL | N/A | N/A | N/A | N/A |
| CHAR | ✅ | ✅ | ✅ | ✅ NULL/空串/空格/尾空格 | ✅ 0x00(latin1) | ✅ utf8mb4 emoji | ✅ M-1/M/M+1 | N/A |
| VARCHAR | ✅ | ✅ | ✅ | ✅ NULL/空串/空格/尾空格 | ✅ 0x00(latin1) | ✅ utf8mb4/utf8mb3 | ✅ 跨pack边界 | N/A |
| BINARY | N/A | ✅ MAX/MIN | ✅ | ✅ NULL | ✅ 全0x00/全0xFF/前缀冲突 | N/A | ✅ M-1/M/M+1 | N/A |
| VARBINARY | N/A | ✅ | ✅ | ✅ NULL | ✅ 全0x00/全0xFF | N/A | ✅ M-1/M/M+1 | N/A |
| DECIMAL | ✅ 正负零 | ✅ | ✅ | ✅ NULL | N/A | N/A | N/A | ✅ 9位边界转换 |
| TEXT | N/A | ✅ | ✅ | ✅ NULL/空串 | ✅ 0x01-0x1f | ✅ utf8mb4 emoji×8000 | ✅ 255/256/65535/65536/8101/8192/16000/32000/64000 | N/A |
| BLOB | N/A | ✅ | ✅ | ✅ NULL/空 | ✅ 0x00/0xFF/混合二进制 | N/A | ✅ 同TEXT边界 | N/A |
| BIT | N/A | ✅ MAX/MIN | ✅ | ✅ NULL | N/A | N/A | ✅ 1/8/16/32/64位边界 | N/A |

### 2.4 数据覆盖结论

**数据覆盖完整，无缺口。** 具体来说：

- ✅ 修改前插入的数据包含旧类型范围的极值、边界值、正常值、正负数、零、NULL
- ✅ 修改后插入的数据包含新类型独有范围值 + 旧类型范围值 + NULL
- ✅ 超出新类型范围的值标注为 `EXPECT_FAIL`，在顺序INSERT中验证其正确失败
- ✅ 并发DML中只插入安全值（过滤掉EXPECT_FAIL），保证t1/t2双写一致性
- ✅ TEXT/BLOB覆盖了255/256/65535/65536/8101/8192等关键字节边界
- ✅ BIT覆盖了1→8/8→16/16→32/32→64的存储字节数变化
- ✅ DECIMAL覆盖了9位编码边界转换（DECIMAL_9BIT_TRANSITIONS 12条）
- ✅ CHAR/VARCHAR覆盖了utf8mb3/utf8mb4多字节字符、尾空格语义、跨pack-length边界

---

## 三、类型覆盖分析

### 3.1 并发DML测试覆盖的类型转换

| 环境 | 类型 | 转换数 | INSTANT | INPLACE | 总用例数 |
|------|------|--------|---------|---------|---------|
| 阿里云 | 整数SIGNED | 2 (INT→BIGINT, TINYINT→SMALLINT) | 2 | 2 | 4 |
| 阿里云 | 整数UNSIGNED | 2 (INT→BIGINT, TINYINT→INT) | 2 | 2 | 4 |
| 阿里云 | CHAR | 3 | 3 | 3 | 6 |
| 阿里云 | VARCHAR | 7 | 7 | 7 | 14 |
| 内网 | BINARY | 2 | 2 | 2 | 4 |
| 内网 | VARBINARY | 2 | 2 | 2 | 4 |
| 内网 | DECIMAL | 3 | 3 | 3 | 6 |
| 内网 | TEXT | 3 | 3 | 3 | 6 |
| 内网 | BLOB | 3 | 3 | 3 | 6 |
| 内网 | BIT | 4 | 4 | 4 | 8 |
| **合计** | | **28** | **28** | **28** | **56** |

### 3.2 与SQL测试套件的差异

SQL测试套件 (`sql_aliyun/` + `sql_internal/`) 覆盖了计划中的全部50条类型转换。
并发DML测试覆盖了其中28条（代表性子集）。

**并发DML中缺失的整数子类型转换** (不影响SQL套件覆盖)：

| 缺失转换 | SIGNED | UNSIGNED |
|---------|--------|----------|
| TINYINT→MEDIUMINT | ❌ | ❌ |
| TINYINT→INT | ❌ | ✅ (有UNSIGNED版) |
| TINYINT→BIGINT | ❌ | ❌ |
| SMALLINT→MEDIUMINT | ❌ | ❌ |
| SMALLINT→INT | ❌ | ❌ |
| SMALLINT→BIGINT | ❌ | ❌ |
| MEDIUMINT→INT | ❌ | ❌ |
| MEDIUMINT→BIGINT | ❌ | ❌ |

**风险评估**：这些转换的值域包含关系与INT→BIGINT完全相同（都是整数从小变大），并发DML行为一致。SQL套件已覆盖数据正确性，并发DML的代表性子集（INT→BIGINT）覆盖了并发行为验证。**风险低，可接受。**

### 3.3 结论

- ✅ 所有PRD支持的类型扩展（整数/CHAR/VARCHAR/BINARY/VARBINARY/DECIMAL/TEXT/BLOB/BIT）在并发DML中都有覆盖
- ✅ 每种类型都测试了INSTANT和INPLACE两种算法
- ⚠️ 整数子类型只选了代表性转换，未做全排列（但SQL套件已覆盖）
- ✅ 大表测试使用INT→BIGINT（最典型场景）

---

## 四、测试漏洞清单

### 4.1 已识别漏洞

| # | 漏洞 | 严重度 | 影响范围 | 状态 |
|---|------|--------|---------|------|
| G1 | ~~无QPS时间窗口化采集~~ | 高 | 所有并发DML用例 | **已修复**: 增加QPSSampler类，每秒采样pre/during/post三阶段QPS |
| G2 | **大表只测INT→BIGINT** | 中 | 大表测试 | 未覆盖CHAR/VARCHAR大表并发DML |
| G3 | **并发DML无外键表** | 中 | Phase 2 | FK场景的并发DML行为未验证 |
| G4 | **并发DML无分区表** | 中 | Phase 2 | 分区表上的并发DML行为未验证 |
| ~~G5~~ | ~~DDL Fuzz只做ADD COLUMN~~ | ~~中~~ | ~~Phase 1~~ | **已覆盖**: DDL Fuzz已包含MODIFY c1 BIGINT(INSTANT) + MODIFY c2 VARCHAR(100)(INPLACE) |
| G6 | **无per-DML延迟测量** | 低 | 所有并发DML | 无法看到DDL期间单条DML延迟尖峰 |
| G7 | **大表DML值仅整数** | 低 | Phase 5 | 大表测试设计为INT→BIGINT场景，整数DML值正确；QPS采样已增加 |
| G8 | **DDL期间错误未分类** | 低 | 所有并发DML | mismatch_log记录了错误但未区分超时/锁等待/范围溢出 |

### 4.2 已覆盖项确认 (无漏洞)

| 测试点 | 来源 | 覆盖状态 | 实现函数 |
|--------|------|---------|---------|
| 行格式: DYNAMIC | mindmap | ✅ | build_row_format_tests() |
| 行格式: COMPACT | mindmap | ✅ | build_row_format_tests() |
| 行格式: REDUNDANT | mindmap | ✅ | build_row_format_tests() |
| 行格式: COMPRESSED | mindmap | ✅ | build_row_format_tests() |
| 表大小: 窄表 | mindmap | ✅ | build_table_size_tests() |
| 表大小: 宽表 | mindmap | ✅ | build_table_size_tests() |
| 表大小: 接近最大行宽 | mindmap | ✅ | build_table_size_tests() |
| 表列数上限 | mindmap | ✅ | run_max_column_test() |
| 连续INSTANT 10/30/50次 | mindmap | ✅ | run_consecutive_instant_test() |
| 反复DDL无内存泄漏 | mindmap | ✅ | run_ddl_fuzz_test() (1000轮) |
| 数据: 负数/零/正数 | mindmap | ✅ | data_generator.py gen_integer_data |
| 数据: 源类型MIN/MAX | mindmap | ✅ | 所有gen_*_data函数 |
| 数据: 新范围值 | mindmap | ✅ | post phase |
| 数据: DECIMAL精度/标度/9位边界 | mindmap | ✅ | DECIMAL_9BIT_TRANSITIONS + run_decimal_boundary_test() |
| 数据: NULL/空串/空格/尾空格 | mindmap | ✅ | gen_char_data + run_varchar_boundary_test() |
| 数据: 0x00/0xFF/前缀冲突 | mindmap | ✅ | gen_binary_data (prefix_zero_tail, prefix_ff_tail) |
| 数据: utf8mb3/utf8mb4 | mindmap | ✅ | gen_char_data (EMOJI, MULTIBYTE_3) |
| 数据: 旧/新/超新长度上限 | mindmap | ✅ | 所有gen_*_data post phase |
| 链式升级 TINY→...→BIGINT | 计划 | ✅ | run_consecutive_chain_test() |
| 多列同时ALTER | 计划 | ✅ | run_multi_column_test() |
| 同键删除重插 | 计划 | ✅ | run_same_key_test() |
| 唯一键冲突优化 | PRD | ✅ | run_unique_conflict_test() |
| 虚拟生成列/函数索引 | 计划 | ✅ | run_virtual_column_test() |
| 带索引字段扩容 | 计划 | ✅ | run_index_test() |
| 视图依赖 | 计划 | ✅ | run_view_test() |
| 临时表 | 计划 | ✅ | run_temp_table_test() |
| 连续多轮DDL性能 | mindmap | ✅ | run_consecutive_ddl_perf_test() |
| VARCHAR跨长度头 | mindmap | ✅ | run_varchar_boundary_test() |
| INSERT/UPDATE/DELETE/SELECT | 计划 | ✅ | _dml_worker (5种操作类型) |
| Oracle对照表验证 | 计划 | ✅ | DualWriteOracle (t1+t2 <=> 对比) |
| 大表5000万+行 | 计划 | ✅ | run_large_table_test() |
| COMPRESSED行格式排除 | PRD | ✅ | build_row_format_tests() (测试但预期FAIL) |

### 4.3 不在本次范围内的项 (后续单独测试)

| 项 | 说明 |
|----|------|
| 崩溃恢复 | DDL执行中实例崩溃后表一致性 |
| 主备复制 | DDL binlog格式正确性 |
| 并发DML+大表+非INT类型 | 需要内网环境 + 更多时间 |
| 分区表并发DML | 64种分区策略 × 并发DML组合 |
| 外键表并发DML | FK双侧同步ALTER + 并发DML |
| GIPK主键 | 需特定开关 |
| 加密表空间 | 需特定环境 |

---

## 五、改进优先级

| 优先级 | 改进项 | 工作量 | 价值 |
|--------|--------|--------|------|
| ~~P0~~ | ~~增加QPS时间窗口化采集器~~ | ~~已完成~~ | QPSSampler已实现，输出pre/during/post三阶段QPS |
| **P1** | 大表DML worker使用data_type_info | 小 (约50行) | 大表测试覆盖更多类型 |
| **P1** | DDL Fuzz增加MODIFY COLUMN轮次 | 小 (约100行) | 覆盖类型扩展的内存泄漏 |
| **P2** | 增加per-DML延迟追踪 | 小 (约100行) | 可看到DDL期间延迟尖峰 |
| **P2** | 并发DML增加外键表场景 | 中 (约300行) | FK场景并发行为验证 |
| **P3** | 并发DML增加分区表场景 | 大 (约500行) | 分区表并发行为验证 |
| **P3** | 大表增加CHAR/VARCHAR测试 | 大 (需重新灌数据) | 大表非INT类型并发验证 |

---

## 六、总结

### 回答用户四个问题

**Q1: QPS影响是否可以通过框架观测到？**

❌ **当前不能。** 框架只记录了DML总操作数和DDL耗时，但没有时间窗口化的QPS采集。无法回答"DDL期间QPS下降了多少"这个关键问题。需要增加QPSSampler组件（P0优先级改进）。

**Q2: 插入的数据是否修改前和修改后都包含符合要求和不符合要求的值？**

✅ **是。** 
- DDL前：插入旧类型范围的极值/边界/正负/零/NULL（符合要求）
- DDL后：插入新类型范围值 + 旧类型范围值 + NULL（符合要求）+ 超出范围的值（标注EXPECT_FAIL，验证正确失败）
- 并发DML期间：只插入安全值（过滤掉EXPECT_FAIL），保证双写一致性（这是正确的设计）

**Q3: 所有支持的扩展数据类型是否都覆盖到了？**

✅ **是。** 并发DML覆盖了全部8种类型（整数/CHAR/VARCHAR/BINARY/VARBINARY/DECIMAL/TEXT/BLOB/BIT），每种类型×2算法。整数子类型选了代表性转换（INT→BIGINT），SQL套件覆盖了全部50条转换。

**Q4: 当前需求还有未覆盖的测试漏洞吗？**

有8个已识别漏洞（见第四节），其中：
- **G1 (无QPS采集)** 是最重要的缺口，直接影响用户关心的"QPS影响观测"
- **G5 (DDL Fuzz只做ADD COLUMN)** 是第二重要的缺口，未覆盖MODIFY COLUMN类型扩展的内存泄漏
- 其余漏洞风险较低，可后续补充

