-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : INSERT privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: INSERT13021
-- source_md: skills/pg-sql-generation/references/statements/dml/table/insert.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/insert.yaml
-- primary_obligation_id: INSERT-EXT|13021|error_assertion|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS insert_13021_tbl, insert_13021_src, insert_13021_ref CASCADE;
RESET ROLE;
DROP OWNED BY insert_13021_actor CASCADE;
DROP ROLE IF EXISTS insert_13021_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE insert_13021_actor LOGIN NOSUPERUSER;
CREATE TABLE insert_13021_tbl (id int PRIMARY KEY, val int);
GRANT SELECT ON insert_13021_tbl TO insert_13021_actor;
SET ROLE insert_13021_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 INSERT。
-- primary-target-begin
WITH insert_13021_cte AS (SELECT 1 AS val)
INSERT INTO insert_13021_tbl AS i (id, val) SELECT 1, val FROM insert_13021_cte;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY insert_13021_actor CASCADE;
DROP ROLE IF EXISTS insert_13021_actor;
DROP TABLE IF EXISTS insert_13021_tbl, insert_13021_src, insert_13021_ref CASCADE;
