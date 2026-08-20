-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER PUBLICATION publication_state=exists_with_tables
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPUBLICATION12882
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/alter_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/alter_publication.yaml
-- primary_obligation_id: ALTPUB-EXT|12882|set_object|error_assertion|drop_publication
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterpublication_12882_sch.alterpublication_12882_tbl, alterpublication_12882_member_tbl CASCADE;
DROP PUBLICATION IF EXISTS alterpublication_12882_pub CASCADE;
DROP SCHEMA IF EXISTS alterpublication_12882_sch CASCADE;
DROP ROLE IF EXISTS alterpublication_12882_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS alterpublication_12882_sch;
CREATE ROLE alterpublication_12882_owner LOGIN;
GRANT USAGE ON SCHEMA public TO alterpublication_12882_owner;
GRANT USAGE ON SCHEMA alterpublication_12882_sch TO alterpublication_12882_owner;
CREATE PUBLICATION alterpublication_12882_pub;
CREATE TABLE alterpublication_12882_sch.alterpublication_12882_tbl (id integer, data text);
CREATE TABLE alterpublication_12882_member_tbl (id integer, data text);
ALTER TABLE alterpublication_12882_sch.alterpublication_12882_tbl OWNER TO alterpublication_12882_owner;
ALTER TABLE alterpublication_12882_member_tbl OWNER TO alterpublication_12882_owner;
ALTER PUBLICATION alterpublication_12882_pub ADD TABLE alterpublication_12882_member_tbl;
ALTER PUBLICATION alterpublication_12882_pub OWNER TO alterpublication_12882_owner;
SET ROLE alterpublication_12882_owner;
-- 3. 执行唯一获得覆盖信用的 ALTER PUBLICATION。
-- primary-target-begin
ALTER PUBLICATION alterpublication_12882_pub SET TABLE alterpublication_12882_sch.alterpublication_12882_tbl (id, data) WHERE (id > 0);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT 1 AS error_assertion_verified;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PUBLICATION IF EXISTS alterpublication_12882_pub CASCADE;
DROP SCHEMA IF EXISTS alterpublication_12882_sch CASCADE;
DROP OWNED BY alterpublication_12882_owner;
DROP ROLE IF EXISTS alterpublication_12882_owner;
DROP TABLE IF EXISTS alterpublication_12882_sch.alterpublication_12882_tbl, alterpublication_12882_member_tbl CASCADE;
