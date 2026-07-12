# 为测试点生成 SQL

## 目标

为一个已审计 test point 的全部 executable obligations 生成 PostgreSQL 18.4 SQL 和 case manifests。把 statement 专用知识留在 statement references 与 combination matrices 中。

## 输入

- `inputs/feature_manifest.yaml`
- `plans/coverage_plan.yaml` 和 `plans/coverage_obligations.json`
- 当前 test point ID 及其 obligations
- 相关 `assets/objects/**/*.sql`
- 相关 `references/statements/**/*.md`
- 相关 `references/combinations/**/*.yaml`
- output、factor、validation、lifecycle、naming 公共规则
- `assets/templates/case_manifest_template.yaml`

## 生成步骤

1. 只处理当前 test point，创建专属 `jobs/<test-point-id>/`、`cases/sql/<test-point-id>/` 和 manifests。
2. 先消费已审计的 matching combination matrices，再补充 marked derived extensions。自由推理不得替代 required baseline。
3. 对每个非 `justified_na` obligation 生成独立 case manifest 和至少一个完整 SQL 文件。
4. 从 obligation assignments 精确绑定 relation/table/object、列类型、语句分支、事务和其他轴；不使用代表对象或代表类型代替 inventory 值。
5. 某组合在 PostgreSQL 18.4 中不合法时，保留为单一、可归因的 `expected_failure` 脚本，不要静默跳过。
6. 每个 SQL 文件只判断一个结果，并包含固定头、前置清理、对象准备、目标操作、稳定验证和结束清理。
7. 使用确定性排序、稳定目录字段和 session 级设置。禁止其他数据库方言、`\!` 宿主机命令、实例级持久设置和真实凭据。
8. 运行 SQL 静态检查后，核对 obligation IDs、assignments、outcomes、SQL paths 和 cleanup/comparison metadata。
9. 生成 test-point 摘要，列出 required、success、expected_failure、justified_na、SQL 数量、缺失数量和输出路径。

可以为大量 obligations 生成辅助程序，但辅助程序只放在当前 run 的 job 目录，必须读取 contracts/inventories，且不得把 statement 特例写回常驻 Python。

## 完成条件

- 所有 executable obligations 都有且只有一个匹配 case manifest。
- 所有 `justified_na` obligations 都保留 reason。
- missing、unexpected 和 mismatched case 数量均为 0。
- SQL 仍需实际在 reference 和 DUT 上执行后才能标记 executed/compared；生成成功不等于数据库验证成功。

```yaml
structured_config:
  kind: mainflow
  skill_name: write_sql_program
  mainflow_role: generate_test_point_cases
  compatibility_target: postgresql-18.4
  case_granularity: one_manifest_per_executable_obligation
  require_case_reconciliation: true
```
