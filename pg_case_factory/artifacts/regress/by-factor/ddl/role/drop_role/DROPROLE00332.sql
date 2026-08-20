-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP ROLE active_session=has_active_session
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPROLE00332
-- source_md: skills/pg-sql-generation/references/statements/ddl/role/drop_role.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/role/drop_role.yaml
-- primary_obligation_id: DROPROLE-EXT|00332|drop_role|catalog_query_pg_roles|drop_owned_then_drop_role
-- expected_outcome: expected_failure
-- expected_sqlstate: 55006
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS "droprole_00332_QuotedRole";
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
SELECT 1 AS target_role_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP ROLE。
-- primary-target-begin
DROP ROLE IF EXISTS "droprole_00332_QuotedRole";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '55006' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS role_absent FROM pg_catalog.pg_roles WHERE rolname = 'droprole_00332_QuotedRole' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP ROLE IF EXISTS "droprole_00332_QuotedRole";
