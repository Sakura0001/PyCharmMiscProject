-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER PUBLICATION publication_state=non_existent
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPUBLICATION08736
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/alter_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/alter_publication.yaml
-- primary_obligation_id: ALTPUB-EXT|08736|add_object|error_assertion|drop_publication
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS "alterpublication_08736_Mixed Sch" CASCADE;
DROP ROLE IF EXISTS alterpublication_08736_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS "alterpublication_08736_Mixed Sch";
CREATE ROLE alterpublication_08736_owner LOGIN;
GRANT USAGE ON SCHEMA public TO alterpublication_08736_owner;
GRANT USAGE ON SCHEMA "alterpublication_08736_Mixed Sch" TO alterpublication_08736_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER PUBLICATION。
-- primary-target-begin
ALTER PUBLICATION "alterpublication_08736_Mixed Pub" ADD TABLES IN SCHEMA "alterpublication_08736_Mixed Sch";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT 1 AS error_assertion_verified;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS "alterpublication_08736_Mixed Sch" CASCADE;
DROP OWNED BY alterpublication_08736_owner;
DROP ROLE IF EXISTS alterpublication_08736_owner;
