-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : LOCK TABLE privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: LOCK00075
-- source_md: skills/pg-sql-generation/references/statements/utility/lock/lock.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/lock/lock.yaml
-- primary_obligation_id: LOCK-EXT|00075|effect_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS lock_00075_t CASCADE;
DROP ROLE IF EXISTS lock_00075_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE ROLE lock_00075_actor LOGIN NOSUPERUSER;
CREATE TABLE lock_00075_t (c integer);
SET ROLE lock_00075_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 LOCK TABLE。
-- primary-target-begin
LOCK TABLE lock_00075_sch.lock_00075_t IN ACCESS EXCLUSIVE MODE NOWAIT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS relation_effect_witness FROM pg_catalog.pg_class WHERE relname = 'lock_00075_t' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY lock_00075_actor;
DROP ROLE IF EXISTS lock_00075_actor;
DROP TABLE IF EXISTS lock_00075_t CASCADE;
