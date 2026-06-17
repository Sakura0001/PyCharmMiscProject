# 技能：naming_rules

生成的表名使用 `tab_*` 前缀，索引名使用 `idx_*` 前缀，函数名使用 `func_*` 前缀，存储过程名使用 `proc_*` 前缀。名称必须保持 ASCII、小写、语义清晰，并在同一批用例内唯一且不冲突。

```yaml
structured_config:
  skill_name: naming_rules
  statement: common
  naming:
    table_prefix: tab_
    index_prefix: idx_
    function_prefix: func_
    procedure_prefix: proc_
    max_identifier_length: 63
```
