-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : REASSIGN OWNED transaction_outcome=commit
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: REASSIGNOWNED00048
-- source_md: skills/pg-sql-generation/references/statements/ddl/ownership/reassign_owned.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/ownership/reassign_owned.yaml
-- primary_obligation_id: REASSIGNOWNED-RISK|transaction|commit
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS reassignowned_00048_t CASCADE;
DROP OWNED BY reassignowned_00048_old;
DROP OWNED BY reassignowned_00048_new;
DROP ROLE IF EXISTS reassignowned_00048_old;
DROP ROLE IF EXISTS reassignowned_00048_new;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE reassignowned_00048_old LOGIN;
CREATE ROLE reassignowned_00048_new LOGIN;
CREATE TABLE reassignowned_00048_t (c integer);
ALTER TABLE reassignowned_00048_t OWNER TO reassignowned_00048_old;
BEGIN;
-- 3. 执行唯一获得覆盖信用的 REASSIGN OWNED。
-- primary-target-begin
REASSIGN OWNED BY reassignowned_00048_old TO reassignowned_00048_new;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
COMMIT;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS ownership_transferred FROM pg_catalog.pg_class AS c JOIN pg_catalog.pg_roles AS r ON c.relowner = r.oid WHERE c.relname = 'reassignowned_00048_t' AND r.rolname = 'reassignowned_00048_new' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP OWNED BY reassignowned_00048_old;
DROP OWNED BY reassignowned_00048_new;
DROP ROLE IF EXISTS reassignowned_00048_old;
DROP ROLE IF EXISTS reassignowned_00048_new;
DROP TABLE IF EXISTS reassignowned_00048_t CASCADE;
