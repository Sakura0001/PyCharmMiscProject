-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER PUBLICATION executor_privilege=non_owner_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPUBLICATION10493
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/alter_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/alter_publication.yaml
-- primary_obligation_id: ALTPUB-EXT|10493|drop_object|pg_publication_tables_catalog|drop_publication
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PUBLICATION IF EXISTS "alterpublication_10493_Mixed Pub" CASCADE;
DROP SCHEMA IF EXISTS "alterpublication_10493_Mixed Sch" CASCADE;
DROP ROLE IF EXISTS alterpublication_10493_owner;
DROP ROLE IF EXISTS alterpublication_10493_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS "alterpublication_10493_Mixed Sch";
CREATE ROLE alterpublication_10493_owner LOGIN;
CREATE ROLE alterpublication_10493_actor LOGIN;
GRANT USAGE ON SCHEMA public TO alterpublication_10493_owner;
GRANT USAGE ON SCHEMA public TO alterpublication_10493_actor;
GRANT USAGE ON SCHEMA "alterpublication_10493_Mixed Sch" TO alterpublication_10493_owner;
CREATE PUBLICATION "alterpublication_10493_Mixed Pub";
ALTER PUBLICATION "alterpublication_10493_Mixed Pub" ADD TABLES IN SCHEMA "alterpublication_10493_Mixed Sch";
ALTER PUBLICATION "alterpublication_10493_Mixed Pub" OWNER TO alterpublication_10493_owner;
SET ROLE alterpublication_10493_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER PUBLICATION。
-- primary-target-begin
ALTER PUBLICATION "alterpublication_10493_Mixed Pub" DROP TABLES IN SCHEMA "alterpublication_10493_Mixed Sch";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT pt.pubname, pt.tablename FROM pg_catalog.pg_publication_tables AS pt WHERE pt.pubname = 'alterpublication_10493_Mixed Pub' ORDER BY pt.tablename;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PUBLICATION IF EXISTS "alterpublication_10493_Mixed Pub" CASCADE;
DROP SCHEMA IF EXISTS "alterpublication_10493_Mixed Sch" CASCADE;
DROP OWNED BY alterpublication_10493_owner;
DROP ROLE IF EXISTS alterpublication_10493_owner;
DROP OWNED BY alterpublication_10493_actor;
DROP ROLE IF EXISTS alterpublication_10493_actor;
