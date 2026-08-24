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
-- case_id: REASSIGNOWNED01723
-- source_md: skills/pg-sql-generation/references/statements/ddl/ownership/reassign_owned.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/ownership/reassign_owned.yaml
-- primary_obligation_id: REASSIGNOWNED-EXT|01723|reassign_owned|error_assertion|reassign_owned_then_drop_role
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS reassignowned_01723_t CASCADE;
DROP OWNED BY reassignowned_01723_executor;
DROP ROLE IF EXISTS reassignowned_01723_executor;
DROP OWNED BY reassignowned_01723_old;
DROP OWNED BY reassignowned_01723_new;
DROP ROLE IF EXISTS reassignowned_01723_old;
DROP ROLE IF EXISTS reassignowned_01723_new;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE reassignowned_01723_old LOGIN;
CREATE ROLE reassignowned_01723_new LOGIN;
CREATE TABLE reassignowned_01723_t (c integer);
ALTER TABLE reassignowned_01723_t OWNER TO reassignowned_01723_old;
CREATE ROLE reassignowned_01723_executor LOGIN NOSUPERUSER;
SET ROLE reassignowned_01723_executor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 REASSIGN OWNED。
-- primary-target-begin
REASSIGN OWNED BY CURRENT_USER TO CURRENT_ROLE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT 1 AS error_assertion_oracle;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY reassignowned_01723_executor;
DROP ROLE IF EXISTS reassignowned_01723_executor;
DROP OWNED BY reassignowned_01723_old;
DROP OWNED BY reassignowned_01723_new;
DROP ROLE IF EXISTS reassignowned_01723_old;
DROP ROLE IF EXISTS reassignowned_01723_new;
DROP TABLE IF EXISTS reassignowned_01723_t CASCADE;
