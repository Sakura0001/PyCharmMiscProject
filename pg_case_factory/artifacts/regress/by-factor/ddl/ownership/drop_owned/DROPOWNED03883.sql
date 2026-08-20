-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP OWNED dependent_objects=has_dependent_objects_restrict_fails
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPOWNED03883
-- source_md: skills/pg-sql-generation/references/statements/ddl/ownership/drop_owned.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/ownership/drop_owned.yaml
-- primary_obligation_id: DROPOWNED-EXT|03883|drop_owned|pg_roles_catalog_query|drop_role_cascade
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropowned_03883_t CASCADE;
DROP VIEW IF EXISTS dropowned_03883_v;
DROP OWNED BY dropowned_03883_actor;
DROP ROLE IF EXISTS dropowned_03883_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE dropowned_03883_actor LOGIN;
CREATE TABLE dropowned_03883_t (c integer);
ALTER TABLE dropowned_03883_t OWNER TO dropowned_03883_actor;
CREATE VIEW dropowned_03883_v AS SELECT * FROM dropowned_03883_t;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP OWNED。
-- primary-target-begin
DROP OWNED BY dropowned_03883_actor RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS role_present FROM pg_catalog.pg_roles WHERE rolname = 'dropowned_03883_actor' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP VIEW IF EXISTS dropowned_03883_v;
DROP OWNED BY dropowned_03883_actor;
DROP ROLE IF EXISTS dropowned_03883_actor;
DROP TABLE IF EXISTS dropowned_03883_t CASCADE;
