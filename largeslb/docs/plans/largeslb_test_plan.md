# LargeSLB 特性测试计划

## 文档头部信息

| 属性 | 值 |
|------|-----|
| 特性名称 | LargeSLB：支持超过 2MB 的 SLB 原子性写入 |
| 内核版本 | Taurus/MySQL 8.0.41 兼容内核，以被测 LargeSLB 分支为准 |
| 特性类型 | 可靠性增强 / 存储链路增强 |
| 风险等级 | 高 |
| 设计日期 | 2026-05-23 |
| 需求来源 | file1.txt 测试设计模板、file2.txt 示例、file3.txt LargeSLB 需求说明 |

## 1. 特性概述

### 1.1 背景

当前一个或多个 GFB 汇聚成某个 SLB 后可能超过 2MB。旧逻辑在组织 slice flush session 时发现待组装 SLB 超过 2MB 会直接 crash 且不写入 slice，但 redo 可能已经并行写入 PWAL。实例重启后会持续 replay 这些 redo 并再次 crash，最终只能通过备份恢复，恢复时间长且存在数据丢失风险。

LargeSLB 的目标是在 SALSQL 模块支持 redo 组装成 SLB 后超过 2MB 的原子性：通过拆分 COMPACT 记录、按 LSN 顺序映射到 slice、拆分并刷写多个 TLB、用 unsafe LSN guard 阻止非安全边界推进 persistLSN/CV-LSN，保证主库、只读实例、恢复、failover 和补洞链路都只能观察到安全边界。

### 1.2 范围

**包含：**

- redo 组装成 SLB 后 `> 2MB` 的 LargeSLB 支持。
- GFB Parsing 阶段对超过 2MB 的 COMPACT 记录进行 segment 拆分。
- `space_page_key::compSeg`、`space_page_value::sealed` 语义正确性。
- `page_ref_map_t` 按日志记录 LSN 递增排序，避免 split-SLB LSN 范围重叠。
- GroupFlushLogHarvester 计算 GFB 所需 TLB 总数，覆盖 fast path 与 split path。
- `fillSliceFragment` 多 TLB 填充、flush、PMP 部分消费和 redo buffer 延迟释放。
- `SliceFlushSession::m_lsnGuard` / `SliceUnsafeLsns` unsafe LSN 保护。
- SYNC_MSG_SLICE 发送时机、CV-LSN、persistLSN、recycle LSN、release LSN 的安全推进。
- 只读实例查询正确性、failover、CR、补洞、gossip、异常恢复和版本替换。
- `enable_large_slb`、`sal_tlb_max_size`、`slice_tlb_size`、`slice_flush_size_threshold`、`slice_tlb_size_max` 参数矩阵。
- `large_mtr`、`large_mtr_size`、内核日志等观测指标。

**不包含：**

- 单个 redo record 自身超过 2MB 的完整支持。该场景在需求中明确需要进一步设计，当前属于不支持场景，预期行为是直接 crash。测试只做隔离负向验证：不得把 crash 判定为 LargeSLB 支持成功，不得在共享回归环境中批量执行。
- DFV 直接承载超过 2MB payload 的方案验证。需求已说明 DFV/Xnet 路径无法承载该能力。

### 1.3 核心验收标准

- `enable_large_slb=1` 时，redo 组装 SLB `> 2MB` 不再触发反复 crash，实例可正常 flush、重启恢复和继续服务。
- 所有 split TLB 成功 flush 到 Slice Store 前，不发送对应 GFB 的 SYNC_MSG_SLICE，不推进 CV-LSN。
- persistLSN/CV-LSN 只在安全 MTR/GFB 边界推进，不暴露非尾部 split-SLB 的 unsafe LSN。
- 主库和只读实例查询结果一致，failover/CR/补洞后数据一致。
- 非 LargeSLB 场景走 fast path，无明显性能退化。
- UT 行覆盖率不低于 95%，分支覆盖率不低于 85%。

## 2. 测试策略

### 2.1 分层策略

| 层级 | 目标 | 主要覆盖 |
|------|------|----------|
| UT | 验证内部数据结构和边界算法 | size 计算、segment 编号、sealed 状态、排序、TLB 总数、unsafe guard |
| 组件测试 | 验证 SALSQL 内部流程 | GFB Parsing、mapPagesToSlices、fillSliceFragment、completion handler、LSN-Watcher |
| 集成测试 | 验证主库到 Slice Store/只读实例链路 | split TLB flush、SYNC_MSG_SLICE、CV-LSN、只读查询 |
| 可靠性测试 | 验证 crash/restart/failover/CR/补洞 | crash loop 修复、故障注入、gossip 填洞 |
| 性能测试 | 验证无拆分退化和拆分开销 | QPS/TPS、flush latency、CPU/内存、TLB 计数开销 |
| 兼容性测试 | 验证参数、升级、版本替换 | `enable_large_slb` 开关、旧版本数据、灰度/回滚 |

### 2.2 优先级定义

| 优先级 | 定义 |
|--------|------|
| P0 | 直接影响数据正确性、原子性、crash recovery、CV-LSN 安全推进 |
| P1 | 影响边界、异常路径、性能退化、只读实例一致性 |
| P2 | 影响可观测性、工具、长尾参数组合、兼容性 |

### 2.3 关键观测点

- perfcounter：`large_mtr`、`large_mtr_size`。
- 参数：`enable_large_slb`、`sal_tlb_max_size`、`slice_tlb_size`、`slice_flush_size_threshold`、`slice_tlb_size_max`。
- 日志：GFB endLSN、split segment 数、每个 TLB startLSN/endLSN、TLB flush completion、SYNC_MSG_SLICE 发送、CV-LSN/persistLSN 推进、unsafe LSN add/remove。
- 内部断言或 debug counter：GFB 需要的 TLB 总数、已完成 TLB 数、m_lsnGuard size、redo buffer release 时机、PMP remaining log bytes。
- 数据校验：主库/只读节点 checksum、行数、事务结果、恢复后业务一致性。

## 3. 功能测试场景

### 3.1 场景分类

