-- --------------------------------------------------------
-- author       : yuzhengwen y00938623
-- create at    : 2026-10-27
-- description  : Multi-column simultaneous upgrade
-- FE           : FE2026081100174
-- --------------------------------------------------------

-- pre-cleanup
DROP TABLE IF EXISTS `tab_tucr_000112_inplace`;
DROP TABLE IF EXISTS `tab_tucr_000112_instant`;
DROP TABLE IF EXISTS `tab_tucr_000112_ref`;
-- create inplace and instant source candidates
CREATE TABLE `tab_tucr_000112_inplace` (
  `id` BIGINT NOT NULL,
  `int_col` INT NOT NULL,
  `char_col` VARCHAR(60) NULL,
  `binary_col` VARBINARY(60) NULL,
  `canary_int` BIGINT NULL,
  `canary_varchar` VARCHAR(64) NULL,
  `canary_varbinary` VARBINARY(64) NULL,
  `canary_decimal` DECIMAL(20,4) NULL,
  PRIMARY KEY (`id`),
  KEY `idx_tucr_000112_target` (`int_col`, `canary_int`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE `tab_tucr_000112_instant` (
  `id` BIGINT NOT NULL,
  `int_col` INT NOT NULL,
  `char_col` VARCHAR(60) NULL,
  `binary_col` VARBINARY(60) NULL,
  `canary_int` BIGINT NULL,
  `canary_varchar` VARCHAR(64) NULL,
  `canary_varbinary` VARBINARY(64) NULL,
  `canary_decimal` DECIMAL(20,4) NULL,
  PRIMARY KEY (`id`),
  KEY `idx_tucr_000112_target` (`int_col`, `canary_int`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- create direct target reference
CREATE TABLE `tab_tucr_000112_ref` (
  `id` BIGINT NOT NULL,
  `int_col` BIGINT NOT NULL,
  `char_col` VARCHAR(120) NULL,
  `binary_col` VARBINARY(120) NULL,
  `canary_int` BIGINT NULL,
  `canary_varchar` VARCHAR(64) NULL,
  `canary_varbinary` VARBINARY(64) NULL,
  `canary_decimal` DECIMAL(20,4) NULL,
  PRIMARY KEY (`id`),
  KEY `idx_tucr_000112_target` (`int_col`, `canary_int`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- seed deterministic rows
INSERT INTO `tab_tucr_000112_inplace` (`id`, `int_col`, `char_col`, `binary_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (1, 0, 'a', x'01', 1, 'c1', x'01', 1.0000),
  (2, 2147483647, REPEAT('b', 60), REPEAT(x'02', 60), 2, 'c2', x'02', 2.0000),
  (3, -2147483648, REPEAT('c', 60), REPEAT(x'03', 60), 3, 'c3', x'03', 3.0000),
  (4, 2, NULL, NULL, 4, 'c4', x'04', 4.0000),
  (5, 1, REPEAT('d', 60), REPEAT(x'04', 60), 5, 'c5', x'05', 5.0000);
INSERT INTO `tab_tucr_000112_instant` (`id`, `int_col`, `char_col`, `binary_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (1, 0, 'a', x'01', 1, 'c1', x'01', 1.0000),
  (2, 2147483647, REPEAT('b', 60), REPEAT(x'02', 60), 2, 'c2', x'02', 2.0000),
  (3, -2147483648, REPEAT('c', 60), REPEAT(x'03', 60), 3, 'c3', x'03', 3.0000),
  (4, 2, NULL, NULL, 4, 'c4', x'04', 4.0000),
  (5, 1, REPEAT('d', 60), REPEAT(x'04', 60), 5, 'c5', x'05', 5.0000);
INSERT INTO `tab_tucr_000112_ref` (`id`, `int_col`, `char_col`, `binary_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (1, 0, 'a', x'01', 1, 'c1', x'01', 1.0000),
  (2, 2147483647, REPEAT('b', 60), REPEAT(x'02', 60), 2, 'c2', x'02', 2.0000),
  (3, -2147483648, REPEAT('c', 60), REPEAT(x'03', 60), 3, 'c3', x'03', 3.0000),
  (4, 2, NULL, NULL, 4, 'c4', x'04', 4.0000),
  (5, 1, REPEAT('d', 60), REPEAT(x'04', 60), 5, 'c5', x'05', 5.0000);
-- direct reference deterministic DML (executed once)
INSERT INTO `tab_tucr_000112_ref` (`id`, `int_col`, `char_col`, `binary_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (6, 9223372036854775807, REPEAT('e', 120), REPEAT(x'05', 120), 6, 'c6', x'06', 6.0000),
  (7, 9223372036854775805, REPEAT('f', 119), REPEAT(x'06', 119), 7, 'c7', x'07', 7.0000);
UPDATE `tab_tucr_000112_ref` SET `int_col` = CASE `id` WHEN 1 THEN 3 WHEN 3 THEN 5 ELSE `int_col` END, `char_col` = CASE `id` WHEN 1 THEN 'x' WHEN 3 THEN 'z' ELSE `char_col` END, `binary_col` = CASE `id` WHEN 1 THEN x'11' WHEN 3 THEN x'13' ELSE `binary_col` END, `canary_int` = `canary_int` + 100 WHERE `id` IN (1, 3, 5);
DELETE FROM `tab_tucr_000112_ref` WHERE `id` IN (2, 4);
INSERT INTO `tab_tucr_000112_ref` (`id`, `int_col`, `char_col`, `binary_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (8, 2, 'g', x'07', 8, 'c8', x'08', 8.0000);
-- INPLACE DDL
ALTER TABLE `tab_tucr_000112_inplace` MODIFY `int_col` BIGINT NOT NULL, MODIFY `char_col` VARCHAR(120) NULL, MODIFY `binary_col` VARBINARY(120) NULL, ALGORITHM=INPLACE, LOCK=NONE;
-- INPLACE post-DDL deterministic DML
INSERT INTO `tab_tucr_000112_inplace` (`id`, `int_col`, `char_col`, `binary_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (6, 9223372036854775807, REPEAT('e', 120), REPEAT(x'05', 120), 6, 'c6', x'06', 6.0000),
  (7, 9223372036854775805, REPEAT('f', 119), REPEAT(x'06', 119), 7, 'c7', x'07', 7.0000);
UPDATE `tab_tucr_000112_inplace` SET `int_col` = CASE `id` WHEN 1 THEN 3 WHEN 3 THEN 5 ELSE `int_col` END, `char_col` = CASE `id` WHEN 1 THEN 'x' WHEN 3 THEN 'z' ELSE `char_col` END, `binary_col` = CASE `id` WHEN 1 THEN x'11' WHEN 3 THEN x'13' ELSE `binary_col` END, `canary_int` = `canary_int` + 100 WHERE `id` IN (1, 3, 5);
DELETE FROM `tab_tucr_000112_inplace` WHERE `id` IN (2, 4);
INSERT INTO `tab_tucr_000112_inplace` (`id`, `int_col`, `char_col`, `binary_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (8, 2, 'g', x'07', 8, 'c8', x'08', 8.0000);
-- INPLACE stable result
SELECT 'TUCR-000112' AS case_id, 'INPLACE' AS algorithm, (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000112_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000112_inplace') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000112_inplace' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000112_ref')) AS schema_diff) AS schema_diff_count, (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000112_inplace`) - (SELECT COUNT(*) FROM `tab_tucr_000112_ref`))) AS row_count_diff, (SELECT COUNT(*) FROM `tab_tucr_000112_inplace` c LEFT JOIN `tab_tucr_000112_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.int_col <=> r.int_col) AND (c.char_col <=> r.char_col) AND (c.binary_col <=> r.binary_col) AND (c.canary_int <=> r.canary_int) AND (c.canary_varchar <=> r.canary_varchar) AND (c.canary_varbinary <=> r.canary_varbinary) AND (c.canary_decimal <=> r.canary_decimal))) AS mismatch_count, (SELECT COUNT(*) FROM `tab_tucr_000112_ref` r LEFT JOIN `tab_tucr_000112_inplace` c ON c.`id`=r.`id` WHERE c.`id` IS NULL) AS extra_count, CASE WHEN (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000112_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000112_inplace') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000112_inplace' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000112_ref')) AS schema_diff)=0 AND (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000112_inplace`) - (SELECT COUNT(*) FROM `tab_tucr_000112_ref`)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000112_inplace` c LEFT JOIN `tab_tucr_000112_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.int_col <=> r.int_col) AND (c.char_col <=> r.char_col) AND (c.binary_col <=> r.binary_col) AND (c.canary_int <=> r.canary_int) AND (c.canary_varchar <=> r.canary_varchar) AND (c.canary_varbinary <=> r.canary_varbinary) AND (c.canary_decimal <=> r.canary_decimal)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000112_ref` r LEFT JOIN `tab_tucr_000112_inplace` c ON c.`id`=r.`id` WHERE c.`id` IS NULL)=0 THEN 'PASS' ELSE 'FAIL' END AS result;
-- INSTANT DDL
ALTER TABLE `tab_tucr_000112_instant` MODIFY `int_col` BIGINT NOT NULL, MODIFY `char_col` VARCHAR(120) NULL, MODIFY `binary_col` VARBINARY(120) NULL, ALGORITHM=INSTANT;
-- INSTANT post-DDL deterministic DML
INSERT INTO `tab_tucr_000112_instant` (`id`, `int_col`, `char_col`, `binary_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (6, 9223372036854775807, REPEAT('e', 120), REPEAT(x'05', 120), 6, 'c6', x'06', 6.0000),
  (7, 9223372036854775805, REPEAT('f', 119), REPEAT(x'06', 119), 7, 'c7', x'07', 7.0000);
UPDATE `tab_tucr_000112_instant` SET `int_col` = CASE `id` WHEN 1 THEN 3 WHEN 3 THEN 5 ELSE `int_col` END, `char_col` = CASE `id` WHEN 1 THEN 'x' WHEN 3 THEN 'z' ELSE `char_col` END, `binary_col` = CASE `id` WHEN 1 THEN x'11' WHEN 3 THEN x'13' ELSE `binary_col` END, `canary_int` = `canary_int` + 100 WHERE `id` IN (1, 3, 5);
DELETE FROM `tab_tucr_000112_instant` WHERE `id` IN (2, 4);
INSERT INTO `tab_tucr_000112_instant` (`id`, `int_col`, `char_col`, `binary_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (8, 2, 'g', x'07', 8, 'c8', x'08', 8.0000);
-- INSTANT stable result
SELECT 'TUCR-000112' AS case_id, 'INSTANT' AS algorithm, (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000112_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000112_instant') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000112_instant' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000112_ref')) AS schema_diff) AS schema_diff_count, (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000112_instant`) - (SELECT COUNT(*) FROM `tab_tucr_000112_ref`))) AS row_count_diff, (SELECT COUNT(*) FROM `tab_tucr_000112_instant` c LEFT JOIN `tab_tucr_000112_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.int_col <=> r.int_col) AND (c.char_col <=> r.char_col) AND (c.binary_col <=> r.binary_col) AND (c.canary_int <=> r.canary_int) AND (c.canary_varchar <=> r.canary_varchar) AND (c.canary_varbinary <=> r.canary_varbinary) AND (c.canary_decimal <=> r.canary_decimal))) AS mismatch_count, (SELECT COUNT(*) FROM `tab_tucr_000112_ref` r LEFT JOIN `tab_tucr_000112_instant` c ON c.`id`=r.`id` WHERE c.`id` IS NULL) AS extra_count, CASE WHEN (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000112_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000112_instant') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000112_instant' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000112_ref')) AS schema_diff)=0 AND (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000112_instant`) - (SELECT COUNT(*) FROM `tab_tucr_000112_ref`)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000112_instant` c LEFT JOIN `tab_tucr_000112_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.int_col <=> r.int_col) AND (c.char_col <=> r.char_col) AND (c.binary_col <=> r.binary_col) AND (c.canary_int <=> r.canary_int) AND (c.canary_varchar <=> r.canary_varchar) AND (c.canary_varbinary <=> r.canary_varbinary) AND (c.canary_decimal <=> r.canary_decimal)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000112_ref` r LEFT JOIN `tab_tucr_000112_instant` c ON c.`id`=r.`id` WHERE c.`id` IS NULL)=0 THEN 'PASS' ELSE 'FAIL' END AS result;
-- final cleanup
DROP TABLE IF EXISTS `tab_tucr_000112_inplace`;
DROP TABLE IF EXISTS `tab_tucr_000112_instant`;
DROP TABLE IF EXISTS `tab_tucr_000112_ref`;
