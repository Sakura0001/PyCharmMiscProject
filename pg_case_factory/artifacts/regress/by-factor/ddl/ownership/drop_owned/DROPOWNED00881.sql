-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP OWNED executor_privilege=normal_user_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPOWNED00881
-- source_md: skills/pg-sql-generation/references/statements/ddl/ownership/drop_owned.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/ownership/drop_owned.yaml
-- primary_obligation_id: DROPOWNED-EXT|00881|drop_owned|error_assertion|reassign_owned_then_drop_role
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropowned_00881_t CASCADE;
DROP VIEW IF EXISTS dropowned_00881_v;
DROP OWNED BY dropowned_00881_executor;
DROP ROLE IF EXISTS dropowned_00881_executor;
DROP OWNED BY dropowned_00881_actor;
DROP ROLE IF EXISTS dropowned_00881_actor;
DROP OWNED BY dropowned_00881_actor2;
DROP ROLE IF EXISTS dropowned_00881_actor2;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE dropowned_00881_actor LOGIN;
CREATE ROLE dropowned_00881_actor2 LOGIN;
CREATE TABLE dropowned_00881_t (c integer);
ALTER TABLE dropowned_00881_t OWNER TO dropowned_00881_actor;
CREATE VIEW dropowned_00881_v AS SELECT * FROM dropowned_00881_t;
CREATE ROLE dropowned_00881_executor LOGIN NOSUPERUSER;
SET ROLE dropowned_00881_executor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP OWNED。
-- primary-target-begin
DROP OWNED BY CURRENT_ROLE, dropowned_00881_actor2 CASCADE;
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
DROP VIEW IF EXISTS dropowned_00881_v;
DROP OWNED BY dropowned_00881_executor;
DROP ROLE IF EXISTS dropowned_00881_executor;
DROP OWNED BY dropowned_00881_actor;
DROP ROLE IF EXISTS dropowned_00881_actor;
DROP OWNED BY dropowned_00881_actor2;
DROP ROLE IF EXISTS dropowned_00881_actor2;
DROP TABLE IF EXISTS dropowned_00881_t CASCADE;
