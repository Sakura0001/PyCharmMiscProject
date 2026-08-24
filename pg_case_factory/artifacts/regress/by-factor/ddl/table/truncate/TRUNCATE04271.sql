-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : TRUNCATE privilege_level=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: TRUNCATE04271
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/truncate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/truncate.yaml
-- primary_obligation_id: TRUNCATE-EXT|04271|select_count_zero|reinsert_data
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS truncate_04271_tbl, truncate_04271_ref CASCADE;
RESET ROLE;
DROP OWNED BY truncate_04271_actor CASCADE;
DROP ROLE IF EXISTS truncate_04271_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE truncate_04271_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA public TO truncate_04271_actor;
CREATE TABLE truncate_04271_tbl (id int, val int);
INSERT INTO truncate_04271_tbl VALUES (1, 100), (2, 200);
SET ROLE truncate_04271_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 TRUNCATE。
-- primary-target-begin
TRUNCATE TABLE truncate_04271_tbl RESTRICT ;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS effect_state FROM truncate_04271_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY truncate_04271_actor CASCADE;
DROP ROLE IF EXISTS truncate_04271_actor;
DROP TABLE IF EXISTS truncate_04271_tbl, truncate_04271_ref CASCADE;
