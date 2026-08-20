-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE PUBLICATION executor_privilege=non_superuser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEPUBLICATION01706
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/create_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/create_publication.yaml
-- primary_obligation_id: CPUB-EXT|01706|pg_publication_catalog|DROP_PUBLICATION_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createpublication_01706_tab, createpublication_01706_tabpart1 CASCADE;
DROP PUBLICATION IF EXISTS createpublication_01706_pub;
DROP PUBLICATION IF EXISTS createpublication_01706_pub;
DROP PUBLICATION IF EXISTS "createpublication_01706_QPub";
DROP PUBLICATION IF EXISTS "createpublication_01706_.pub";
DROP PUBLICATION IF EXISTS "all";
DROP TABLE IF EXISTS createpublication_01706_tab CASCADE;
DROP TABLE IF EXISTS createpublication_01706_tab2 CASCADE;
DROP TABLE IF EXISTS createpublication_01706_tabpart1 CASCADE;
DROP TABLE IF EXISTS createpublication_01706_notab CASCADE;
DROP SCHEMA IF EXISTS createpublication_01706_sch CASCADE;
DROP SCHEMA IF EXISTS createpublication_01706_nosch CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createpublication_01706_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createpublication_01706_actor LOGIN NOSUPERUSER;
CREATE TABLE createpublication_01706_tab (id integer, data text) PARTITION BY RANGE (id);
CREATE TABLE createpublication_01706_tabpart1 PARTITION OF createpublication_01706_tab FOR VALUES FROM (0) TO (100);
SET ROLE createpublication_01706_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE PUBLICATION。
-- primary-target-begin
CREATE PUBLICATION createpublication_01706_pub FOR TABLE ONLY createpublication_01706_tab(id) WHERE (id > 0 AND id < 100) WITH (publish = 'insert, update, delete, truncate');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS pub_state FROM pg_catalog.pg_publication WHERE pubname = 'createpublication_01706_pub' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PUBLICATION IF EXISTS createpublication_01706_pub;
DROP OWNED BY createpublication_01706_actor CASCADE;
DROP ROLE IF EXISTS createpublication_01706_actor;
DROP TABLE IF EXISTS createpublication_01706_tabpart1, createpublication_01706_tab CASCADE;
