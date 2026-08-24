-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP OWNED owned_objects_state=owns_tables
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPOWNED00138
-- source_md: skills/pg-sql-generation/references/statements/ddl/ownership/drop_owned.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/ownership/drop_owned.yaml
-- primary_obligation_id: DROPOWNED-EXT|00138|drop_owned|pg_roles_catalog_query|drop_owned_cascade
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropowned_00138_t CASCADE;
DROP VIEW IF EXISTS dropowned_00138_v;
DROP OWNED BY dropowned_00138_actor;
DROP ROLE IF EXISTS dropowned_00138_actor;
DROP OWNED BY dropowned_00138_actor2;
DROP ROLE IF EXISTS dropowned_00138_actor2;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE dropowned_00138_actor LOGIN;
CREATE ROLE dropowned_00138_actor2 LOGIN;
CREATE TABLE dropowned_00138_t (c integer);
ALTER TABLE dropowned_00138_t OWNER TO dropowned_00138_actor;
CREATE VIEW dropowned_00138_v AS SELECT * FROM dropowned_00138_t;
-- 3. 执行唯一获得覆盖信用的 DROP OWNED。
-- primary-target-begin
DROP OWNED BY dropowned_00138_actor, dropowned_00138_actor2 CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS role_present FROM pg_catalog.pg_roles WHERE rolname = 'dropowned_00138_actor' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP VIEW IF EXISTS dropowned_00138_v;
DROP OWNED BY dropowned_00138_actor;
DROP ROLE IF EXISTS dropowned_00138_actor;
DROP OWNED BY dropowned_00138_actor2;
DROP ROLE IF EXISTS dropowned_00138_actor2;
DROP TABLE IF EXISTS dropowned_00138_t CASCADE;
