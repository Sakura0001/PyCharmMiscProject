-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : SELECT privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: SELECT10064
-- source_md: skills/pg-sql-generation/references/statements/dml/query/select.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/query/select.yaml
-- primary_obligation_id: SELECT-EXT|10064|effect_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS select_10064_tbl, select_10064_src, select_10064_ref CASCADE;
RESET ROLE;
DROP OWNED BY select_10064_actor CASCADE;
DROP ROLE IF EXISTS select_10064_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE select_10064_actor LOGIN NOSUPERUSER;
CREATE TABLE select_10064_tbl (id int, val int);
INSERT INTO select_10064_tbl VALUES (1, 100), (2, 200);
GRANT SELECT ON select_10064_tbl TO select_10064_actor;
SET ROLE select_10064_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 SELECT。
-- primary-target-begin
SELECT 1 FROM "select_10064_tbl" WHERE id = 999;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) >= 0 AS effect_state FROM select_10064_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY select_10064_actor CASCADE;
DROP ROLE IF EXISTS select_10064_actor;
DROP TABLE IF EXISTS select_10064_tbl, select_10064_src, select_10064_ref CASCADE;