| 场景类型 | 覆盖情况 | 说明 |
|----------|----------|------|
| 正向场景 | 覆盖 | LargeSLB 拆分、flush、同步、恢复成功 |
| 边界场景 | 覆盖 | 2MB 附近、TLB 大小边界、多 segment、多 slice、多 GFB |
| 异常场景 | 覆盖 | flush 失败、crash、网络异常、磁盘满、单 redo >2MB 不支持并直接 crash |
| 组合场景 | 覆盖 | 只读实例、failover、CR、补洞、版本替换、长稳 |
| 回归场景 | 覆盖 | 非 LargeSLB fast path、watchPersistLsn、普通主从复制 |

### 3.2 功能用例列表

#### TC-001：非 LargeSLB fast path 回归

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 回归 |
| 前置条件 | `enable_large_slb=1`，业务写入正常，构造每个 slice 的 SLB 小于 2MB |
| 测试步骤 | 1. 使用 sysbench 或自定义脚本持续写入普通小事务。<br>2. 观察 GroupFlushLogHarvester 未设置 split 标志。<br>3. 校验每个 GFB 到目标 slice 仍最多一个 TLB。<br>4. 校验主库、只读实例数据一致。 |
| 预期结果 | fast path 生效；无 split TLB；`large_mtr` 不增长；QPS/TPS 与基线无明显退化。 |
| 验证点 | 无拆分路径性能、旧逻辑兼容、指标不误报。 |

#### TC-002：单会话单 slice 多批 redo 触发 LargeSLB 拆分

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 正向 |
| 前置条件 | `enable_large_slb=1`；`innodb_log_write_max_size` 最大只有 512KB，因此单次 redo write 不会达到 2MB；使用单会话大事务产生多批 redo/GFB，并使其在同一 slice flush session 中汇聚 |
| 测试步骤 | 1. 设置 `innodb_log_write_max_size=524288`、`innodb_log_write_min_time_interval=1000000`、`innodb_log_write_min_size=131072`。<br>2. 构造单会话大事务，使多批 redo 映射到同一 slice 后累计超过当前 TLB/SLB 阈值。<br>3. 等待 flush 完成并观察 split segment/TLB 日志。<br>4. 校验业务事务提交成功并可查询。 |
| 预期结果 | 多批 GFB 在同一 slice 汇聚后触发 LargeSLB，被拆成多个 split TLB，全部 flush 成功；不 crash；业务结果正确。 |
| 验证点 | 多批 redo/GFB 汇聚、split 触发、TLB 数正确、flush 完整、数据正确。 |

#### TC-003：多个 GFB 汇聚成同一 SLB 超过 2MB

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 正向 |
| 前置条件 | 多个并发写入线程命中同一目标 slice，使多个 GFB 汇聚后 SLB 超阈值 |
| 测试步骤 | 1. 启动多连接写入热点 page/slice。<br>2. 控制 flush 周期，使多个 GFB 被组织到同一 slice flush session。<br>3. 观察 split TLB 与 GFB_info 依赖关系。<br>4. 校验所有 GFB 的 endLSN 最终安全推进。 |
| 预期结果 | 多 GFB 场景下 TLB 总数计算正确；每个 GFB 所依赖的 split TLB 都完成后才推进。 |
| 验证点 | 跨 GFB 计数、依赖关系、SYNC_MSG_SLICE 时机。 |

#### TC-004：同一 page-id 多个 COMPACT segment 拆分

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 正向 / UT |
| 前置条件 | 可通过 UT 或 debug 注入构造同一 page-id 的多条 COMPACT redo，总大小超过 TLB 上限 |
| 测试步骤 | 1. 调用 `sal_scan_redo_log_buffer` 构建 page_map_t。<br>2. 逐条加入同 page-id log record。<br>3. 在超过上限时检查旧 segment 被 seal，并创建新 segment。 |
| 预期结果 | `space_page_key::compSeg` 从 0 递增；同一 page-id 存在多个 map entry；head segment 的 `sealed` 非 0 时表示当前活跃 segment；非 head segment 的 `sealed` 与自身 segment 编号一致。 |
| 验证点 | segment 编号、sealed 语义、head/current segment 查找。 |

#### TC-005：2MB 边界值：低于、等于、刚超过

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 边界 |
| 前置条件 | 可精确控制 log payload 与元数据大小 |
| 测试步骤 | 1. UT/debug 注入精确构造含 `RECORD_LSN_SIZE`、`SLICE_LOG_RECORD_FOOTER_SIZE`、`PACK_HEADER_SIZE`、`SLB_HEADER_SIZE`、`SLB_FOOTER_SIZE` 和 Intel Disk padding 后总大小为 `2MB-1`。<br>2. UT/debug 注入精确构造总大小等于 `2MB`。<br>3. UT/debug 注入精确构造总大小为 `2MB+1`。<br>4. SQL 辅助脚本使用 511/512/513 行 x 4KB 作为近似压力流量，最终边界判定以 UT/debug size 统计为准。 |
| 预期结果 | `<=2MB` 不拆分或不超过单 TLB 上限；`>2MB` 必须拆分；size 计算包含所有元数据和 padding。 |
| 验证点 | size 计算精确性、off-by-one、padding 影响。 |

#### TC-006：单条 redo record 超过 2MB 不支持并直接 crash

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 异常 / 负向 / 不支持 |
| 前置条件 | 隔离可丢弃实例；优先用 debug/UT 构造单条 redo record 含元数据后超过 2MB。SQL 脚本只能作为尝试性压力输入，不保证一定产生单条 redo record |
| 测试步骤 | 1. 输入单条超大 redo record。<br>2. 执行 parsing/flush 路径。<br>3. 观察实例 crash、错误栈和最后 LSN。<br>4. 清理或重建隔离实例。 |
| 预期结果 | 实例直接 crash；该场景明确不属于 LargeSLB 支持范围；不得将 crash 误判为缺陷修复失败；不得在共享环境批量执行。 |
| 验证点 | out-of-scope 场景隔离、crash 行为符合预期、不会被测试报告误标为支持。 |

#### TC-007：page_ref_map_t 按 LSN 递增排序

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | UT / 组件 |
| 前置条件 | 构造乱序 page_map_t，包含多个 page-id、多个 compSeg、多个 LSN 范围 |
| 测试步骤 | 1. 执行 `mapPagesToSlices`。<br>2. 读取每个 slice 的 `page_ref_map_t`。<br>3. 检查 log record 的 LSN 顺序。 |
| 预期结果 | 每个 slice 中的记录按 LSN 递增；split-SLB LSN 范围无重叠、无倒序。 |
| 验证点 | 排序稳定性、跨 page-id 顺序、跨 segment 顺序。 |

