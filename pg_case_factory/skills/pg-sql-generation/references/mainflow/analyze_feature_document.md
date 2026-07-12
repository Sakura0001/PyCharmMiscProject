# 分析特性文档

## 目标

把用户提供的特性文档转成可追溯的 `feature_manifest.yaml`，只提取可验证需求，不在此阶段生成 SQL 或猜测底层实现。

## 输入与输出

- 输入：用户指定的原始特性文档及其版本信息。
- 模板：`assets/templates/feature_manifest_template.yaml`。
- 输出：
  - `work/<run-id>/<original-name>`：run 初始化前的受控原文副本。
  - `work/<run-id>/feature_manifest.yaml`：run 初始化前的结构化需求。
  - `work/<run-id>/analysis_notes.md`：歧义、假设和待确认项。

## 执行步骤

1. 为本次任务选择稳定的 `<run-id>`，建立 `work/<run-id>/` 受控工作目录，但此时不要执行 `run init`。严格 run metadata 不允许先建空 run、之后再静默补挂 plan/profile；manifest、plan 与 execution profile 审批后由覆盖设计流程一次性初始化 run。
2. 原样保存输入文档，记录相对路径、内容 SHA-256、文档修订号和获取时间。不要把外部链接当作已保存原文。
3. 完整读取文档，按标题、章节、页码、段落或行号建立定位信息。文档格式无法稳定定位时，保存短的结构化 locator，不复制大段原文。
4. 将复合需求拆成可独立验证的原子 requirement。为每条 requirement 分配稳定 ID，并回链到原文定位。
5. 区分以下内容：
   - 明确的 SQL/用户可见行为要求；
   - 可能影响 SQL 行为的底层改动；
   - 仅用于实现说明、不能直接作为测试 oracle 的内容；
   - 未定义、矛盾或需要用户决定的内容。
6. 对每条需求列出可观察面：命令是否成功、SQLSTATE/错误文本、command tag、结果行、排序、目录可见属性、事务可见性、持久性和清理结果。
7. 初步标记受影响的 statement、对象、relation/table 类型、列类型、数据形态、事务阶段、会话状态、并发或恢复边界。这里只建立候选清单；完整 inventory 在覆盖设计阶段确定。
8. 把无法从原文证明的内容写入 `metadata.assumptions` 或 `metadata.unresolved_questions`。后者必须显式存在且始终是 list；会改变需求语义或覆盖范围的问题未解决时，停止进入正式 run，不要静默采用默认值。分析期和 `plan validate` 可以保留问题，但 `run init` 在创建目录前要求该 list 已由用户决议并清空为 `[]`，缺字段也失败。
9. 校验每条 requirement 都有受支持的非空 source locator，且 `feature_id`、标题、源文件与哈希一致。CLI 在收到 `--manifest` 时会读取 `source.path` 指向的保存副本并重新计算 SHA-256；默认相对 manifest 目录解析，需要其他布局时显式传 `--source-root`。缺文件、越界路径或哈希漂移都必须失败。

完成 manifest 后进入 `design_feature_coverage_plan.md`。只有 manifest、coverage plan 与 run 外 execution profile 同时通过校验，才执行一次 `pg-case run init --manifest ... --plan ... --execution-profile ...`，由 CLI 将已解析对象、原始文档和 canonical profile 复制为 run 内不可变快照；不要在初始化后手工补复制 profile。

## 兼容性口径

- 固定 `compatibility_target: postgresql-18.4`。
- 把 upstream PostgreSQL 18.4 的 SQL 与用户可见输出作为 oracle。
- 不把内部页布局、I/O 路径或存算分离日志写成 SQL 兼容性预期。
- 不分析存储日志或给出底层根因；用户负责该部分。保留足够的 SQL、输出和环境标识供用户定位。

## 安全规则

- 不在原文副本、manifest、notes 或提示词中新增密码、token、私钥或带凭据的 URI。
- 原文包含真实凭据时，停止传播该片段；保留经过脱敏的引用并告知用户处理源文档。
- 只记录逻辑 target/service 名，不记录密码。

```yaml
structured_config:
  kind: mainflow
  skill_name: analyze_feature_document
  output_contract: assets/templates/feature_manifest_template.yaml
  compatibility_target: postgresql-18.4
  require_source_sha256: true
  require_requirement_locator: true
  forbid_credential_persistence: true
```
