-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER PUBLICATION publication_name_shape=non_existent_name
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPUBLICATION03124
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/alter_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/alter_publication.yaml
-- primary_obligation_id: ALTPUB-EXT|03124|add_object|pg_publication_catalog|drop_publication
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterpublication_03124_sch.alterpublication_03124_tbl CASCADE;
DROP SCHEMA IF EXISTS alterpublication_03124_sch CASCADE;
DROP ROLE IF EXISTS alterpublication_03124_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS alterpublication_03124_sch;
CREATE ROLE alterpublication_03124_owner LOGIN;
GRANT USAGE ON SCHEMA public TO alterpublication_03124_owner;
GRANT USAGE ON SCHEMA alterpublication_03124_sch TO alterpublication_03124_owner;
CREATE TABLE alterpublication_03124_sch.alterpublication_03124_tbl (id integer, data text);
ALTER TABLE alterpublication_03124_sch.alterpublication_03124_tbl OWNER TO alterpublication_03124_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER PUBLICATION。
-- primary-target-begin
ALTER PUBLICATION alterpublication_03124_no_such_pub ADD TABLE alterpublication_03124_sch.alterpublication_03124_tbl WHERE (id > 0);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT pub.pubname FROM pg_catalog.pg_publication AS pub WHERE pub.pubname = 'alterpublication_03124_no_such_pub' ORDER BY pub.pubname;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS alterpublication_03124_sch CASCADE;
DROP OWNED BY alterpublication_03124_owner;
DROP ROLE IF EXISTS alterpublication_03124_owner;
DROP TABLE IF EXISTS alterpublication_03124_sch.alterpublication_03124_tbl CASCADE;
