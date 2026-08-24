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
-- case_id: ALTERPUBLICATION02281
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/alter_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/alter_publication.yaml
-- primary_obligation_id: ALTPUB-EXT|02281|add_object|pg_publication_catalog|drop_publication
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterpublication_02281_sch.alterpublication_02281_tbl CASCADE;
DROP PUBLICATION IF EXISTS "alterpublication_02281_Mixed Pub" CASCADE;
DROP SCHEMA IF EXISTS alterpublication_02281_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS alterpublication_02281_sch;
CREATE PUBLICATION "alterpublication_02281_Mixed Pub";
CREATE TABLE alterpublication_02281_sch.alterpublication_02281_tbl (id integer, data text);
-- 3. 执行唯一获得覆盖信用的 ALTER PUBLICATION。
-- primary-target-begin
ALTER PUBLICATION "alterpublication_02281_Mixed Pub" ADD TABLE alterpublication_02281_sch.alterpublication_02281_tbl (id, data) WHERE (id > 0);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT pub.pubname FROM pg_catalog.pg_publication AS pub WHERE pub.pubname = 'alterpublication_02281_Mixed Pub' ORDER BY pub.pubname;
-- 5. 清理全部本编号对象。
DROP PUBLICATION IF EXISTS "alterpublication_02281_Mixed Pub" CASCADE;
DROP SCHEMA IF EXISTS alterpublication_02281_sch CASCADE;
DROP TABLE IF EXISTS alterpublication_02281_sch.alterpublication_02281_tbl CASCADE;
