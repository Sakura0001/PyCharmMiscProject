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
-- case_id: CREATEOPERATORCLASS01556
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/create_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/create_operator_class.yaml
-- primary_obligation_id: COPC-EXT|01556|catalog_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR CLASS IF EXISTS public.createoperatorclass_01556_oc CASCADE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_01556_oc CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_01556_fam CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_01556_nofam CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_01556_sortfam CASCADE;
DROP OPERATOR IF EXISTS createoperatorclass_01556_op(createoperatorclass_01556_geom, createoperatorclass_01556_geom);
DROP FUNCTION IF EXISTS createoperatorclass_01556_opfn(createoperatorclass_01556_geom, createoperatorclass_01556_geom);
DROP FUNCTION IF EXISTS createoperatorclass_01556_fn(createoperatorclass_01556_geom, createoperatorclass_01556_geom);
DROP TYPE IF EXISTS createoperatorclass_01556_geom CASCADE;
DROP TYPE IF EXISTS createoperatorclass_01556_badtype CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createoperatorclass_01556_geom AS (x float8, y float8);
CREATE FUNCTION createoperatorclass_01556_opfn(createoperatorclass_01556_geom, createoperatorclass_01556_geom) RETURNS boolean AS 'SELECT $1 = $2' LANGUAGE SQL IMMUTABLE;
CREATE OPERATOR createoperatorclass_01556_op (LEFTARG = createoperatorclass_01556_geom, RIGHTARG = createoperatorclass_01556_geom, PROCEDURE = createoperatorclass_01556_opfn);
CREATE FUNCTION createoperatorclass_01556_fn(createoperatorclass_01556_geom, createoperatorclass_01556_geom) RETURNS boolean AS 'SELECT $1 = $2' LANGUAGE SQL IMMUTABLE;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE OPERATOR CLASS。
-- primary-target-begin
CREATE OPERATOR CLASS public.createoperatorclass_01556_oc FOR TYPE createoperatorclass_01556_geom USING gist FAMILY createoperatorclass_01556_nofam AS
  OPERATOR 1 createoperatorclass_01556_op FOR SEARCH,
  FUNCTION 1 (createoperatorclass_01556_geom) createoperatorclass_01556_fn (createoperatorclass_01556_geom, createoperatorclass_01556_geom),
  STORAGE createoperatorclass_01556_geom;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS opclass_state FROM pg_catalog.pg_opclass WHERE opcname = 'createoperatorclass_01556_oc' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP OPERATOR CLASS IF EXISTS public.createoperatorclass_01556_oc CASCADE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_01556_nofam CASCADE;
DROP OPERATOR IF EXISTS createoperatorclass_01556_op(createoperatorclass_01556_geom, createoperatorclass_01556_geom);
DROP FUNCTION IF EXISTS createoperatorclass_01556_opfn(createoperatorclass_01556_geom, createoperatorclass_01556_geom);
DROP FUNCTION IF EXISTS createoperatorclass_01556_fn(createoperatorclass_01556_geom, createoperatorclass_01556_geom);
DROP TYPE IF EXISTS createoperatorclass_01556_geom CASCADE;
