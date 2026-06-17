# LargeSLB 场景化测试计划

这版用于讲述测试计划。结构不再按测试因子展开，而是按测试场景展开。每个场景固定说明：测什么、怎么测、怎么构造数据、怎么执行、观测什么、预期结果。

## 1. 讲述主线

- 背景：旧逻辑遇到 SLB 超过 2MB 会 crash，redo 已写入 PWAL 后可能 replay 反复 crash。
- 支持边界：多条 redo / 多批 GFB 汇聚后 SLB 超过 2MB 是支持范围。
- 不支持边界：单条 redo record 自身超过 2MB 不支持，预期直接 crash。
- 当前约束：`innodb_log_write_max_size` 最大 524288，单次 redo write 最大约 512KB，因此正向 LargeSLB 依赖多批 redo/GFB 在 slice flush session 中汇聚。
- 落地方式：SQL 只生成负载入口，完整验证还需要内核日志、perfcounter、debug hook、UT 断言和外部故障注入。

## 2. 场景总览

| 场景分组 | 场景 | 核心目的 |
|----------|------|----------|
| 通用前置 | 环境与参数准备 | 确认被测实例支持 LargeSLB 开关和 Slice/TLB 参数 |
| 回归场景 | 普通小 SLB fast path 回归 | 验证开启 LargeSLB 后，普通小事务不触发 split |
| 支持场景 | 多批 redo/GFB 汇聚触发 LargeSLB | 验证正向 LargeSLB 核心路径 |
| 支持场景 | 多 slice 同时触发 LargeSLB | 验证多个 slice 同时出现 split 时，各 slice 计数和完成条件互不干扰 |
| 边界场景 | 2MB 边界和 TLB 阈值矩阵 | 验证 2MB-1、2MB、2MB+1 的拆分边界 |
| 支持场景 | COMPACT 记录拆 segment | 验证同一 page-id 下 COMPACT 日志累计超过阈值后，能拆成多个 segment |
| 支持场景 | LSN 排序和 GFB TLB 总数计算 | 验证 page_ref_map_t 按 LSN 递增排序 |
| 支持场景 | TLB 填充、PMP 和 redo buffer 生命周期 | 验证当前 TLB 空间不足时先 flush |
| 支持场景 | unsafe LSN、SYNC_MSG_SLICE 和 CV-LSN 安全推进 | 验证非尾部 split TLB 的 endLSN 不可见 |
| 支持场景 | 只读实例一致性 | 验证只读实例只读取 safe CV-LSN |
| 可靠性场景 | failover、CR 和版本替换 | 验证 LargeSLB 未完成期间 failover 不选 unsafe LSN |
| 可靠性场景 | Slice Store 补洞和 replica 连续性 | 验证缺失 split-SLB 时可以按 split 粒度补洞 |
| 异常可恢复场景 | flush 失败、crash、磁盘满、网络断连 | 验证异常期间不提前推进 safe LSN |
| 参数与兼容场景 | 开关、参数边界、升级回滚 | 验证 enable_large_slb 开关有效 |
| 性能与稳定性场景 | 性能基准、长稳和大小事务混合 | 验证 fast path 性能不退化 |
| 不支持场景 | 单条 redo record 超过 2MB | 验证当前明确不支持单 redo >2MB |

## 3. 详细场景

### 1. 通用前置：环境与参数准备

**测什么**

- 确认被测实例支持 LargeSLB 开关和 Slice/TLB 参数
- 确认当前 redo write 参数合法范围
- 准备主库、只读实例、Slice Store、故障注入能力

**怎么测**

- 执行 variables_info 查询确认参数范围
- 按场景选择 Profile A 或 Profile B
- 开启内核日志、perfcounter、debug hook 或 UT 断言

**怎么构造数据**

