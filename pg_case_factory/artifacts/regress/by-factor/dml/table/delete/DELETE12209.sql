-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DELETE target_action=delete
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DELETE12209
-- source_md: skills/pg-sql-generation/references/statements/dml/table/delete.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/delete.yaml
-- primary_obligation_id: DELETE-EXT|12209|catalog_query|reset_state
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS delete_12209_tbl, delete_12209_src, delete_12209_ref CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE delete_12209_tbl (id int, val int);
INSERT INTO delete_12209_tbl VALUES (1, 100), (2, 200);
CREATE TABLE delete_12209_src (val int);
INSERT INTO delete_12209_src VALUES (1);
-- 3. 执行唯一获得覆盖信用的 DELETE。
-- primary-target-begin
DELETE FROM "delete_12209_tbl" WHERE id = 999;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS relation_state FROM pg_catalog.pg_class WHERE relname = 'delete_12209_tbl' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS delete_12209_tbl, delete_12209_src, delete_12209_ref CASCADE;
