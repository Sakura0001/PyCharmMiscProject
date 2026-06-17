# 技能：factor_policy

## 作用

定义 SQL 用例生成时的通用因子组合策略。具体 statement reference 负责声明哪些因子属于主覆盖因子、哪些属于附属因子；本规则只定义展开与挂靠方式。

## 组合规则

- 重要因子采用完整笛卡尔积覆盖。
- 非重要因子按轮转方式挂靠到主组合上。
- 若主组合数量不足，则复制主组合骨架，直到每个非重要因子的每个取值都至少覆盖一次。
- 当生成规模超过 statement reference 的阈值时，优先保留 T1 主因子完整覆盖，再裁剪或轮转 T2，最后才允许压缩语句分支数量。
- 附属因子不得破坏主因子的可识别性、成功/失败归因或生命周期前置条件。

```yaml
structured_config:
  skill_name: factor_policy
  statement: common
  factor_policy:
    important_factor_strategy: full_cross
    non_important_factor_strategy: rotate_attach
    clone_main_skeleton_if_needed: true
    preserve_main_axes_first: true
```
