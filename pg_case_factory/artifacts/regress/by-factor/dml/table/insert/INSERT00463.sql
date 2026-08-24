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
-- case_id: INSERT00463
-- source_md: skills/pg-sql-generation/references/statements/dml/table/insert.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/insert.yaml
-- primary_obligation_id: INSERT-EXT|00463|effect_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS insert_00463_tbl, insert_00463_src, insert_00463_ref CASCADE;
RESET ROLE;
DROP OWNED BY insert_00463_actor CASCADE;
DROP ROLE IF EXISTS insert_00463_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE insert_00463_actor LOGIN NOSUPERUSER;
CREATE TABLE insert_00463_tbl (id int PRIMARY KEY, val int);
GRANT SELECT ON insert_00463_tbl TO insert_00463_actor;
SET ROLE insert_00463_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 INSERT。
-- primary-target-begin
WITH insert_00463_cte AS (SELECT 1 AS val)
INSERT INTO "insert_00463_tbl" (id, val) SELECT 1, val FROM insert_00463_cte;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) >= 0 AS effect_state FROM insert_00463_tbl ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY insert_00463_actor CASCADE;
DROP ROLE IF EXISTS insert_00463_actor;
DROP TABLE IF EXISTS insert_00463_tbl, insert_00463_src, insert_00463_ref CASCADE;