- 公共 redo 参数取当前合法上限：max_size=524288、min_time_interval=1000000、min_size=131072
- Profile A 真实 2MB：sal_tlb_max_size/slice_tlb_size/slice_flush_size_threshold/slice_tlb_size_max 均为 2097152
- Profile B 加速拆分：sal_tlb_max_size=65536、slice_tlb_size=4096、slice_flush_size_threshold=4096、slice_tlb_size_max=65536

**怎么执行**

- 先设置实例参数并重启或动态 SET GLOBAL
- 加载 SQL 过程或执行单个 TC SQL 文件
- 确认 TC-001 fast path 不使用 Profile B

**观测什么**

- SHOW VARIABLES 和 variables_info
- large_mtr、large_mtr_size
- split TLB 日志、SYNC_MSG_SLICE、CV-LSN/persistLSN
- 主库/只读 checksum

**预期结果**

- 参数在合法范围内生效
- 观测链路可看到 LargeSLB 是否触发
- 不同场景使用正确 profile，不混淆 fast path 和 split path

### 2. 回归场景：普通小 SLB fast path 回归

**测什么**

- 验证开启 LargeSLB 后，普通小事务不触发 split
- 验证普通路径仍走 fast path，没有性能退化

**怎么测**

- 使用真实 2MB 或默认阈值，不使用低阈值 Profile B
- 执行小 payload、小批量 update
- 与关闭 LargeSLB 或基线版本对比

**怎么构造数据**

- 准备 1000 行，每行约 512B
- 单轮更新 100 行，每行约 1KB
- 也可使用 sysbench 普通 OLTP 小事务

**怎么执行**

- 执行 TC-001 SQL 作为负载入口
- 并行采集 QPS/TPS、P99 latency
- 重复多轮排除抖动

**观测什么**

- large_mtr 不增长
- 无 split-SLB / split-TLB 日志
- GroupFlushLogHarvester 未设置 split 标志
- QPS/TPS 与基线差异

**预期结果**

- 不产生 LargeSLB
- 每个 GFB 到目标 slice 仍最多一个 TLB
- fast path 性能退化不超过 3%

### 3. 支持场景：多批 redo/GFB 汇聚触发 LargeSLB

**测什么**

- 验证正向 LargeSLB 核心路径
- 验证多批 redo/GFB 在同一 slice flush session 中累计超过阈值后可以拆分写入
- 强调不是单次 redo write 达到 2MB

**怎么测**

- 将 redo write 参数设为当前合法上限，使单批 redo 尽量接近 512KB
- 使用同 bucket / 热点数据让多批 redo 更容易映射到同一 slice
- 先用 Profile B 快速触发，再用 Profile A 验证真实 2MB

**怎么构造数据**

- 单会话：192 行 x 32KB，更新 160 行，约 5MB payload 压力
- 多批：384 行 x 16KB，分 3 批同 bucket 更新
- 数据量要显著大于 2MB，因为实际 redo 和 slice 映射会受压缩、页分布、元数据影响

**怎么执行**

- 执行对应 SQL 负载入口
- 单会话大事务验证多批 redo 汇聚
- 多客户端并发验证多 GFB 汇聚
- 控制 slice flush session 周期或使用故障注入延迟 flush

**观测什么**

- large_mtr 增长
- large_mtr_size 大于阈值
- 同一 GFB 下 TLB 总数大于 1
- 每个 split TLB 的 startLSN/endLSN
- 业务查询结果

**预期结果**

- SLB 被拆成多个 split TLB
- 所有 split TLB flush 成功
- 不 crash，不丢数据
- GFB 完成条件等待所有 split TLB

### 4. 支持场景：多 slice 同时触发 LargeSLB

**测什么**

- 验证多个 slice 同时出现 split 时，各 slice 计数和完成条件互不干扰
- 验证 GFB 总 TLB 数等于各 slice split TLB 之和

**怎么测**

- 构造多个 bucket / 多组热点数据，模拟映射到多个 slice
- 同时对多个 bucket 做大 payload 更新
- 观察每个 slice 的 TLB flush completion

**怎么构造数据**

- 准备 768 行 x 16KB
- 4 个 bucket，每个 bucket 更新 96 行
- 必要时用多客户端分别打不同 bucket

