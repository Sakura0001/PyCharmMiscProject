-- --------------------------------------------------------
-- author       : yuzhengwen y00938623
-- create at    : 2026-10-27
-- description  : BINARY(10) foreign key RESTRICT
-- FE           : FE2026081100174
-- --------------------------------------------------------

-- pre-cleanup
DROP TABLE IF EXISTS `tab_tucr_000091_inplace`;
DROP TABLE IF EXISTS `tab_tucr_000091_instant`;
DROP TABLE IF EXISTS `tab_tucr_000091_ref`;
DROP TABLE IF EXISTS `tab_tucr_000091_parent_inplace`;
DROP TABLE IF EXISTS `tab_tucr_000091_parent_instant`;
DROP TABLE IF EXISTS `tab_tucr_000091_parent_ref`;
-- create source and target parent tables
CREATE TABLE `tab_tucr_000091_parent_inplace` (
  `id` BIGINT NOT NULL,
  `target_col` BINARY(10) NOT NULL,
  `payload` VARCHAR(64) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tucr_000091_parent` (`target_col`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE `tab_tucr_000091_parent_instant` (
  `id` BIGINT NOT NULL,
  `target_col` BINARY(10) NOT NULL,
  `payload` VARCHAR(64) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tucr_000091_parent` (`target_col`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE `tab_tucr_000091_parent_ref` (
  `id` BIGINT NOT NULL,
  `target_col` BINARY(20) NOT NULL,
  `payload` VARCHAR(64) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tucr_000091_parent` (`target_col`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- create inplace and instant source candidates
CREATE TABLE `tab_tucr_000091_inplace` (
  `id` BIGINT NOT NULL,
  `target_col` BINARY(10) NOT NULL,
  `canary_int` BIGINT NULL,
  `canary_varchar` VARCHAR(64) NULL,
  `canary_varbinary` VARBINARY(64) NULL,
  `canary_decimal` DECIMAL(20,4) NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_tucr_000091_tab_tucr_000091_inplace` FOREIGN KEY (`target_col`) REFERENCES `tab_tucr_000091_parent_inplace` (`target_col`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `idx_tucr_000091_target` (`target_col`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE `tab_tucr_000091_instant` (
  `id` BIGINT NOT NULL,
  `target_col` BINARY(10) NOT NULL,
  `canary_int` BIGINT NULL,
  `canary_varchar` VARCHAR(64) NULL,
  `canary_varbinary` VARBINARY(64) NULL,
  `canary_decimal` DECIMAL(20,4) NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_tucr_000091_tab_tucr_000091_instant` FOREIGN KEY (`target_col`) REFERENCES `tab_tucr_000091_parent_instant` (`target_col`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `idx_tucr_000091_target` (`target_col`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- create direct target reference
CREATE TABLE `tab_tucr_000091_ref` (
  `id` BIGINT NOT NULL,
  `target_col` BINARY(20) NOT NULL,
  `canary_int` BIGINT NULL,
  `canary_varchar` VARCHAR(64) NULL,
  `canary_varbinary` VARBINARY(64) NULL,
  `canary_decimal` DECIMAL(20,4) NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_tucr_000091_tab_tucr_000091_ref` FOREIGN KEY (`target_col`) REFERENCES `tab_tucr_000091_parent_ref` (`target_col`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `idx_tucr_000091_target` (`target_col`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- seed deterministic rows
INSERT INTO `tab_tucr_000091_inplace` (`id`, `target_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (1, x'01', 1, 'c1', x'01', 1.0000),
  (2, REPEAT(x'02', 10), 2, 'c2', x'02', 2.0000),
  (3, REPEAT(x'03', 10), 3, 'c3', x'03', 3.0000),
  (4, x'', 4, 'c4', x'04', 4.0000),
  (5, REPEAT(x'04', 10), 5, 'c5', x'05', 5.0000);
INSERT INTO `tab_tucr_000091_instant` (`id`, `target_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (1, x'01', 1, 'c1', x'01', 1.0000),
  (2, REPEAT(x'02', 10), 2, 'c2', x'02', 2.0000),
  (3, REPEAT(x'03', 10), 3, 'c3', x'03', 3.0000),
  (4, x'', 4, 'c4', x'04', 4.0000),
  (5, REPEAT(x'04', 10), 5, 'c5', x'05', 5.0000);
INSERT INTO `tab_tucr_000091_ref` (`id`, `target_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (1, x'01', 1, 'c1', x'01', 1.0000),
  (2, REPEAT(x'02', 10), 2, 'c2', x'02', 2.0000),
  (3, REPEAT(x'03', 10), 3, 'c3', x'03', 3.0000),
  (4, x'', 4, 'c4', x'04', 4.0000),
  (5, REPEAT(x'04', 10), 5, 'c5', x'05', 5.0000);
INSERT INTO `tab_tucr_000091_parent_inplace` (`id`, `target_col`, `payload`) VALUES
  (1, x'01', 'p1'),
  (2, REPEAT(x'02', 10), 'p2'),
  (3, REPEAT(x'03', 10), 'p3'),
  (4, x'', 'p4'),
  (5, REPEAT(x'04', 10), 'p5');
INSERT INTO `tab_tucr_000091_parent_instant` (`id`, `target_col`, `payload`) VALUES
  (1, x'01', 'p1'),
  (2, REPEAT(x'02', 10), 'p2'),
  (3, REPEAT(x'03', 10), 'p3'),
  (4, x'', 'p4'),
  (5, REPEAT(x'04', 10), 'p5');
INSERT INTO `tab_tucr_000091_parent_ref` (`id`, `target_col`, `payload`) VALUES
  (1, x'01', 'p1'),
  (2, REPEAT(x'02', 10), 'p2'),
  (3, REPEAT(x'03', 10), 'p3'),
  (4, x'', 'p4'),
  (5, REPEAT(x'04', 10), 'p5');
-- direct reference deterministic DML (executed once)
INSERT INTO `tab_tucr_000091_parent_ref` (`id`, `target_col`, `payload`) VALUES
  (6, REPEAT(x'05', 20), 'p6'),
  (7, REPEAT(x'06', 19), 'p7');
INSERT INTO `tab_tucr_000091_ref` (`id`, `target_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (6, REPEAT(x'05', 20), 6, 'c6', x'06', 6.0000),
  (7, REPEAT(x'06', 19), 7, 'c7', x'07', 7.0000);
UPDATE `tab_tucr_000091_parent_ref` SET `target_col` = CASE `id` WHEN 1 THEN x'11' WHEN 3 THEN x'13' ELSE `target_col` END WHERE `id` IN (1, 3, 5);
UPDATE `tab_tucr_000091_ref` SET `target_col` = CASE `id` WHEN 1 THEN x'11' WHEN 3 THEN x'13' ELSE `target_col` END, `canary_int` = `canary_int` + 100 WHERE `id` IN (1, 3, 5);
DELETE FROM `tab_tucr_000091_ref` WHERE `id` IN (2, 4);
DELETE FROM `tab_tucr_000091_parent_ref` WHERE `id` IN (2, 4);
INSERT INTO `tab_tucr_000091_parent_ref` (`id`, `target_col`, `payload`) VALUES
  (8, x'07', 'p8');
INSERT INTO `tab_tucr_000091_ref` (`id`, `target_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (8, x'07', 8, 'c8', x'08', 8.0000);
-- INPLACE DDL
ALTER TABLE `tab_tucr_000091_parent_inplace` MODIFY `target_col` BINARY(20) NOT NULL, ALGORITHM=INPLACE, LOCK=NONE;
ALTER TABLE `tab_tucr_000091_inplace` MODIFY `target_col` BINARY(20) NOT NULL, ALGORITHM=INPLACE, LOCK=NONE;
-- INPLACE post-DDL deterministic DML
INSERT INTO `tab_tucr_000091_parent_inplace` (`id`, `target_col`, `payload`) VALUES
  (6, REPEAT(x'05', 20), 'p6'),
  (7, REPEAT(x'06', 19), 'p7');
INSERT INTO `tab_tucr_000091_inplace` (`id`, `target_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (6, REPEAT(x'05', 20), 6, 'c6', x'06', 6.0000),
  (7, REPEAT(x'06', 19), 7, 'c7', x'07', 7.0000);
UPDATE `tab_tucr_000091_parent_inplace` SET `target_col` = CASE `id` WHEN 1 THEN x'11' WHEN 3 THEN x'13' ELSE `target_col` END WHERE `id` IN (1, 3, 5);
UPDATE `tab_tucr_000091_inplace` SET `target_col` = CASE `id` WHEN 1 THEN x'11' WHEN 3 THEN x'13' ELSE `target_col` END, `canary_int` = `canary_int` + 100 WHERE `id` IN (1, 3, 5);
DELETE FROM `tab_tucr_000091_inplace` WHERE `id` IN (2, 4);
DELETE FROM `tab_tucr_000091_parent_inplace` WHERE `id` IN (2, 4);
INSERT INTO `tab_tucr_000091_parent_inplace` (`id`, `target_col`, `payload`) VALUES
  (8, x'07', 'p8');
INSERT INTO `tab_tucr_000091_inplace` (`id`, `target_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (8, x'07', 8, 'c8', x'08', 8.0000);
-- INPLACE stable result
SELECT 'TUCR-000091' AS case_id, 'INPLACE' AS algorithm, (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000091_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000091_inplace') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000091_inplace' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000091_ref')) AS schema_diff) AS schema_diff_count, (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000091_inplace`) - (SELECT COUNT(*) FROM `tab_tucr_000091_ref`))) AS row_count_diff, (SELECT COUNT(*) FROM `tab_tucr_000091_inplace` c LEFT JOIN `tab_tucr_000091_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col) AND (c.canary_int <=> r.canary_int) AND (c.canary_varchar <=> r.canary_varchar) AND (c.canary_varbinary <=> r.canary_varbinary) AND (c.canary_decimal <=> r.canary_decimal))) AS mismatch_count, (SELECT COUNT(*) FROM `tab_tucr_000091_ref` r LEFT JOIN `tab_tucr_000091_inplace` c ON c.`id`=r.`id` WHERE c.`id` IS NULL) AS extra_count, CASE WHEN (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000091_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000091_inplace') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000091_inplace' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000091_ref')) AS schema_diff)=0 AND (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000091_inplace`) - (SELECT COUNT(*) FROM `tab_tucr_000091_ref`)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000091_inplace` c LEFT JOIN `tab_tucr_000091_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col) AND (c.canary_int <=> r.canary_int) AND (c.canary_varchar <=> r.canary_varchar) AND (c.canary_varbinary <=> r.canary_varbinary) AND (c.canary_decimal <=> r.canary_decimal)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000091_ref` r LEFT JOIN `tab_tucr_000091_inplace` c ON c.`id`=r.`id` WHERE c.`id` IS NULL)=0 THEN 'PASS' ELSE 'FAIL' END AS result;
-- INSTANT DDL
ALTER TABLE `tab_tucr_000091_parent_instant` MODIFY `target_col` BINARY(20) NOT NULL, ALGORITHM=INSTANT;
ALTER TABLE `tab_tucr_000091_instant` MODIFY `target_col` BINARY(20) NOT NULL, ALGORITHM=INSTANT;
-- INSTANT post-DDL deterministic DML
INSERT INTO `tab_tucr_000091_parent_instant` (`id`, `target_col`, `payload`) VALUES
  (6, REPEAT(x'05', 20), 'p6'),
  (7, REPEAT(x'06', 19), 'p7');
INSERT INTO `tab_tucr_000091_instant` (`id`, `target_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (6, REPEAT(x'05', 20), 6, 'c6', x'06', 6.0000),
  (7, REPEAT(x'06', 19), 7, 'c7', x'07', 7.0000);
UPDATE `tab_tucr_000091_parent_instant` SET `target_col` = CASE `id` WHEN 1 THEN x'11' WHEN 3 THEN x'13' ELSE `target_col` END WHERE `id` IN (1, 3, 5);
UPDATE `tab_tucr_000091_instant` SET `target_col` = CASE `id` WHEN 1 THEN x'11' WHEN 3 THEN x'13' ELSE `target_col` END, `canary_int` = `canary_int` + 100 WHERE `id` IN (1, 3, 5);
DELETE FROM `tab_tucr_000091_instant` WHERE `id` IN (2, 4);
DELETE FROM `tab_tucr_000091_parent_instant` WHERE `id` IN (2, 4);
INSERT INTO `tab_tucr_000091_parent_instant` (`id`, `target_col`, `payload`) VALUES
  (8, x'07', 'p8');
INSERT INTO `tab_tucr_000091_instant` (`id`, `target_col`, `canary_int`, `canary_varchar`, `canary_varbinary`, `canary_decimal`) VALUES
  (8, x'07', 8, 'c8', x'08', 8.0000);
-- INSTANT stable result
SELECT 'TUCR-000091' AS case_id, 'INSTANT' AS algorithm, (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000091_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000091_instant') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000091_instant' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000091_ref')) AS schema_diff) AS schema_diff_count, (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000091_instant`) - (SELECT COUNT(*) FROM `tab_tucr_000091_ref`))) AS row_count_diff, (SELECT COUNT(*) FROM `tab_tucr_000091_instant` c LEFT JOIN `tab_tucr_000091_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col) AND (c.canary_int <=> r.canary_int) AND (c.canary_varchar <=> r.canary_varchar) AND (c.canary_varbinary <=> r.canary_varbinary) AND (c.canary_decimal <=> r.canary_decimal))) AS mismatch_count, (SELECT COUNT(*) FROM `tab_tucr_000091_ref` r LEFT JOIN `tab_tucr_000091_instant` c ON c.`id`=r.`id` WHERE c.`id` IS NULL) AS extra_count, CASE WHEN (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000091_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000091_instant') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000091_instant' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000091_ref')) AS schema_diff)=0 AND (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000091_instant`) - (SELECT COUNT(*) FROM `tab_tucr_000091_ref`)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000091_instant` c LEFT JOIN `tab_tucr_000091_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col) AND (c.canary_int <=> r.canary_int) AND (c.canary_varchar <=> r.canary_varchar) AND (c.canary_varbinary <=> r.canary_varbinary) AND (c.canary_decimal <=> r.canary_decimal)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000091_ref` r LEFT JOIN `tab_tucr_000091_instant` c ON c.`id`=r.`id` WHERE c.`id` IS NULL)=0 THEN 'PASS' ELSE 'FAIL' END AS result;
-- final cleanup
DROP TABLE IF EXISTS `tab_tucr_000091_inplace`;
DROP TABLE IF EXISTS `tab_tucr_000091_instant`;
DROP TABLE IF EXISTS `tab_tucr_000091_ref`;
DROP TABLE IF EXISTS `tab_tucr_000091_parent_inplace`;
DROP TABLE IF EXISTS `tab_tucr_000091_parent_instant`;
DROP TABLE IF EXISTS `tab_tucr_000091_parent_ref`;
