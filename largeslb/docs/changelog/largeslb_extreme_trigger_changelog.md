# LargeSLB 极致触发方案 — 修改记录

> 日期：2026-06-17
> 背景：华为云数据库环境（4 存储节点 × 3 副本），`sal_tlb_max_size` 固定为 2MB 不可修改，需在真实 2MB 阈值上触发 LargeSLB 分拆路径。

---

## 一、新增文件

### 1. `largeslb_extreme_trigger.sql`（新建）

**用途**：5 种手动 SQL 触发脚本，最快 5 分钟验证 LargeSLB 分拆路径可达。

| 方式 | 名称 | 核心逻辑 | 预估 redo 量 | 触发可靠性 |
|------|------|----------|-------------|-----------|
| 1 | `lslb_extreme_same_page_hot` | 1 行更新 96 次 × 32KB payload | 96 × 32KB ≈ 3MB | 🟢 最可靠 |
| 2 | `lslb_extreme_large_single_bucket` | 160 行 × 32KB payload，单桶 | 160 × 32KB ≈ 5MB | 🟢 高 |
| 3 | `lslb_extreme_multi_batch` | 3 批次 × 128 行 × 16KB，同桶连续 | 3 × 2MB ≈ 6MB | 🟡 需延迟刷盘 |
| 4 | `lslb_extreme_boundary_2m` | 513 行 × 4KB = 2MB + 4KB | ≈ 2.001MB | 🟡 精确边界 |
| 5 | `lslb_extreme_blob_max` | 96 行 × 1MB LONGBLOB payload | 96 × 1MB ≈ 96MB | 🟢 极致 |

**每种方式都包含**：
- 建表 + 插入种子行
- 触发操作（事务/循环更新）
- 结果验证 SELECT
- `SHOW STATUS LIKE 'large_mtr'` 检查注释提示

**执行方式**：
```bash
mysql -h <host> -u root -p<pass> testdb < largeslb_extreme_trigger.sql
```

---

### 2. `largeslb_fuzz_extreme.py`（基于 `largeslb_fuzz.py` 修改）

**用途**：极致触发版 Fuzz 引擎，只运行能触发 SLB > 2MB 的场景。

---

## 二、源码修改细节

### 修改 1：场景权重（`weighted_kinds`）

**文件**：`largeslb_fuzz_extreme.py` 第 310-315 行

**原值**（9 个混合场景，总权重 130）：
```python
self.weighted_kinds = [
    ("large_single_bucket", 25),
    ("multi_batch_large", 20),
    ("multi_bucket_large", 15),
    ("same_page_hot", 10),
    ("boundary_2m", 10),
    ("char_varchar_boundary", 10),
    ("blob_family_large", 10),
    ("text_family_large", 10),
    ("small_fast_path", 20),
]
```

**修改后**（4 个触发场景，总权重 100）：
```python
self.weighted_kinds = [
    ("same_page_hot", 40),          # 同 page-id 累积，最可靠
    ("large_single_bucket", 30),    # 单桶大 payload
    ("multi_batch_large", 20),      # 多批次同桶累积
    ("boundary_2m", 10),            # 2MB 精确边界
]
```

**删除的场景及理由**：

| 删除场景 | 原权重 | 删除理由 |
|----------|--------|---------|
| `small_fast_path` | 20 | payload 128-2048 bytes，不可能触发 2MB 分拆，纯浪费时间 |
| `multi_bucket_large` | 15 | 2-4 桶分散写入，4 存储节点下 redo 被分散到多个 Slice |
| `char_varchar_boundary` | 10 | `char_255` 场景 payload 只有 255 bytes，不可能触发 |
| `blob_family_large` | 10 | 与 `large_single_bucket` 重复，且权重不够高 |
| `text_family_large` | 10 | 同上，与 `large_single_bucket` 重复 |

---

### 修改 2：`same_page_hot` repeat_updates 加倍

**文件**：`largeslb_fuzz_extreme.py` 第 371-384 行

**原值**：
```python
repeat_updates=self.rng.choice([64, 96, 128])
```

**修改后**：
```python
repeat_updates=self.rng.choice([128, 192, 256])
```

**效果对比**：

| repeat_updates | payload (longtext) | 单操作 redo 总量 | 超过 2MB |
|---------------|-------------------|-----------------|---------|
| 64 × 64KB | 4MB | ✅ | 原版最低 |
| 96 × 64KB | 6MB | ✅ | 原版中等 |
| **128 × 64KB** | 8MB | ✅ | 极致版最低 |
| **192 × 128KB** | 24MB | ✅ | 极致版中等 |
| **256 × 256KB** | 64MB | ✅ | 极致版最高 |

**核心原理**：same_page_hot 的所有 redo 属于同一 page_id → 映射到同一 Slice → 不受 4 存储节点分片影响，是唯一不受节点架构制约的触发方式。提高重复次数直接提高 redo 累积量。

---

### 修改 3：`large_single_bucket` rows_per_bucket 下限提高

**文件**：`largeslb_fuzz_extreme.py` 第 324-336 行

**原值**：
```python
rows_per_bucket=self.rng.choice([160, 192, 256, 384, 512])
```

**修改后**：
```python
rows_per_bucket=self.rng.choice([256, 384, 512])
```

**效果对比**（以 longtext_col safe_lengths 为例）：

| rows × payload | 原版最低 | 极致版最低 | 极致版最高 |
|-----------------|---------|-----------|-----------|
| 160 × 64KB | 10MB | — | — |
| 192 × 64KB | 12MB | — | — |
| **256 × 64KB** | — | 16MB | — |
| 384 × 256KB | — | — | 96MB |
| 512 × 1MB | — | — | 512MB |