#### TC-008：多 slice 同时存在 LargeSLB

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 正向 |
| 前置条件 | 构造写入命中多个 slice，至少两个 slice 产生 split TLB |
| 测试步骤 | 1. 并发写入不同表/页使多个 slice 触发 LargeSLB。<br>2. 观察每个 slice 的 TLB 计数和 flush completion。<br>3. 校验 GFB 总完成条件。 |
| 预期结果 | 每个 slice 的 split 独立正确；GFB 总 TLB 完成计数等于各 slice split TLB 之和；所有完成后才推进 CV-LSN。 |
| 验证点 | 多 slice 计数、并发完成顺序、全局推进条件。 |

#### TC-009：GroupFlushLogHarvester TLB 总数计算

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | UT / 组件 |
| 前置条件 | 准备无拆分、单 slice 拆分、多 slice 拆分、多 GFB 汇聚四类输入 |
| 测试步骤 | 1. 分别输入四类 page_ref_map。<br>2. 计算期望 TLB 总数。<br>3. 对比 GroupFlushLogHarvester 维护的 GFB TLB 个数。 |
| 预期结果 | 无拆分时仍走快速路径；拆分时总数精确，不少算导致提前 SYNC，不多算导致卡住。 |
| 验证点 | fast path、split 标志、计数准确性。 |

#### TC-010：fillSliceFragment 当前 TLB 不足时先 flush

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 组件 |
| 前置条件 | 当前 TLB 已含前一个 SLB 的部分数据，剩余空间不足以容纳下一条 log record |
| 测试步骤 | 1. 构造当前 TLB 非空且空间不足。<br>2. 调用 `fillSliceFragment`。<br>3. 观察先 flush 当前 TLB，再分配/填充新 TLB。 |
| 预期结果 | 不覆盖旧数据；不产生超限 TLB；flush 顺序与 LSN 顺序一致。 |
| 验证点 | TLB 空间判断、flush 顺序、动态临时 TLB 分配。 |

#### TC-011：PMP 部分消费后继续处理

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 组件 |
| 前置条件 | 一个 PMP 上挂载的 log record 需要跨多个 TLB 拆分 |
| 测试步骤 | 1. 调用 `fillSliceFragment` 消费部分 log record。<br>2. 触发 TLB 满并 flush。<br>3. 再次调用 `fillSliceFragment`。 |
| 预期结果 | PMP 不会被过早从 flush session 列表删除；已消费偏移正确记录；后续调用从正确位置继续。 |
| 验证点 | PMP 生命周期、remaining bytes、无重复/遗漏复制。 |

#### TC-012：redo log buffer 延迟释放

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 组件 / 可靠性 |
| 前置条件 | 构造大型 SLB，需要多个 split TLB 才能完整复制 |
| 测试步骤 | 1. 在第一个 split TLB 复制后暂停。<br>2. 检查 redo log buffer 是否仍被持有。<br>3. 所有 split TLB 复制完成后再次检查。 |
| 预期结果 | 所有日志被消费并复制到 split TLB 之前，redo log buffer 不释放回 SQL 层；全部复制后正常释放。 |
| 验证点 | buffer 生命周期、并发安全、无 use-after-free。 |

#### TC-013：unsafe LSN guard 阻止非安全边界 persistLSN

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 组件 / 正向 |
| 前置条件 | 一个 LargeSLB 拆为 3 个 TLB，前 2 个为非尾部 split TLB |
| 测试步骤 | 1. flush 第 1 个非尾部 TLB。<br>2. 尝试推进 persistLSN 到该 TLB endLSN。<br>3. flush 第 2 个非尾部 TLB 并再次尝试。<br>4. flush 尾部 TLB。 |
| 预期结果 | 非尾部 endLSN 被加入 m_lsnGuard，persistLSN 不得推进到 unsafe LSN；尾部完成后推进到 GFB 安全边界，并清理小于等于 safe persist LSN 的 unsafe LSN。 |
| 验证点 | unsafe add/check/remove、safe boundary、guard 清理。 |

#### TC-014：completion handler 和 LSN-Watcher 双路径推进

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 组件 / 回归 |
| 前置条件 | 支持控制 flush completion handler 或 LSN-Watcher 分别成为推进 persistLSN 的触发方 |
| 测试步骤 | 1. 场景 A：由 completion handler 推进 persistLSN。<br>2. 场景 B：阻塞 completion 推进，由 LSN-Watcher 发现并推进。<br>3. 对比 unsafe guard 行为。 |
| 预期结果 | 两条路径都检查 m_lsnGuard；都只推进 safe persist LSN；unsafe LSN 清理一致。 |
| 验证点 | watchPersistLsn 历史问题回归、双路径一致性。 |

#### TC-015：所有 TLB 完成前不发送 SYNC_MSG_SLICE

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 集成 |
| 前置条件 | 一个 GFB 拆成多个 TLB，可注入部分 TLB flush 延迟 |
| 测试步骤 | 1. 触发 LargeSLB。<br>2. 延迟最后一个 split TLB 的 async-flush completion。<br>3. 观察 SyncMsgSliceManager 状态和消息发送。<br>4. 恢复最后一个 completion。 |
| 预期结果 | 延迟期间不发送该 GFB 的 SYNC_MSG_SLICE，不推进 SQL Replica CV-LSN；最后一个 TLB 完成后才发送并推进。 |
| 验证点 | TLB completion 计数、SYNC 发送时机、CV-LSN 安全性。 |

#### TC-016：只读实例读取安全 CV-LSN

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 集成 |
| 前置条件 | 一主一只读实例，LargeSLB 流量稳定触发 |
| 测试步骤 | 1. 主库持续写入触发 LargeSLB。<br>2. 只读实例持续按最新可见 CV-LSN 查询。<br>3. 在 split TLB 部分完成期间读取热点数据。<br>4. 对比主库安全边界数据。 |
| 预期结果 | 只读实例只观察到 safe CV-LSN；查询无缺页、无半个 MTR 可见、无数据不一致。 |
| 验证点 | 只读一致性、CV-LSN 边界、查询正确性。 |

