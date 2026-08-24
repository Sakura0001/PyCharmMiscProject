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
-- case_id: ALTERPUBLICATION05956
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/alter_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/alter_publication.yaml
-- primary_obligation_id: ALTPUB-EXT|05956|add_object|pg_publication_catalog|drop_publication
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterpublication_05956_tbl, alterpublication_05956_member_tbl CASCADE;
DROP PUBLICATION IF EXISTS "alterpublication_05956_Mixed Pub" CASCADE;
DROP ROLE IF EXISTS alterpublication_05956_owner;
DROP ROLE IF EXISTS alterpublication_05956_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
CREATE ROLE alterpublication_05956_owner LOGIN;
CREATE ROLE alterpublication_05956_actor LOGIN;
GRANT USAGE ON SCHEMA public TO alterpublication_05956_owner;
GRANT USAGE ON SCHEMA public TO alterpublication_05956_actor;
CREATE PUBLICATION "alterpublication_05956_Mixed Pub";
CREATE TABLE alterpublication_05956_tbl (id integer, data text);
CREATE TABLE alterpublication_05956_member_tbl (id integer, data text);
ALTER PUBLICATION "alterpublication_05956_Mixed Pub" ADD TABLE alterpublication_05956_member_tbl;
ALTER PUBLICATION "alterpublication_05956_Mixed Pub" OWNER TO alterpublication_05956_owner;
SET ROLE alterpublication_05956_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER PUBLICATION。
-- primary-target-begin
ALTER PUBLICATION "alterpublication_05956_Mixed Pub" ADD TABLE alterpublication_05956_tbl (id) WHERE (id > 0);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT pub.pubname FROM pg_catalog.pg_publication AS pub WHERE pub.pubname = 'alterpublication_05956_Mixed Pub' ORDER BY pub.pubname;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PUBLICATION IF EXISTS "alterpublication_05956_Mixed Pub" CASCADE;
DROP OWNED BY alterpublication_05956_owner;
DROP ROLE IF EXISTS alterpublication_05956_owner;
DROP OWNED BY alterpublication_05956_actor;
DROP ROLE IF EXISTS alterpublication_05956_actor;
DROP TABLE IF EXISTS alterpublication_05956_tbl, alterpublication_05956_member_tbl CASCADE;
