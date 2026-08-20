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
-- case_id: ALTERPUBLICATION03004
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/alter_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/alter_publication.yaml
-- primary_obligation_id: ALTPUB-EXT|03004|owner|pg_publication_catalog|drop_publication
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterpublication_03004_tbl, alterpublication_03004_member_tbl CASCADE;
DROP PUBLICATION IF EXISTS alterpublication_03004_pub CASCADE;
DROP ROLE IF EXISTS alterpublication_03004_owner;
DROP ROLE IF EXISTS alterpublication_03004_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
CREATE ROLE alterpublication_03004_owner LOGIN;
CREATE ROLE alterpublication_03004_actor LOGIN;
GRANT USAGE ON SCHEMA public TO alterpublication_03004_owner;
GRANT USAGE ON SCHEMA public TO alterpublication_03004_actor;
CREATE PUBLICATION alterpublication_03004_pub;
CREATE TABLE alterpublication_03004_tbl (id integer, data text);
CREATE TABLE alterpublication_03004_member_tbl (id integer, data text);
ALTER PUBLICATION alterpublication_03004_pub ADD TABLE alterpublication_03004_member_tbl;
SET ROLE alterpublication_03004_actor;
-- 3. 执行唯一获得覆盖信用的 ALTER PUBLICATION。
-- primary-target-begin
ALTER PUBLICATION alterpublication_03004_pub OWNER TO SESSION_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT pub.pubname FROM pg_catalog.pg_publication AS pub WHERE pub.pubname = 'alterpublication_03004_pub' ORDER BY pub.pubname;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PUBLICATION IF EXISTS alterpublication_03004_pub CASCADE;
DROP OWNED BY alterpublication_03004_owner;
DROP ROLE IF EXISTS alterpublication_03004_owner;
DROP OWNED BY alterpublication_03004_actor;
DROP ROLE IF EXISTS alterpublication_03004_actor;
DROP TABLE IF EXISTS alterpublication_03004_tbl, alterpublication_03004_member_tbl CASCADE;