**怎么执行**

- 执行多 slice SQL 负载入口
- 使用多客户端并发放大跨 slice 并发
- 可配合 Profile B 快速覆盖 split path

**观测什么**

- 每个 slice 的 split TLB 数
- GFB_info 依赖 TLB 总数
- 各 slice flush completion 顺序
- CV-LSN 是否等所有 slice 完成后推进

**预期结果**

- 各 slice 独立拆分和 flush
- GFB 总完成条件准确
- 不会因为某个 slice 提前完成而提前推进 CV-LSN

### 5. 边界场景：2MB 边界和 TLB 阈值矩阵

**测什么**

- 验证 2MB-1、2MB、2MB+1 的拆分边界
- 验证 sal_tlb_max_size 不同值下 split 数量正确
- 验证 size 计算包含 record 元数据、SLB 元数据和 padding

**怎么测**

- 精确边界必须用 UT/debug 注入
- SQL 只作为近似压力流量
- Profile A 验证真实 2MB，Profile B 验证快速拆分

**怎么构造数据**

- UT/debug：构造总大小为 2MB-1、2MB、2MB+1
- SQL 近似：511/512/513 行 x 4KB
- 矩阵：sal_tlb_max_size 取 64KB、128KB、512KB、1MB、2MB

**怎么执行**

- 先跑 UT/debug 精确边界
- 再跑 SQL 压力流量确认端到端行为
- 每个 sal_tlb_max_size 值单独执行并记录 split 数

**观测什么**

- size 计算日志
- 是否拆分
- TLB 是否超过上限
- split TLB 数与预期是否一致
- off-by-one 边界

**预期结果**

- <=2MB 不因边界误拆或超限
- >2MB 必须拆分
- 每个 TLB 不超过 sal_tlb_max_size
- 矩阵下 split 数趋势合理

### 6. 支持场景：COMPACT 记录拆 segment

**测什么**

- 验证同一 page-id 下 COMPACT 日志累计超过阈值后，能拆成多个 segment
- 验证 compSeg 和 sealed 语义正确

**怎么测**

- 优先使用 UT/debug 构造同 page-id 记录
- SQL 使用单行重复更新近似制造同 page 热点
- 检查 page_map_t 中同 page-id 多个 entry

**怎么构造数据**

- 单行重复更新 96 次，每次 payload 约 32KB，约 3MB redo 压力
- UT 输入固定同 space/page，不同 LSN 的多条 COMPACT record

**怎么执行**

- 执行单行重复 update SQL
- 同步运行 UT 检查 page_map_t
- 在超阈值位置检查 seal 和新 segment 创建

**观测什么**

- space_page_key::compSeg 从 0 递增
- head segment sealed 非 0 表示当前活跃 segment
- non-head sealed 与自身 segment 编号一致
- map entry 无覆盖

**预期结果**

- 同 page-id 可拆成多个 COMPACT segment
- segment 编号连续
- sealed 状态正确
- 后续 mapping 和 flush 能消费所有 segment

### 7. 支持场景：LSN 排序和 GFB TLB 总数计算

**测什么**

- 验证 page_ref_map_t 按 LSN 递增排序
- 验证 split-SLB LSN 范围无重叠
- 验证 GroupFlushLogHarvester 计算 TLB 总数准确

**怎么测**

- 构造乱序 bucket 更新，使输入顺序和 LSN 顺序不完全一致
- 分别构造无拆分、单 slice 拆分、多 slice 拆分、多 GFB 汇聚
- 对比实际 TLB 数与预期 TLB 数

**怎么构造数据**

- 512 行 x 8KB，按 bucket 5、2、7、0 乱序更新
- 960 行 x 8KB，包含 no_split、single_split、multi_split 三组

**怎么执行**

- 执行 LSN 排序 SQL 负载
- 执行 TLB 总数 SQL 负载
- 结合 debug 输出 dump page_ref_map_t 和 GFB_info

