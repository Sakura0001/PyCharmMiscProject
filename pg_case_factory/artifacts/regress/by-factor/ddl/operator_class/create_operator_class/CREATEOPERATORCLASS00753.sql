-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE OPERATOR CLASS target_form=create_with_entries
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEOPERATORCLASS00753
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/create_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/create_operator_class.yaml
-- primary_obligation_id: COPC-EXT|00753|effect_query|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR CLASS IF EXISTS createoperatorclass_00753_oc CASCADE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_00753_oc CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_00753_fam CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_00753_nofam CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_00753_sortfam CASCADE;
DROP OPERATOR IF EXISTS createoperatorclass_00753_op(createoperatorclass_00753_geom, createoperatorclass_00753_geom);
DROP FUNCTION IF EXISTS createoperatorclass_00753_opfn(createoperatorclass_00753_geom, createoperatorclass_00753_geom);
DROP FUNCTION IF EXISTS createoperatorclass_00753_fn(createoperatorclass_00753_geom, createoperatorclass_00753_geom);
DROP TYPE IF EXISTS createoperatorclass_00753_geom CASCADE;
DROP TYPE IF EXISTS createoperatorclass_00753_badtype CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TYPE createoperatorclass_00753_geom AS (x float8, y float8);
CREATE OPERATOR FAMILY createoperatorclass_00753_sortfam USING btree;
CREATE OPERATOR FAMILY createoperatorclass_00753_fam USING gist;
CREATE FUNCTION createoperatorclass_00753_opfn(createoperatorclass_00753_geom, createoperatorclass_00753_geom) RETURNS boolean AS 'SELECT $1 = $2' LANGUAGE SQL IMMUTABLE;
CREATE OPERATOR createoperatorclass_00753_op (LEFTARG = createoperatorclass_00753_geom, RIGHTARG = createoperatorclass_00753_geom, PROCEDURE = createoperatorclass_00753_opfn);
CREATE FUNCTION createoperatorclass_00753_fn(createoperatorclass_00753_geom, createoperatorclass_00753_geom) RETURNS boolean AS 'SELECT $1 = $2' LANGUAGE SQL IMMUTABLE;
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE OPERATOR CLASS。
-- primary-target-begin
CREATE OPERATOR CLASS createoperatorclass_00753_oc FOR TYPE createoperatorclass_00753_geom USING gist FAMILY createoperatorclass_00753_fam AS
  OPERATOR 1 createoperatorclass_00753_op FOR ORDER BY createoperatorclass_00753_sortfam,
  FUNCTION 1 (createoperatorclass_00753_geom) createoperatorclass_00753_fn (createoperatorclass_00753_geom, createoperatorclass_00753_geom),
  STORAGE createoperatorclass_00753_geom;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT opcname AS opclass_effect FROM pg_catalog.pg_opclass WHERE opcname = 'createoperatorclass_00753_oc' ORDER BY opcname;
-- 5. 清理全部本编号对象。
DROP OPERATOR CLASS IF EXISTS createoperatorclass_00753_oc CASCADE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_00753_fam CASCADE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_00753_sortfam CASCADE;
DROP OPERATOR IF EXISTS createoperatorclass_00753_op(createoperatorclass_00753_geom, createoperatorclass_00753_geom);
DROP FUNCTION IF EXISTS createoperatorclass_00753_opfn(createoperatorclass_00753_geom, createoperatorclass_00753_geom);
DROP FUNCTION IF EXISTS createoperatorclass_00753_fn(createoperatorclass_00753_geom, createoperatorclass_00753_geom);
DROP TYPE IF EXISTS createoperatorclass_00753_geom CASCADE;
