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
-- case_id: DROPOWNED02768
-- source_md: skills/pg-sql-generation/references/statements/ddl/ownership/drop_owned.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/ownership/drop_owned.yaml
-- primary_obligation_id: DROPOWNED-EXT|02768|drop_owned|pg_roles_catalog_query|reassign_owned_then_drop_role
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropowned_02768_t CASCADE;
DROP OWNED BY dropowned_02768_actor;
DROP ROLE IF EXISTS dropowned_02768_actor;
DROP OWNED BY dropowned_02768_actor2;
DROP ROLE IF EXISTS dropowned_02768_actor2;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE dropowned_02768_actor LOGIN;
CREATE ROLE dropowned_02768_actor2 LOGIN;
CREATE TABLE dropowned_02768_t (c integer);
ALTER TABLE dropowned_02768_t OWNER TO dropowned_02768_actor;
-- 3. 执行唯一获得覆盖信用的 DROP OWNED。
-- primary-target-begin
DROP OWNED BY dropowned_02768_actor, dropowned_02768_actor2;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS role_present FROM pg_catalog.pg_roles WHERE rolname = 'dropowned_02768_actor' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP OWNED BY dropowned_02768_actor;
DROP ROLE IF EXISTS dropowned_02768_actor;
DROP OWNED BY dropowned_02768_actor2;
DROP ROLE IF EXISTS dropowned_02768_actor2;
DROP TABLE IF EXISTS dropowned_02768_t CASCADE;
