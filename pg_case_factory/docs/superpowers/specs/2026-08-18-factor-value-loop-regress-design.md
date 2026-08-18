# 全语句因子值独立循环 Regress 生成设计

状态：`approved_design_pending_written_review`

批准日期：2026-08-18

## 1. 目标

本设计将全语句 regress 的正式生成口径从“所有独立因子的完整交互积”简化为“所有适用因子值的独立循环全覆盖”。

对 183 条语句逐条执行时，完成一条语句必须证明：

1. 官方语法、canonical 因子、适用的表/列/类型库存、权限、对象状态、事务和必要风险中的每条义务都有真实 SQL witness；
2. 每条义务恰好有一个主要覆盖用例；
3. 可达的非法值以 expected-failure 用例覆盖，不能记为 N/A；
4. 所有正式 SQL 在隔离的本地 PostgreSQL 18.4 中从干净状态执行两遍，结果符合预期且确定；
5. 当前语句完成并固化证据后，才进入下一条语句。

本设计不要求任意两个或多个普通因子互相做笛卡尔积。只有官方语法本身、函数依赖、互斥关系或已知检查顺序明确要求组合时，才建立一条专门的组合义务。

## 2. 覆盖义务

每条语句的 required obligation ledger 由以下四类义务的并集组成：

| kind | 内容 | 身份粒度 |
|---|---|---|
| `GRM` | 官方 branch、target action、可选关键字、有限 alternative、列表边界 | statement + branch/action + grammar factor + value |
| `SFV` | 当前项目 canonical statement factor/value | statement + branch/action/context + canonical row id |
| `INV` | 适用的关系、表、列结构和类型库存成员 | statement + consumer action + inventory selector/dimension + member |
| `RISK` | 权限、对象状态、事务、并发、重启或外部能力等必要边界 | statement + applicable branch/action + risk id + value |

同一个库存成员如果在两个 action 中具有不同目标语义，必须形成两条义务。例如类型成员分别作为 `ADD COLUMN` 的新列类型和 `ALTER COLUMN TYPE` 的目标类型时，分别生成 witness。仅仅在两个 action 中读取同一个既存 fixture、且目标语义没有变化时，不重复建立义务。

共享库存仍属于正式范围：

- 关系和表结构；
- 20 个列结构维度；
- 七份 selector-qualified PostgreSQL 18 类型库存，共 359 个成员；
- 语句明确适用的 routine、constraint、dependency 或其他共享库存。

库存之间即使解析到同一个 PostgreSQL 对象也不按名称去重；义务身份保留 selector/dimension。

## 3. 用例归因合同

每个正式 SQL program 必须满足：

1. `primary_obligation_id` 精确一个；
2. 同一个 canonical factor key 在该用例中最多取一个值；
3. 其他因子只能由 resolver 选择合法 baseline，且 baseline 不领取主要覆盖信用；
4. primary value 必须真实落在目标 SQL、必要 fixture、事务/harness operation 或可验证状态中，注释和 sidecar metadata 不能单独作为 witness；
5. 一个 SQL 可以自然地体现多个 baseline 状态，但不能借此让同一用例同时领取多个主要义务；
6. 语义完全等价的 alias 可以复用同一个 resolver 和 SQL 模板，但每条 obligation 仍生成独立编号 program 并单独结算，禁止一个文件领取多个 primary id；
7. 每个文件精确包含一次被测 target statement；清理阶段中同类 SQL 不领取覆盖信用。

按此合同，覆盖完成等式为：

```text
Bag(required obligation ids)
= Bag(primary obligation ids from validated programs)

missing   = 0
duplicate = 0
unknown   = 0
```

## 4. 因子循环算法

每条语句使用固定算法生成：

1. 按官方语法、canonical inventory 和共享库存的冻结顺序编译 required obligation ledger；
2. 依次遍历 ledger，每条 obligation 创建一个 case request；
3. statement-specific resolver 选择该值的适用 branch/action、合法 table/column fixture、baseline assignments 和验证方式；
4. 如果值能到达目标语句并被 PostgreSQL 拒绝，生成 isolated expected-failure；
5. 如果值与当前 action 在语法或语义上不适用，将它路由到其真实 consumer action；只有语句本质上无法消费且有明确承接者时才允许 delegated N/A；
6. renderer 为每个 case request 输出一个完整 SQL program；
7. validator 从最终 SQL/harness 中重新提取 primary value，核对 ledger 等式；
8. 通过静态门禁后进入本地 PostgreSQL 18.4 双跑。

遍历顺序和编号只依赖冻结 ledger，不依赖生成时间、机器路径、进程数或运行结果。重新生成必须得到相同相对路径和相同字节。

## 5. 明确禁止的扩展方式

以下数量只能作为诊断，不能决定正式 SQL 数量：

- 将所有因子值无条件相乘；
- 将同一列的类型、nullability、default、identity、generation 等状态视为多个独立列角色后相乘；
- 将 expected status、verification、cleanup 当作自由语义轴；
- 为证明“更全”而把每个类型与每个 action、拓扑、权限状态重复相乘；
- 先生成大量组合，再凭 expected status 或字符串规则删除无效组合。

