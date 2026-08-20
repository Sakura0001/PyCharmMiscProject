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
-- case_id: DROPROLE02566
-- source_md: skills/pg-sql-generation/references/statements/ddl/role/drop_role.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/role/drop_role.yaml
-- primary_obligation_id: DROPROLE-EXT|02566|drop_role|effect_query|revoke_privileges_then_drop_role
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droprole_02566_t CASCADE;
DROP FUNCTION IF EXISTS droprole_02566_fn();
DROP VIEW IF EXISTS droprole_02566_v;
DROP SEQUENCE IF EXISTS droprole_02566_seq;
DROP ROLE IF EXISTS "droprole_02566_MixedCase";
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
SELECT 1 AS setup_boundary;
SELECT 1 AS target_role_intentionally_absent;
CREATE TABLE droprole_02566_t (c integer);
ALTER TABLE droprole_02566_t OWNER TO "droprole_02566_MixedCase";
CREATE SEQUENCE droprole_02566_seq;
ALTER SEQUENCE droprole_02566_seq OWNER TO "droprole_02566_MixedCase";
CREATE VIEW droprole_02566_v AS SELECT 1;
ALTER VIEW droprole_02566_v OWNER TO "droprole_02566_MixedCase";
CREATE FUNCTION droprole_02566_fn() RETURNS integer AS 'SELECT 1' LANGUAGE sql;
ALTER FUNCTION droprole_02566_fn() OWNER TO "droprole_02566_MixedCase";
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP ROLE。
-- primary-target-begin
DROP ROLE IF EXISTS "droprole_02566_MixedCase";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS role_absent FROM pg_catalog.pg_roles WHERE rolname = 'droprole_02566_MixedCase' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP ROLE IF EXISTS "droprole_02566_MixedCase";
DROP FUNCTION IF EXISTS droprole_02566_fn();
DROP VIEW IF EXISTS droprole_02566_v;
DROP SEQUENCE IF EXISTS droprole_02566_seq;
DROP TABLE IF EXISTS droprole_02566_t CASCADE;
