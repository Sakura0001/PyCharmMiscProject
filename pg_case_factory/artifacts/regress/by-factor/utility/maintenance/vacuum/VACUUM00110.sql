-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : VACUUM privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: VACUUM00110
-- source_md: skills/pg-sql-generation/references/statements/utility/maintenance/vacuum.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/maintenance/vacuum.yaml
-- primary_obligation_id: VACUUM-EXT|00110|catalog_query|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS vacuum_00110_t CASCADE;
DROP SCHEMA IF EXISTS vacuum_00110_sch CASCADE;
DROP ROLE IF EXISTS vacuum_00110_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA vacuum_00110_sch;
CREATE ROLE vacuum_00110_actor LOGIN NOSUPERUSER;
CREATE TABLE vacuum_00110_t (id integer);
INSERT INTO vacuum_00110_t (id) VALUES (1), (2);
SET ROLE vacuum_00110_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 VACUUM。
-- primary-target-begin
VACUUM FULL vacuum_00110_sch.vacuum_00110_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS catalog_relation_count FROM pg_catalog.pg_class c WHERE c.relname = 'vacuum_00110_t' AND c.relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS vacuum_00110_sch CASCADE;
DROP OWNED BY vacuum_00110_actor;
DROP ROLE IF EXISTS vacuum_00110_actor;
ROLLBACK;
DROP TABLE IF EXISTS vacuum_00110_t CASCADE;
