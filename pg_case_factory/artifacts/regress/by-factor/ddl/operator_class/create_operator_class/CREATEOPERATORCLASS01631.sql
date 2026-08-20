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
-- case_id: CREATEOPERATORCLASS01631
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/create_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/create_operator_class.yaml
-- primary_obligation_id: COPC-EXT|01631|error_assertion|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR CLASS IF EXISTS public.createoperatorclass_01631_oc CASCADE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_01631_oc CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_01631_fam CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_01631_nofam CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_01631_sortfam CASCADE;
DROP OPERATOR IF EXISTS createoperatorclass_01631_op(createoperatorclass_01631_geom, createoperatorclass_01631_geom);
DROP FUNCTION IF EXISTS createoperatorclass_01631_opfn(createoperatorclass_01631_geom, createoperatorclass_01631_geom);
DROP FUNCTION IF EXISTS createoperatorclass_01631_fn(createoperatorclass_01631_geom, createoperatorclass_01631_geom);
DROP TYPE IF EXISTS createoperatorclass_01631_geom CASCADE;
DROP TYPE IF EXISTS createoperatorclass_01631_badtype CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createoperatorclass_01631_geom AS (x float8, y float8);
CREATE OPERATOR FAMILY createoperatorclass_01631_sortfam USING btree;
CREATE FUNCTION createoperatorclass_01631_opfn(createoperatorclass_01631_geom, createoperatorclass_01631_geom) RETURNS boolean AS 'SELECT $1 = $2' LANGUAGE SQL IMMUTABLE;
CREATE OPERATOR createoperatorclass_01631_op (LEFTARG = createoperatorclass_01631_geom, RIGHTARG = createoperatorclass_01631_geom, PROCEDURE = createoperatorclass_01631_opfn);
CREATE FUNCTION createoperatorclass_01631_fn(createoperatorclass_01631_geom, createoperatorclass_01631_geom) RETURNS boolean AS 'SELECT $1 = $2' LANGUAGE SQL IMMUTABLE;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE OPERATOR CLASS。
-- primary-target-begin
CREATE OPERATOR CLASS public.createoperatorclass_01631_oc FOR TYPE createoperatorclass_01631_geom USING gist FAMILY createoperatorclass_01631_nofam AS
  OPERATOR 1 createoperatorclass_01631_op FOR ORDER BY createoperatorclass_01631_sortfam,
  FUNCTION 1 (createoperatorclass_01631_geom) createoperatorclass_01631_fn (createoperatorclass_01631_geom, createoperatorclass_01631_geom),
  STORAGE createoperatorclass_01631_geom;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP OPERATOR CLASS IF EXISTS public.createoperatorclass_01631_oc CASCADE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_01631_nofam CASCADE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_01631_sortfam CASCADE;
DROP OPERATOR IF EXISTS createoperatorclass_01631_op(createoperatorclass_01631_geom, createoperatorclass_01631_geom);
DROP FUNCTION IF EXISTS createoperatorclass_01631_opfn(createoperatorclass_01631_geom, createoperatorclass_01631_geom);
DROP FUNCTION IF EXISTS createoperatorclass_01631_fn(createoperatorclass_01631_geom, createoperatorclass_01631_geom);
DROP TYPE IF EXISTS createoperatorclass_01631_geom CASCADE;
