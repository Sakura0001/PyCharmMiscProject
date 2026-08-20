-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP ROLE owned_objects=owns_multiple_objects
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPROLE05642
-- source_md: skills/pg-sql-generation/references/statements/ddl/role/drop_role.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/role/drop_role.yaml
-- primary_obligation_id: DROPROLE-EXT|05642|drop_role|error_assertion|revoke_privileges_then_drop_role
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droprole_05642_t CASCADE;
DROP FUNCTION IF EXISTS droprole_05642_fn();
DROP VIEW IF EXISTS droprole_05642_v;
DROP SEQUENCE IF EXISTS droprole_05642_seq;
DROP ROLE IF EXISTS "droprole_05642_MixedCase";
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
SELECT 1 AS setup_boundary;
SELECT 1 AS target_role_intentionally_absent;
CREATE TABLE droprole_05642_t (c integer);
ALTER TABLE droprole_05642_t OWNER TO "droprole_05642_MixedCase";
CREATE SEQUENCE droprole_05642_seq;
ALTER SEQUENCE droprole_05642_seq OWNER TO "droprole_05642_MixedCase";
CREATE VIEW droprole_05642_v AS SELECT 1;
ALTER VIEW droprole_05642_v OWNER TO "droprole_05642_MixedCase";
CREATE FUNCTION droprole_05642_fn() RETURNS integer AS 'SELECT 1' LANGUAGE sql;
ALTER FUNCTION droprole_05642_fn() OWNER TO "droprole_05642_MixedCase";
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP ROLE。
-- primary-target-begin
DROP ROLE "droprole_05642_MixedCase";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS role_absent FROM pg_catalog.pg_roles WHERE rolname = 'droprole_05642_MixedCase' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP ROLE IF EXISTS "droprole_05642_MixedCase";
DROP FUNCTION IF EXISTS droprole_05642_fn();
DROP VIEW IF EXISTS droprole_05642_v;
DROP SEQUENCE IF EXISTS droprole_05642_seq;
DROP TABLE IF EXISTS droprole_05642_t CASCADE;
