-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER LARGE OBJECT new_owner_shape=plain_role
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERLARGEOBJECT00203
-- source_md: skills/pg-sql-generation/references/statements/ddl/large_object/alter_large_object.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/large_object/alter_large_object.yaml
-- primary_obligation_id: ALO-EXT|00203|owner_change|effect_query|reset_state
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT lo_unlink(oid) FROM pg_catalog.pg_largeobject_metadata WHERE oid = 2000203 ORDER BY oid;
DROP ROLE IF EXISTS alterlargeobject_00203_new_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地大对象和因子专用夹具。
CREATE ROLE alterlargeobject_00203_new_owner LOGIN;
SELECT lo_create(2000203);
-- 3. 执行唯一获得覆盖信用的 ALTER LARGE OBJECT。
-- primary-target-begin
ALTER LARGE OBJECT 2000203 OWNER TO alterlargeobject_00203_new_owner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS owner_is_target FROM pg_catalog.pg_largeobject_metadata AS m JOIN pg_catalog.pg_roles AS r ON m.lomowner = r.oid WHERE m.oid = 2000203 AND r.rolname = 'alterlargeobject_00203_new_owner' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
SELECT lo_unlink(oid) FROM pg_catalog.pg_largeobject_metadata WHERE oid = 2000203 ORDER BY oid;
DROP OWNED BY alterlargeobject_00203_new_owner;
DROP ROLE IF EXISTS alterlargeobject_00203_new_owner;
