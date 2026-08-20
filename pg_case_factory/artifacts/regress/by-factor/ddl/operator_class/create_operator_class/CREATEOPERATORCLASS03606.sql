-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE OPERATOR CLASS family_clause=present_missing
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEOPERATORCLASS03606
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/create_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/create_operator_class.yaml
-- primary_obligation_id: COPC-EXT|03606|error_assertion|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR CLASS IF EXISTS public.createoperatorclass_03606_oc CASCADE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_03606_oc CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_03606_fam CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_03606_nofam CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_03606_sortfam CASCADE;
DROP OPERATOR IF EXISTS createoperatorclass_03606_op(createoperatorclass_03606_geom, createoperatorclass_03606_geom);
DROP FUNCTION IF EXISTS createoperatorclass_03606_opfn(createoperatorclass_03606_geom, createoperatorclass_03606_geom);
DROP FUNCTION IF EXISTS createoperatorclass_03606_fn(createoperatorclass_03606_geom, createoperatorclass_03606_geom);
DROP TYPE IF EXISTS createoperatorclass_03606_geom CASCADE;
DROP TYPE IF EXISTS createoperatorclass_03606_badtype CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createoperatorclass_03606_geom AS (x float8, y float8);
CREATE FUNCTION createoperatorclass_03606_opfn(createoperatorclass_03606_geom, createoperatorclass_03606_geom) RETURNS boolean AS 'SELECT $1 = $2' LANGUAGE SQL IMMUTABLE;
CREATE OPERATOR createoperatorclass_03606_op (LEFTARG = createoperatorclass_03606_geom, RIGHTARG = createoperatorclass_03606_geom, PROCEDURE = createoperatorclass_03606_opfn);
CREATE FUNCTION createoperatorclass_03606_fn(createoperatorclass_03606_geom, createoperatorclass_03606_geom) RETURNS boolean AS 'SELECT $1 = $2' LANGUAGE SQL IMMUTABLE;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE OPERATOR CLASS。
-- primary-target-begin
CREATE OPERATOR CLASS public.createoperatorclass_03606_oc FOR TYPE createoperatorclass_03606_geom USING gist FAMILY createoperatorclass_03606_nofam AS
  OPERATOR 1 createoperatorclass_03606_op,
  FUNCTION 1 (createoperatorclass_03606_geom) createoperatorclass_03606_fn (createoperatorclass_03606_geom, createoperatorclass_03606_geom),
  STORAGE createoperatorclass_03606_geom;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP OPERATOR CLASS IF EXISTS public.createoperatorclass_03606_oc CASCADE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_03606_nofam CASCADE;
DROP OPERATOR IF EXISTS createoperatorclass_03606_op(createoperatorclass_03606_geom, createoperatorclass_03606_geom);
DROP FUNCTION IF EXISTS createoperatorclass_03606_opfn(createoperatorclass_03606_geom, createoperatorclass_03606_geom);
DROP FUNCTION IF EXISTS createoperatorclass_03606_fn(createoperatorclass_03606_geom, createoperatorclass_03606_geom);
DROP TYPE IF EXISTS createoperatorclass_03606_geom CASCADE;
