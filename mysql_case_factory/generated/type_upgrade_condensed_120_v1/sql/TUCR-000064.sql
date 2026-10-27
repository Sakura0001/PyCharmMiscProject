-- --------------------------------------------------------
-- author       : yuzhengwen y00938623
-- create at    : 2026-10-27
-- description  : TINYBLOB to BLOB
-- FE           : FE2026081100174
-- --------------------------------------------------------

-- pre-cleanup
DROP TABLE IF EXISTS `tab_tucr_000064_inplace`;
DROP TABLE IF EXISTS `tab_tucr_000064_instant`;
DROP TABLE IF EXISTS `tab_tucr_000064_ref`;
-- create inplace and instant source candidates
CREATE TABLE `tab_tucr_000064_inplace` (
  `id` BIGINT NOT NULL,
  `target_col` TINYBLOB NULL,
  PRIMARY KEY (`id`),
  KEY `idx_tucr_000064_target` (`target_col`(32))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE `tab_tucr_000064_instant` (
  `id` BIGINT NOT NULL,
  `target_col` TINYBLOB NULL,
  PRIMARY KEY (`id`),
  KEY `idx_tucr_000064_target` (`target_col`(32))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- create direct target reference
CREATE TABLE `tab_tucr_000064_ref` (
  `id` BIGINT NOT NULL,
  `target_col` BLOB NULL,
  PRIMARY KEY (`id`),
  KEY `idx_tucr_000064_target` (`target_col`(32))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- seed deterministic rows
INSERT INTO `tab_tucr_000064_inplace` (`id`, `target_col`) VALUES
  (1, x'01'),
  (2, REPEAT(x'02', 255)),
  (3, REPEAT(x'03', 255)),
  (4, NULL),
  (5, REPEAT(x'04', 255));
INSERT INTO `tab_tucr_000064_instant` (`id`, `target_col`) VALUES
  (1, x'01'),
  (2, REPEAT(x'02', 255)),
  (3, REPEAT(x'03', 255)),
  (4, NULL),
  (5, REPEAT(x'04', 255));
INSERT INTO `tab_tucr_000064_ref` (`id`, `target_col`) VALUES
  (1, x'01'),
  (2, REPEAT(x'02', 255)),
  (3, REPEAT(x'03', 255)),
  (4, NULL),
  (5, REPEAT(x'04', 255));
-- direct reference deterministic DML (executed once)
INSERT INTO `tab_tucr_000064_ref` (`id`, `target_col`) VALUES
  (6, REPEAT(x'05', 4096)),
  (7, REPEAT(x'06', 4095));
UPDATE `tab_tucr_000064_ref` SET `target_col` = CASE `id` WHEN 1 THEN x'11' WHEN 3 THEN x'13' ELSE `target_col` END WHERE `id` IN (1, 3, 5);
DELETE FROM `tab_tucr_000064_ref` WHERE `id` IN (2, 4);
INSERT INTO `tab_tucr_000064_ref` (`id`, `target_col`) VALUES
  (8, x'07');
-- INPLACE DDL
ALTER TABLE `tab_tucr_000064_inplace` MODIFY `target_col` BLOB NULL, ALGORITHM=INPLACE, LOCK=NONE;
-- INPLACE post-DDL deterministic DML
INSERT INTO `tab_tucr_000064_inplace` (`id`, `target_col`) VALUES
  (6, REPEAT(x'05', 4096)),
  (7, REPEAT(x'06', 4095));
UPDATE `tab_tucr_000064_inplace` SET `target_col` = CASE `id` WHEN 1 THEN x'11' WHEN 3 THEN x'13' ELSE `target_col` END WHERE `id` IN (1, 3, 5);
DELETE FROM `tab_tucr_000064_inplace` WHERE `id` IN (2, 4);
INSERT INTO `tab_tucr_000064_inplace` (`id`, `target_col`) VALUES
  (8, x'07');
-- INPLACE stable result
SELECT 'TUCR-000064' AS case_id, 'INPLACE' AS algorithm, (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000064_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000064_inplace') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000064_inplace' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000064_ref')) AS schema_diff) AS schema_diff_count, (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000064_inplace`) - (SELECT COUNT(*) FROM `tab_tucr_000064_ref`))) AS row_count_diff, (SELECT COUNT(*) FROM `tab_tucr_000064_inplace` c LEFT JOIN `tab_tucr_000064_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col))) AS mismatch_count, (SELECT COUNT(*) FROM `tab_tucr_000064_ref` r LEFT JOIN `tab_tucr_000064_inplace` c ON c.`id`=r.`id` WHERE c.`id` IS NULL) AS extra_count, CASE WHEN (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000064_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000064_inplace') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000064_inplace' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000064_ref')) AS schema_diff)=0 AND (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000064_inplace`) - (SELECT COUNT(*) FROM `tab_tucr_000064_ref`)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000064_inplace` c LEFT JOIN `tab_tucr_000064_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000064_ref` r LEFT JOIN `tab_tucr_000064_inplace` c ON c.`id`=r.`id` WHERE c.`id` IS NULL)=0 THEN 'PASS' ELSE 'FAIL' END AS result;
-- INSTANT DDL
ALTER TABLE `tab_tucr_000064_instant` MODIFY `target_col` BLOB NULL, ALGORITHM=INSTANT;
-- INSTANT post-DDL deterministic DML
INSERT INTO `tab_tucr_000064_instant` (`id`, `target_col`) VALUES
  (6, REPEAT(x'05', 4096)),
  (7, REPEAT(x'06', 4095));
