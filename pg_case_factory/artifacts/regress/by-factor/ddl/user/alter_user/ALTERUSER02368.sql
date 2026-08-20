-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER USER privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERUSER02368
-- source_md: skills/pg-sql-generation/references/statements/ddl/user/alter_user.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user/alter_user.yaml
-- primary_obligation_id: AUSR-EXT|02368|catalog_query_pg_roles|revert_option
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS alteruser_02368_role;
DROP OWNED BY alteruser_02368_actor CASCADE;
DROP ROLE IF EXISTS alteruser_02368_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alteruser_02368_actor LOGIN NOSUPERUSER;
CREATE ROLE alteruser_02368_role LOGIN;
SET ROLE alteruser_02368_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER USER。
-- primary-target-begin
ALTER USER alteruser_02368_role RESET work_mem;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS role_state FROM pg_catalog.pg_roles WHERE rolname = 'alteruser_02368_role' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS alteruser_02368_role;
DROP OWNED BY alteruser_02368_actor CASCADE;
DROP ROLE IF EXISTS alteruser_02368_actor;
