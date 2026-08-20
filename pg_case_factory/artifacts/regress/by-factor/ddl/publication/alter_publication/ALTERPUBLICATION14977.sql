-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER PUBLICATION table_dependency=table_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPUBLICATION14977
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/alter_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/alter_publication.yaml
-- primary_obligation_id: ALTPUB-EXT|14977|set_object|pg_publication_catalog|drop_publication
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterpublication_14977_member_tbl CASCADE;
DROP PUBLICATION IF EXISTS alterpublication_14977_pub CASCADE;
DROP SCHEMA IF EXISTS alterpublication_14977_sch CASCADE;
DROP ROLE IF EXISTS alterpublication_14977_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS alterpublication_14977_sch;
CREATE ROLE alterpublication_14977_owner LOGIN;
GRANT USAGE ON SCHEMA public TO alterpublication_14977_owner;
GRANT USAGE ON SCHEMA alterpublication_14977_sch TO alterpublication_14977_owner;
CREATE PUBLICATION alterpublication_14977_pub;
CREATE TABLE alterpublication_14977_member_tbl (id integer, data text);
ALTER TABLE alterpublication_14977_member_tbl OWNER TO alterpublication_14977_owner;
ALTER PUBLICATION alterpublication_14977_pub ADD TABLE alterpublication_14977_member_tbl;
ALTER PUBLICATION alterpublication_14977_pub OWNER TO alterpublication_14977_owner;
SET ROLE alterpublication_14977_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER PUBLICATION。
-- primary-target-begin
ALTER PUBLICATION alterpublication_14977_pub SET TABLE alterpublication_14977_sch.alterpublication_14977_tbl;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P01' AS target_sqlstate_matches_expected;
SELECT pub.pubname FROM pg_catalog.pg_publication AS pub WHERE pub.pubname = 'alterpublication_14977_pub' ORDER BY pub.pubname;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PUBLICATION IF EXISTS alterpublication_14977_pub CASCADE;
DROP SCHEMA IF EXISTS alterpublication_14977_sch CASCADE;
DROP OWNED BY alterpublication_14977_owner;
DROP ROLE IF EXISTS alterpublication_14977_owner;
DROP TABLE IF EXISTS alterpublication_14977_member_tbl CASCADE;
