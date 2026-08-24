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
-- case_id: CREATEOPERATORCLASS03875
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/create_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/create_operator_class.yaml
-- primary_obligation_id: COPC-EXT|03875|error_assertion|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR CLASS IF EXISTS createoperatorclass_03875_oc CASCADE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_03875_oc CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_03875_fam CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_03875_nofam CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_03875_sortfam CASCADE;
DROP OPERATOR IF EXISTS createoperatorclass_03875_op(createoperatorclass_03875_geom, createoperatorclass_03875_geom);
DROP FUNCTION IF EXISTS createoperatorclass_03875_opfn(createoperatorclass_03875_geom, createoperatorclass_03875_geom);
DROP FUNCTION IF EXISTS createoperatorclass_03875_fn(createoperatorclass_03875_geom, createoperatorclass_03875_geom);
DROP TYPE IF EXISTS createoperatorclass_03875_geom CASCADE;
DROP TYPE IF EXISTS createoperatorclass_03875_badtype CASCADE;
RESET ROLE;
DROP ROLE IF EXISTS createoperatorclass_03875_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createoperatorclass_03875_actor LOGIN NOSUPERUSER;
CREATE TYPE createoperatorclass_03875_geom AS (x float8, y float8);
CREATE FUNCTION createoperatorclass_03875_opfn(createoperatorclass_03875_geom, createoperatorclass_03875_geom) RETURNS boolean AS 'SELECT $1 = $2' LANGUAGE SQL IMMUTABLE;
CREATE OPERATOR createoperatorclass_03875_op (LEFTARG = createoperatorclass_03875_geom, RIGHTARG = createoperatorclass_03875_geom, PROCEDURE = createoperatorclass_03875_opfn);
CREATE FUNCTION createoperatorclass_03875_fn(createoperatorclass_03875_geom, createoperatorclass_03875_geom) RETURNS boolean AS 'SELECT $1 = $2' LANGUAGE SQL IMMUTABLE;
SET ROLE createoperatorclass_03875_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE OPERATOR CLASS。
-- primary-target-begin
CREATE OPERATOR CLASS createoperatorclass_03875_oc FOR TYPE createoperatorclass_03875_geom USING gist AS
  OPERATOR 1 createoperatorclass_03875_op (createoperatorclass_03875_geom, createoperatorclass_03875_geom),
  FUNCTION 1 (createoperatorclass_03875_geom) createoperatorclass_03875_fn (createoperatorclass_03875_geom, createoperatorclass_03875_geom),
  STORAGE createoperatorclass_03875_geom;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_03875_oc CASCADE;
DROP OPERATOR IF EXISTS createoperatorclass_03875_op(createoperatorclass_03875_geom, createoperatorclass_03875_geom);
DROP FUNCTION IF EXISTS createoperatorclass_03875_opfn(createoperatorclass_03875_geom, createoperatorclass_03875_geom);
DROP FUNCTION IF EXISTS createoperatorclass_03875_fn(createoperatorclass_03875_geom, createoperatorclass_03875_geom);
DROP TYPE IF EXISTS createoperatorclass_03875_geom CASCADE;
DROP OWNED BY createoperatorclass_03875_actor CASCADE;
DROP ROLE IF EXISTS createoperatorclass_03875_actor;