**观测什么**

- page_ref_map_t 中 LSN 是否递增
- split-SLB 范围是否重叠
- GFB 记录的 required TLB count
- completed TLB count

**预期结果**

- 排序稳定且无倒序
- TLB 总数不少算也不多算
- 不会提前 SYNC，也不会因为多算导致卡住

### 8. 支持场景：TLB 填充、PMP 和 redo buffer 生命周期

**测什么**

- 验证当前 TLB 空间不足时先 flush
- 验证 PMP 跨 TLB 后继续处理
- 验证 redo buffer 不会过早释放

**怎么测**

- 先填充小数据让当前 TLB 非空
- 再写入大数据使当前 TLB 放不下
- 使用单行重复更新制造 PMP 跨 TLB
- 在 split TLB 复制中间暂停检查 buffer 状态

**怎么构造数据**

- 260 行，先更新 10 行 x 4KB，再更新 240 行 x 8KB
- 单行重复更新 128 次 x 24KB
- 320 行 x 24KB，更新 256 行

**怎么执行**

- 执行对应 SQL 负载入口
- 在 fillSliceFragment 前后打日志或断点
- 可使用 ASAN/TSAN 或 debug refcount 检查生命周期

**观测什么**

- 当前 TLB 是否先 flush
- PMP 是否仍保留在 session list
- PMP consumed offset
- redo buffer release 时机
- 是否重复/遗漏复制

**预期结果**

- TLB 不超限
- PMP 可从正确位置继续
- 所有 split TLB 复制完成前 redo buffer 不释放
- 无 use-after-free

### 9. 支持场景：unsafe LSN、SYNC_MSG_SLICE 和 CV-LSN 安全推进

**测什么**

- 验证非尾部 split TLB 的 endLSN 不可见
- 验证 persistLSN/CV-LSN 只在 safe boundary 推进
- 验证所有 TLB 完成前不发送 SYNC_MSG_SLICE

**怎么测**

- 构造一个 LargeSLB 拆成多个 TLB
- 延迟最后一个 TLB completion
- 分别触发 completion handler 和 LSN-Watcher 推进路径

**怎么构造数据**

- 384 行 x 16KB，约 6MB，目标拆成多个 TLB
- 448 行 x 16KB，约 7MB，用于延迟最后 completion
- 两组 bucket 分别覆盖 handler 和 watcher

**怎么执行**

- 执行 SQL 负载
- 注入 TLB flush completion 延迟
- 手动或自动触发 LSN-Watcher
- 只读侧持续查询最新可见 CV-LSN

**观测什么**

- m_lsnGuard add/check/remove
- persistLSN 是否尝试推进到 unsafe LSN
- SYNC_MSG_SLICE 是否被延迟
- CV-LSN/recycle/release LSN
- 只读查询是否半事务可见

**预期结果**

- 非尾部 endLSN 被 guard 拦住
- 尾部 TLB 完成后才推进 safe persistLSN/CV-LSN
- 所有 TLB 完成前不发 SYNC_MSG_SLICE
- 只读实例无缺页和半 MTR 可见

### 10. 支持场景：只读实例一致性

**测什么**

- 验证只读实例只读取 safe CV-LSN
- 验证 LargeSLB 部分 split TLB 完成期间不会看到半个 MTR

**怎么测**

- 主库持续写入 LargeSLB 负载
- 只读实例持续查询热点表和 checksum
- 人为延迟部分 split TLB completion

**怎么构造数据**

- 512 行 x 16KB，4 bucket 更新
- 只读侧周期性执行 count、checksum、业务聚合查询

**怎么执行**

- 主库执行 LargeSLB SQL 负载
- 只读侧并发查询
- 注入最后 TLB flush 延迟并观察 CV-LSN

**观测什么**

- 只读 CV-LSN
- 主只 row count/checksum
- 查询错误、缺页、数据不一致
- SYNC_MSG_SLICE 发送时间

**预期结果**

