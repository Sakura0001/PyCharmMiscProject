# 技能：output_sql_style

生成的 SQL 必须是完整测试脚本，而不是裸语句。

该脚本将作为流水线长稳用例执行，要求同一输入在多次执行时输出内容保持一致。

每个文件应包含：
- 文件头注释
- 前置清理
- 基于 `assets/objects/` 中基础对象模板的建表语句。
- 为了达成测试目的的一系列目标语句
- 目标语句验证
- 结束清理，删除所有表

附加约束：
- 头部注释采用固定模板，包含版权、author、create at、version、description 等字段
- 如果需要设置开关，必须使用 session 级别设置，不允许使用实例级或持久化设置
- 避免输出多次执行后会变化的信息；例如 `EXPLAIN` 这类结果只有在确认稳定一致时才能打印
- FE号码，根据输入FE生成，如果未输入，则置为空。
- 如果是相似语句，例如删除表，执行多次插入数据，此时行与行之间不需要有空行，否则语句与语句之间应该有空行，
- 生成的表名使用 `tab_*` 前缀，索引名使用 `idx_*` 前缀，函数名使用 `func_*` 前缀，存储过程名使用 `proc_*` 前缀。名称必须保持 ASCII、小写、语义清晰，并在同一批用例内唯一且不冲突。
- SQL 文件必须仅使用 PostgreSQL 18.4 语法；禁止混入 `AUTO_INCREMENT`、`DEFAULT CHARSET`、`optimizer_switch` 等其他数据库方言。
- 禁止使用 `\!` 或其他 psql 宿主机命令。需要多会话、进程控制或输出规范化时，由受控 runner 在 SQL 文件外完成。


示例：
-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-03-15
-- description  : PostgreSQL 18.4 普通表写入、连接查询与聚合的确定性基础用例。
-- FE           :
-- ++
-- --------------------------------------------------------

SET TIME ZONE 'UTC';
SET statement_timeout = '30s';

DROP TABLE IF EXISTS tab_order_item_001;
DROP TABLE IF EXISTS tab_order_001;

CREATE TABLE tab_order_001 (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_name text NOT NULL
);

CREATE TABLE tab_order_item_001 (
    order_id integer NOT NULL REFERENCES tab_order_001(id),
    item_no integer NOT NULL,
    amount numeric(12, 2) NOT NULL,
    PRIMARY KEY (order_id, item_no)
);

INSERT INTO tab_order_001 (customer_name) VALUES ('alice'), ('bob');
INSERT INTO tab_order_item_001 (order_id, item_no, amount)
VALUES (1, 1, 10.00), (1, 2, 15.50), (2, 1, 7.25);

-- 结果查询显式排序，预期为 alice/25.50、bob/7.25。
SELECT o.customer_name, sum(i.amount) AS total_amount
FROM tab_order_001 AS o
JOIN tab_order_item_001 AS i ON i.order_id = o.id
GROUP BY o.customer_name
ORDER BY o.customer_name;

-- 使用稳定目录字段验证主键，避免输出 OID、路径或耗时等易变值。
SELECT c.relname, i.indisprimary, i.indisvalid
FROM pg_catalog.pg_class AS c
JOIN pg_catalog.pg_index AS i ON i.indexrelid = c.oid
JOIN pg_catalog.pg_class AS t ON t.oid = i.indrelid
WHERE t.relname IN ('tab_order_001', 'tab_order_item_001')
  AND i.indisprimary
ORDER BY t.relname, c.relname;

DROP TABLE IF EXISTS tab_order_item_001;
DROP TABLE IF EXISTS tab_order_001;

RESET statement_timeout;
RESET timezone;

```yaml
structured_config:
  skill_name: output_script_style
  statement: common
  output:
    require_complete_script: true
    require_header: true
    require_pre_cleanup: true
    require_object_setup_from_templates: true
    require_target_statement: true
    require_verification: true
    require_final_cleanup: true
    deterministic_output: true
```
