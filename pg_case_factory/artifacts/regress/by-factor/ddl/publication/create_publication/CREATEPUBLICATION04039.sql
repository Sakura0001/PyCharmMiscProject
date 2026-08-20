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
-- case_id: CREATEPUBLICATION04039
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/create_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/create_publication.yaml
-- primary_obligation_id: CPUB-EXT|04039|pg_publication_catalog|DROP_PUBLICATION
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PUBLICATION IF EXISTS createpublication_04039_pub;
DROP PUBLICATION IF EXISTS createpublication_04039_pub;
DROP PUBLICATION IF EXISTS "createpublication_04039_QPub";
DROP PUBLICATION IF EXISTS "createpublication_04039_.pub";
DROP PUBLICATION IF EXISTS "all";
DROP TABLE IF EXISTS createpublication_04039_tab CASCADE;
DROP TABLE IF EXISTS createpublication_04039_tab2 CASCADE;
DROP TABLE IF EXISTS createpublication_04039_tabpart1 CASCADE;
DROP TABLE IF EXISTS createpublication_04039_notab CASCADE;
DROP SCHEMA IF EXISTS createpublication_04039_sch CASCADE;
DROP SCHEMA IF EXISTS createpublication_04039_nosch CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createpublication_04039_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createpublication_04039_actor LOGIN NOSUPERUSER;
CREATE SCHEMA "createpublication_04039_QSch";
SET ROLE createpublication_04039_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE PUBLICATION。
-- primary-target-begin
CREATE PUBLICATION createpublication_04039_pub FOR TABLES IN SCHEMA "createpublication_04039_QSch" WITH (publish = 'insert, update, delete, truncate');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS pub_state FROM pg_catalog.pg_publication WHERE pubname = 'createpublication_04039_pub' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PUBLICATION createpublication_04039_pub;
DROP SCHEMA IF EXISTS "createpublication_04039_QSch" CASCADE;
DROP OWNED BY createpublication_04039_actor CASCADE;
DROP ROLE IF EXISTS createpublication_04039_actor;
