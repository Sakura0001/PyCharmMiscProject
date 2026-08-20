-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SEQUENCE object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSEQUENCE25820
-- source_md: skills/pg-sql-generation/references/statements/ddl/sequence/alter_sequence.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/sequence/alter_sequence.yaml
-- primary_obligation_id: ALTSEQ-EXT|25820|alter_parameters|pg_class_catalog_query|DROP_SEQUENCE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SEQUENCE IF EXISTS "altersequence_25820_user" CASCADE;
DROP ROLE IF EXISTS altersequence_25820_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地序列和因子专用夹具。
CREATE ROLE altersequence_25820_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altersequence_25820_owner;
CREATE SEQUENCE "altersequence_25820_user" AS bigint START WITH 1 INCREMENT BY 1;
ALTER SEQUENCE "altersequence_25820_user" OWNER TO altersequence_25820_owner;
SET ROLE altersequence_25820_owner;
-- 3. 执行唯一获得覆盖信用的 ALTER SEQUENCE。
-- primary-target-begin
ALTER SEQUENCE IF EXISTS "altersequence_25820_user";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS seq_exists FROM pg_catalog.pg_class WHERE relname = 'altersequence_25820_user' AND relkind = 'S' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SEQUENCE IF EXISTS "altersequence_25820_user" CASCADE;
DROP OWNED BY altersequence_25820_owner;
DROP ROLE IF EXISTS altersequence_25820_owner;
