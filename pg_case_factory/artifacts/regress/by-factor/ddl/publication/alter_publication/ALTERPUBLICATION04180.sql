-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER PUBLICATION publication_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPUBLICATION04180
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/alter_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/alter_publication.yaml
-- primary_obligation_id: ALTPUB-EXT|04180|add_object|pg_publication_catalog|drop_publication
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterpublication_04180_sch.alterpublication_04180_tbl CASCADE;
DROP PUBLICATION IF EXISTS alterpublication_04180_pub CASCADE;
DROP SCHEMA IF EXISTS alterpublication_04180_sch CASCADE;
DROP ROLE IF EXISTS alterpublication_04180_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS alterpublication_04180_sch;
CREATE ROLE alterpublication_04180_owner LOGIN;
GRANT USAGE ON SCHEMA public TO alterpublication_04180_owner;
GRANT USAGE ON SCHEMA alterpublication_04180_sch TO alterpublication_04180_owner;
CREATE PUBLICATION alterpublication_04180_pub;
CREATE TABLE alterpublication_04180_sch.alterpublication_04180_tbl (id integer, data text);
ALTER TABLE alterpublication_04180_sch.alterpublication_04180_tbl OWNER TO alterpublication_04180_owner;
ALTER PUBLICATION alterpublication_04180_pub OWNER TO alterpublication_04180_owner;
SET ROLE alterpublication_04180_owner;
-- 3. 执行唯一获得覆盖信用的 ALTER PUBLICATION。
-- primary-target-begin
ALTER PUBLICATION alterpublication_04180_pub ADD TABLE alterpublication_04180_sch.alterpublication_04180_tbl WHERE (id > 0);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT pub.pubname FROM pg_catalog.pg_publication AS pub WHERE pub.pubname = 'alterpublication_04180_pub' ORDER BY pub.pubname;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PUBLICATION IF EXISTS alterpublication_04180_pub CASCADE;
DROP SCHEMA IF EXISTS alterpublication_04180_sch CASCADE;
DROP OWNED BY alterpublication_04180_owner;
DROP ROLE IF EXISTS alterpublication_04180_owner;
DROP TABLE IF EXISTS alterpublication_04180_sch.alterpublication_04180_tbl CASCADE;
