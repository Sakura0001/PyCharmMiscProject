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
-- case_id: CREATEOPERATORCLASS02147
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/create_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/create_operator_class.yaml
-- primary_obligation_id: COPC-EXT|02147|error_assertion|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42601
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR CLASS IF EXISTS createoperatorclass_02147_oc CASCADE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_02147_oc CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_02147_fam CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_02147_nofam CASCADE;
DROP OPERATOR FAMILY IF EXISTS createoperatorclass_02147_sortfam CASCADE;
DROP OPERATOR IF EXISTS createoperatorclass_02147_op(text, text);
DROP FUNCTION IF EXISTS createoperatorclass_02147_opfn(text, text);
DROP FUNCTION IF EXISTS createoperatorclass_02147_fn(text, text);
DROP TYPE IF EXISTS createoperatorclass_02147_geom CASCADE;
DROP TYPE IF EXISTS createoperatorclass_02147_badtype CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE OPERATOR FAMILY createoperatorclass_02147_fam USING hash;
CREATE FUNCTION createoperatorclass_02147_opfn(text, text) RETURNS boolean AS 'SELECT $1 = $2' LANGUAGE SQL IMMUTABLE;
CREATE OPERATOR createoperatorclass_02147_op (LEFTARG = text, RIGHTARG = text, PROCEDURE = createoperatorclass_02147_opfn);
CREATE FUNCTION createoperatorclass_02147_fn(text, text) RETURNS boolean AS 'SELECT $1 = $2' LANGUAGE SQL IMMUTABLE;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE OPERATOR CLASS。
-- primary-target-begin
CREATE OPERATOR CLASS createoperatorclass_02147_oc FOR TYPE text USING hash FAMILY createoperatorclass_02147_fam AS
  OPERATOR 1 createoperatorclass_02147_op FOR SEARCH,
  FUNCTION 1 (text) createoperatorclass_02147_fn (text, text),
  STORAGE text;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42601' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP OPERATOR CLASS IF EXISTS createoperatorclass_02147_oc CASCADE;
DROP OPERATOR CLASS IF EXISTS createoperatorclass_02147_fam CASCADE;
DROP OPERATOR IF EXISTS createoperatorclass_02147_op(text, text);
DROP FUNCTION IF EXISTS createoperatorclass_02147_opfn(text, text);
DROP FUNCTION IF EXISTS createoperatorclass_02147_fn(text, text);
