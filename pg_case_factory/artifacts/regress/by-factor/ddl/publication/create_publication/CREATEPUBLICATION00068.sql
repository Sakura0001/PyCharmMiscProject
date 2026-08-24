-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE PUBLICATION with_parameter_clause=multiple_parameters
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEPUBLICATION00068
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/create_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/create_publication.yaml
-- primary_obligation_id: CPUB-SFV|sfv-f539f1358fccd5db818a436e|for_all_tables
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PUBLICATION IF EXISTS createpublication_00068_pub;
DROP PUBLICATION IF EXISTS createpublication_00068_pub;
DROP PUBLICATION IF EXISTS "createpublication_00068_QPub";
DROP PUBLICATION IF EXISTS "createpublication_00068_.pub";
DROP PUBLICATION IF EXISTS "all";
DROP TABLE IF EXISTS createpublication_00068_tab CASCADE;
DROP TABLE IF EXISTS createpublication_00068_tab2 CASCADE;
DROP TABLE IF EXISTS createpublication_00068_tabpart1 CASCADE;
DROP TABLE IF EXISTS createpublication_00068_notab CASCADE;
DROP SCHEMA IF EXISTS createpublication_00068_sch CASCADE;
DROP SCHEMA IF EXISTS createpublication_00068_nosch CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE PUBLICATION。
-- primary-target-begin
CREATE PUBLICATION createpublication_00068_pub FOR ALL TABLES WITH (publish = 'insert, update', publish_via_partition_root = true);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS pub_state FROM pg_catalog.pg_publication WHERE pubname = 'createpublication_00068_pub' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP PUBLICATION createpublication_00068_pub;
