-- --------------------------------------------------------
-- author       : yuzhengwen y00938623
-- create at    : 2026-10-27
-- description  : All dependency objects combined
-- FE           : FE2026081100174
-- --------------------------------------------------------

-- pre-cleanup
DROP TABLE IF EXISTS `tab_tucr_000117_inplace`;
DROP TABLE IF EXISTS `tab_tucr_000117_instant`;
DROP TABLE IF EXISTS `tab_tucr_000117_ref`;
DROP TABLE IF EXISTS `tab_tucr_000117_audit_inplace`;
DROP TABLE IF EXISTS `tab_tucr_000117_audit_instant`;
DROP TABLE IF EXISTS `tab_tucr_000117_audit_ref`;
DROP VIEW IF EXISTS `v_tucr_000117_tab_tucr_000117_inplace`;
DROP VIEW IF EXISTS `v_tucr_000117_tab_tucr_000117_instant`;
DROP VIEW IF EXISTS `v_tucr_000117_tab_tucr_000117_ref`;
DROP TRIGGER IF EXISTS `trg_tucr_000117_tab_tucr_000117_inplace`;
DROP TRIGGER IF EXISTS `trg_tucr_000117_tab_tucr_000117_instant`;
DROP TRIGGER IF EXISTS `trg_tucr_000117_tab_tucr_000117_ref`;
DROP FUNCTION IF EXISTS `fn_tucr_000117`;
DROP PROCEDURE IF EXISTS `pr_tucr_000117_tab_tucr_000117_inplace`;
DROP PROCEDURE IF EXISTS `pr_tucr_000117_tab_tucr_000117_instant`;
DROP PROCEDURE IF EXISTS `pr_tucr_000117_tab_tucr_000117_ref`;
-- create inplace and instant source candidates
CREATE TABLE `tab_tucr_000117_inplace` (
  `id` BIGINT NOT NULL,
  `target_col` SMALLINT NOT NULL,
  `canary_int` BIGINT NULL,
  `canary_varchar` VARCHAR(64) NULL,
  `canary_varbinary` VARBINARY(64) NULL,
  `canary_decimal` DECIMAL(20,4) NULL,
  PRIMARY KEY (`id`),
  KEY `idx_tucr_000117_target` (`target_col`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE `tab_tucr_000117_instant` (
  `id` BIGINT NOT NULL,
  `target_col` SMALLINT NOT NULL,
  `canary_int` BIGINT NULL,
  `canary_varchar` VARCHAR(64) NULL,
  `canary_varbinary` VARBINARY(64) NULL,
  `canary_decimal` DECIMAL(20,4) NULL,
  PRIMARY KEY (`id`),
  KEY `idx_tucr_000117_target` (`target_col`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- create direct target reference
CREATE TABLE `tab_tucr_000117_ref` (
  `id` BIGINT NOT NULL,
  `target_col` BIGINT NOT NULL,
  `canary_int` BIGINT NULL,
  `canary_varchar` VARCHAR(64) NULL,
  `canary_varbinary` VARBINARY(64) NULL,
  `canary_decimal` DECIMAL(20,4) NULL,
  PRIMARY KEY (`id`),
  KEY `idx_tucr_000117_target` (`target_col`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- seed deterministic rows
INSERT INTO `tab_tucr_000117_inplace` (`id`, `target_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (1, 0, 1, 'c1', x'01', 1.0000),
  (2, 32767, 2, 'c2', x'02', 2.0000),
  (3, -32768, 3, 'c3', x'03', 3.0000),
  (4, 2, 4, 'c4', x'04', 4.0000),
  (5, 1, 5, 'c5', x'05', 5.0000);
INSERT INTO `tab_tucr_000117_instant` (`id`, `target_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (1, 0, 1, 'c1', x'01', 1.0000),
  (2, 32767, 2, 'c2', x'02', 2.0000),
  (3, -32768, 3, 'c3', x'03', 3.0000),
  (4, 2, 4, 'c4', x'04', 4.0000),
  (5, 1, 5, 'c5', x'05', 5.0000);
INSERT INTO `tab_tucr_000117_ref` (`id`, `target_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (1, 0, 1, 'c1', x'01', 1.0000),
  (2, 32767, 2, 'c2', x'02', 2.0000),
  (3, -32768, 3, 'c3', x'03', 3.0000),
  (4, 2, 4, 'c4', x'04', 4.0000),
  (5, 1, 5, 'c5', x'05', 5.0000);
CREATE FUNCTION `fn_tucr_000117`(v BIGINT) RETURNS BIGINT DETERMINISTIC RETURN v + 1;
CREATE TABLE `tab_tucr_000117_audit_inplace` (
  `id` BIGINT NOT NULL,
  `canary_int` BIGINT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE VIEW `v_tucr_000117_tab_tucr_000117_inplace` AS SELECT `id`, `target_col` FROM `tab_tucr_000117_inplace`;
CREATE TRIGGER `trg_tucr_000117_tab_tucr_000117_inplace` AFTER INSERT ON `tab_tucr_000117_inplace` FOR EACH ROW INSERT INTO `tab_tucr_000117_audit_inplace` VALUES (NEW.`id`, NEW.`canary_int`);
CREATE PROCEDURE `pr_tucr_000117_tab_tucr_000117_inplace`(IN p_id BIGINT) UPDATE `tab_tucr_000117_inplace` SET `canary_int` = p_id + 1 WHERE `id` = p_id;
CREATE TABLE `tab_tucr_000117_audit_instant` (
  `id` BIGINT NOT NULL,
  `canary_int` BIGINT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE VIEW `v_tucr_000117_tab_tucr_000117_instant` AS SELECT `id`, `target_col` FROM `tab_tucr_000117_instant`;
CREATE TRIGGER `trg_tucr_000117_tab_tucr_000117_instant` AFTER INSERT ON `tab_tucr_000117_instant` FOR EACH ROW INSERT INTO `tab_tucr_000117_audit_instant` VALUES (NEW.`id`, NEW.`canary_int`);
CREATE PROCEDURE `pr_tucr_000117_tab_tucr_000117_instant`(IN p_id BIGINT) UPDATE `tab_tucr_000117_instant` SET `canary_int` = p_id + 1 WHERE `id` = p_id;
CREATE TABLE `tab_tucr_000117_audit_ref` (
  `id` BIGINT NOT NULL,
  `canary_int` BIGINT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE VIEW `v_tucr_000117_tab_tucr_000117_ref` AS SELECT `id`, `target_col` FROM `tab_tucr_000117_ref`;
CREATE TRIGGER `trg_tucr_000117_tab_tucr_000117_ref` AFTER INSERT ON `tab_tucr_000117_ref` FOR EACH ROW INSERT INTO `tab_tucr_000117_audit_ref` VALUES (NEW.`id`, NEW.`canary_int`);
CREATE PROCEDURE `pr_tucr_000117_tab_tucr_000117_ref`(IN p_id BIGINT) UPDATE `tab_tucr_000117_ref` SET `canary_int` = p_id + 1 WHERE `id` = p_id;
-- direct reference deterministic DML (executed once)
INSERT INTO `tab_tucr_000117_ref` (`id`, `target_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (6, 9223372036854775807, 6, 'c6', x'06', 6.0000),
  (7, 9223372036854775805, 7, 'c7', x'07', 7.0000);
UPDATE `tab_tucr_000117_ref` SET `target_col` = CASE `id` WHEN 1 THEN 3 WHEN 3 THEN 5 ELSE `target_col` END, `canary_int` = `canary_int` + 100 WHERE `id` IN (1, 3, 5);
DELETE FROM `tab_tucr_000117_ref` WHERE `id` IN (2, 4);
INSERT INTO `tab_tucr_000117_ref` (`id`, `target_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (8, 2, 8, 'c8', x'08', 8.0000);
-- INPLACE DDL
ALTER TABLE `tab_tucr_000117_inplace` MODIFY `target_col` BIGINT NOT NULL, ALGORITHM=INPLACE, LOCK=NONE;
-- INPLACE post-DDL deterministic DML
INSERT INTO `tab_tucr_000117_inplace` (`id`, `target_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (6, 9223372036854775807, 6, 'c6', x'06', 6.0000),
  (7, 9223372036854775805, 7, 'c7', x'07', 7.0000);
UPDATE `tab_tucr_000117_inplace` SET `target_col` = CASE `id` WHEN 1 THEN 3 WHEN 3 THEN 5 ELSE `target_col` END, `canary_int` = `canary_int` + 100 WHERE `id` IN (1, 3, 5);
DELETE FROM `tab_tucr_000117_inplace` WHERE `id` IN (2, 4);
INSERT INTO `tab_tucr_000117_inplace` (`id`, `target_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (8, 2, 8, 'c8', x'08', 8.0000);
UPDATE `tab_tucr_000117_inplace` SET `canary_int` = `fn_tucr_000117`(`id`) WHERE `id` IN (1, 3, 5);
UPDATE `tab_tucr_000117_ref` SET `canary_int` = `fn_tucr_000117`(`id`) WHERE `id` IN (1, 3, 5);
PREPARE `stmt_tucr_000117_tab_tucr_000117_inplace` FROM 'UPDATE `tab_tucr_000117_inplace` SET `canary_int` = `id` + 1 WHERE `id` = 1';
EXECUTE `stmt_tucr_000117_tab_tucr_000117_inplace`;
DEALLOCATE PREPARE `stmt_tucr_000117_tab_tucr_000117_inplace`;
PREPARE `stmt_tucr_000117_tab_tucr_000117_ref` FROM 'UPDATE `tab_tucr_000117_ref` SET `canary_int` = `id` + 1 WHERE `id` = 1';
EXECUTE `stmt_tucr_000117_tab_tucr_000117_ref`;
DEALLOCATE PREPARE `stmt_tucr_000117_tab_tucr_000117_ref`;
CALL `pr_tucr_000117_tab_tucr_000117_inplace`(1);
CALL `pr_tucr_000117_tab_tucr_000117_ref`(1);
-- INPLACE stable result
SELECT 'TUCR-000117' AS case_id, 'INPLACE' AS algorithm, (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000117_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000117_inplace') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000117_inplace' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000117_ref')) AS schema_diff) AS schema_diff_count, (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000117_inplace`) - (SELECT COUNT(*) FROM `tab_tucr_000117_ref`))) AS row_count_diff, (SELECT COUNT(*) FROM `tab_tucr_000117_inplace` c LEFT JOIN `tab_tucr_000117_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col) AND (c.canary_int <=> r.canary_int) AND (c.canary_varchar <=> r.canary_varchar) AND (c.canary_varbinary <=> r.canary_varbinary) AND (c.canary_decimal <=> r.canary_decimal))) AS mismatch_count, (SELECT COUNT(*) FROM `tab_tucr_000117_ref` r LEFT JOIN `tab_tucr_000117_inplace` c ON c.`id`=r.`id` WHERE c.`id` IS NULL) AS extra_count, CASE WHEN (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000117_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000117_inplace') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000117_inplace' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000117_ref')) AS schema_diff)=0 AND (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000117_inplace`) - (SELECT COUNT(*) FROM `tab_tucr_000117_ref`)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000117_inplace` c LEFT JOIN `tab_tucr_000117_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col) AND (c.canary_int <=> r.canary_int) AND (c.canary_varchar <=> r.canary_varchar) AND (c.canary_varbinary <=> r.canary_varbinary) AND (c.canary_decimal <=> r.canary_decimal)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000117_ref` r LEFT JOIN `tab_tucr_000117_inplace` c ON c.`id`=r.`id` WHERE c.`id` IS NULL)=0 THEN 'PASS' ELSE 'FAIL' END AS result;
-- INSTANT DDL
ALTER TABLE `tab_tucr_000117_instant` MODIFY `target_col` BIGINT NOT NULL, ALGORITHM=INSTANT;
-- INSTANT post-DDL deterministic DML
INSERT INTO `tab_tucr_000117_instant` (`id`, `target_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (6, 9223372036854775807, 6, 'c6', x'06', 6.0000),
  (7, 9223372036854775805, 7, 'c7', x'07', 7.0000);
UPDATE `tab_tucr_000117_instant` SET `target_col` = CASE `id` WHEN 1 THEN 3 WHEN 3 THEN 5 ELSE `target_col` END, `canary_int` = `canary_int` + 100 WHERE `id` IN (1, 3, 5);
DELETE FROM `tab_tucr_000117_instant` WHERE `id` IN (2, 4);
INSERT INTO `tab_tucr_000117_instant` (`id`, `target_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (8, 2, 8, 'c8', x'08', 8.0000);
UPDATE `tab_tucr_000117_instant` SET `canary_int` = `fn_tucr_000117`(`id`) WHERE `id` IN (1, 3, 5);
UPDATE `tab_tucr_000117_ref` SET `canary_int` = `fn_tucr_000117`(`id`) WHERE `id` IN (1, 3, 5);
PREPARE `stmt_tucr_000117_tab_tucr_000117_instant` FROM 'UPDATE `tab_tucr_000117_instant` SET `canary_int` = `id` + 1 WHERE `id` = 1';
EXECUTE `stmt_tucr_000117_tab_tucr_000117_instant`;
DEALLOCATE PREPARE `stmt_tucr_000117_tab_tucr_000117_instant`;
PREPARE `stmt_tucr_000117_tab_tucr_000117_ref` FROM 'UPDATE `tab_tucr_000117_ref` SET `canary_int` = `id` + 1 WHERE `id` = 1';
EXECUTE `stmt_tucr_000117_tab_tucr_000117_ref`;
DEALLOCATE PREPARE `stmt_tucr_000117_tab_tucr_000117_ref`;
CALL `pr_tucr_000117_tab_tucr_000117_instant`(1);
CALL `pr_tucr_000117_tab_tucr_000117_ref`(1);
-- INSTANT stable result
SELECT 'TUCR-000117' AS case_id, 'INSTANT' AS algorithm, (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000117_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000117_instant') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000117_instant' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000117_ref')) AS schema_diff) AS schema_diff_count, (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000117_instant`) - (SELECT COUNT(*) FROM `tab_tucr_000117_ref`))) AS row_count_diff, (SELECT COUNT(*) FROM `tab_tucr_000117_instant` c LEFT JOIN `tab_tucr_000117_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col) AND (c.canary_int <=> r.canary_int) AND (c.canary_varchar <=> r.canary_varchar) AND (c.canary_varbinary <=> r.canary_varbinary) AND (c.canary_decimal <=> r.canary_decimal))) AS mismatch_count, (SELECT COUNT(*) FROM `tab_tucr_000117_ref` r LEFT JOIN `tab_tucr_000117_instant` c ON c.`id`=r.`id` WHERE c.`id` IS NULL) AS extra_count, CASE WHEN (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000117_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000117_instant') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000117_instant' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000117_ref')) AS schema_diff)=0 AND (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000117_instant`) - (SELECT COUNT(*) FROM `tab_tucr_000117_ref`)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000117_instant` c LEFT JOIN `tab_tucr_000117_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col) AND (c.canary_int <=> r.canary_int) AND (c.canary_varchar <=> r.canary_varchar) AND (c.canary_varbinary <=> r.canary_varbinary) AND (c.canary_decimal <=> r.canary_decimal)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000117_ref` r LEFT JOIN `tab_tucr_000117_instant` c ON c.`id`=r.`id` WHERE c.`id` IS NULL)=0 THEN 'PASS' ELSE 'FAIL' END AS result;
-- final cleanup
DROP TABLE IF EXISTS `tab_tucr_000117_inplace`;
DROP TABLE IF EXISTS `tab_tucr_000117_instant`;
DROP TABLE IF EXISTS `tab_tucr_000117_ref`;
DROP TABLE IF EXISTS `tab_tucr_000117_audit_inplace`;
DROP TABLE IF EXISTS `tab_tucr_000117_audit_instant`;
DROP TABLE IF EXISTS `tab_tucr_000117_audit_ref`;
DROP VIEW IF EXISTS `v_tucr_000117_tab_tucr_000117_inplace`;
DROP VIEW IF EXISTS `v_tucr_000117_tab_tucr_000117_instant`;
DROP VIEW IF EXISTS `v_tucr_000117_tab_tucr_000117_ref`;
DROP TRIGGER IF EXISTS `trg_tucr_000117_tab_tucr_000117_inplace`;
DROP TRIGGER IF EXISTS `trg_tucr_000117_tab_tucr_000117_instant`;
DROP TRIGGER IF EXISTS `trg_tucr_000117_tab_tucr_000117_ref`;
DROP FUNCTION IF EXISTS `fn_tucr_000117`;
DROP PROCEDURE IF EXISTS `pr_tucr_000117_tab_tucr_000117_inplace`;
DROP PROCEDURE IF EXISTS `pr_tucr_000117_tab_tucr_000117_instant`;
DROP PROCEDURE IF EXISTS `pr_tucr_000117_tab_tucr_000117_ref`;