- 只读实例只能观察到 safe CV-LSN
- 部分 split 完成期间不可见半事务
- 全部完成后只读追上且数据一致

### 11. 可靠性场景：failover、CR 和版本替换

**测什么**

- 验证 LargeSLB 未完成期间 failover 不选 unsafe LSN
- 验证 CR 起点来自 safe CV-LSN
- 验证历史异常后替换版本能正常拉起

**怎么测**

- 在 LargeSLB flush 中间发起 failover
- 在不同 split 完成阶段触发 CR
- 构造旧版本/旧配置异常后替换新版本

**怎么构造数据**

- 512 行 x 16KB，2 bucket 更新，用于 failover/CR
- 768 行 x 16KB，同 bucket 更新 512 行，用于版本替换

**怎么执行**

- 执行 SQL 负载后注入 TLB flush 延迟
- 发起 failover 或 CR
- 新主/恢复实例拉起后执行一致性校验
- 版本替换场景重启实例

**观测什么**

- 倒换选择的 LSN
- CR 起始 LSN
- CV-LSN 是否在 GFB 边界
- 新主/恢复实例 checksum
- 是否反复 crash

**预期结果**

- failover 不选择 unsafe LSN
- CR 起点位于 safe CV-LSN/GFB 边界
- 版本替换后正常拉起
- 数据无丢失、无半事务

### 12. 可靠性场景：Slice Store 补洞和 replica 连续性

**测什么**

- 验证缺失 split-SLB 时可以按 split 粒度补洞
- 验证至少一个 replica 能连续服务到 GFB endLSN 后再推进

**怎么测**

- 成功写入多个 split TLB 后，屏蔽或删除其中一个 split-SLB
- 触发 gossip/补洞
- 对部分 replica 注入网络延迟或断连

**怎么构造数据**

- 512 行 x 16KB，2 bucket 更新生成多个 split TLB
- 4 bucket 更新覆盖多 replica / 多 slice 场景

**怎么执行**

- 执行负载后注入缺洞
- 触发 Slice Store gossip
- 恢复网络后观察副本追平
- 执行主只一致性校验

**观测什么**

- served LSN
- gap 检测结果
- 补洞请求和响应
- replica 可服务区间
- 补洞后 checksum

**预期结果**

- 缺失 split-SLB 可按 split 粒度填充
- served LSN 连续后再推进
- 网络恢复后副本补洞追平
- 数据可读且一致

### 13. 异常可恢复场景：flush 失败、crash、磁盘满、网络断连

**测什么**

- 验证异常期间不提前推进 safe LSN
- 验证故障解除后可重试或恢复
- 验证 crash replay 不反复 crash

**怎么测**

- 注入单个 split TLB flush 失败
- 在 parsing 后、部分 flush 后、全部 flush 前、全部 flush 后 kill -9
- 注入 Slice Store/WAL 磁盘满
- 注入 replica 网络抖动或断连

**怎么构造数据**

- 512 行 x 16KB，作为 flush retry、crash replay、磁盘满、网络异常共同负载
- 4 bucket 更新用于 replica 网络异常

**怎么执行**

- 执行 SQL 负载入口
- 按阶段触发故障注入
- 故障期间持续观察 LSN 和消息
- 恢复故障后重试或重启实例

**观测什么**

- 错误日志
- TLB completion 状态
- m_lsnGuard
- SYNC_MSG_SLICE 是否发送
- CV-LSN/persistLSN 是否推进
- 重启 replay 结果

**预期结果**

- 失败期间不推进 unsafe LSN
- 不发送未完成 GFB 的 SYNC_MSG_SLICE
- 故障解除后可完成或恢复
- 不会反复 crash，数据一致

### 14. 参数与兼容场景：开关、参数边界、升级回滚

**测什么**

- 验证 enable_large_slb 开关有效
- 验证 slice/TLB 参数合法性
- 验证升级、灰度、回滚、备份恢复安全

**怎么测**

