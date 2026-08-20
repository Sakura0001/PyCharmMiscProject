-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : UPDATE privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: UPDATE17206
-- source_md: skills/pg-sql-generation/references/statements/dml/table/update.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/update.yaml
-- primary_obligation_id: UPDATE-EXT|17206|returned_rows|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS update_17206_tbl, update_17206_src, update_17206_ref CASCADE;
RESET ROLE;
DROP OWNED BY update_17206_actor CASCADE;
DROP ROLE IF EXISTS update_17206_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE update_17206_actor LOGIN NOSUPERUSER;
CREATE TABLE update_17206_tbl (id int, val int);
INSERT INTO update_17206_tbl VALUES (1, 100), (2, 200);
CREATE TABLE update_17206_src (val int);
INSERT INTO update_17206_src VALUES (1);
GRANT SELECT ON update_17206_tbl TO update_17206_actor;
SET ROLE update_17206_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 UPDATE。
-- primary-target-begin
UPDATE update_17206_tbl SET val = (SELECT val FROM update_17206_src) WHERE id = 1;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) >= 0 AS returned_rows_state FROM update_17206_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY update_17206_actor CASCADE;
DROP ROLE IF EXISTS update_17206_actor;
DROP TABLE IF EXISTS update_17206_tbl, update_17206_src, update_17206_ref CASCADE;
