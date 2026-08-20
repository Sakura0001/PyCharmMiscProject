-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SYSTEM value_shape=invalid_value_type
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSYSTEM00660
-- source_md: skills/pg-sql-generation/references/statements/ddl/system/alter_system.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/system/alter_system.yaml
-- primary_obligation_id: ASYS-EXT|00660|show_command|alter_system_reset_parameter
-- expected_outcome: expected_failure
-- expected_sqlstate: 22023
-- 1. 清理本编号对象，保证脚本可重复执行。
ALTER SYSTEM RESET enable_hashjoin;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SYSTEM。
-- primary-target-begin
ALTER SYSTEM SET enable_hashjoin = 'not_a_number';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '22023' AS target_sqlstate_matches_expected;
SHOW enable_hashjoin;
-- 5. 清理全部本编号对象。
ALTER SYSTEM RESET enable_hashjoin;
