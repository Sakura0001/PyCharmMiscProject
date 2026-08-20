-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE PUBLICATION publication_identity=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEPUBLICATION03730
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/create_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/create_publication.yaml
-- primary_obligation_id: CPUB-EXT|03730|pg_publication_tables_catalog|DROP_PUBLICATION_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createpublication_03730_tab CASCADE;
DROP PUBLICATION IF EXISTS createpublication_03730_pub;
DROP PUBLICATION IF EXISTS createpublication_03730_pub;
DROP PUBLICATION IF EXISTS "createpublication_03730_QPub";
DROP PUBLICATION IF EXISTS "createpublication_03730_.pub";
DROP PUBLICATION IF EXISTS "all";
DROP TABLE IF EXISTS createpublication_03730_tab CASCADE;
DROP TABLE IF EXISTS createpublication_03730_tab2 CASCADE;
DROP TABLE IF EXISTS createpublication_03730_tabpart1 CASCADE;
DROP TABLE IF EXISTS createpublication_03730_notab CASCADE;
DROP SCHEMA IF EXISTS createpublication_03730_sch CASCADE;
DROP SCHEMA IF EXISTS createpublication_03730_nosch CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE PUBLICATION createpublication_03730_pub;
CREATE TABLE createpublication_03730_tab (id integer, data text);
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE PUBLICATION。
-- primary-target-begin
CREATE PUBLICATION createpublication_03730_pub FOR TABLE createpublication_03730_tab WITH (publish = 'insert, update', publish_via_partition_root = true);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS pub_tables_state FROM pg_catalog.pg_publication_tables WHERE pubname = 'createpublication_03730_pub' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP PUBLICATION IF EXISTS createpublication_03730_pub;
DROP TABLE IF EXISTS createpublication_03730_tab CASCADE;
