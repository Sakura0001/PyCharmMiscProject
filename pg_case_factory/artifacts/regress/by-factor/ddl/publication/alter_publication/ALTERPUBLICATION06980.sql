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
-- case_id: ALTERPUBLICATION06980
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/alter_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/alter_publication.yaml
-- primary_obligation_id: ALTPUB-EXT|06980|add_object|pg_publication_tables_catalog|drop_publication
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterpublication_06980_tbl CASCADE;
DROP PUBLICATION IF EXISTS "alterpublication_06980_Mixed Pub" CASCADE;
DROP ROLE IF EXISTS alterpublication_06980_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
CREATE ROLE alterpublication_06980_owner LOGIN;
GRANT USAGE ON SCHEMA public TO alterpublication_06980_owner;
CREATE PUBLICATION "alterpublication_06980_Mixed Pub";
CREATE TABLE alterpublication_06980_tbl (id integer, data text);
ALTER TABLE alterpublication_06980_tbl OWNER TO alterpublication_06980_owner;
ALTER PUBLICATION "alterpublication_06980_Mixed Pub" OWNER TO alterpublication_06980_owner;
SET ROLE alterpublication_06980_owner;
-- 3. 执行唯一获得覆盖信用的 ALTER PUBLICATION。
-- primary-target-begin
ALTER PUBLICATION "alterpublication_06980_Mixed Pub" ADD TABLE alterpublication_06980_tbl (id);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT pt.pubname, pt.tablename FROM pg_catalog.pg_publication_tables AS pt WHERE pt.pubname = 'alterpublication_06980_Mixed Pub' ORDER BY pt.tablename;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PUBLICATION IF EXISTS "alterpublication_06980_Mixed Pub" CASCADE;
DROP OWNED BY alterpublication_06980_owner;
DROP ROLE IF EXISTS alterpublication_06980_owner;
DROP TABLE IF EXISTS alterpublication_06980_tbl CASCADE;
