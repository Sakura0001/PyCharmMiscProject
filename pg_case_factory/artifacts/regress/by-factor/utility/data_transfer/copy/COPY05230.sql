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
-- case_id: COPY05230
-- source_md: skills/pg-sql-generation/references/statements/utility/data_transfer/copy.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/data_transfer/copy.yaml
-- primary_obligation_id: COPY-EXT|05230|returned_rows|rollback
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS copy_05230_t;
DROP ROLE IF EXISTS copy_05230_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE copy_05230_actor LOGIN NOSUPERUSER;
CREATE TABLE copy_05230_t (copy_05230_c int);
INSERT INTO copy_05230_t VALUES (1), (2), (3);
GRANT SELECT, INSERT ON copy_05230_t TO copy_05230_actor;
SET ROLE copy_05230_actor;
-- 3. 执行唯一获得覆盖信用的 COPY。
-- primary-target-begin
COPY copy_05230_t TO 'copy_05230_out.csv';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS copy_ran FROM pg_catalog.pg_class WHERE relname = 'copy_05230_t' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
ROLLBACK;
DROP ROLE IF EXISTS copy_05230_actor;
DROP TABLE IF EXISTS copy_05230_t;
