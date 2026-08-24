-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER PUBLICATION schema_dependency=schema_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPUBLICATION08939
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/alter_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/alter_publication.yaml
-- primary_obligation_id: ALTPUB-EXT|08939|add_object|pg_publication_tables_catalog|drop_publication
-- expected_outcome: expected_failure
-- expected_sqlstate: 3F000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterpublication_08939_member_tbl CASCADE;
DROP PUBLICATION IF EXISTS alterpublication_08939_pub CASCADE;
DROP ROLE IF EXISTS alterpublication_08939_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
CREATE ROLE alterpublication_08939_owner LOGIN;
GRANT USAGE ON SCHEMA public TO alterpublication_08939_owner;
CREATE PUBLICATION alterpublication_08939_pub;
CREATE TABLE alterpublication_08939_member_tbl (id integer, data text);
ALTER TABLE alterpublication_08939_member_tbl OWNER TO alterpublication_08939_owner;
ALTER PUBLICATION alterpublication_08939_pub ADD TABLE alterpublication_08939_member_tbl;
ALTER PUBLICATION alterpublication_08939_pub OWNER TO alterpublication_08939_owner;
SET ROLE alterpublication_08939_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER PUBLICATION。
-- primary-target-begin
ALTER PUBLICATION alterpublication_08939_pub ADD TABLES IN SCHEMA alterpublication_08939_sch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '3F000' AS target_sqlstate_matches_expected;
SELECT pt.pubname, pt.tablename FROM pg_catalog.pg_publication_tables AS pt WHERE pt.pubname = 'alterpublication_08939_pub' ORDER BY pt.tablename;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PUBLICATION IF EXISTS alterpublication_08939_pub CASCADE;
DROP OWNED BY alterpublication_08939_owner;
DROP ROLE IF EXISTS alterpublication_08939_owner;
DROP TABLE IF EXISTS alterpublication_08939_member_tbl CASCADE;
