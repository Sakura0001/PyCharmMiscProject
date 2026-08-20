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
-- case_id: DROPOWNED01435
-- source_md: skills/pg-sql-generation/references/statements/ddl/ownership/drop_owned.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/ownership/drop_owned.yaml
-- primary_obligation_id: DROPOWNED-EXT|01435|drop_owned|pg_roles_catalog_query|drop_role_cascade
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropowned_01435_t CASCADE;
DROP OWNED BY dropowned_01435_executor;
DROP ROLE IF EXISTS dropowned_01435_executor;
DROP OWNED BY dropowned_01435_actor;
DROP ROLE IF EXISTS dropowned_01435_actor;
DROP OWNED BY dropowned_01435_actor2;
DROP ROLE IF EXISTS dropowned_01435_actor2;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE dropowned_01435_actor LOGIN;
CREATE ROLE dropowned_01435_actor2 LOGIN;
CREATE TABLE dropowned_01435_t (c integer);
ALTER TABLE dropowned_01435_t OWNER TO dropowned_01435_actor;
CREATE ROLE dropowned_01435_executor LOGIN NOSUPERUSER;
SET ROLE dropowned_01435_executor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP OWNED。
-- primary-target-begin
DROP OWNED BY dropowned_01435_actor, dropowned_01435_actor2 CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS role_present FROM pg_catalog.pg_roles WHERE rolname = 'dropowned_01435_actor' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY dropowned_01435_executor;
DROP ROLE IF EXISTS dropowned_01435_executor;
DROP OWNED BY dropowned_01435_actor;
DROP ROLE IF EXISTS dropowned_01435_actor;
DROP OWNED BY dropowned_01435_actor2;
DROP ROLE IF EXISTS dropowned_01435_actor2;
DROP TABLE IF EXISTS dropowned_01435_t CASCADE;
