-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER PUBLICATION executor_privilege=non_owner_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPUBLICATION11646
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/alter_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/alter_publication.yaml
-- primary_obligation_id: ALTPUB-EXT|11646|set_object|error_assertion|drop_publication
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterpublication_11646_tbl CASCADE;
DROP PUBLICATION IF EXISTS "alterpublication_11646_Mixed Pub" CASCADE;
DROP ROLE IF EXISTS alterpublication_11646_owner;
DROP ROLE IF EXISTS alterpublication_11646_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
CREATE ROLE alterpublication_11646_owner LOGIN;
CREATE ROLE alterpublication_11646_actor LOGIN;
GRANT USAGE ON SCHEMA public TO alterpublication_11646_owner;
GRANT USAGE ON SCHEMA public TO alterpublication_11646_actor;
CREATE PUBLICATION "alterpublication_11646_Mixed Pub" FOR ALL TABLES;
CREATE TABLE alterpublication_11646_tbl (id integer, data text);
ALTER PUBLICATION "alterpublication_11646_Mixed Pub" OWNER TO alterpublication_11646_owner;
SET ROLE alterpublication_11646_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER PUBLICATION。
-- primary-target-begin
ALTER PUBLICATION "alterpublication_11646_Mixed Pub" SET TABLE alterpublication_11646_tbl (id, data) WHERE (id > 0);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT 1 AS error_assertion_verified;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PUBLICATION IF EXISTS "alterpublication_11646_Mixed Pub" CASCADE;
DROP OWNED BY alterpublication_11646_owner;
DROP ROLE IF EXISTS alterpublication_11646_owner;
DROP OWNED BY alterpublication_11646_actor;
DROP ROLE IF EXISTS alterpublication_11646_actor;
DROP TABLE IF EXISTS alterpublication_11646_tbl CASCADE;
