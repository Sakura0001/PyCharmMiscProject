-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER LARGE OBJECT privilege_context=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERLARGEOBJECT00054
-- source_md: skills/pg-sql-generation/references/statements/ddl/large_object/alter_large_object.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/large_object/alter_large_object.yaml
-- primary_obligation_id: ALO-EXT|00054|owner_change|error_assertion|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT lo_unlink(oid) FROM pg_catalog.pg_largeobject_metadata WHERE oid = 2000054 ORDER BY oid;
DROP ROLE IF EXISTS alterlargeobject_00054_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地大对象和因子专用夹具。
CREATE ROLE alterlargeobject_00054_actor LOGIN;
SELECT lo_create(2000054);
SET ROLE alterlargeobject_00054_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER LARGE OBJECT。
-- primary-target-begin
ALTER LARGE OBJECT 2000054 OWNER TO CURRENT_ROLE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS large_object_present FROM pg_catalog.pg_largeobject_metadata WHERE oid = 2000054 ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
SELECT lo_unlink(oid) FROM pg_catalog.pg_largeobject_metadata WHERE oid = 2000054 ORDER BY oid;
DROP OWNED BY alterlargeobject_00054_actor CASCADE;
DROP ROLE IF EXISTS alterlargeobject_00054_actor;
