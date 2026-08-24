-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : COPY target_action=copy_to
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: COPY05535
-- source_md: skills/pg-sql-generation/references/statements/utility/data_transfer/copy.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/data_transfer/copy.yaml
-- primary_obligation_id: COPY-EXT|05535|error_assertion|reset_state
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS copy_05535_t;
DROP ROLE IF EXISTS copy_05535_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE copy_05535_actor LOGIN NOSUPERUSER;
CREATE TABLE copy_05535_t (copy_05535_c int);
INSERT INTO copy_05535_t VALUES (1), (2), (3);
GRANT SELECT, INSERT ON copy_05535_t TO copy_05535_actor;
SET ROLE copy_05535_actor;
-- 3. 执行唯一获得覆盖信用的 COPY。
-- primary-target-begin
COPY "copy_05535_t" (copy_05535_c) TO STDOUT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
RESET search_path;
DROP ROLE IF EXISTS copy_05535_actor;
DROP TABLE IF EXISTS copy_05535_t;
