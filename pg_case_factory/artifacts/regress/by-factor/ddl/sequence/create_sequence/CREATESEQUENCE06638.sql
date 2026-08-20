-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE SEQUENCE object_state=already_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATESEQUENCE06638
-- source_md: skills/pg-sql-generation/references/statements/ddl/sequence/create_sequence.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/sequence/create_sequence.yaml
-- primary_obligation_id: CSQ-EXT|06638|nextval_call|DROP_SEQUENCE|naming_options
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SEQUENCE IF EXISTS createsequence_06638_schema.createsequence_06638_seq CASCADE;
DROP SCHEMA IF EXISTS createsequence_06638_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createsequence_06638_schema;
CREATE SEQUENCE createsequence_06638_schema.createsequence_06638_seq;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE SEQUENCE。
-- primary-target-begin
CREATE UNLOGGED SEQUENCE createsequence_06638_schema.createsequence_06638_seq OWNED BY NONE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT nextval('createsequence_06638_schema.createsequence_06638_seq') AS nextval_check ORDER BY 1;
-- 5. 清理全部本编号对象。
DROP SEQUENCE createsequence_06638_schema.createsequence_06638_seq CASCADE;
DROP SEQUENCE createsequence_06638_schema.createsequence_06638_seq CASCADE;
DROP SCHEMA IF EXISTS createsequence_06638_schema CASCADE;
