-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE SEQUENCE target_form=define_sequence
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATESEQUENCE02695
-- source_md: skills/pg-sql-generation/references/statements/ddl/sequence/create_sequence.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/sequence/create_sequence.yaml
-- primary_obligation_id: CSQ-EXT|02695|nextval_call|DROP_SEQUENCE_CASCADE|bound_options
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SEQUENCE IF EXISTS createsequence_02695_seq CASCADE;
DROP SCHEMA IF EXISTS createsequence_02695_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA createsequence_02695_schema;
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE SEQUENCE。
-- primary-target-begin
CREATE SEQUENCE createsequence_02695_seq START WITH 5;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT nextval('createsequence_02695_seq') AS nextval_check ORDER BY 1;
-- 5. 清理全部本编号对象。
DROP SEQUENCE createsequence_02695_seq CASCADE;
DROP SCHEMA IF EXISTS createsequence_02695_schema CASCADE;
