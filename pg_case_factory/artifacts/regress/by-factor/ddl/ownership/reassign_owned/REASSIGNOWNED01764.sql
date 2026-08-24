-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : REASSIGN OWNED executor_privilege=normal_user_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: REASSIGNOWNED01764
-- source_md: skills/pg-sql-generation/references/statements/ddl/ownership/reassign_owned.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/ownership/reassign_owned.yaml
-- primary_obligation_id: REASSIGNOWNED-EXT|01764|reassign_owned|pg_roles_catalog_query|drop_role_cascade
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS reassignowned_01764_t CASCADE;
DROP OWNED BY reassignowned_01764_executor;
DROP ROLE IF EXISTS reassignowned_01764_executor;
DROP OWNED BY reassignowned_01764_old;
DROP OWNED BY reassignowned_01764_new;
DROP ROLE IF EXISTS reassignowned_01764_old;
DROP ROLE IF EXISTS reassignowned_01764_new;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE reassignowned_01764_old LOGIN;
CREATE ROLE reassignowned_01764_new LOGIN;
CREATE TABLE reassignowned_01764_t (c integer);
ALTER TABLE reassignowned_01764_t OWNER TO reassignowned_01764_old;
CREATE ROLE reassignowned_01764_executor LOGIN NOSUPERUSER;
SET ROLE reassignowned_01764_executor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 REASSIGN OWNED。
-- primary-target-begin
REASSIGN OWNED BY reassignowned_01764_old TO CURRENT_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS role_present FROM pg_catalog.pg_roles WHERE rolname = 'reassignowned_01764_old' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY reassignowned_01764_executor;
DROP ROLE IF EXISTS reassignowned_01764_executor;
DROP OWNED BY reassignowned_01764_old;
DROP OWNED BY reassignowned_01764_new;
DROP ROLE IF EXISTS reassignowned_01764_old;
DROP ROLE IF EXISTS reassignowned_01764_new;
DROP TABLE IF EXISTS reassignowned_01764_t CASCADE;
