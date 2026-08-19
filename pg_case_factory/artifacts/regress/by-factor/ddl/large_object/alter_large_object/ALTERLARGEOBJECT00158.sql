-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER LARGE OBJECT oid_shape=nonexistent_oid
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERLARGEOBJECT00158
-- source_md: skills/pg-sql-generation/references/statements/ddl/large_object/alter_large_object.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/large_object/alter_large_object.yaml
-- primary_obligation_id: ALO-EXT|00158|owner_change|catalog_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT lo_unlink(oid) FROM pg_catalog.pg_largeobject_metadata WHERE oid = 2000158 ORDER BY oid;
\set ON_ERROR_STOP on
-- 2. 创建完整本地大对象和因子专用夹具。
SELECT lo_create(2000158);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER LARGE OBJECT。
-- primary-target-begin
ALTER LARGE OBJECT 4000158 OWNER TO SESSION_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS large_object_absent FROM pg_catalog.pg_largeobject_metadata WHERE oid = 4000158 ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
SELECT lo_unlink(oid) FROM pg_catalog.pg_largeobject_metadata WHERE oid = 2000158 ORDER BY oid;
