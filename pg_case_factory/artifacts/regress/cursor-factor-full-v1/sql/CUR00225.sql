-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 DECLARE with statement_branch=branch_1, expected_status=failure, cursor_state=declared_open, direction_shape=prior, hold_scroll_shape=scroll, cursor_name_shape=plain_identifier, query_shape=ordered_select, transaction_context=outside_transaction, dependency_state=missing_dependency, invalid_combination=syntax_valid_semantic_error, position_boundary=middle, verification_mode=returned_rows, cleanup_mode=drop_objects
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor cursor_state=declared_open
-- factor direction_shape=prior
-- factor hold_scroll_shape=scroll
-- factor cursor_name_shape=plain_identifier
-- factor query_shape=ordered_select
-- factor transaction_context=outside_transaction
-- factor dependency_state=missing_dependency
-- factor invalid_combination=syntax_valid_semantic_error
-- factor position_boundary=middle
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS cur_00225_table;
CREATE TABLE cur_00225_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00225_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
DECLARE cur_00225_cursor SCROLL CURSOR FOR SELECT missing_column FROM cur_00225_table ORDER BY missing_column;
DECLARE cur_00225_cursor SCROLL CURSOR FOR SELECT missing_column FROM cur_00225_table ORDER BY missing_column;
SELECT id, payload FROM cur_00225_table ORDER BY id;
COMMIT;
DROP TABLE IF EXISTS cur_00225_table;