#### TC-017：recycle LSN / release LSN 安全推进

| 字段 | 内容 |
|------|------|
| 优先级 | P1 |
| 场景类型 | 集成 |
| 前置条件 | LargeSLB 写入持续运行，开启 recycle/release 相关日志或指标 |
| 测试步骤 | 1. 触发多个 LargeSLB。<br>2. 记录 CV-LSN、recycle LSN、release LSN。<br>3. 注入部分 TLB flush 延迟。 |
| 预期结果 | recycle LSN 和 release LSN 依赖 safe CV-LSN，不越过未完成 LargeSLB 的安全边界。 |
| 验证点 | 日志回收安全、buffer release 安全。 |

#### TC-018：failover 期间存在未完成 split TLB

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 可靠性 |
| 前置条件 | 主备/只读拓扑可执行 failover，LargeSLB 正在 flush |
| 测试步骤 | 1. 触发 LargeSLB 并延迟部分 split TLB。<br>2. 在 flush 未完全完成时发起 failover。<br>3. 新主拉起后执行一致性校验。 |
| 预期结果 | failover 不选择 unsafe LSN 作为可见边界；新主正常服务；数据无丢失、无半事务。 |
| 验证点 | 倒换 LSN、恢复边界、拓扑一致性。 |

#### TC-019：CR 恢复起点基于 safe CV-LSN

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 可靠性 |
| 前置条件 | 可触发 CR 流程，LargeSLB 流量存在 |
| 测试步骤 | 1. 写入并触发多个 LargeSLB。<br>2. 在不同 split 完成阶段触发 CR。<br>3. 记录恢复起始点 LSN。<br>4. 校验恢复后数据。 |
| 预期结果 | CR 起点来自 safe CV-LSN 且位于 GFB 边界；恢复成功；数据一致。 |
| 验证点 | CR 起点、GFB 边界、恢复正确性。 |

#### TC-020：Slice Store 补洞按 split-SLB 粒度填充

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 可靠性 / 补洞 |
| 前置条件 | Slice Store 支持模拟缺失某个 split-SLB |
| 测试步骤 | 1. 触发 LargeSLB 并成功生成多个 split TLB。<br>2. 人为删除或屏蔽其中一个非尾部或尾部 split-SLB。<br>3. 触发 gossip/补洞。<br>4. 校验 served LSN 和数据。 |
| 预期结果 | Slice Store 可按 split-SLB 粒度识别空洞并填充；补洞后 served LSN 连续；数据可读。 |
| 验证点 | gap 检测、gossip 填充、尾部/非尾部差异。 |

#### TC-021：异常后版本替换正常拉起

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 兼容 / 可靠性 |
| 前置条件 | sysbench 标准模型表已导入数据；写负载运行；旧版本或旧配置可触发 LargeSLB 异常 |
| 测试步骤 | 1. 配置 `innodb_log_write_max_size`、`innodb_log_write_min_time_interval`、`innodb_log_write_min_size` 为大值。<br>2. 触发历史异常场景。<br>3. 替换到支持 LargeSLB 的版本。<br>4. 重启拉起实例并校验数据。 |
| 预期结果 | 版本替换后实例正常拉起，不再反复 crash；数据一致。 |
| 验证点 | 历史问题修复、恢复兼容、数据完整性。 |

#### TC-022：`enable_large_slb` 开启前后对比

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 参数 / 兼容 |
| 前置条件 | sysbench 标准模型表；`sal_tlb_max_size` 设置为小值便于触发 |
| 测试步骤 | 1. 设置 `enable_large_slb=0`，触发 LargeSLB 对照场景并记录行为。<br>2. 设置 `enable_large_slb=1`。<br>3. 使用相同负载再次触发。<br>4. 对比日志、指标和恢复结果。 |
| 预期结果 | 开启后 LargeSLB 正常处理并能拉起；关闭时行为符合旧版本/旧配置预期且不得误报为通过。 |
| 验证点 | 开关有效性、对照实验、观测指标。 |

#### TC-023：参数合法性与边界

| 字段 | 内容 |
|------|------|
| 优先级 | P1 |
| 场景类型 | 参数 |
| 前置条件 | 可动态或重启配置相关参数 |
| 测试步骤 | 1. 分别设置 `slice_tlb_size` 为 4KB、64KB、2MB。<br>2. 分别设置 `slice_flush_size_threshold` 为 4KB、64KB、2MB。<br>3. 分别设置 `slice_tlb_size_max` 为 64KB、2MB。<br>4. 尝试非法组合：`slice_tlb_size > slice_tlb_size_max`、`slice_flush_size_threshold > slice_tlb_size_max`。 |
| 预期结果 | 合法范围内行为正确；非法组合被拒绝或有明确错误；不会进入不可诊断状态。 |
| 验证点 | 参数约束、错误提示、重启/动态变更行为。 |

#### TC-024：`sal_tlb_max_size` 从 64KB 到 2MB 矩阵

| 字段 | 内容 |
|------|------|
| 优先级 | P1 |
| 场景类型 | 参数 / 边界 |
| 前置条件 | `enable_large_slb=1` |
| 测试步骤 | 1. 取 `sal_tlb_max_size` = 64KB、128KB、512KB、1MB、2MB。<br>2. 对每个值构造超过该上限的 LargeSLB。<br>3. 记录 split TLB 数量和 flush latency。 |
| 预期结果 | 每个参数值下 TLB 不超过上限；split 数量与预期一致；2MB 最大值仍可正确处理。 |
| 验证点 | 最大 TLB 限制、拆分比例、性能趋势。 |

#### TC-025：flush 失败和重试

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 异常 |
| 前置条件 | 可注入 Slice Store 单个 split TLB flush 失败 |
| 测试步骤 | 1. 触发 LargeSLB，注入第 N 个 split TLB 首次 flush 失败。<br>2. 观察 completion、guard、SYNC 消息。<br>3. 解除故障后重试 flush。 |
| 预期结果 | 失败期间不推进 safe LSN，不发送 SYNC_MSG_SLICE；重试成功后完整推进；无重复写入导致的数据错误。 |
| 验证点 | 失败隔离、重试幂等、LSN 安全。 |

