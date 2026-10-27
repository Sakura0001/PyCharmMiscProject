-- --------------------------------------------------------
-- author       : yuzhengwen y00938623
-- create at    : 2026-10-27
-- description  : CHAR(0) to BINARY(1)
-- FE           : FE2026081100174
-- --------------------------------------------------------

-- pre-cleanup
DROP TABLE IF EXISTS `tab_tucr_000069_inplace`;
DROP TABLE IF EXISTS `tab_tucr_000069_instant`;
DROP TABLE IF EXISTS `tab_tucr_000069_ref`;
-- create inplace and instant source candidates
CREATE TABLE `tab_tucr_000069_inplace` (
  `id` BIGINT NOT NULL,
  `target_col` CHAR(0) NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE `tab_tucr_000069_instant` (
  `id` BIGINT NOT NULL,
  `target_col` CHAR(0) NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- create direct target reference
CREATE TABLE `tab_tucr_000069_ref` (
  `id` BIGINT NOT NULL,
  `target_col` BINARY(1) NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- seed deterministic rows
INSERT INTO `tab_tucr_000069_inplace` (`id`, `target_col`) VALUES
  (1, ''),
  (2, ''),
  (3, ''),
  (4, NULL),
  (5, '');
INSERT INTO `tab_tucr_000069_instant` (`id`, `target_col`) VALUES
  (1, ''),
  (2, ''),
  (3, ''),
  (4, NULL),
  (5, '');
INSERT INTO `tab_tucr_000069_ref` (`id`, `target_col`) VALUES
  (1, ''),
  (2, ''),
  (3, ''),
  (4, NULL),
  (5, '');
-- direct reference deterministic DML (executed once)
INSERT INTO `tab_tucr_000069_ref` (`id`, `target_col`) VALUES
  (6, REPEAT(x'05', 1)),
  (7, x'');
UPDATE `tab_tucr_000069_ref` SET `target_col` = CASE `id` WHEN 1 THEN x'11' WHEN 3 THEN x'13' ELSE `target_col` END WHERE `id` IN (1, 3, 5);
DELETE FROM `tab_tucr_000069_ref` WHERE `id` IN (2, 4);
INSERT INTO `tab_tucr_000069_ref` (`id`, `target_col`) VALUES
  (8, x'07');
-- INPLACE DDL
ALTER TABLE `tab_tucr_000069_inplace` MODIFY `target_col` BINARY(1) NULL, ALGORITHM=INPLACE, LOCK=NONE;
-- INPLACE post-DDL deterministic DML
INSERT INTO `tab_tucr_000069_inplace` (`id`, `target_col`) VALUES
  (6, REPEAT(x'05', 1)),
  (7, x'');
UPDATE `tab_tucr_000069_inplace` SET `target_col` = CASE `id` WHEN 1 THEN x'11' WHEN 3 THEN x'13' ELSE `target_col` END WHERE `id` IN (1, 3, 5);
DELETE FROM `tab_tucr_000069_inplace` WHERE `id` IN (2, 4);
INSERT INTO `tab_tucr_000069_inplace` (`id`, `target_col`) VALUES
  (8, x'07');
-- INPLACE stable result
SELECT 'TUCR-000069' AS case_id, 'INPLACE' AS algorithm, (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000069_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000069_inplace') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000069_inplace' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000069_ref')) AS schema_diff) AS schema_diff_count, (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000069_inplace`) - (SELECT COUNT(*) FROM `tab_tucr_000069_ref`))) AS row_count_diff, (SELECT COUNT(*) FROM `tab_tucr_000069_inplace` c LEFT JOIN `tab_tucr_000069_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col))) AS mismatch_count, (SELECT COUNT(*) FROM `tab_tucr_000069_ref` r LEFT JOIN `tab_tucr_000069_inplace` c ON c.`id`=r.`id` WHERE c.`id` IS NULL) AS extra_count, CASE WHEN (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000069_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000069_inplace') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000069_inplace' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000069_ref')) AS schema_diff)=0 AND (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000069_inplace`) - (SELECT COUNT(*) FROM `tab_tucr_000069_ref`)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000069_inplace` c LEFT JOIN `tab_tucr_000069_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000069_ref` r LEFT JOIN `tab_tucr_000069_inplace` c ON c.`id`=r.`id` WHERE c.`id` IS NULL)=0 THEN 'PASS' ELSE 'FAIL' END AS result;
-- INSTANT DDL
ALTER TABLE `tab_tucr_000069_instant` MODIFY `target_col` BINARY(1) NULL, ALGORITHM=INSTANT;
-- INSTANT post-DDL deterministic DML
INSERT INTO `tab_tucr_000069_instant` (`id`, `target_col`) VALUES
  (6, REPEAT(x'05', 1)),
  (7, x'');
UPDATE `tab_tucr_000069_instant` SET `target_col` = CASE `id` WHEN 1 THEN x'11' WHEN 3 THEN x'13' ELSE `target_col` END WHERE `id` IN (1, 3, 5);
DELETE FROM `tab_tucr_000069_instant` WHERE `id` IN (2, 4);
INSERT INTO `tab_tucr_000069_instant` (`id`, `target_col`) VALUES
  (8, x'07');
-- INSTANT stable result
SELECT 'TUCR-000069' AS case_id, 'INSTANT' AS algorithm, (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000069_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000069_instant') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000069_instant' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000069_ref')) AS schema_diff) AS schema_diff_count, (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000069_instant`) - (SELECT COUNT(*) FROM `tab_tucr_000069_ref`))) AS row_count_diff, (SELECT COUNT(*) FROM `tab_tucr_000069_instant` c LEFT JOIN `tab_tucr_000069_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col))) AS mismatch_count, (SELECT COUNT(*) FROM `tab_tucr_000069_ref` r LEFT JOIN `tab_tucr_000069_instant` c ON c.`id`=r.`id` WHERE c.`id` IS NULL) AS extra_count, CASE WHEN (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000069_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000069_instant') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000069_instant' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000069_ref')) AS schema_diff)=0 AND (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000069_instant`) - (SELECT COUNT(*) FROM `tab_tucr_000069_ref`)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000069_instant` c LEFT JOIN `tab_tucr_000069_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000069_ref` r LEFT JOIN `tab_tucr_000069_instant` c ON c.`id`=r.`id` WHERE c.`id` IS NULL)=0 THEN 'PASS' ELSE 'FAIL' END AS result;
-- final cleanup
DROP TABLE IF EXISTS `tab_tucr_000069_inplace`;
DROP TABLE IF EXISTS `tab_tucr_000069_instant`;
DROP TABLE IF EXISTS `tab_tucr_000069_ref`;
