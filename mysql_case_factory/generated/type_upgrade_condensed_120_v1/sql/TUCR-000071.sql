-- --------------------------------------------------------
-- author       : yuzhengwen y00938623
-- create at    : 2026-10-27
-- description  : VARCHAR(0) to CHAR(1)
-- FE           : FE2026081100174
-- --------------------------------------------------------

-- pre-cleanup
DROP TABLE IF EXISTS `tab_tucr_000071_inplace`;
DROP TABLE IF EXISTS `tab_tucr_000071_instant`;
DROP TABLE IF EXISTS `tab_tucr_000071_ref`;
-- create inplace and instant source candidates
CREATE TABLE `tab_tucr_000071_inplace` (
  `id` BIGINT NOT NULL,
  `target_col` VARCHAR(0) NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE `tab_tucr_000071_instant` (
  `id` BIGINT NOT NULL,
  `target_col` VARCHAR(0) NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- create direct target reference
CREATE TABLE `tab_tucr_000071_ref` (
  `id` BIGINT NOT NULL,
  `target_col` CHAR(1) NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- seed deterministic rows
INSERT INTO `tab_tucr_000071_inplace` (`id`, `target_col`) VALUES
  (1, ''),
  (2, ''),
  (3, ''),
  (4, NULL),
  (5, '');
INSERT INTO `tab_tucr_000071_instant` (`id`, `target_col`) VALUES
  (1, ''),
  (2, ''),
  (3, ''),
  (4, NULL),
  (5, '');
INSERT INTO `tab_tucr_000071_ref` (`id`, `target_col`) VALUES
  (1, ''),
  (2, ''),
  (3, ''),
  (4, NULL),
  (5, '');
-- direct reference deterministic DML (executed once)
INSERT INTO `tab_tucr_000071_ref` (`id`, `target_col`) VALUES
  (6, REPEAT('e', 1)),
  (7, '');
UPDATE `tab_tucr_000071_ref` SET `target_col` = CASE `id` WHEN 1 THEN 'x' WHEN 3 THEN 'z' ELSE `target_col` END WHERE `id` IN (1, 3, 5);
DELETE FROM `tab_tucr_000071_ref` WHERE `id` IN (2, 4);
INSERT INTO `tab_tucr_000071_ref` (`id`, `target_col`) VALUES
  (8, 'g');
-- INPLACE DDL
ALTER TABLE `tab_tucr_000071_inplace` MODIFY `target_col` CHAR(1) NULL, ALGORITHM=INPLACE, LOCK=NONE;
-- INPLACE post-DDL deterministic DML
INSERT INTO `tab_tucr_000071_inplace` (`id`, `target_col`) VALUES
  (6, REPEAT('e', 1)),
  (7, '');
UPDATE `tab_tucr_000071_inplace` SET `target_col` = CASE `id` WHEN 1 THEN 'x' WHEN 3 THEN 'z' ELSE `target_col` END WHERE `id` IN (1, 3, 5);
DELETE FROM `tab_tucr_000071_inplace` WHERE `id` IN (2, 4);
INSERT INTO `tab_tucr_000071_inplace` (`id`, `target_col`) VALUES
  (8, 'g');
-- INPLACE stable result
SELECT 'TUCR-000071' AS case_id, 'INPLACE' AS algorithm, (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000071_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000071_inplace') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000071_inplace' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000071_ref')) AS schema_diff) AS schema_diff_count, (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000071_inplace`) - (SELECT COUNT(*) FROM `tab_tucr_000071_ref`))) AS row_count_diff, (SELECT COUNT(*) FROM `tab_tucr_000071_inplace` c LEFT JOIN `tab_tucr_000071_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col))) AS mismatch_count, (SELECT COUNT(*) FROM `tab_tucr_000071_ref` r LEFT JOIN `tab_tucr_000071_inplace` c ON c.`id`=r.`id` WHERE c.`id` IS NULL) AS extra_count, CASE WHEN (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000071_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000071_inplace') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000071_inplace' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000071_ref')) AS schema_diff)=0 AND (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000071_inplace`) - (SELECT COUNT(*) FROM `tab_tucr_000071_ref`)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000071_inplace` c LEFT JOIN `tab_tucr_000071_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000071_ref` r LEFT JOIN `tab_tucr_000071_inplace` c ON c.`id`=r.`id` WHERE c.`id` IS NULL)=0 THEN 'PASS' ELSE 'FAIL' END AS result;
-- INSTANT DDL
ALTER TABLE `tab_tucr_000071_instant` MODIFY `target_col` CHAR(1) NULL, ALGORITHM=INSTANT;
-- INSTANT post-DDL deterministic DML
INSERT INTO `tab_tucr_000071_instant` (`id`, `target_col`) VALUES
  (6, REPEAT('e', 1)),
  (7, '');
UPDATE `tab_tucr_000071_instant` SET `target_col` = CASE `id` WHEN 1 THEN 'x' WHEN 3 THEN 'z' ELSE `target_col` END WHERE `id` IN (1, 3, 5);
DELETE FROM `tab_tucr_000071_instant` WHERE `id` IN (2, 4);
INSERT INTO `tab_tucr_000071_instant` (`id`, `target_col`) VALUES
  (8, 'g');
-- INSTANT stable result
SELECT 'TUCR-000071' AS case_id, 'INSTANT' AS algorithm, (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000071_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000071_instant') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000071_instant' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000071_ref')) AS schema_diff) AS schema_diff_count, (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000071_instant`) - (SELECT COUNT(*) FROM `tab_tucr_000071_ref`))) AS row_count_diff, (SELECT COUNT(*) FROM `tab_tucr_000071_instant` c LEFT JOIN `tab_tucr_000071_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col))) AS mismatch_count, (SELECT COUNT(*) FROM `tab_tucr_000071_ref` r LEFT JOIN `tab_tucr_000071_instant` c ON c.`id`=r.`id` WHERE c.`id` IS NULL) AS extra_count, CASE WHEN (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000071_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000071_instant') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000071_instant' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000071_ref')) AS schema_diff)=0 AND (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000071_instant`) - (SELECT COUNT(*) FROM `tab_tucr_000071_ref`)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000071_instant` c LEFT JOIN `tab_tucr_000071_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000071_ref` r LEFT JOIN `tab_tucr_000071_instant` c ON c.`id`=r.`id` WHERE c.`id` IS NULL)=0 THEN 'PASS' ELSE 'FAIL' END AS result;
-- final cleanup
DROP TABLE IF EXISTS `tab_tucr_000071_inplace`;
DROP TABLE IF EXISTS `tab_tucr_000071_instant`;
DROP TABLE IF EXISTS `tab_tucr_000071_ref`;