- 分别用 enable_large_slb=0/1 执行同一负载
- 遍历 slice_tlb_size、slice_flush_size_threshold、slice_tlb_size_max、sal_tlb_max_size 合法/非法组合
- 执行原地升级、参数回滚、备份恢复

**怎么构造数据**

- 640 行 x 16KB，同 bucket 更新 320 行用于开关对比
- 512 行，4KB/64KB/1MB 三档更新用于参数边界
- 1100 行 x 4KB 用于 sal_tlb_max_size 矩阵

**怎么执行**

- 每个参数组合单独启动或动态设置
- 非法组合验证启动失败或 SET GLOBAL 失败
- 升级/回滚前后执行相同负载和 checksum

**观测什么**

- 参数是否生效
- 非法参数错误信息
- large_mtr/large_mtr_size
- split 数量变化
- 升级前后数据一致性

**预期结果**

- 开关行为明确
- 非法组合被拒绝且错误可诊断
- 参数回滚后 split 减少或回到 fast path
- 升级/备份恢复无数据损坏

### 15. 性能与稳定性场景：性能基准、长稳和大小事务混合

**测什么**

- 验证 fast path 性能不退化
- 验证 split path 性能趋势可解释
- 验证长稳无 crash、无泄漏、无 LSN 卡死
- 验证大事务不明显拖垮小事务

**怎么测**

- fast path 使用真实阈值和普通小事务
- split path 使用低阈值和真实 2MB 双 profile
- 长稳运行 72 小时
- 大小事务按 20%/80% 混合并发

**怎么构造数据**

- 长稳：1024 行 x 8KB，两轮全量更新作为单轮负载，可循环执行
- 混合：大事务 256 行 x 16KB，小事务 7 x 80 行 x 2KB
- 性能压测使用 sysbench 或多客户端脚本

**怎么执行**

- 分别跑 baseline、LargeSLB fast path、split path
- 记录 QPS/TPS/P99/CPU/内存/IO
- 长稳期间周期性校验 checksum
- 混合负载中单独统计小事务延迟

**观测什么**

- QPS/TPS
- P99 latency
- TLB flush latency
- CPU/内存/IO
- large_mtr 增长趋势
- 错误率和连接数

**预期结果**

- fast path 退化不超过 3%
- split path 延迟随 split 数线性可解释
- 72 小时无 crash、无泄漏、无 LSN 卡死
- 小事务 P99 无异常放大

### 16. 不支持场景：单条 redo record 超过 2MB

**测什么**

- 验证当前明确不支持单 redo >2MB
- 验证该场景预期 crash，不作为 LargeSLB 正向能力
- 防止测试报告误判

**怎么测**

- 必须在隔离可丢弃实例执行
- 优先使用 debug/UT 构造单条 redo record 含元数据超过 2MB
- SQL 只作为尝试性大 payload 输入，不保证生成单条 redo

**怎么构造数据**

- debug/UT：单条 redo record >2MB
- SQL：单行更新 2,200,000B payload 作为压力输入

**怎么执行**

- 隔离实例执行 TC-006 或 UT 注入
- 记录 crash 栈、最后 LSN、错误日志
- 执行后清理或重建实例

**观测什么**

- 是否直接 crash
- crash 栈是否指向不支持路径
- 是否有部分数据写入或错误推进 LSN
- 测试报告是否标注不支持

**预期结果**

- 实例直接 crash 属于预期
- 不进入 LargeSLB 正向验收
- 不得在共享回归环境执行
- 不把 crash 误判成修复失败

## 4. 推荐讲述顺序

1. 先讲通用前置：参数范围、Profile A/B、观测手段。
2. 再讲支持场景：多批 redo/GFB 汇聚、拆分、排序、TLB 生命周期、LSN 安全推进。
3. 再讲可靠性场景：只读、failover、CR、补洞、异常恢复。
4. 再讲参数与性能场景：开关、边界、升级回滚、长稳和混合负载。
5. 最后强调不支持场景：单 redo >2MB 预期 crash，必须隔离执行。