#### TC-026：进程 crash 后 replay LargeSLB

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 可靠性 |
| 前置条件 | LargeSLB redo 已写 PWAL，可在不同阶段 kill 进程 |
| 测试步骤 | 1. 在 parsing 后、部分 TLB flush 后、全部 TLB flush 前、全部 TLB flush 后四个阶段分别 `kill -9`。<br>2. 重启实例。<br>3. 观察 redo replay、slice flush 和数据校验。 |
| 预期结果 | 不发生反复 crash；replay 后要么回到上一个 safe LSN，要么完成 LargeSLB；数据一致。 |
| 验证点 | crash recovery、原子性、幂等。 |

#### TC-027：磁盘满/空间不足

| 字段 | 内容 |
|------|------|
| 优先级 | P1 |
| 场景类型 | 异常 |
| 前置条件 | 可对 Slice Store 或 WAL 所在盘注入空间不足 |
| 测试步骤 | 1. 触发 LargeSLB。<br>2. 在 split TLB flush 中途注入磁盘满。<br>3. 观察错误处理、LSN 推进和恢复。 |
| 预期结果 | 返回明确错误或进入可恢复状态；不推进 unsafe LSN；释放故障后可继续或按预期恢复。 |
| 验证点 | 资源耗尽处理、错误日志、数据安全。 |

#### TC-028：网络抖动/断连影响 Slice Store replica

| 字段 | 内容 |
|------|------|
| 优先级 | P1 |
| 场景类型 | 异常 / 集成 |
| 前置条件 | 至少一个 slice store replica，可注入网络延迟/断连 |
| 测试步骤 | 1. 触发 LargeSLB。<br>2. 对部分 replica 注入网络抖动。<br>3. 确认至少一个 replica 可服务到 GFB endLSN。 |
| 预期结果 | 只在满足 replica 服务连续性后推进；网络恢复后副本通过补洞追平。 |
| 验证点 | replica 可服务性、served LSN、补洞。 |

#### TC-029：长稳写入 LargeSLB

| 字段 | 内容 |
|------|------|
| 优先级 | P0 |
| 场景类型 | 稳定性 |
| 前置条件 | sysbench 标准模型表；写负载可持续触发 LargeSLB |
| 测试步骤 | 1. 配置小 TLB 阈值和大 redo 聚合参数。<br>2. 持续运行读写混合负载 72 小时。<br>3. 周期性校验数据、指标和日志。 |
| 预期结果 | 正常执行，不 crash；无内存泄漏；`large_mtr` 持续增长且 large_mtr_size 合理；只读查询正确。 |
| 验证点 | 长稳、资源泄漏、持续拆分正确性。 |

#### TC-030：高并发大事务混合小事务

| 字段 | 内容 |
|------|------|
| 优先级 | P1 |
| 场景类型 | 组合 / 性能 |
| 前置条件 | 同时运行大 MTR 写入和普通 OLTP 写入 |
| 测试步骤 | 1. 20% 连接构造 LargeSLB，80% 连接运行普通 sysbench oltp_write。<br>2. 持续 30 分钟。<br>3. 校验小事务延迟和大事务成功率。 |
| 预期结果 | 大小事务都正确提交；普通事务不被长期阻塞；无锁等待异常放大。 |
| 验证点 | 并发互相影响、延迟尾部、吞吐。 |

### 3.3 用例 SQL 验证脚本

每个 TC 用例的 SQL 已整理为独立脚本：[largeslb_case_sql.sql](</Users/yuyu/Documents/New project 7/largeslb_case_sql.sql>)。脚本通过存储过程造数和更新，避免在测试计划中展开超长 INSERT/UPDATE。

执行建议：

- 先加载过程：`mysql -h127.0.0.1 -P3306 -utest -ptest < /Users/yuyu/Documents/New\ project\ 7/largeslb_case_sql.sql`
- 每次只执行一个用例过程，例如：`CALL largeslb_test.lgslb_tc002();`
- 执行前建议设置 `max_allowed_packet >= 64M`，并按用例需要配置 `enable_large_slb`、`sal_tlb_max_size`、`slice_tlb_size`、`slice_flush_size_threshold`、`slice_tlb_size_max`。
- 当前内核中 `innodb_log_write_max_size` 最大只有 512KB，因此 SQL 用例不能依赖单次 redo write 形成 2MB；所有 `>2MB` 正向用例都应理解为“多批 redo/GFB 在 slice flush session 内累计汇聚后超过阈值”。
- 若要稳定覆盖拆分代码路径，可先使用低 TLB 阈值参数 profile；若要验证真实 2MB 边界，必须使用真实 2MB profile 并结合内核 size 统计确认。
- SQL 中的 `bucket` 是 SQL 侧的分组代理，用来制造热点/多组数据；真实 slice-id、page-id、TLB 数、unsafe LSN 和 SYNC_MSG_SLICE 时机仍需以内核日志、perfcounter、debug hook 或 UT 断言为准。
- 并发、failover、CR、kill -9、磁盘满、网络断连、flush 失败等场景无法由单个 SQL 文件独立完成；对应 SQL 只提供负载入口，必须配合多客户端压测工具或故障注入框架执行完整场景。
- TC-006 是不支持场景，过程 `lgslb_tc006_unsupported_single_redo_crash()` 默认只在脚本末尾以注释形式给出。必须在隔离可丢弃实例中单独执行，预期结果是直接 crash。

