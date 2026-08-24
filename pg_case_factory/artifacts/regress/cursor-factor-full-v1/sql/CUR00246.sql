-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 DECLARE with statement_branch=branch_1, expected_status=failure, cursor_state=declared_open, direction_shape=forward_backward_count, hold_scroll_shape=no_scroll, cursor_name_shape=quoted_identifier, query_shape=empty_result, transaction_context=outside_transaction, dependency_state=ready, invalid_combination=syntax_valid_semantic_error, position_boundary=after_last, verification_mode=error_assertion, cleanup_mode=drop_objects
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor cursor_state=declared_open
-- factor direction_shape=forward_backward_count
-- factor hold_scroll_shape=no_scroll
-- factor cursor_name_shape=quoted_identifier
-- factor query_shape=empty_result
-- factor transaction_context=outside_transaction
-- factor dependency_state=ready
-- factor invalid_combination=syntax_valid_semantic_error
-- factor position_boundary=after_last
-- factor verification_mode=error_assertion
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS cur_00246_table;
CREATE TABLE cur_00246_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00246_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
DECLARE "cur_00246_Cursor" NO SCROLL CURSOR FOR SELECT missing_column FROM cur_00246_table ORDER BY missing_column;
DECLARE "cur_00246_Cursor" NO SCROLL CURSOR FOR SELECT missing_column FROM cur_00246_table ORDER BY missing_column;
SELECT 'expected_cursor_error' AS error_assertion;
COMMIT;
DROP TABLE IF EXISTS cur_00246_table;
