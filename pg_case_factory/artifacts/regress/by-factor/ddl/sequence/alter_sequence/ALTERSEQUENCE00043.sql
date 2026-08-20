-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SEQUENCE new_schema_name=non_existing_schema
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSEQUENCE00043
-- source_md: skills/pg-sql-generation/references/statements/ddl/sequence/alter_sequence.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/sequence/alter_sequence.yaml
-- primary_obligation_id: ALTERSEQUENCE-SFV|sfv-56c021a2285256bb6f8075d6|set_schema
-- expected_outcome: expected_failure
-- expected_sqlstate: 3F000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SEQUENCE IF EXISTS altersequence_00043_seq CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地序列和因子专用夹具。
CREATE SEQUENCE altersequence_00043_seq AS bigint START WITH 1;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SEQUENCE。
-- primary-target-begin
ALTER SEQUENCE altersequence_00043_seq SET SCHEMA altersequence_00043_no_such_sch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '3F000' AS target_sqlstate_matches_expected;
SELECT count(*) AS seq_exists FROM pg_catalog.pg_class WHERE relname = 'altersequence_00043_seq' AND relkind = 'S' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP SEQUENCE IF EXISTS altersequence_00043_seq CASCADE;
