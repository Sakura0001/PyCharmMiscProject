-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE COLLATION target_form=from_existing
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATECOLLATION01022
-- source_md: skills/pg-sql-generation/references/statements/ddl/collation/create_collation.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/collation/create_collation.yaml
-- primary_obligation_id: CCOL-EXT|01022|pg_collation_catalog_query|DROP_COLLATION
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP COLLATION IF EXISTS "createcollation_01022_QCol" CASCADE;
DROP COLLATION IF EXISTS createcollation_01022_src CASCADE;
DROP COLLATION IF EXISTS createcollation_01022_nosuch CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE COLLATION createcollation_01022_src FROM "C";
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE COLLATION。
-- primary-target-begin
CREATE COLLATION IF NOT EXISTS "createcollation_01022_QCol" FROM createcollation_01022_src;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS collation_state FROM pg_catalog.pg_collation WHERE collname = 'createcollation_01022_QCol' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP COLLATION "createcollation_01022_QCol";
DROP COLLATION createcollation_01022_src;
