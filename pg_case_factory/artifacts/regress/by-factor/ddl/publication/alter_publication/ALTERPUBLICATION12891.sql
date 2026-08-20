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
-- case_id: ALTERPUBLICATION12891
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/alter_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/alter_publication.yaml
-- primary_obligation_id: ALTPUB-EXT|12891|set_object|error_assertion|drop_publication
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterpublication_12891_tbl, alterpublication_12891_member_tbl CASCADE;
DROP PUBLICATION IF EXISTS alterpublication_12891_pub CASCADE;
DROP ROLE IF EXISTS alterpublication_12891_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
CREATE ROLE alterpublication_12891_owner LOGIN;
GRANT USAGE ON SCHEMA public TO alterpublication_12891_owner;
CREATE PUBLICATION alterpublication_12891_pub;
CREATE TABLE alterpublication_12891_tbl (id integer, data text);
CREATE TABLE alterpublication_12891_member_tbl (id integer, data text);
ALTER TABLE alterpublication_12891_tbl OWNER TO alterpublication_12891_owner;
ALTER TABLE alterpublication_12891_member_tbl OWNER TO alterpublication_12891_owner;
ALTER PUBLICATION alterpublication_12891_pub ADD TABLE alterpublication_12891_member_tbl;
ALTER PUBLICATION alterpublication_12891_pub OWNER TO alterpublication_12891_owner;
SET ROLE alterpublication_12891_owner;
-- 3. 执行唯一获得覆盖信用的 ALTER PUBLICATION。
-- primary-target-begin
ALTER PUBLICATION alterpublication_12891_pub SET TABLE "alterpublication_12891_tbl" (id, data);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT 1 AS error_assertion_verified;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PUBLICATION IF EXISTS alterpublication_12891_pub CASCADE;
DROP OWNED BY alterpublication_12891_owner;
DROP ROLE IF EXISTS alterpublication_12891_owner;
DROP TABLE IF EXISTS alterpublication_12891_tbl, alterpublication_12891_member_tbl CASCADE;
