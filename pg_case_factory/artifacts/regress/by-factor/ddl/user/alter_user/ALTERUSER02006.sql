-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER USER new_name_shape=duplicate_name
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERUSER02006
-- source_md: skills/pg-sql-generation/references/statements/ddl/user/alter_user.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user/alter_user.yaml
-- primary_obligation_id: AUSR-EXT|02006|error_assertion|reset_config
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS "alteruser_02006_Mixed Role";
DROP ROLE IF EXISTS alteruser_02006_conflict;
DROP ROLE IF EXISTS alteruser_02006_conflict;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE "alteruser_02006_Mixed Role" LOGIN;
CREATE ROLE alteruser_02006_conflict LOGIN;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER USER。
-- primary-target-begin
ALTER USER "alteruser_02006_Mixed Role" RENAME TO alteruser_02006_conflict;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP ROLE IF EXISTS "alteruser_02006_Mixed Role";
DROP ROLE IF EXISTS alteruser_02006_conflict;
DROP ROLE IF EXISTS alteruser_02006_conflict;
