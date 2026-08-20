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
-- case_id: SELECT16760
-- source_md: skills/pg-sql-generation/references/statements/dml/query/select.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/query/select.yaml
-- primary_obligation_id: SELECT-EXT|16760|effect_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS select_16760_tbl, select_16760_src, select_16760_ref CASCADE;
RESET ROLE;
DROP OWNED BY select_16760_actor CASCADE;
DROP ROLE IF EXISTS select_16760_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE select_16760_actor LOGIN NOSUPERUSER;
CREATE TABLE select_16760_tbl (id int, val int);
INSERT INTO select_16760_tbl VALUES (1, 100), (2, 200);
CREATE TABLE select_16760_src (val int);
INSERT INTO select_16760_src VALUES (1);
GRANT SELECT ON select_16760_tbl TO select_16760_actor;
SET ROLE select_16760_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 SELECT。
-- primary-target-begin
SELECT 1 FROM select_16760_tbl AS s WHERE id IN (SELECT val FROM select_16760_src);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) >= 0 AS effect_state FROM select_16760_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY select_16760_actor CASCADE;
DROP ROLE IF EXISTS select_16760_actor;
DROP TABLE IF EXISTS select_16760_tbl, select_16760_src, select_16760_ref CASCADE;
