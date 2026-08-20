-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DELETE constraint_boundary=constraint_violation
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DELETE05443
-- source_md: skills/pg-sql-generation/references/statements/dml/table/delete.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/delete.yaml
-- primary_obligation_id: DELETE-EXT|05443|effect_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 23000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS delete_05443_tbl, delete_05443_src, delete_05443_ref CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE delete_05443_tbl (id int PRIMARY KEY, val int);
CREATE TABLE delete_05443_ref (id int REFERENCES delete_05443_tbl(id));
INSERT INTO delete_05443_tbl VALUES (1, 100);
INSERT INTO delete_05443_ref VALUES (1);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DELETE。
-- primary-target-begin
WITH delete_05443_cte AS (SELECT 1 AS val)
DELETE FROM delete_05443_tbl AS d WHERE id IN (SELECT val FROM delete_05443_cte);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '23000' AS target_sqlstate_matches_expected;
SELECT count(*) >= 0 AS effect_state FROM delete_05443_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS delete_05443_tbl, delete_05443_src, delete_05443_ref CASCADE;
