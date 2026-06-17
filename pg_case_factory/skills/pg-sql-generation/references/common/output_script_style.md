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


示例：
-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-03-15
-- description  : 场景1（查询包含GROUP BY或DISTINCT，且无聚合函数；若仅有DISTINCT则不应含窗口函数），基础功能测试。
-- FE           :
-- ++
-- --------------------------------------------------------

SET optimizer_switch='left_join_elimination=on';

DROP TABLE IF EXISTS tab_left_join_elimination_004_001;
DROP TABLE IF EXISTS tab_left_join_elimination_004_002;

CREATE TABLE tab_left_join_elimination_004_001 (
    id INT PRIMARY KEY AUTO_INCREMENT,
    a  INT,
    b  VARCHAR(20)
) DEFAULT CHARSET = utf8mb4;

CREATE TABLE tab_left_join_elimination_004_002 (
    id INT PRIMARY KEY AUTO_INCREMENT,
    a  INT,
    b  VARCHAR(20)
) DEFAULT CHARSET = utf8mb4;

-- t2中a=1存在两条记录，用于验证消除后不产生重复行
INSERT INTO tab_left_join_elimination_004_001 (a, b) VALUES (1, 'a'), (2, 'b'), (3, 'c');
INSERT INTO tab_left_join_elimination_004_002 (a, b) VALUES (1, 'x'), (1, 'y'), (2, 'z');

-- 正例：GROUP BY无聚合函数，t2应被消除，预期返回3行
SELECT t1.a FROM tab_left_join_elimination_004_001 t1 LEFT JOIN tab_left_join_elimination_004_002 t2 ON t1.a = t2.a GROUP BY t1.a ORDER BY 1;

-- 正例：DISTINCT无窗口函数，t2应被消除，预期返回3行
SELECT DISTINCT t1.a FROM tab_left_join_elimination_004_001 t1 LEFT JOIN tab_left_join_elimination_004_002 t2 ON t1.a = t2.a ORDER BY 1;

-- 反例：GROUP BY含聚合函数COUNT(*)，t2不应被消除（a=1消除前COUNT=2，消除后COUNT=1）
SELECT t1.a, COUNT(*) FROM tab_left_join_elimination_004_001 t1 LEFT JOIN tab_left_join_elimination_004_002 t2 ON t1.a = t2.a GROUP BY t1.a ORDER BY 1;

-- 反例：DISTINCT含窗口函数ROW_NUMBER()，t2不应被消除（消除前4行，消除后3行）
SELECT DISTINCT t1.a, ROW_NUMBER() OVER (ORDER BY t1.a) AS rn FROM tab_left_join_elimination_004_001 t1 LEFT JOIN tab_left_join_elimination_004_002 t2 ON t1.a = t2.a ORDER BY 1, 2;

-- EXPLAIN验证：DISTINCT无窗口函数，执行计划中t2应被消除
\! bash -c 'awk -f <(printf "BEGIN{FS=OFS=\x22\x7c\x22}\n/^[\x7c]/{NF=4\nprint \x240 \x22\x7c\x22\nnext}\n{print}\n") <(sh commonScript/execute_sql_with_root.sh master test "EXPLAIN SELECT DISTINCT t1.a FROM tab_left_join_elimination_004_001 t1 LEFT JOIN tab_left_join_elimination_004_002 t2 ON t1.a = t2.a")'

-- EXPLAIN验证：GROUP BY含COUNT(*)，执行计划中t2不应被消除
\! bash -c 'awk -f <(printf "BEGIN{FS=OFS=\x22\x7c\x22}\n/^[\x7c]/{NF=4\nprint \x240 \x22\x7c\x22\nnext}\n{print}\n") <(sh commonScript/execute_sql_with_root.sh master test "EXPLAIN SELECT t1.a, COUNT(*) FROM tab_left_join_elimination_004_001 t1 LEFT JOIN tab_left_join_elimination_004_002 t2 ON t1.a = t2.a GROUP BY t1.a")'

-- EXPLAIN验证：DISTINCT含ROW_NUMBER()，执行计划中t2不应被消除
\! bash -c 'awk -f <(printf "BEGIN{FS=OFS=\x22\x7c\x22}\n/^[\x7c]/{NF=4\nprint \x240 \x22\x7c\x22\nnext}\n{print}\n") <(sh commonScript/execute_sql_with_root.sh master test "EXPLAIN SELECT DISTINCT t1.a, ROW_NUMBER() OVER (ORDER BY t1.a) AS rn FROM tab_left_join_elimination_004_001 t1 LEFT JOIN tab_left_join_elimination_004_002 t2 ON t1.a = t2.a")'

DROP TABLE IF EXISTS tab_left_join_elimination_004_001;
DROP TABLE IF EXISTS tab_left_join_elimination_004_002;

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
