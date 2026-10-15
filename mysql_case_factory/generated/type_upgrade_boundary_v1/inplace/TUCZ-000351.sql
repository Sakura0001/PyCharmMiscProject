-- --------------------------------------------------------
-- author       : yuzhengwen y00938623
-- create at    : 2026-10-15
-- description  : 场景 TUCZ-000351 BINARY(0) -> VARBINARY(1) -> VARBINARY(2)
-- FE           : FE2026081100174
-- BATCH_ID: 2026-10-15-type-upgrade-boundary-v1
-- BATCH_KIND: boundary_extension
-- --------------------------------------------------------
-- CASE_ID: TUCZ-000351
-- PROFILE: inplace
-- 判定：两阶段升级后，升级前数据、第一阶段升级后写入数据、最终结构、索引、外键和统计信息全部一致。
-- 运行：mysql --batch --raw --skip-column-names --force，输出必须与 expected_output.tsv 一致。
-- pre-cleanup
DROP TABLE IF EXISTS tab_tucz_351_algo;
DROP TABLE IF EXISTS tab_tucz_351_ref;
-- create objects
CREATE TABLE tab_tucz_351_ref (v VARBINARY(2) NOT NULL DEFAULT x'00', id BIGINT NOT NULL, c VARCHAR(50) DEFAULT NULL, d CHAR(20) DEFAULT NULL, e INT DEFAULT NULL, f BIGINT DEFAULT NULL, KEY idx_tucz_351_v (v), PRIMARY KEY (id)) ENGINE=InnoDB ROW_FORMAT=COMPRESSED DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE tab_tucz_351_algo (id BIGINT NOT NULL, v BINARY(0) NOT NULL DEFAULT x'', c VARCHAR(50) DEFAULT NULL, d CHAR(20) DEFAULT NULL, e INT DEFAULT NULL, f BIGINT DEFAULT NULL, PRIMARY KEY (id)) ENGINE=InnoDB ROW_FORMAT=COMPRESSED DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- seed data before first upgrade
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (1, x'', 'canary-001', 'dddd-001', 111, 1111111111);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (2, x'', 'canary-002', 'dddd-002', 222, 2222222222);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (3, x'', 'canary-003', 'dddd-003', 333, 3333333333);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (4, x'', 'canary-004', 'dddd-004', 444, 4444444444);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (5, x'', 'canary-005', 'dddd-005', 555, 5555555555);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (6, x'', 'canary-006', 'dddd-006', 666, 6666666666);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (7, x'', 'canary-007', 'dddd-007', 777, 7777777777);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (8, x'', 'canary-008', 'dddd-008', 888, 8888888888);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (9, x'', 'canary-009', 'dddd-009', 999, 9999999999);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (10, x'', 'canary-010', 'dddd-010', 1110, 11111111110);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (11, x'', 'canary-011', 'dddd-011', 1221, 12222222221);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (12, x'', 'canary-012', 'dddd-012', 1332, 13333333332);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (13, x'', 'canary-013', 'dddd-013', 1443, 14444444443);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (14, x'', 'canary-014', 'dddd-014', 1554, 15555555554);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (15, x'', 'canary-015', 'dddd-015', 1665, 16666666665);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (16, x'', 'canary-016', 'dddd-016', 1776, 17777777776);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (17, x'', 'canary-017', 'dddd-017', 1887, 18888888887);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (18, x'', 'canary-018', 'dddd-018', 1998, 19999999998);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (19, x'', 'canary-019', 'dddd-019', 2109, 21111111109);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (20, x'', 'canary-020', 'dddd-020', 2220, 22222222220);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (21, x'', 'canary-021', 'dddd-021', 2331, 23333333331);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (22, x'', 'canary-022', 'dddd-022', 2442, 24444444442);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (23, x'', 'canary-023', 'dddd-023', 2553, 25555555553);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (24, x'', 'canary-024', 'dddd-024', 2664, 26666666664);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (1, x'', 'canary-001', 'dddd-001', 111, 1111111111);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (2, x'', 'canary-002', 'dddd-002', 222, 2222222222);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (3, x'', 'canary-003', 'dddd-003', 333, 3333333333);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (4, x'', 'canary-004', 'dddd-004', 444, 4444444444);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (5, x'', 'canary-005', 'dddd-005', 555, 5555555555);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (6, x'', 'canary-006', 'dddd-006', 666, 6666666666);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (7, x'', 'canary-007', 'dddd-007', 777, 7777777777);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (8, x'', 'canary-008', 'dddd-008', 888, 8888888888);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (9, x'', 'canary-009', 'dddd-009', 999, 9999999999);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (10, x'', 'canary-010', 'dddd-010', 1110, 11111111110);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (11, x'', 'canary-011', 'dddd-011', 1221, 12222222221);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (12, x'', 'canary-012', 'dddd-012', 1332, 13333333332);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (13, x'', 'canary-013', 'dddd-013', 1443, 14444444443);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (14, x'', 'canary-014', 'dddd-014', 1554, 15555555554);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (15, x'', 'canary-015', 'dddd-015', 1665, 16666666665);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (16, x'', 'canary-016', 'dddd-016', 1776, 17777777776);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (17, x'', 'canary-017', 'dddd-017', 1887, 18888888887);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (18, x'', 'canary-018', 'dddd-018', 1998, 19999999998);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (19, x'', 'canary-019', 'dddd-019', 2109, 21111111109);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (20, x'', 'canary-020', 'dddd-020', 2220, 22222222220);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (21, x'', 'canary-021', 'dddd-021', 2331, 23333333331);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (22, x'', 'canary-022', 'dddd-022', 2442, 24444444442);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (23, x'', 'canary-023', 'dddd-023', 2553, 25555555553);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (24, x'', 'canary-024', 'dddd-024', 2664, 26666666664);
ALTER TABLE tab_tucz_351_algo MODIFY v VARBINARY(1) NOT NULL DEFAULT x'00' FIRST, ADD KEY idx_tucz_351_v (v), ALGORITHM=INPLACE;
-- post-first-upgrade target-boundary data
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (101, x'00', 'canary-101', 'dddd-101', 11211, 112222222211);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (102, x'01', 'canary-102', 'dddd-102', 11322, 113333333322);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (103, x'7f', 'canary-103', 'dddd-103', 11433, 114444444433);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (104, x'ff', 'canary-104', 'dddd-104', 11544, 115555555544);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (105, x'00', 'canary-105', 'dddd-105', 11655, 116666666655);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (106, x'01', 'canary-106', 'dddd-106', 11766, 117777777766);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (107, x'7f', 'canary-107', 'dddd-107', 11877, 118888888877);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (108, x'ff', 'canary-108', 'dddd-108', 11988, 119999999988);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (109, x'00', 'canary-109', 'dddd-109', 12099, 121111111099);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (110, x'01', 'canary-110', 'dddd-110', 12210, 122222222210);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (111, x'7f', 'canary-111', 'dddd-111', 12321, 123333333321);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (112, x'ff', 'canary-112', 'dddd-112', 12432, 124444444432);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (113, x'00', 'canary-113', 'dddd-113', 12543, 125555555543);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (114, x'01', 'canary-114', 'dddd-114', 12654, 126666666654);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (115, x'7f', 'canary-115', 'dddd-115', 12765, 127777777765);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (116, x'ff', 'canary-116', 'dddd-116', 12876, 128888888876);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (117, x'00', 'canary-117', 'dddd-117', 12987, 129999999987);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (118, x'01', 'canary-118', 'dddd-118', 13098, 131111111098);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (119, x'7f', 'canary-119', 'dddd-119', 13209, 132222222209);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (120, x'ff', 'canary-120', 'dddd-120', 13320, 133333333320);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (121, x'00', 'canary-121', 'dddd-121', 13431, 134444444431);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (122, x'01', 'canary-122', 'dddd-122', 13542, 135555555542);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (123, x'7f', 'canary-123', 'dddd-123', 13653, 136666666653);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (124, x'ff', 'canary-124', 'dddd-124', 13764, 137777777764);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (101, x'00', 'canary-101', 'dddd-101', 11211, 112222222211);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (102, x'01', 'canary-102', 'dddd-102', 11322, 113333333322);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (103, x'7f', 'canary-103', 'dddd-103', 11433, 114444444433);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (104, x'ff', 'canary-104', 'dddd-104', 11544, 115555555544);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (105, x'00', 'canary-105', 'dddd-105', 11655, 116666666655);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (106, x'01', 'canary-106', 'dddd-106', 11766, 117777777766);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (107, x'7f', 'canary-107', 'dddd-107', 11877, 118888888877);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (108, x'ff', 'canary-108', 'dddd-108', 11988, 119999999988);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (109, x'00', 'canary-109', 'dddd-109', 12099, 121111111099);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (110, x'01', 'canary-110', 'dddd-110', 12210, 122222222210);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (111, x'7f', 'canary-111', 'dddd-111', 12321, 123333333321);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (112, x'ff', 'canary-112', 'dddd-112', 12432, 124444444432);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (113, x'00', 'canary-113', 'dddd-113', 12543, 125555555543);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (114, x'01', 'canary-114', 'dddd-114', 12654, 126666666654);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (115, x'7f', 'canary-115', 'dddd-115', 12765, 127777777765);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (116, x'ff', 'canary-116', 'dddd-116', 12876, 128888888876);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (117, x'00', 'canary-117', 'dddd-117', 12987, 129999999987);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (118, x'01', 'canary-118', 'dddd-118', 13098, 131111111098);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (119, x'7f', 'canary-119', 'dddd-119', 13209, 132222222209);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (120, x'ff', 'canary-120', 'dddd-120', 13320, 133333333320);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (121, x'00', 'canary-121', 'dddd-121', 13431, 134444444431);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (122, x'01', 'canary-122', 'dddd-122', 13542, 135555555542);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (123, x'7f', 'canary-123', 'dddd-123', 13653, 136666666653);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (124, x'ff', 'canary-124', 'dddd-124', 13764, 137777777764);
ALTER TABLE tab_tucz_351_algo MODIFY v VARBINARY(2) NOT NULL DEFAULT x'00' FIRST, ALGORITHM=INPLACE;
-- post-second-upgrade final-boundary data
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (201, x'0000', 'canary-201', 'dddd-201', 22311, 223333333311);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (202, x'0101', 'canary-202', 'dddd-202', 22422, 224444444422);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (203, x'7f7f', 'canary-203', 'dddd-203', 22533, 225555555533);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (204, x'ffff', 'canary-204', 'dddd-204', 22644, 226666666644);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (205, x'0000', 'canary-205', 'dddd-205', 22755, 227777777755);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (206, x'0101', 'canary-206', 'dddd-206', 22866, 228888888866);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (207, x'7f7f', 'canary-207', 'dddd-207', 22977, 229999999977);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (208, x'ffff', 'canary-208', 'dddd-208', 23088, 231111111088);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (209, x'0000', 'canary-209', 'dddd-209', 23199, 232222222199);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (210, x'0101', 'canary-210', 'dddd-210', 23310, 233333333310);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (211, x'7f7f', 'canary-211', 'dddd-211', 23421, 234444444421);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (212, x'ffff', 'canary-212', 'dddd-212', 23532, 235555555532);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (213, x'0000', 'canary-213', 'dddd-213', 23643, 236666666643);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (214, x'0101', 'canary-214', 'dddd-214', 23754, 237777777754);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (215, x'7f7f', 'canary-215', 'dddd-215', 23865, 238888888865);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (216, x'ffff', 'canary-216', 'dddd-216', 23976, 239999999976);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (217, x'0000', 'canary-217', 'dddd-217', 24087, 241111111087);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (218, x'0101', 'canary-218', 'dddd-218', 24198, 242222222198);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (219, x'7f7f', 'canary-219', 'dddd-219', 24309, 243333333309);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (220, x'ffff', 'canary-220', 'dddd-220', 24420, 244444444420);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (221, x'0000', 'canary-221', 'dddd-221', 24531, 245555555531);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (222, x'0101', 'canary-222', 'dddd-222', 24642, 246666666642);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (223, x'7f7f', 'canary-223', 'dddd-223', 24753, 247777777753);
INSERT INTO tab_tucz_351_ref (id,v,c,d,e,f) VALUES (224, x'ffff', 'canary-224', 'dddd-224', 24864, 248888888864);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (201, x'0000', 'canary-201', 'dddd-201', 22311, 223333333311);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (202, x'0101', 'canary-202', 'dddd-202', 22422, 224444444422);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (203, x'7f7f', 'canary-203', 'dddd-203', 22533, 225555555533);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (204, x'ffff', 'canary-204', 'dddd-204', 22644, 226666666644);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (205, x'0000', 'canary-205', 'dddd-205', 22755, 227777777755);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (206, x'0101', 'canary-206', 'dddd-206', 22866, 228888888866);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (207, x'7f7f', 'canary-207', 'dddd-207', 22977, 229999999977);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (208, x'ffff', 'canary-208', 'dddd-208', 23088, 231111111088);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (209, x'0000', 'canary-209', 'dddd-209', 23199, 232222222199);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (210, x'0101', 'canary-210', 'dddd-210', 23310, 233333333310);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (211, x'7f7f', 'canary-211', 'dddd-211', 23421, 234444444421);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (212, x'ffff', 'canary-212', 'dddd-212', 23532, 235555555532);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (213, x'0000', 'canary-213', 'dddd-213', 23643, 236666666643);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (214, x'0101', 'canary-214', 'dddd-214', 23754, 237777777754);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (215, x'7f7f', 'canary-215', 'dddd-215', 23865, 238888888865);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (216, x'ffff', 'canary-216', 'dddd-216', 23976, 239999999976);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (217, x'0000', 'canary-217', 'dddd-217', 24087, 241111111087);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (218, x'0101', 'canary-218', 'dddd-218', 24198, 242222222198);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (219, x'7f7f', 'canary-219', 'dddd-219', 24309, 243333333309);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (220, x'ffff', 'canary-220', 'dddd-220', 24420, 244444444420);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (221, x'0000', 'canary-221', 'dddd-221', 24531, 245555555531);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (222, x'0101', 'canary-222', 'dddd-222', 24642, 246666666642);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (223, x'7f7f', 'canary-223', 'dddd-223', 24753, 247777777753);
INSERT INTO tab_tucz_351_algo (id,v,c,d,e,f) VALUES (224, x'ffff', 'canary-224', 'dddd-224', 24864, 248888888864);
-- deterministic assertions
SELECT CASE WHEN NOT EXISTS ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucz_351_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucz_351_algo') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucz_351_algo' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucz_351_ref') LIMIT 1) THEN 'TUCZ-000351|SCHEMA|OK' ELSE 'TUCZ-000351|SCHEMA|FAIL' END;
SELECT CASE WHEN NOT EXISTS (SELECT 1 FROM tab_tucz_351_ref r LEFT JOIN tab_tucz_351_algo a USING(id) WHERE a.id IS NULL UNION ALL SELECT 1 FROM tab_tucz_351_algo a LEFT JOIN tab_tucz_351_ref r USING(id) WHERE r.id IS NULL UNION ALL SELECT 1 FROM tab_tucz_351_ref r JOIN tab_tucz_351_algo a USING(id) WHERE NOT (r.v <=> a.v AND  r.c <=> a.c AND r.d <=> a.d AND r.e <=> a.e AND r.f <=> a.f) LIMIT 1) THEN 'TUCZ-000351|DATA|OK' ELSE 'TUCZ-000351|DATA|FAIL' END;
SELECT CASE WHEN NOT EXISTS ((SELECT index_name, non_unique, seq_in_index, column_name, collation, sub_part, packed, nullable, index_type, comment, index_comment, expression FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='tab_tucz_351_ref' EXCEPT SELECT index_name, non_unique, seq_in_index, column_name, collation, sub_part, packed, nullable, index_type, comment, index_comment, expression FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='tab_tucz_351_algo') UNION ALL (SELECT index_name, non_unique, seq_in_index, column_name, collation, sub_part, packed, nullable, index_type, comment, index_comment, expression FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='tab_tucz_351_algo' EXCEPT SELECT index_name, non_unique, seq_in_index, column_name, collation, sub_part, packed, nullable, index_type, comment, index_comment, expression FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='tab_tucz_351_ref') LIMIT 1) THEN 'TUCZ-000351|INDEX|OK' ELSE 'TUCZ-000351|INDEX|FAIL' END;
-- final cleanup
DROP TABLE IF EXISTS tab_tucz_351_algo;
DROP TABLE IF EXISTS tab_tucz_351_ref;
