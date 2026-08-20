-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TYPE privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTYPE01455
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/drop_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/drop_type.yaml
-- primary_obligation_id: DROPTYPE-EXT|01455|drop_type|information_schema_user_defined_types|manual_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droptype_01455_dtbl CASCADE;
DROP TYPE IF EXISTS droptype_01455_type CASCADE;
DROP OWNED BY droptype_01455_actor;
DROP ROLE IF EXISTS droptype_01455_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地类型和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE ROLE droptype_01455_actor LOGIN NOSUPERUSER;
CREATE TYPE droptype_01455_type AS (c integer);
CREATE TABLE droptype_01455_dtbl OF droptype_01455_type;
SET ROLE droptype_01455_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP TYPE。
-- primary-target-begin
DROP TYPE droptype_01455_type CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS type_present FROM pg_catalog.pg_type WHERE typname = 'droptype_01455_type' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TYPE IF EXISTS droptype_01455_type CASCADE;
DROP OWNED BY droptype_01455_actor;
DROP ROLE IF EXISTS droptype_01455_actor;
DROP TABLE IF EXISTS droptype_01455_dtbl CASCADE;
