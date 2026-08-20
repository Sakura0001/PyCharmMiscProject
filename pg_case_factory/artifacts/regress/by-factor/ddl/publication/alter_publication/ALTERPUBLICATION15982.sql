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
-- case_id: ALTERPUBLICATION15982
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/alter_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/alter_publication.yaml
-- primary_obligation_id: ALTPUB-EXT|15982|set_object|pg_publication_catalog|drop_publication
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterpublication_15982_member_tbl CASCADE;
DROP PUBLICATION IF EXISTS alterpublication_15982_pub CASCADE;
DROP SCHEMA IF EXISTS alterpublication_15982_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS alterpublication_15982_sch;
CREATE PUBLICATION alterpublication_15982_pub;
CREATE TABLE alterpublication_15982_member_tbl (id integer, data text);
ALTER PUBLICATION alterpublication_15982_pub ADD TABLE alterpublication_15982_member_tbl;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER PUBLICATION。
-- primary-target-begin
ALTER PUBLICATION alterpublication_15982_pub SET TABLE alterpublication_15982_sch.alterpublication_15982_tbl WHERE (id > 0);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P01' AS target_sqlstate_matches_expected;
SELECT pub.pubname FROM pg_catalog.pg_publication AS pub WHERE pub.pubname = 'alterpublication_15982_pub' ORDER BY pub.pubname;
-- 5. 清理全部本编号对象。
DROP PUBLICATION IF EXISTS alterpublication_15982_pub CASCADE;
DROP SCHEMA IF EXISTS alterpublication_15982_sch CASCADE;
DROP TABLE IF EXISTS alterpublication_15982_member_tbl CASCADE;