| 用例 | 存储过程 | 数据规模 | 主要验证点 |
|------|----------|----------|------------|
| TC-001 | `CALL largeslb_test.lgslb_tc001();` | 1000 行，seed 512B，更新 100 行 x 1KB | 非 LargeSLB fast path，不触发 split |
| TC-002 | `CALL largeslb_test.lgslb_tc002();` | 192 行 x 32KB，同 bucket 更新 160 行，约 5MB | 单会话多批 redo/GFB 在同一 slice 汇聚后拆分 |
| TC-003 | `CALL largeslb_test.lgslb_tc003();` | 384 行 x 16KB，三批同 bucket 更新 | 多 GFB 汇聚同一 SLB |
| TC-004 | `CALL largeslb_test.lgslb_tc004();` | 单行重复更新 96 次 x 32KB，约 3MB redo 压力 | 同 page-id COMPACT segment 拆分辅助触发 |
| TC-005 | `CALL largeslb_test.lgslb_tc005();` | 511/512/513 行 x 4KB，覆盖 2MB 附近 | `2MB-1`、`2MB`、`2MB+1` 边界 |
| TC-006 | `CALL largeslb_test.lgslb_tc006_unsupported_single_redo_crash();` | 单行更新 2,200,000B | 单 redo >2MB 不支持，隔离执行，预期 crash |
| TC-007 | `CALL largeslb_test.lgslb_tc007();` | 512 行 x 8KB，乱序 bucket 更新 | LSN 排序辅助触发 |
| TC-008 | `CALL largeslb_test.lgslb_tc008();` | 768 行 x 16KB，4 个 bucket 各 96 行 | 多 slice 同时 split |
| TC-009 | `CALL largeslb_test.lgslb_tc009();` | 960 行 x 8KB，无拆分/单拆分/多拆分三组 | GFB TLB 总数计算 |
| TC-010 | `CALL largeslb_test.lgslb_tc010();` | 260 行，先小更新再 240 行 x 8KB | 当前 TLB 不足时先 flush |
| TC-011 | `CALL largeslb_test.lgslb_tc011();` | 单行重复更新 128 次 x 24KB | PMP 部分消费后继续处理 |
| TC-012 | `CALL largeslb_test.lgslb_tc012();` | 320 行 x 24KB，更新 256 行 | redo buffer 延迟释放 |
| TC-013 | `CALL largeslb_test.lgslb_tc013();` | 384 行 x 16KB，约 6MB | unsafe LSN guard |
| TC-014 | `CALL largeslb_test.lgslb_tc014();` | 384 行 x 16KB，两个 bucket 分别更新 | completion handler 与 LSN-Watcher 双路径 |
| TC-015 | `CALL largeslb_test.lgslb_tc015();` | 448 行 x 16KB，约 7MB | 全部 TLB 完成前不发 SYNC_MSG_SLICE |
| TC-016 | `CALL largeslb_test.lgslb_tc016();` | 512 行 x 16KB，4 bucket 更新 | 只读实例 safe CV-LSN |
| TC-017 | `CALL largeslb_test.lgslb_tc017();` | 640 行 x 8KB，4 bucket 更新 | recycle/release LSN 安全推进 |
| TC-018 | `CALL largeslb_test.lgslb_tc018();` | 512 行 x 16KB，2 bucket 更新 | failover 期间未完成 split TLB |
| TC-019 | `CALL largeslb_test.lgslb_tc019();` | 512 行 x 16KB，2 bucket 更新 | CR 起点基于 safe CV-LSN |
| TC-020 | `CALL largeslb_test.lgslb_tc020();` | 512 行 x 16KB，2 bucket 更新 | Slice Store 按 split-SLB 补洞 |
| TC-021 | `CALL largeslb_test.lgslb_tc021();` | 768 行 x 16KB，同 bucket 更新 512 行 | 异常后版本替换拉起 |
| TC-022 | `CALL largeslb_test.lgslb_tc022();` | 640 行 x 16KB，同 bucket 更新 320 行 | `enable_large_slb` 开启前后对比 |
| TC-023 | `CALL largeslb_test.lgslb_tc023();` | 512 行，4KB/64KB/1MB 三档更新 | 参数合法性与边界 |
| TC-024 | `CALL largeslb_test.lgslb_tc024();` | 1100 行 x 4KB，64KB 到 2MB+ 阶梯更新 | `sal_tlb_max_size` 矩阵 |
| TC-025 | `CALL largeslb_test.lgslb_tc025();` | 512 行 x 16KB | flush 失败和重试注入 |
| TC-026 | `CALL largeslb_test.lgslb_tc026();` | 512 行 x 16KB | crash 后 replay LargeSLB |
| TC-027 | `CALL largeslb_test.lgslb_tc027();` | 512 行 x 16KB | 磁盘满/空间不足注入 |
| TC-028 | `CALL largeslb_test.lgslb_tc028();` | 512 行 x 16KB，4 bucket 更新 | replica 网络抖动/断连 |
| TC-029 | `CALL largeslb_test.lgslb_tc029();` | 1024 行 x 8KB，两轮全量更新 | 72 小时长稳的单轮 SQL 负载 |
| TC-030 | `CALL largeslb_test.lgslb_tc030();` | 1280 行，大事务 256 行 x 16KB，小事务 7x80 行 x 2KB | 高并发大小事务混合 |

## 4. UT 设计

### 4.1 UT 覆盖清单

| 编号 | 模块/函数 | 输入 | 验证点 | 优先级 |
|------|-----------|------|--------|--------|
| UT-001 | size 计算 | 不同 payload、metadata、padding 组合 | 每条记录和每个 SLB 的 size 包含完整元数据 | P0 |
| UT-002 | `sal_scan_redo_log_buffer` | 同 page-id 累计超过上限 | seal 当前 segment 并创建新 compSeg | P0 |
| UT-003 | `space_page_key` | 相同 space/page、不同 compSeg | hash/equal/order 行为正确，不互相覆盖 | P0 |
| UT-004 | `space_page_value::sealed` | head/non-head segment | sealed=0/非0 语义正确 | P0 |
| UT-005 | `mapPagesToSlices` | 乱序 LSN 输入 | 输出按 LSN 递增排序 | P0 |
| UT-006 | GroupFlushLogHarvester | 无拆分输入 | fast path 不引入额外开销 | P1 |
| UT-007 | GroupFlushLogHarvester | 单/多 slice 拆分输入 | GFB TLB 总数正确 | P0 |
| UT-008 | `fillSliceFragment` | 当前 TLB 空间不足 | 先 flush 再继续填充，不超限 | P0 |
| UT-009 | `fillSliceFragment` | PMP 跨 TLB | 消费偏移正确，PMP 生命周期正确 | P0 |
| UT-010 | redo buffer 管理 | 多 split TLB | 所有 log 被复制前不释放 | P0 |
| UT-011 | `SliceUnsafeLsns` | add/check/remove | unsafe LSN 被保护，safe 推进后清理 | P0 |
| UT-012 | completion handler | 非尾部 split 完成 | 不推进到 unsafe LSN | P0 |
| UT-013 | LSN-Watcher | watcher 触发推进 | 与 completion handler 行为一致 | P0 |
| UT-014 | SyncMsgSliceManager | 多 split TLB completion | 全部完成前不生成 SYNC_MSG_SLICE | P0 |
| UT-015 | 异常输入 | 单 redo >2MB | 不支持场景，直接 crash；仅在隔离测试中确认行为 | P0 |

