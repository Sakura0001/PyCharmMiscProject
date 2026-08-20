-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SCHEMA new_owner_shape=non_existing_role
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSCHEMA02062
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/alter_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/alter_schema.yaml
-- primary_obligation_id: AS-EXT|02062|current_schema_query|DROP_SCHEMA
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterschema_02062_tab CASCADE;
DROP SCHEMA IF EXISTS "alterschema_02062_dotted.sch" CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA "alterschema_02062_dotted.sch";
SET search_path TO "alterschema_02062_dotted.sch";
CREATE TABLE alterschema_02062_tab (alterschema_02062_col integer);
RESET search_path;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SCHEMA。
-- primary-target-begin
ALTER SCHEMA "alterschema_02062_dotted.sch" OWNER TO alterschema_02062_no_such_role;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SET search_path TO "alterschema_02062_dotted.sch"; SELECT current_schema() = 'alterschema_02062_dotted.sch' AS in_target_schema;
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS "alterschema_02062_dotted.sch" CASCADE;
DROP TABLE IF EXISTS alterschema_02062_tab CASCADE;
