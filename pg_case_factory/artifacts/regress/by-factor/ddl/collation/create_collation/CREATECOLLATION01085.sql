-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE COLLATION object_state=already_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATECOLLATION01085
-- source_md: skills/pg-sql-generation/references/statements/ddl/collation/create_collation.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/collation/create_collation.yaml
-- primary_obligation_id: CCOL-EXT|01085|actual_collation_usage|DROP_COLLATION
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP COLLATION IF EXISTS "createcollation_01085_QCol" CASCADE;
DROP COLLATION IF EXISTS createcollation_01085_src CASCADE;
DROP COLLATION IF EXISTS createcollation_01085_nosuch CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE COLLATION "createcollation_01085_QCol" FROM "C";
CREATE COLLATION createcollation_01085_src FROM "C";
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE COLLATION。
-- primary-target-begin
CREATE COLLATION "createcollation_01085_QCol" FROM createcollation_01085_src;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT 'a' COLLATE "createcollation_01085_QCol" AS usage_check;
-- 5. 清理全部本编号对象。
DROP COLLATION "createcollation_01085_QCol";
DROP COLLATION createcollation_01085_src;
