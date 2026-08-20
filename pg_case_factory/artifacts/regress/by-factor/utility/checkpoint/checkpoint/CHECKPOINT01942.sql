-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CHECKPOINT privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CHECKPOINT01942
-- source_md: skills/pg-sql-generation/references/statements/utility/checkpoint/checkpoint.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/checkpoint/checkpoint.yaml
-- primary_obligation_id: CP-EXT|01942|error_assertion|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS checkpoint_01942_data;
DROP OWNED BY checkpoint_01942_actor CASCADE;
DROP ROLE IF EXISTS checkpoint_01942_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE checkpoint_01942_data (id integer, payload text);
INSERT INTO checkpoint_01942_data VALUES (1, 'checkpoint_fixture');
CREATE ROLE checkpoint_01942_actor LOGIN NOSUPERUSER;
SET ROLE checkpoint_01942_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CHECKPOINT。
-- primary-target-begin
CHECKPOINT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY checkpoint_01942_actor CASCADE;
DROP ROLE IF EXISTS checkpoint_01942_actor;
DROP TABLE IF EXISTS checkpoint_01942_data;
