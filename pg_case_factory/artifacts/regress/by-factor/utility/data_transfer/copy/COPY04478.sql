-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : COPY target_action=copy_from
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: COPY04478
-- source_md: skills/pg-sql-generation/references/statements/utility/data_transfer/copy.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/data_transfer/copy.yaml
-- primary_obligation_id: COPY-EXT|04478|error_assertion|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS copy_04478_t;
DROP ROLE IF EXISTS copy_04478_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE copy_04478_actor LOGIN NOSUPERUSER;
CREATE TABLE copy_04478_t (copy_04478_c int);
GRANT SELECT, INSERT ON copy_04478_t TO copy_04478_actor;
SET ROLE copy_04478_actor;
-- 3. 执行唯一获得覆盖信用的 COPY。
-- primary-target-begin
COPY copy_04478_t FROM 'copy_04478_src.csv';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS copy_04478_actor;
DROP TABLE IF EXISTS copy_04478_t;
