-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE PUBLICATION table_dependency=table_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEPUBLICATION01470
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/create_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/create_publication.yaml
-- primary_obligation_id: CPUB-EXT|01470|error_assertion|DROP_PUBLICATION_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PUBLICATION IF EXISTS createpublication_01470_pub;
DROP PUBLICATION IF EXISTS createpublication_01470_pub;
DROP PUBLICATION IF EXISTS "createpublication_01470_QPub";
DROP PUBLICATION IF EXISTS "createpublication_01470_.pub";
DROP PUBLICATION IF EXISTS "all";
DROP TABLE IF EXISTS createpublication_01470_tab CASCADE;
DROP TABLE IF EXISTS createpublication_01470_tab2 CASCADE;
DROP TABLE IF EXISTS createpublication_01470_tabpart1 CASCADE;
DROP TABLE IF EXISTS createpublication_01470_notab CASCADE;
DROP SCHEMA IF EXISTS createpublication_01470_sch CASCADE;
DROP SCHEMA IF EXISTS createpublication_01470_nosch CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE PUBLICATION。
-- primary-target-begin
CREATE PUBLICATION createpublication_01470_pub FOR TABLE createpublication_01470_notab(id, data) WITH (publish = 'insert, update, delete, truncate');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P01' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP PUBLICATION IF EXISTS createpublication_01470_pub;
