-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TYPE object_state=exists_composite
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTYPE01012
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/drop_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/drop_type.yaml
-- primary_obligation_id: DROPTYPE-EXT|01012|drop_type|information_schema_user_defined_types|rollback
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR IF EXISTS #(droptype_01012_type, droptype_01012_type);
DROP FUNCTION IF EXISTS droptype_01012_opfn CASCADE;
DROP TYPE IF EXISTS droptype_01012_type CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地类型和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE TYPE droptype_01012_type;
CREATE FUNCTION droptype_01012_opfn(droptype_01012_type, droptype_01012_type) RETURNS boolean LANGUAGE sql AS $$ SELECT $1 IS NOT NULL; $$;
CREATE OPERATOR # (PROCEDURE = droptype_01012_opfn, LEFTARG = droptype_01012_type, RIGHTARG = droptype_01012_type);
-- 3. 执行唯一获得覆盖信用的 DROP TYPE。
-- primary-target-begin
DROP TYPE droptype_01012_type CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS type_absent FROM pg_catalog.pg_type WHERE typname = 'droptype_01012_type' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP OPERATOR IF EXISTS #(droptype_01012_type, droptype_01012_type);
DROP FUNCTION IF EXISTS droptype_01012_opfn CASCADE;
DROP TYPE IF EXISTS droptype_01012_type CASCADE;
