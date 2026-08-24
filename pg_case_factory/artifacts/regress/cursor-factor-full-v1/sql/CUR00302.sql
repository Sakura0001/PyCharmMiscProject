-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 DECLARE with statement_branch=branch_1, expected_status=failure, cursor_state=closed_cursor, direction_shape=forward_backward_count, hold_scroll_shape=default, cursor_name_shape=quoted_identifier, query_shape=empty_result, transaction_context=after_rollback, dependency_state=ready, invalid_combination=none, position_boundary=after_last, verification_mode=error_assertion, cleanup_mode=rollback
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor cursor_state=closed_cursor
-- factor direction_shape=forward_backward_count
-- factor hold_scroll_shape=default
-- factor cursor_name_shape=quoted_identifier
-- factor query_shape=empty_result
-- factor transaction_context=after_rollback
-- factor dependency_state=ready
-- factor invalid_combination=none
-- factor position_boundary=after_last
-- factor verification_mode=error_assertion
-- factor cleanup_mode=rollback
DROP TABLE IF EXISTS cur_00302_table;
CREATE TABLE cur_00302_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00302_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
BEGIN;
ROLLBACK;
DECLARE "cur_00302_Cursor" CURSOR FOR SELECT id, payload FROM cur_00302_table WHERE false ORDER BY id;
CLOSE "cur_00302_Cursor";
FETCH NEXT FROM "cur_00302_Cursor";
SELECT 'expected_cursor_error' AS error_assertion;
ROLLBACK;
DROP TABLE IF EXISTS cur_00302_table;
