-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE OPERATOR CLASS index_method_compatibility=storage_not_allowed_btree_hash
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEOPERATORCLASS01118
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/create_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/create_operator_class.yaml
-- primary_obligation_id: COPC-EXT|01118|catalog_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42601
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR CLASS IF EXISTS public.createoperatorclass_01118_oc CASCADE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_01118_oc CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_01118_fam CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_01118_nofam CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_01118_sortfam CASCADE;
DROP OPERATOR IF EXISTS createoperatorclass_01118_op(integer, integer);
DROP FUNCTION IF EXISTS createoperatorclass_01118_opfn(integer, integer);
DROP FUNCTION IF EXISTS createoperatorclass_01118_fn(integer, integer);
DROP TYPE IF EXISTS createoperatorclass_01118_geom CASCADE;
DROP TYPE IF EXISTS createoperatorclass_01118_badtype CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createoperatorclass_01118_opfn(integer, integer) RETURNS boolean AS 'SELECT $1 = $2' LANGUAGE SQL IMMUTABLE;
CREATE OPERATOR createoperatorclass_01118_op (LEFTARG = integer, RIGHTARG = integer, PROCEDURE = createoperatorclass_01118_opfn);
CREATE FUNCTION createoperatorclass_01118_fn(integer, integer) RETURNS boolean AS 'SELECT $1 = $2' LANGUAGE SQL IMMUTABLE;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE OPERATOR CLASS。
-- primary-target-begin
CREATE OPERATOR CLASS public.createoperatorclass_01118_oc FOR TYPE integer USING btree AS
  OPERATOR 1 createoperatorclass_01118_op (integer, integer),
  FUNCTION 1 (integer) createoperatorclass_01118_fn (integer, integer),
  STORAGE integer;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42601' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS opclass_state FROM pg_catalog.pg_opclass WHERE opcname = 'createoperatorclass_01118_oc' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP OPERATOR CLASS IF EXISTS public.createoperatorclass_01118_oc CASCADE;
DROP OPERATOR IF EXISTS createoperatorclass_01118_op(integer, integer);
DROP FUNCTION IF EXISTS createoperatorclass_01118_opfn(integer, integer);
DROP FUNCTION IF EXISTS createoperatorclass_01118_fn(integer, integer);
