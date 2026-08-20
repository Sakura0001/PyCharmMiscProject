-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE PUBLICATION target_form=for_table
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEPUBLICATION00954
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/create_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/create_publication.yaml
-- primary_obligation_id: CPUB-EXT|00954|error_assertion|DROP_PUBLICATION_IF_EXISTS
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createpublication_00954_tab, createpublication_00954_tabpart1 CASCADE;
DROP PUBLICATION IF EXISTS createpublication_00954_pub;
DROP PUBLICATION IF EXISTS createpublication_00954_pub;
DROP PUBLICATION IF EXISTS "createpublication_00954_QPub";
DROP PUBLICATION IF EXISTS "createpublication_00954_.pub";
DROP PUBLICATION IF EXISTS "all";
DROP TABLE IF EXISTS createpublication_00954_tab CASCADE;
DROP TABLE IF EXISTS createpublication_00954_tab2 CASCADE;
DROP TABLE IF EXISTS createpublication_00954_tabpart1 CASCADE;
DROP TABLE IF EXISTS createpublication_00954_notab CASCADE;
DROP SCHEMA IF EXISTS createpublication_00954_sch CASCADE;
DROP SCHEMA IF EXISTS createpublication_00954_nosch CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createpublication_00954_tab (id integer, data text) PARTITION BY RANGE (id);
CREATE TABLE createpublication_00954_tabpart1 PARTITION OF createpublication_00954_tab FOR VALUES FROM (0) TO (100);
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE PUBLICATION。
-- primary-target-begin
CREATE PUBLICATION createpublication_00954_pub FOR TABLE ONLY createpublication_00954_tab(id, data) WITH (publish = 'insert');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP PUBLICATION IF EXISTS createpublication_00954_pub;
DROP TABLE IF EXISTS createpublication_00954_tabpart1, createpublication_00954_tab CASCADE;
