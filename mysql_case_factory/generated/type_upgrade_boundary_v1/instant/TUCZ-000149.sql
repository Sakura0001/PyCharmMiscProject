-- --------------------------------------------------------
-- author       : yuzhengwen y00938623
-- create at    : 2026-10-15
-- description  : 场景 TUCZ-000149 VARCHAR(0) -> VARCHAR(1) -> VARCHAR(2)
-- FE           : FE2026081100174
-- BATCH_ID: 2026-10-15-type-upgrade-boundary-v1
-- BATCH_KIND: boundary_extension
-- --------------------------------------------------------
-- CASE_ID: TUCZ-000149
-- PROFILE: instant
-- 判定：两阶段升级后，升级前数据、第一阶段升级后写入数据、最终结构、索引、外键和统计信息全部一致。
-- 运行：mysql --batch --raw --skip-column-names --force，输出必须与 expected_output.tsv 一致。
-- pre-cleanup
DROP TABLE IF EXISTS tab_tucz_149_algo;
DROP TABLE IF EXISTS tab_tucz_149_ref;
-- create objects
CREATE TABLE tab_tucz_149_ref (id BIGINT NOT NULL, v VARCHAR(2) NOT NULL DEFAULT '', c VARCHAR(50) DEFAULT NULL, d CHAR(20) DEFAULT NULL, e INT DEFAULT NULL, f BIGINT DEFAULT NULL, PRIMARY KEY (id)) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;
CREATE TABLE tab_tucz_149_algo (id BIGINT NOT NULL, v VARCHAR(0) NOT NULL DEFAULT '', c VARCHAR(50) DEFAULT NULL, d CHAR(20) DEFAULT NULL, e INT DEFAULT NULL, f BIGINT DEFAULT NULL, PRIMARY KEY (id)) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;
-- seed data before first upgrade
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (1, '', 'canary-001', 'dddd-001', 111, 1111111111);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (2, '', 'canary-002', 'dddd-002', 222, 2222222222);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (3, '', 'canary-003', 'dddd-003', 333, 3333333333);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (4, '', 'canary-004', 'dddd-004', 444, 4444444444);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (5, '', 'canary-005', 'dddd-005', 555, 5555555555);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (6, '', 'canary-006', 'dddd-006', 666, 6666666666);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (7, '', 'canary-007', 'dddd-007', 777, 7777777777);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (8, '', 'canary-008', 'dddd-008', 888, 8888888888);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (9, '', 'canary-009', 'dddd-009', 999, 9999999999);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (10, '', 'canary-010', 'dddd-010', 1110, 11111111110);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (11, '', 'canary-011', 'dddd-011', 1221, 12222222221);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (12, '', 'canary-012', 'dddd-012', 1332, 13333333332);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (13, '', 'canary-013', 'dddd-013', 1443, 14444444443);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (14, '', 'canary-014', 'dddd-014', 1554, 15555555554);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (15, '', 'canary-015', 'dddd-015', 1665, 16666666665);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (16, '', 'canary-016', 'dddd-016', 1776, 17777777776);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (17, '', 'canary-017', 'dddd-017', 1887, 18888888887);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (18, '', 'canary-018', 'dddd-018', 1998, 19999999998);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (19, '', 'canary-019', 'dddd-019', 2109, 21111111109);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (20, '', 'canary-020', 'dddd-020', 2220, 22222222220);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (21, '', 'canary-021', 'dddd-021', 2331, 23333333331);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (22, '', 'canary-022', 'dddd-022', 2442, 24444444442);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (23, '', 'canary-023', 'dddd-023', 2553, 25555555553);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (24, '', 'canary-024', 'dddd-024', 2664, 26666666664);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (1, '', 'canary-001', 'dddd-001', 111, 1111111111);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (2, '', 'canary-002', 'dddd-002', 222, 2222222222);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (3, '', 'canary-003', 'dddd-003', 333, 3333333333);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (4, '', 'canary-004', 'dddd-004', 444, 4444444444);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (5, '', 'canary-005', 'dddd-005', 555, 5555555555);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (6, '', 'canary-006', 'dddd-006', 666, 6666666666);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (7, '', 'canary-007', 'dddd-007', 777, 7777777777);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (8, '', 'canary-008', 'dddd-008', 888, 8888888888);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (9, '', 'canary-009', 'dddd-009', 999, 9999999999);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (10, '', 'canary-010', 'dddd-010', 1110, 11111111110);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (11, '', 'canary-011', 'dddd-011', 1221, 12222222221);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (12, '', 'canary-012', 'dddd-012', 1332, 13333333332);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (13, '', 'canary-013', 'dddd-013', 1443, 14444444443);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (14, '', 'canary-014', 'dddd-014', 1554, 15555555554);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (15, '', 'canary-015', 'dddd-015', 1665, 16666666665);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (16, '', 'canary-016', 'dddd-016', 1776, 17777777776);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (17, '', 'canary-017', 'dddd-017', 1887, 18888888887);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (18, '', 'canary-018', 'dddd-018', 1998, 19999999998);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (19, '', 'canary-019', 'dddd-019', 2109, 21111111109);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (20, '', 'canary-020', 'dddd-020', 2220, 22222222220);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (21, '', 'canary-021', 'dddd-021', 2331, 23333333331);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (22, '', 'canary-022', 'dddd-022', 2442, 24444444442);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (23, '', 'canary-023', 'dddd-023', 2553, 25555555553);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (24, '', 'canary-024', 'dddd-024', 2664, 26666666664);
ALTER TABLE tab_tucz_149_algo MODIFY v VARCHAR(1) NOT NULL DEFAULT '' AFTER id, ALGORITHM=INSTANT;
-- post-first-upgrade target-boundary data
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (101, 'a', 'canary-101', 'dddd-101', 11211, 112222222211);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (102, 'b', 'canary-102', 'dddd-102', 11322, 113333333322);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (103, 'c', 'canary-103', 'dddd-103', 11433, 114444444433);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (104, 'd', 'canary-104', 'dddd-104', 11544, 115555555544);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (105, 'a', 'canary-105', 'dddd-105', 11655, 116666666655);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (106, 'b', 'canary-106', 'dddd-106', 11766, 117777777766);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (107, 'c', 'canary-107', 'dddd-107', 11877, 118888888877);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (108, 'd', 'canary-108', 'dddd-108', 11988, 119999999988);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (109, 'a', 'canary-109', 'dddd-109', 12099, 121111111099);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (110, 'b', 'canary-110', 'dddd-110', 12210, 122222222210);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (111, 'c', 'canary-111', 'dddd-111', 12321, 123333333321);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (112, 'd', 'canary-112', 'dddd-112', 12432, 124444444432);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (113, 'a', 'canary-113', 'dddd-113', 12543, 125555555543);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (114, 'b', 'canary-114', 'dddd-114', 12654, 126666666654);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (115, 'c', 'canary-115', 'dddd-115', 12765, 127777777765);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (116, 'd', 'canary-116', 'dddd-116', 12876, 128888888876);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (117, 'a', 'canary-117', 'dddd-117', 12987, 129999999987);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (118, 'b', 'canary-118', 'dddd-118', 13098, 131111111098);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (119, 'c', 'canary-119', 'dddd-119', 13209, 132222222209);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (120, 'd', 'canary-120', 'dddd-120', 13320, 133333333320);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (121, 'a', 'canary-121', 'dddd-121', 13431, 134444444431);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (122, 'b', 'canary-122', 'dddd-122', 13542, 135555555542);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (123, 'c', 'canary-123', 'dddd-123', 13653, 136666666653);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (124, 'd', 'canary-124', 'dddd-124', 13764, 137777777764);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (101, 'a', 'canary-101', 'dddd-101', 11211, 112222222211);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (102, 'b', 'canary-102', 'dddd-102', 11322, 113333333322);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (103, 'c', 'canary-103', 'dddd-103', 11433, 114444444433);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (104, 'd', 'canary-104', 'dddd-104', 11544, 115555555544);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (105, 'a', 'canary-105', 'dddd-105', 11655, 116666666655);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (106, 'b', 'canary-106', 'dddd-106', 11766, 117777777766);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (107, 'c', 'canary-107', 'dddd-107', 11877, 118888888877);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (108, 'd', 'canary-108', 'dddd-108', 11988, 119999999988);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (109, 'a', 'canary-109', 'dddd-109', 12099, 121111111099);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (110, 'b', 'canary-110', 'dddd-110', 12210, 122222222210);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (111, 'c', 'canary-111', 'dddd-111', 12321, 123333333321);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (112, 'd', 'canary-112', 'dddd-112', 12432, 124444444432);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (113, 'a', 'canary-113', 'dddd-113', 12543, 125555555543);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (114, 'b', 'canary-114', 'dddd-114', 12654, 126666666654);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (115, 'c', 'canary-115', 'dddd-115', 12765, 127777777765);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (116, 'd', 'canary-116', 'dddd-116', 12876, 128888888876);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (117, 'a', 'canary-117', 'dddd-117', 12987, 129999999987);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (118, 'b', 'canary-118', 'dddd-118', 13098, 131111111098);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (119, 'c', 'canary-119', 'dddd-119', 13209, 132222222209);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (120, 'd', 'canary-120', 'dddd-120', 13320, 133333333320);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (121, 'a', 'canary-121', 'dddd-121', 13431, 134444444431);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (122, 'b', 'canary-122', 'dddd-122', 13542, 135555555542);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (123, 'c', 'canary-123', 'dddd-123', 13653, 136666666653);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (124, 'd', 'canary-124', 'dddd-124', 13764, 137777777764);
ALTER TABLE tab_tucz_149_algo MODIFY v VARCHAR(2) NOT NULL DEFAULT '' AFTER id, ALGORITHM=INSTANT;
-- post-second-upgrade final-boundary data
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (201, 'aa', 'canary-201', 'dddd-201', 22311, 223333333311);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (202, 'bb', 'canary-202', 'dddd-202', 22422, 224444444422);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (203, 'cc', 'canary-203', 'dddd-203', 22533, 225555555533);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (204, 'dd', 'canary-204', 'dddd-204', 22644, 226666666644);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (205, 'aa', 'canary-205', 'dddd-205', 22755, 227777777755);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (206, 'bb', 'canary-206', 'dddd-206', 22866, 228888888866);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (207, 'cc', 'canary-207', 'dddd-207', 22977, 229999999977);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (208, 'dd', 'canary-208', 'dddd-208', 23088, 231111111088);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (209, 'aa', 'canary-209', 'dddd-209', 23199, 232222222199);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (210, 'bb', 'canary-210', 'dddd-210', 23310, 233333333310);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (211, 'cc', 'canary-211', 'dddd-211', 23421, 234444444421);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (212, 'dd', 'canary-212', 'dddd-212', 23532, 235555555532);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (213, 'aa', 'canary-213', 'dddd-213', 23643, 236666666643);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (214, 'bb', 'canary-214', 'dddd-214', 23754, 237777777754);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (215, 'cc', 'canary-215', 'dddd-215', 23865, 238888888865);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (216, 'dd', 'canary-216', 'dddd-216', 23976, 239999999976);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (217, 'aa', 'canary-217', 'dddd-217', 24087, 241111111087);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (218, 'bb', 'canary-218', 'dddd-218', 24198, 242222222198);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (219, 'cc', 'canary-219', 'dddd-219', 24309, 243333333309);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (220, 'dd', 'canary-220', 'dddd-220', 24420, 244444444420);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (221, 'aa', 'canary-221', 'dddd-221', 24531, 245555555531);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (222, 'bb', 'canary-222', 'dddd-222', 24642, 246666666642);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (223, 'cc', 'canary-223', 'dddd-223', 24753, 247777777753);
INSERT INTO tab_tucz_149_ref (id,v,c,d,e,f) VALUES (224, 'dd', 'canary-224', 'dddd-224', 24864, 248888888864);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (201, 'aa', 'canary-201', 'dddd-201', 22311, 223333333311);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (202, 'bb', 'canary-202', 'dddd-202', 22422, 224444444422);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (203, 'cc', 'canary-203', 'dddd-203', 22533, 225555555533);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (204, 'dd', 'canary-204', 'dddd-204', 22644, 226666666644);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (205, 'aa', 'canary-205', 'dddd-205', 22755, 227777777755);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (206, 'bb', 'canary-206', 'dddd-206', 22866, 228888888866);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (207, 'cc', 'canary-207', 'dddd-207', 22977, 229999999977);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (208, 'dd', 'canary-208', 'dddd-208', 23088, 231111111088);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (209, 'aa', 'canary-209', 'dddd-209', 23199, 232222222199);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (210, 'bb', 'canary-210', 'dddd-210', 23310, 233333333310);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (211, 'cc', 'canary-211', 'dddd-211', 23421, 234444444421);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (212, 'dd', 'canary-212', 'dddd-212', 23532, 235555555532);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (213, 'aa', 'canary-213', 'dddd-213', 23643, 236666666643);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (214, 'bb', 'canary-214', 'dddd-214', 23754, 237777777754);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (215, 'cc', 'canary-215', 'dddd-215', 23865, 238888888865);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (216, 'dd', 'canary-216', 'dddd-216', 23976, 239999999976);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (217, 'aa', 'canary-217', 'dddd-217', 24087, 241111111087);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (218, 'bb', 'canary-218', 'dddd-218', 24198, 242222222198);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (219, 'cc', 'canary-219', 'dddd-219', 24309, 243333333309);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (220, 'dd', 'canary-220', 'dddd-220', 24420, 244444444420);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (221, 'aa', 'canary-221', 'dddd-221', 24531, 245555555531);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (222, 'bb', 'canary-222', 'dddd-222', 24642, 246666666642);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (223, 'cc', 'canary-223', 'dddd-223', 24753, 247777777753);
INSERT INTO tab_tucz_149_algo (id,v,c,d,e,f) VALUES (224, 'dd', 'canary-224', 'dddd-224', 24864, 248888888864);
-- deterministic assertions
SELECT CASE WHEN NOT EXISTS ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucz_149_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucz_149_algo') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucz_149_algo' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucz_149_ref') LIMIT 1) THEN 'TUCZ-000149|SCHEMA|OK' ELSE 'TUCZ-000149|SCHEMA|FAIL' END;
SELECT CASE WHEN NOT EXISTS (SELECT 1 FROM tab_tucz_149_ref r LEFT JOIN tab_tucz_149_algo a USING(id) WHERE a.id IS NULL UNION ALL SELECT 1 FROM tab_tucz_149_algo a LEFT JOIN tab_tucz_149_ref r USING(id) WHERE r.id IS NULL UNION ALL SELECT 1 FROM tab_tucz_149_ref r JOIN tab_tucz_149_algo a USING(id) WHERE NOT (r.v <=> a.v AND  r.c <=> a.c AND r.d <=> a.d AND r.e <=> a.e AND r.f <=> a.f) LIMIT 1) THEN 'TUCZ-000149|DATA|OK' ELSE 'TUCZ-000149|DATA|FAIL' END;
SELECT CASE WHEN NOT EXISTS ((SELECT index_name, non_unique, seq_in_index, column_name, collation, sub_part, packed, nullable, index_type, comment, index_comment, expression FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='tab_tucz_149_ref' EXCEPT SELECT index_name, non_unique, seq_in_index, column_name, collation, sub_part, packed, nullable, index_type, comment, index_comment, expression FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='tab_tucz_149_algo') UNION ALL (SELECT index_name, non_unique, seq_in_index, column_name, collation, sub_part, packed, nullable, index_type, comment, index_comment, expression FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='tab_tucz_149_algo' EXCEPT SELECT index_name, non_unique, seq_in_index, column_name, collation, sub_part, packed, nullable, index_type, comment, index_comment, expression FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='tab_tucz_149_ref') LIMIT 1) THEN 'TUCZ-000149|INDEX|OK' ELSE 'TUCZ-000149|INDEX|FAIL' END;
-- final cleanup
DROP TABLE IF EXISTS tab_tucz_149_algo;
DROP TABLE IF EXISTS tab_tucz_149_ref;