UPDATE `tab_tucr_000064_instant` SET `target_col` = CASE `id` WHEN 1 THEN x'11' WHEN 3 THEN x'13' ELSE `target_col` END WHERE `id` IN (1, 3, 5);
DELETE FROM `tab_tucr_000064_instant` WHERE `id` IN (2, 4);
INSERT INTO `tab_tucr_000064_instant` (`id`, `target_col`) VALUES
  (8, x'07');
-- INSTANT stable result
SELECT 'TUCR-000064' AS case_id, 'INSTANT' AS algorithm, (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000064_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000064_instant') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000064_instant' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000064_ref')) AS schema_diff) AS schema_diff_count, (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000064_instant`) - (SELECT COUNT(*) FROM `tab_tucr_000064_ref`))) AS row_count_diff, (SELECT COUNT(*) FROM `tab_tucr_000064_instant` c LEFT JOIN `tab_tucr_000064_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col))) AS mismatch_count, (SELECT COUNT(*) FROM `tab_tucr_000064_ref` r LEFT JOIN `tab_tucr_000064_instant` c ON c.`id`=r.`id` WHERE c.`id` IS NULL) AS extra_count, CASE WHEN (SELECT COUNT(*) FROM ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000064_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000064_instant') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000064_instant' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucr_000064_ref')) AS schema_diff)=0 AND (SELECT ABS((SELECT COUNT(*) FROM `tab_tucr_000064_instant`) - (SELECT COUNT(*) FROM `tab_tucr_000064_ref`)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000064_instant` c LEFT JOIN `tab_tucr_000064_ref` r ON r.`id`=c.`id` WHERE r.`id` IS NULL OR NOT ((c.id <=> r.id) AND (c.target_col <=> r.target_col)))=0 AND (SELECT COUNT(*) FROM `tab_tucr_000064_ref` r LEFT JOIN `tab_tucr_000064_instant` c ON c.`id`=r.`id` WHERE c.`id` IS NULL)=0 THEN 'PASS' ELSE 'FAIL' END AS result;
-- final cleanup
DROP TABLE IF EXISTS `tab_tucr_000064_inplace`;
DROP TABLE IF EXISTS `tab_tucr_000064_instant`;
DROP TABLE IF EXISTS `tab_tucr_000064_ref`;