### 4.2 UT 覆盖率要求

- LargeSLB 相关新增/修改代码行覆盖率不低于 95%。
- LargeSLB 相关新增/修改代码分支覆盖率不低于 85%。
- 必须包含 `2MB-1`、`2MB`、`2MB+1` 三类边界。
- 必须包含 head segment 与非 head segment 的 sealed 状态。
- 必须包含 completion handler 和 LSN-Watcher 两条 persistLSN 推进路径。

## 5. 性能测试

### 5.1 性能指标

| 指标类型 | 指标名称 | 基准参考 | 验收标准 |
|----------|----------|----------|----------|
| 吞吐 | QPS/TPS | 未开启 LargeSLB 或无拆分 fast path | 无拆分场景退化不超过 3%，拆分场景符合容量预期 |
| 延迟 | 事务平均/P99 延迟 | 同配置旧版本或关闭开关 | 无拆分 P99 退化不超过 5%，拆分场景无不可接受尖刺 |
| Flush | TLB flush latency | 普通 SLB | split TLB 单次 flush 不超基线 1.5 倍，总耗时随 split 数线性增长 |
| 同步 | SYNC_MSG_SLICE 发送延迟 | 普通 GFB | 不提前发送，额外等待只来自真实 split TLB completion |
| 资源 | CPU/内存 | 开关关闭 | CPU 增幅可解释，内存无持续增长 |
| 观测 | `large_mtr_size` | 构造数据大小 | 与预期大小偏差在可解释范围内 |

### 5.2 性能场景

| 编号 | 场景 | 数据/配置 | 并发 | 时长 | 验收 |
|------|------|-----------|------|------|------|
| PT-001 | fast path 基准 | `enable_large_slb=1`，但 SLB < 阈值 | 1/16/64/128 | 每组 10 分钟 | 与关闭开关相比 QPS/TPS 退化不超过 3% |
| PT-002 | 小阈值拆分压力 | `slice_tlb_size=4KB`，稳定触发多 split | 16/64 | 每组 30 分钟 | 无 crash，无 LSN 卡死，延迟可解释 |
| PT-003 | 64KB TLB | `sal_tlb_max_size=64KB` | 64 | 30 分钟 | split 数、flush 次数符合预期 |
| PT-004 | 2MB TLB | `sal_tlb_max_size=2MB`，真实大 SLB | 64 | 30 分钟 | 大于 2MB 时拆分，TLB 不超 2MB |
| PT-005 | 大小事务混合 | LargeSLB 20%，普通 OLTP 80% | 128 | 60 分钟 | 普通事务 P99 无异常放大 |
| PT-006 | 只读实例延迟 | 主库 LargeSLB + 只读持续查询 | 读 64 / 写 64 | 60 分钟 | 只读 CV-LSN 延迟可解释，查询正确 |
| PT-007 | 版本对比 | 修复前/后或开关前/后 | 相同 | 每组 30 分钟 | 新版本不反复 crash；fast path 无显著退化 |

## 6. 兼容性与升级测试

| 编号 | 场景 | 步骤 | 预期 |
|------|------|------|------|
| CT-001 | 原地升级 | 旧版本写入普通数据，升级到 LargeSLB 版本，运行普通 + LargeSLB 流量 | 数据无损，普通路径正常，LargeSLB 生效 |
| CT-002 | 异常后版本替换 | 按 TC-021 触发历史异常后替换版本 | 能正常拉起并恢复 |
| CT-003 | 开关灰度 | `enable_large_slb=0 -> 1 -> 0 -> 1` 重启/动态配置按实际能力验证 | 开关行为明确，无状态污染 |
| CT-004 | 参数回滚 | 从小 TLB 阈值恢复到默认/2MB | 恢复后 split 减少，fast path 正常 |
| CT-005 | 备份恢复 | LargeSLB 后做物理/逻辑备份恢复 | 恢复实例数据一致 |
| CT-006 | 混合版本拓扑 | 若产品支持，主/只读不同小版本组合 | 不支持时阻断明确；支持时 CV-LSN 安全 |

## 7. 稳定性与可靠性测试

| 编号 | 场景 | 故障注入 | 验收标准 |
|------|------|----------|----------|
| ST-001 | 72 小时长稳 | 无 | 无 crash、无资源泄漏、无 LSN 卡死、数据一致 |
| ST-002 | crash recovery | parsing 后、部分 flush 后、全部 flush 前、全部 flush 后 kill -9 | 重启成功，不反复 crash，数据一致 |
| ST-003 | Slice Store flush 失败 | 单个 split TLB flush fail/retry | 不提前推进，重试后完成 |
| ST-004 | 网络异常 | replica 延迟、断连、恢复 | safe replica 规则满足，恢复后补洞追平 |
| ST-005 | 磁盘满 | Slice Store/WAL 磁盘满 | 错误可诊断，不推进 unsafe LSN |
| ST-006 | failover | LargeSLB flush 中 failover | 新主使用 safe LSN，业务可继续 |
| ST-007 | CR | LargeSLB 不同阶段触发 CR | 起点在 safe CV-LSN/GFB 边界 |
| ST-008 | gossip 补洞 | 缺失非尾部/尾部 split-SLB | 按 split 粒度补洞成功 |

## 8. 测试环境

### 8.1 基础拓扑

| 环境 | 用途 | 建议拓扑 |
|------|------|----------|
| UT/组件环境 | 边界和注入 | 单进程或 mock Slice Store |
| 单机集成环境 | LargeSLB 基本功能 | 1 主 + 本地 Slice Store |
| 主从/只读环境 | CV-LSN 和查询正确性 | 1 主 + 1 只读 + 多 Slice Store replica |
| 可靠性环境 | failover/CR/补洞 | 1 主 + 1 备/只读 + 故障注入工具 |
| 性能环境 | 基准和长稳 | 独占机器，固定 CPU/内存/磁盘，避免混部干扰 |

### 8.2 关键配置

**公共配置：**