去掉 160 和 192 两个低值，确保单桶操作 redo 至少 16MB（远超 2MB 阈值）。但在 4 存储节点下，单桶的行可能分散到多个 Slice，所以需要更大的总量来保证每个 Slice 上的份额超过 2MB。

---

## 三、参数策略建议

### 新增：高并发 sub-2MB burst 模式

如果目标是“每个 worker 生成大量但单事务 payload 低于 2MB 的 redo，并尽量同时提交，让底层更可能在同一存储/slice 上聚合触发”，应使用新模式：

```bash
python3.7 -u largeslb_fuzz_extreme.py \
  --sub2m-concurrent-burst \
  --sub2m-target-bytes 1835008 \
  --workers 32 \
  --bucket-count 1 \
  --rows-per-bucket 8192 \
  --target-fields longtext_col \
  --readonly-check-rate 0 \
  --replica-poll-interval 2 \
  --duration 2h \
  ...
```

该模式只生成 `sub2m_concurrent_burst` 场景：每个 worker 选择同一个逻辑 bucket 的不同连续行段，单 worker 单事务 payload 约 1.5MiB-1.9MiB 且小于 2MiB，并在事务提交前等待 barrier，尽量形成高并发同时提交。

### 内核参数（必须设置）

```sql
SET GLOBAL enable_large_slb = 1;                    -- 功能开关
SET GLOBAL innodb_log_write_max_size = 524288;      -- 512KB 最大 redo 批次
SET GLOBAL innodb_log_write_min_time_interval = 1000000; -- 1秒延迟刷盘
SET GLOBAL innodb_log_write_min_size = 131072;       -- 128KB 最小刷盘阈值
```

**如果不设这组参数**，redo 会频繁小批量刷盘，每个 flush session 累积量不够 2MB，即使 Fuzz payload 极大也无法触发。

### Fuzz CLI 参数对照

| 参数 | 原命令 | 极致触发推荐 | 改动理由 |
|------|--------|-------------|---------|
| `--bucket-count` | 64 ❌ | **2** ✅ | 少桶 → 少 Slice → 单 Slice 累积密度最大化 |
| `--workers` | 16 | **2** ✅ | ≤ bucket-count，避免锁竞争打断 flush session |
| `--target-fields` | 7个 | **longtext_col,longblob_col** | 专注最大容量字段（safe_lengths 到 1MB） |
| `--readonly-check-rate` | 1(每次) ❌ | **0** ✅ | 关闭只读验证开销，最大化 redo 生成速率 |
| `--replica-poll-interval` | 0.5 | **2** | 降低轮询频率 |
| `--duration` | 24h | **2h** | 极致触发只需短时间验证路径可达 |
| `--rows-per-bucket` | 4096 | **2048** | 2 桶 × 2048 行足够，太多行浪费种子时间 |

### 为什么 bucket-count=64 难触发

```
64 桶 → 数据分布到 ~64+ 个 Slice
4 存储节点 → Slice 分散到 4 个节点
每个 Slice 平均获得 redo = 总 redo / 64+ Slice 数

即使 Fuzz 总 redo 达到 100MB：
  单 Slice redo ≈ 100MB / 64 ≈ 1.56MB < 2MB ❌ 不触发

而 bucket-count=2：
  2 桶 → 数据集中在 ~2-4 个 Slice
  单 Slice redo ≈ 100MB / 4 ≈ 25MB >> 2MB ✅ 触发
```

---

## 四、打包文件

**文件名**：`largeslb_extreme_trigger_toolkit.tar.gz`
**位置**：`/Users/yuyu/Documents/largeslb/largeslb_extreme_trigger_toolkit.tar.gz`
**大小**：82KB

**包含内容**：

| 文件 | 类型 | 说明 |
|------|------|------|
| `largeslb_fuzz_extreme.py` | Python | 极致触发版 Fuzz 引擎 |
| `largeslb_extreme_trigger.sql` | SQL | 5 种手动触发脚本 |
| `largeslb_fuzz.py` | Python | 原版 Fuzz（未修改） |
| `largeslb_console.py` | Python | Web 控制台 |
| `largeslb_fuzz_toolkit_usage.md` | Markdown | 使用文档 |
| `largeslb_test_plan.md` | Markdown | 30 TC 测试计划 |
| `largeslb_test_plan_layered.md` | Markdown | 分层测试计划 |
| `largeslb_test_plan_scenario_chain.md` | Markdown | 场景链测试计划 |
| `requirements-largeslb-fuzz.txt` | Text | 依赖列表 |
| `largeslb_sql_cases/` | 目录 | 30 个 TC SQL 文件 |

---

## 五、推荐执行流程

```
Step 1: 设置内核参数（5 分钟）
  → SET GLOBAL enable_large_slb = 1;
  → SET GLOBAL innodb_log_write_max_size/min_time_interval/min_size

Step 2: SQL 手动触发验证（5 分钟）
  → mysql < largeslb_extreme_trigger.sql
  → SHOW STATUS LIKE 'large_mtr'
  → 如果 large_mtr > 0 → 路径可达，继续 Step 3
  → 如果 large_mtr = 0 → 检查内核参数是否生效

Step 3: 极致触发 Fuzz 持续压力（2 小时）
  → python3.7 -u largeslb_fuzz_extreme.py \
      --workers 2 --bucket-count 2 --duration 2h \
      --target-fields 'longtext_col,longblob_col' \
      --readonly-check-rate 0 ...

Step 4: 原版 Fuzz 回归测试（4-24 小时）
  → 确认触发后，用原版 largeslb_fuzz.py + 合理参数做回归
  → 验证高并发下分拆路径不出 bug
```
