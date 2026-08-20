-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TYPE dependency_state=used_in_operators
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTYPE02611
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/drop_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/drop_type.yaml
-- primary_obligation_id: DROPTYPE-EXT|02611|drop_type|error_assertion|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR IF EXISTS #(droptype_02611_type, droptype_02611_type);
DROP FUNCTION IF EXISTS droptype_02611_opfn CASCADE;
DROP TYPE IF EXISTS droptype_02611_type CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地类型和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE TYPE droptype_02611_type AS (c integer);
CREATE FUNCTION droptype_02611_opfn(droptype_02611_type, droptype_02611_type) RETURNS boolean LANGUAGE sql AS $$ SELECT $1 IS NOT NULL; $$;
CREATE OPERATOR # (PROCEDURE = droptype_02611_opfn, LEFTARG = droptype_02611_type, RIGHTARG = droptype_02611_type);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP TYPE。
-- primary-target-begin
DROP TYPE IF EXISTS droptype_02611_type;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS type_present FROM pg_catalog.pg_type WHERE typname = 'droptype_02611_type' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP OPERATOR IF EXISTS #(droptype_02611_type, droptype_02611_type);
DROP FUNCTION IF EXISTS droptype_02611_opfn CASCADE;
DROP TYPE IF EXISTS droptype_02611_type CASCADE;
