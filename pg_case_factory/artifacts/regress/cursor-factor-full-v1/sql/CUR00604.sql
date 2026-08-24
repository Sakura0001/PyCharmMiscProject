-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 MOVE with statement_branch=branch_1, expected_status=failure, cursor_state=missing_cursor, direction_shape=all, hold_scroll_shape=with_hold, cursor_name_shape=missing_name, query_shape=simple_select, transaction_context=inside_transaction, dependency_state=ready, invalid_combination=object_type_mismatch, position_boundary=before_first, verification_mode=effect_query, cleanup_mode=reset_state
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor cursor_state=missing_cursor
-- factor direction_shape=all
-- factor hold_scroll_shape=with_hold
-- factor cursor_name_shape=missing_name
-- factor query_shape=simple_select
-- factor transaction_context=inside_transaction
-- factor dependency_state=ready
-- factor invalid_combination=object_type_mismatch
-- factor position_boundary=before_first
-- factor verification_mode=effect_query
-- factor cleanup_mode=reset_state
DROP TABLE IF EXISTS cur_00604_table;
CREATE TABLE cur_00604_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00604_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
BEGIN;
MOVE ABSOLUTE 0 FROM cur_00604_table;
SELECT 1 AS failure_boundary;
SELECT count(*) AS cursor_effect_rows FROM cur_00604_table;
ROLLBACK;
RESET ALL;
DROP TABLE IF EXISTS cur_00604_table;
