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
-- case_id: VACUUM00427
-- source_md: skills/pg-sql-generation/references/statements/utility/maintenance/vacuum.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/maintenance/vacuum.yaml
-- primary_obligation_id: VACUUM-EXT|00427|error_assertion|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS vacuum_00427_t CASCADE;
DROP ROLE IF EXISTS vacuum_00427_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE ROLE vacuum_00427_actor LOGIN NOSUPERUSER;
CREATE TABLE vacuum_00427_t (id integer);
SET ROLE vacuum_00427_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 VACUUM。
-- primary-target-begin
VACUUM VERBOSE "vacuum_00427_t";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY vacuum_00427_actor;
DROP ROLE IF EXISTS vacuum_00427_actor;
RESET statement_timeout;
DROP TABLE IF EXISTS vacuum_00427_t CASCADE;
