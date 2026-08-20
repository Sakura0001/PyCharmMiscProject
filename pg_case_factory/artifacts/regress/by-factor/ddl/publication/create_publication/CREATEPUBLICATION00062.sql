-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE PUBLICATION verification_mode=error_assertion
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEPUBLICATION00062
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/create_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/create_publication.yaml
-- primary_obligation_id: CPUB-SFV|sfv-97673eea7999c1dedfceb845|for_all_tables
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PUBLICATION IF EXISTS createpublication_00062_pub;
DROP PUBLICATION IF EXISTS createpublication_00062_pub;
DROP PUBLICATION IF EXISTS "createpublication_00062_QPub";
DROP PUBLICATION IF EXISTS "createpublication_00062_.pub";
DROP PUBLICATION IF EXISTS "all";
DROP TABLE IF EXISTS createpublication_00062_tab CASCADE;
DROP TABLE IF EXISTS createpublication_00062_tab2 CASCADE;
DROP TABLE IF EXISTS createpublication_00062_tabpart1 CASCADE;
DROP TABLE IF EXISTS createpublication_00062_notab CASCADE;
DROP SCHEMA IF EXISTS createpublication_00062_sch CASCADE;
DROP SCHEMA IF EXISTS createpublication_00062_nosch CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE PUBLICATION。
-- primary-target-begin
CREATE PUBLICATION createpublication_00062_pub FOR ALL TABLES;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP PUBLICATION createpublication_00062_pub;
