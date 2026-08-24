-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 DECLARE with statement_branch=branch_1, expected_status=failure, cursor_state=with_hold_after_commit, direction_shape=relative, hold_scroll_shape=default, cursor_name_shape=quoted_identifier, query_shape=empty_result, transaction_context=inside_transaction, dependency_state=ready, invalid_combination=object_type_mismatch, position_boundary=after_last, verification_mode=error_assertion, cleanup_mode=reset_state
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor cursor_state=with_hold_after_commit
-- factor direction_shape=relative
-- factor hold_scroll_shape=default
-- factor cursor_name_shape=quoted_identifier
-- factor query_shape=empty_result
-- factor transaction_context=inside_transaction
-- factor dependency_state=ready
-- factor invalid_combination=object_type_mismatch
-- factor position_boundary=after_last
-- factor verification_mode=error_assertion
-- factor cleanup_mode=reset_state
DROP TABLE IF EXISTS cur_00322_table;
CREATE TABLE cur_00322_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00322_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
BEGIN;
DECLARE "cur_00322_Cursor" CURSOR WITH HOLD FOR SELECT id FROM cur_00322_cursor ORDER BY id;
DECLARE "cur_00322_Cursor" CURSOR WITH HOLD FOR SELECT id FROM cur_00322_cursor ORDER BY id;
SELECT 'expected_cursor_error' AS error_assertion;
ROLLBACK;
RESET ALL;
DROP TABLE IF EXISTS cur_00322_table;
