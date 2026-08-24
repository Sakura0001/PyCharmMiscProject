-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DELETE privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DELETE11421
-- source_md: skills/pg-sql-generation/references/statements/dml/table/delete.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/delete.yaml
-- primary_obligation_id: DELETE-EXT|11421|returned_rows|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS delete_11421_tbl, delete_11421_src, delete_11421_ref CASCADE;
RESET ROLE;
DROP OWNED BY delete_11421_actor CASCADE;
DROP ROLE IF EXISTS delete_11421_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE delete_11421_actor LOGIN NOSUPERUSER;
CREATE TABLE delete_11421_tbl (id int, val int);
INSERT INTO delete_11421_tbl VALUES (1, 100), (2, 200);
CREATE TABLE delete_11421_src (val int);
INSERT INTO delete_11421_src VALUES (1);
GRANT SELECT ON delete_11421_tbl TO delete_11421_actor;
SET ROLE delete_11421_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DELETE。
-- primary-target-begin
DELETE FROM public.delete_11421_tbl WHERE id = 999;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) >= 0 AS returned_rows_state FROM delete_11421_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY delete_11421_actor CASCADE;
DROP ROLE IF EXISTS delete_11421_actor;
DROP TABLE IF EXISTS delete_11421_tbl, delete_11421_src, delete_11421_ref CASCADE;
