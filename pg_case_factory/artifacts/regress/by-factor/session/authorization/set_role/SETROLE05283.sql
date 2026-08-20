-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : SET ROLE target_action=set_role
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: SETROLE05283
-- source_md: skills/pg-sql-generation/references/statements/session/authorization/set_role.md
-- factor_md: skills/pg-sql-generation/references/combinations/session/authorization/set_role.yaml
-- primary_obligation_id: SETROLE-EXT|05283|error_assertion|rollback|invalid_transaction
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
ROLLBACK;
RESET ROLE;
DROP ROLE IF EXISTS setrole_05283_witness;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE setrole_05283_witness LOGIN;
GRANT setrole_05283_witness TO CURRENT_USER;
-- 3. 执行唯一获得覆盖信用的 SET ROLE。
-- primary-target-begin
SET ROLE setrole_05283_witness;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS setrole_05283_witness;
