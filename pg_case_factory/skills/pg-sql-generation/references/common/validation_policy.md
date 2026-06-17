6# 技能：validation_policy

## 作用

定义 SQL 用例中验证语句与清理语句的公共规则。用于约束生成 agent 输出可执行、可复跑、可定位原因的测试脚本。

## 验证规则

- 成功路径必须验证目标对象存在、目标属性生效或目标行为可观测。
- 失败路径必须让失败原因单一、可归因；必要时在注释中标明预期失败原因。
- 优先使用稳定的系统目录查询、对象可用性查询或确定性结果查询。
- 避免输出多次执行会变化的信息；`EXPLAIN` 仅在输出稳定且经过裁剪时使用。
- 验证查询应保持排序稳定，避免依赖非确定性行序。

## 清理规则

- 结束清理必须幂等，优先使用 `IF EXISTS` 与明确的反向依赖顺序。
- 对自定义类型、函数、过程、角色、schema、tablespace、extension 等依赖对象，应按依赖关系从叶子到根清理。
- 失败路径也必须执行可复跑清理，避免污染后续 SQL 文件。
- 不允许使用实例级或持久化设置；需要开关时仅使用 session 级设置。

```yaml
structured_config:
  skill_name: validation_policy
  statement: common
  validation:
    require_success_verification: true
    require_single_failure_reason: true
    prefer_stable_catalog_queries: true
    require_idempotent_cleanup: true
```
