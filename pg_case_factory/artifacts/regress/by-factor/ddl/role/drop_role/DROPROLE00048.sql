-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP ROLE role_name_shape=non_existing_name
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPROLE00048
-- source_md: skills/pg-sql-generation/references/statements/ddl/role/drop_role.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/role/drop_role.yaml
-- primary_obligation_id: DROPROLE-SFV|sfv-8238eaf32606fb10e4395793|drop_role
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS droprole_00048_nonexistent_role;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
SELECT 1 AS target_role_intentionally_absent;
-- 3. 执行唯一获得覆盖信用的 DROP ROLE。
-- primary-target-begin
DROP ROLE droprole_00048_nonexistent_role;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS role_absent FROM pg_catalog.pg_roles WHERE rolname = 'droprole_00048_nonexistent_role' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP ROLE IF EXISTS droprole_00048_nonexistent_role;
