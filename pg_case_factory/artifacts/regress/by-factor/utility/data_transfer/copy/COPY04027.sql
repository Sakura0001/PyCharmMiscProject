-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : COPY resource_boundary=missing_file_or_library
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: COPY04027
-- source_md: skills/pg-sql-generation/references/statements/utility/data_transfer/copy.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/data_transfer/copy.yaml
-- primary_obligation_id: COPY-EXT|04027|effect_query|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 58P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS copy_04027_t;
DROP ROLE IF EXISTS copy_04027_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE copy_04027_actor LOGIN NOSUPERUSER;
CREATE TABLE copy_04027_t (copy_04027_c int);
INSERT INTO copy_04027_t VALUES (1), (2), (3);
GRANT SELECT, INSERT ON copy_04027_t TO copy_04027_actor;
SET ROLE copy_04027_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 COPY。
-- primary-target-begin
COPY public.copy_04027_t (copy_04027_c) TO STDOUT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '58P01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS rows_in_table FROM pg_catalog.pg_class WHERE relname = 'copy_04027_t' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
ROLLBACK;
DROP ROLE IF EXISTS copy_04027_actor;
DROP TABLE IF EXISTS copy_04027_t;
