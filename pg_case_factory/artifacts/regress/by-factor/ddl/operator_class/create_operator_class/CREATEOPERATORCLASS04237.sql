-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE OPERATOR CLASS privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEOPERATORCLASS04237
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/create_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/create_operator_class.yaml
-- primary_obligation_id: COPC-EXT|04237|catalog_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR CLASS IF EXISTS public.createoperatorclass_04237_oc CASCADE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_04237_oc CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_04237_fam CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_04237_nofam CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_04237_sortfam CASCADE;
DROP OPERATOR IF EXISTS createoperatorclass_04237_op(createoperatorclass_04237_geom, createoperatorclass_04237_geom);
DROP FUNCTION IF EXISTS createoperatorclass_04237_opfn(createoperatorclass_04237_geom, createoperatorclass_04237_geom);
DROP FUNCTION IF EXISTS createoperatorclass_04237_fn(createoperatorclass_04237_geom, createoperatorclass_04237_geom);
DROP TYPE IF EXISTS createoperatorclass_04237_geom CASCADE;
DROP TYPE IF EXISTS createoperatorclass_04237_badtype CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createoperatorclass_04237_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createoperatorclass_04237_actor LOGIN NOSUPERUSER;
CREATE TYPE createoperatorclass_04237_geom AS (x float8, y float8);
CREATE OPERATOR FAMILY createoperatorclass_04237_fam USING gist;
CREATE FUNCTION createoperatorclass_04237_opfn(createoperatorclass_04237_geom, createoperatorclass_04237_geom) RETURNS boolean AS 'SELECT $1 = $2' LANGUAGE SQL IMMUTABLE;
CREATE OPERATOR createoperatorclass_04237_op (LEFTARG = createoperatorclass_04237_geom, RIGHTARG = createoperatorclass_04237_geom, PROCEDURE = createoperatorclass_04237_opfn);
CREATE FUNCTION createoperatorclass_04237_fn(createoperatorclass_04237_geom, createoperatorclass_04237_geom) RETURNS boolean AS 'SELECT $1 = $2' LANGUAGE SQL IMMUTABLE;
SET ROLE createoperatorclass_04237_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE OPERATOR CLASS。
-- primary-target-begin
CREATE OPERATOR CLASS public.createoperatorclass_04237_oc FOR TYPE createoperatorclass_04237_geom USING gist FAMILY createoperatorclass_04237_fam AS
  OPERATOR 1 createoperatorclass_04237_op,
  FUNCTION 1 (createoperatorclass_04237_geom) createoperatorclass_04237_fn (createoperatorclass_04237_geom, createoperatorclass_04237_geom),
  STORAGE createoperatorclass_04237_geom;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS opclass_state FROM pg_catalog.pg_opclass WHERE opcname = 'createoperatorclass_04237_oc' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OPERATOR CLASS IF EXISTS public.createoperatorclass_04237_oc CASCADE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_04237_fam CASCADE;
DROP OPERATOR IF EXISTS createoperatorclass_04237_op(createoperatorclass_04237_geom, createoperatorclass_04237_geom);
DROP FUNCTION IF EXISTS createoperatorclass_04237_opfn(createoperatorclass_04237_geom, createoperatorclass_04237_geom);
DROP FUNCTION IF EXISTS createoperatorclass_04237_fn(createoperatorclass_04237_geom, createoperatorclass_04237_geom);
DROP TYPE IF EXISTS createoperatorclass_04237_geom CASCADE;
DROP OWNED BY createoperatorclass_04237_actor CASCADE;
DROP ROLE IF EXISTS createoperatorclass_04237_actor;
