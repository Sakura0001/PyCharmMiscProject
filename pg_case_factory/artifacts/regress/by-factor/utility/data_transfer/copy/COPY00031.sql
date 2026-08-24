-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : COPY privilege_context=granted_role
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: COPY00031
-- source_md: skills/pg-sql-generation/references/statements/utility/data_transfer/copy.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/data_transfer/copy.yaml
-- primary_obligation_id: COPY-SFV|sfv-af82f47d870c0ce3799e4692|copy_from
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS copy_00031_t;
DROP ROLE IF EXISTS copy_00031_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE copy_00031_actor LOGIN NOSUPERUSER;
CREATE TABLE copy_00031_t (copy_00031_c int);
INSERT INTO copy_00031_t VALUES (1), (2), (3);
GRANT SELECT, INSERT ON copy_00031_t TO copy_00031_actor;
SET ROLE copy_00031_actor;
-- 3. 执行唯一获得覆盖信用的 COPY。
-- primary-target-begin
COPY copy_00031_t FROM 'copy_00031_src.csv';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS rows_in_table FROM pg_catalog.pg_class WHERE relname = 'copy_00031_t' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS copy_00031_actor;
DROP TABLE IF EXISTS copy_00031_t;