```ini
[mysqld]
enable_large_slb = 1

# 根据当前 variables_info 查询结果，取合法上限以尽量放大单批 redo 写入窗口
innodb_log_write_max_size = 524288
innodb_log_write_min_time_interval = 1000000
innodb_log_write_min_size = 131072
```

**Profile A：真实 2MB 边界验证。** 用于 TC-005、TC-024 的 2MB 最大值、PT-004，以及最终发布前端到端验证。

```ini
[mysqld]
sal_tlb_max_size = 2097152
slice_tlb_size = 2097152
slice_flush_size_threshold = 2097152
slice_tlb_size_max = 2097152
```

**Profile B：低阈值加速拆分。** 用于快速覆盖 split-SLB/split-TLB、unsafe LSN、SYNC_MSG_SLICE 等代码路径。TC-001 fast path 回归不要使用此 profile。

```ini
[mysqld]
sal_tlb_max_size = 65536
slice_tlb_size = 4096
slice_flush_size_threshold = 4096
slice_tlb_size_max = 65536
```

参数约束需要覆盖：

- `slice_tlb_size <= slice_tlb_size_max`
- `slice_flush_size_threshold <= slice_tlb_size_max`
- `slice_tlb_size` 范围：4KB 到 2MB
- `slice_flush_size_threshold` 范围：4KB 到 2MB
- `slice_tlb_size_max` 范围：64KB 到 2MB
- `sal_tlb_max_size` 范围：64KB 到 2MB
- `innodb_log_write_max_size` 当前查询范围：0 到 524288，推荐测试值取 524288
- `innodb_log_write_min_time_interval` 当前查询范围：0 到 18446744073709551615，推荐测试值取 1000000
- `innodb_log_write_min_size` 当前查询范围：0 到 131072，推荐测试值取 131072

## 9. 测试数据准备

### 9.1 sysbench 基础数据

```bash
sysbench oltp_write_only \
  --mysql-host=127.0.0.1 \
  --mysql-port=3306 \
  --mysql-user=test \
  --mysql-password=test \
  --mysql-db=test \
  --tables=16 \
  --table-size=1000000 \
  prepare
```

### 9.2 大 MTR 构造建议

- 将 InnoDB log write 相关参数设置到当前合法上限，使单批 redo 尽量达到 512KB，并通过多批 redo/GFB 在 slice flush session 中汇聚形成 LargeSLB。
- 调小 `slice_tlb_size`、`slice_flush_size_threshold`、`slice_tlb_size_max`，先在低阈值下稳定触发 split 路径，再回到 2MB 真实阈值验证发布边界。
- 使用热点更新、批量 insert/update、同一事务多行更新，制造同一 slice/page 附近的 redo 聚合。
- 对精确边界和同 page-id COMPACT 拆分，优先使用 UT/debug 注入，避免 SQL 层数据分布不可控。

### 9.3 数据校验

- 主库和只读实例对关键表执行 row count、checksum、业务聚合校验。
- crash/failover/CR/补洞后重复校验。
- 对测试期间提交成功的事务生成事务流水，恢复后按流水逐条核对。

## 10. 风险评估

| 风险项 | 风险等级 | 影响范围 | 缓解措施 |
|--------|----------|----------|----------|
| TLB 总数少算导致提前 SYNC/CV-LSN | 高 | 只读实例、恢复、数据一致性 | P0 UT + 集成注入延迟 completion |
| unsafe LSN 未拦截导致半个 MTR 可见 | 高 | Slice Manager、只读查询 | completion handler 和 LSN-Watcher 双路径测试 |
| redo buffer 过早释放 | 高 | crash、内存安全、数据损坏 | 组件测试加 ASAN/TSAN/生命周期断言 |
| LSN 排序错误或重叠 | 高 | split-SLB 原子性 | 乱序输入 UT + 实际日志校验 |
| 单 redo >2MB 被误认为支持 | 高 | 数据损坏/不可恢复 | 隔离负向测试，预期直接 crash，测试报告明确标注不支持 |
| fast path 性能退化 | 中 | 所有普通写负载 | 性能基准和开关对比 |
| flush 失败重试不幂等 | 高 | Slice Store 数据一致性 | 故障注入和补洞验证 |
| 参数组合非法导致不可诊断 | 中 | 运维可用性 | 参数边界和错误提示测试 |
| watchPersistLsn 历史问题复发 | 高 | persistLSN 推进 | 专项回归 TC-014 |

## 11. 准入与退出标准

### 11.1 准入标准

- 需求中涉及的核心代码路径已具备 debug 日志或 counter，可观测 split、TLB 计数、unsafe guard、SYNC 发送。
- 支持构造 LargeSLB 的测试环境和故障注入工具可用。
- `enable_large_slb`、TLB 大小、slice flush 相关参数可配置。
- UT 可在 CI 或本地稳定运行。

### 11.2 退出标准

- 所有 P0 用例通过。
- P1 用例通过率不低于 95%，未通过项有明确风险评估和修复计划。
- UT 行覆盖率不低于 95%，分支覆盖率不低于 85%。
- 72 小时长稳无 crash、无资源泄漏、无 LSN 卡死。
- crash recovery、failover、CR、补洞四类可靠性场景全部通过。
- fast path 性能退化满足阈值。
- 所有已知问题都有缺陷单或豁免说明。

## 12. 测试输出物

- LargeSLB 测试设计文档。
- UT 覆盖率报告。
- 功能/集成测试执行记录。
- 故障注入测试报告。
- 72 小时长稳报告。
- 性能对比报告。
- 主库/只读/恢复后数据一致性校验报告。
- 缺陷清单和风险豁免清单。

## 13. 执行顺序建议

| 阶段 | 内容 | 目标 |
|------|------|------|
| 阶段 1 | UT：size、segment、sealed、排序、TLB 计数、unsafe guard | 先锁定算法正确性 |
| 阶段 2 | 单机组件：fillSliceFragment、redo buffer、completion handler | 验证 SALSQL 内部流程 |
| 阶段 3 | 端到端：单 slice、多 slice、多 GFB、只读实例 | 验证真实链路 |
| 阶段 4 | 可靠性：crash、failover、CR、补洞、版本替换 | 验证高风险路径 |
| 阶段 5 | 性能和长稳：fast path、split path、72 小时 | 验证可发布性 |
| 阶段 6 | 兼容和参数矩阵 | 验证灰度、回滚、运维安全 |