只有以下组合需要单独生成：

- 某个 factor value 的语法成立依赖另一个值；
- 两个值构成官方明确的合法或非法 alternative；
- PostgreSQL 的检查顺序必须通过复合 fixture 才能观察；
- 多 action、事务、并发或重启本身就是一条独立义务。

这些组合记录为独立 `GRM` 或 `RISK` obligation，不开启全局笛卡尔积。

## 6. SQL program 结构

每个文件使用稳定编号和同源对象前缀，并至少包含：

1. 固定 header；
2. 幂等 pre-cleanup；
3. 完整表结构和完整列结构 fixture；
4. 必要数据、角色、schema、server/FDW 或依赖对象；
5. 精确一次 target statement；
6. success 或 expected-failure oracle；
7. 无条件 final cleanup；
8. cleanup 后残留检查由 runner 执行。

表和列相关语句不能使用只有一列、没有约束含义的占位表来冒充完整 fixture。完整 fixture 应包含稳定主键或标识列、被测列、辅助列、必要约束和确定性数据；与 primary obligation 冲突的结构由 resolver 调整，但必须记录调整原因。

## 7. expected-failure 规则

非法也是正式覆盖的一部分。expected-failure program 必须：

- 只有一个 primary failure obligation；
- fixture 中的其他条件均合法，避免更早错误遮蔽目标值；
- 保存五位 SQLSTATE、目标 phase 和冻结失败原因；
- 失败后验证目标对象及相关元数据没有发生未预期变化；
- 即使 target 失败也执行 final cleanup；
- 第二遍得到相同的规范化输出、SQLSTATE 和退出状态。

如果一个非法值在某个表拓扑中会被更早 guard 遮蔽，应选择不会遮蔽它的 baseline topology；需要验证 guard 顺序时另建一条 `RISK` obligation，而不是把所有 topology 与该非法值相乘。

## 8. 本地执行合同

正式运行固定使用隔离 PostgreSQL 18.4，不复用用户的其他本地实例。对每个 SQL program：

1. 恢复干净 baseline；
2. 执行 run-01；
3. 无条件 cleanup 并验证残留为零；
4. 再次恢复相同 baseline；
5. 执行 run-02；
6. 比较规范化 stdout、stderr、退出状态、SQLSTATE、oracle 和 cleanup 结果；
7. 任一 mismatch 使当前语句保持未完成。

success 必须命中 `00000` 且 oracle 为 true；expected failure 必须命中计划 SQLSTATE 和 primary failure。运行证据必须绑定当前 SQL SHA，SQL 变化后旧运行证据失效。

## 9. ALTER FOREIGN TABLE 迁移口径

当前 `ALTER FOREIGN TABLE` 已编译的 `2,766,876` 条单 action candidate 和约 `9.4867×10^20` 的机械上界降级为诊断数据，不再作为正式生成 universe。

新口径的初始数量估算：

```text
列成员 × 适用 action obligation     1,569
官方语法 obligation                    136
canonical factor value                 103
权限/状态/事务/风险补充               约 50–300
------------------------------------------------
预计正式 SQL program                约 1,800–2,100
```

精确数量由 required obligation ledger 编译结果决定，不以估算值作为通过条件。正式物理 program 数必须等于 required obligation 数；alias 只复用 renderer 模板，不合并 primary credit。如果一个风险值需要多个不可合并的合法上下文，应先把它拆成多个独立 `RISK` obligation，再按一义务一 program 生成。

已经完成的 PG18.4 类型、COLLATE、nullability、default、generation、identity、storage/compression 校准继续作为 resolver 证据使用，但不再把每个校准值与全部 grammar/topology 组合相乘。

## 10. 每条语句的完成门禁

只有以下条件全部成立，计划表才允许为当前语句打勾：

- required obligation ledger count 和 SHA 已冻结；
- 每条 obligation 的 disposition 与 primary case 已确定；
- ledger 等式的 missing/duplicate/unknown 均为 0；
- 每个 primary value 已从最终 SQL/harness 重新提取并匹配；
- SQL 文件编号连续、对象前缀一致、setup/oracle/cleanup 完整；
- regress style validator 通过；
- 全部文件在本地 PostgreSQL 18.4 执行两遍；
- success、expected failure、SQLSTATE、oracle、cleanup 和确定性全部通过；
- 运行证据绑定当前 package SHA；
- 当前语句完成后才开始下一条语句。

## 11. 全局循环

183 条语句继续使用冻结 statement order。对每条语句执行：

```text
compile obligations
→ plan one primary case per obligation
→ render complete SQL
→ static validate
→ local PostgreSQL 18.4 run twice
→ freeze evidence
→ mark statement complete
→ advance to next statement
```

旧有 SQL 不因本设计自动删除。纳入新流程时必须重新映射到当前 obligation ledger；能够通过静态和运行门禁的文件可以保留，不能证明 primary obligation 的文件只作为 legacy artifact，不领取当前覆盖信用。
