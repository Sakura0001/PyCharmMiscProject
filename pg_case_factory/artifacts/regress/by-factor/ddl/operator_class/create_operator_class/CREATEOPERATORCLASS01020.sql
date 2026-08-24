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
-- case_id: CREATEOPERATORCLASS01020
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/create_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/create_operator_class.yaml
-- primary_obligation_id: COPC-EXT|01020|error_assertion|reset_state
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR CLASS IF EXISTS public.createoperatorclass_01020_oc CASCADE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_01020_oc CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_01020_fam CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_01020_nofam CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_01020_sortfam CASCADE;
DROP OPERATOR IF EXISTS createoperatorclass_01020_op(integer, integer);
DROP FUNCTION IF EXISTS createoperatorclass_01020_opfn(integer, integer);
DROP FUNCTION IF EXISTS createoperatorclass_01020_fn(integer, integer);
DROP TYPE IF EXISTS createoperatorclass_01020_geom CASCADE;
DROP TYPE IF EXISTS createoperatorclass_01020_badtype CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE OPERATOR FAMILY createoperatorclass_01020_sortfam USING btree;
CREATE OPERATOR FAMILY createoperatorclass_01020_fam USING btree;
CREATE FUNCTION createoperatorclass_01020_opfn(integer, integer) RETURNS boolean AS 'SELECT $1 = $2' LANGUAGE SQL IMMUTABLE;
CREATE OPERATOR createoperatorclass_01020_op (LEFTARG = integer, RIGHTARG = integer, PROCEDURE = createoperatorclass_01020_opfn);
CREATE FUNCTION createoperatorclass_01020_fn(integer, integer) RETURNS boolean AS 'SELECT $1 = $2' LANGUAGE SQL IMMUTABLE;
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE OPERATOR CLASS。
-- primary-target-begin
CREATE OPERATOR CLASS public.createoperatorclass_01020_oc FOR TYPE integer USING btree FAMILY createoperatorclass_01020_fam AS
  OPERATOR 1 createoperatorclass_01020_op FOR ORDER BY createoperatorclass_01020_sortfam,
  FUNCTION 1 (integer) createoperatorclass_01020_fn (integer, integer);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP OPERATOR CLASS IF EXISTS public.createoperatorclass_01020_oc CASCADE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_01020_fam CASCADE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_01020_sortfam CASCADE;
DROP OPERATOR IF EXISTS createoperatorclass_01020_op(integer, integer);
DROP FUNCTION IF EXISTS createoperatorclass_01020_opfn(integer, integer);
DROP FUNCTION IF EXISTS createoperatorclass_01020_fn(integer, integer);
