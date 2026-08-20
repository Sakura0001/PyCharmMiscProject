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
-- case_id: CREATEPUBLICATION00131
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/create_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/create_publication.yaml
-- primary_obligation_id: CPUB-EXT|00131|error_assertion|DROP_PUBLICATION
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PUBLICATION IF EXISTS createpublication_00131_pub;
DROP PUBLICATION IF EXISTS createpublication_00131_pub;
DROP PUBLICATION IF EXISTS "createpublication_00131_QPub";
DROP PUBLICATION IF EXISTS "createpublication_00131_.pub";
DROP PUBLICATION IF EXISTS "all";
DROP TABLE IF EXISTS createpublication_00131_tab CASCADE;
DROP TABLE IF EXISTS createpublication_00131_tab2 CASCADE;
DROP TABLE IF EXISTS createpublication_00131_tabpart1 CASCADE;
DROP TABLE IF EXISTS createpublication_00131_notab CASCADE;
DROP SCHEMA IF EXISTS createpublication_00131_sch CASCADE;
DROP SCHEMA IF EXISTS createpublication_00131_nosch CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createpublication_00131_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createpublication_00131_actor LOGIN NOSUPERUSER;
SET ROLE createpublication_00131_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE PUBLICATION。
-- primary-target-begin
CREATE PUBLICATION createpublication_00131_pub FOR ALL TABLES WITH (publish = 'insert, update', publish_via_partition_root = true);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PUBLICATION createpublication_00131_pub;
DROP OWNED BY createpublication_00131_actor CASCADE;
DROP ROLE IF EXISTS createpublication_00131_actor;
