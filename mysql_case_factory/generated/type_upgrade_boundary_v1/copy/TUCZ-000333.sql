-- --------------------------------------------------------
-- author       : yuzhengwen y00938623
-- create at    : 2026-10-15
-- description  : 场景 TUCZ-000333 BINARY(0) -> VARBINARY(1) -> VARBINARY(2)
-- FE           : FE2026081100174
-- BATCH_ID: 2026-10-15-type-upgrade-boundary-v1
-- BATCH_KIND: boundary_extension
-- --------------------------------------------------------
-- CASE_ID: TUCZ-000333
-- PROFILE: copy
-- 判定：两阶段升级后，升级前数据、第一阶段升级后写入数据、最终结构、索引、外键和统计信息全部一致。
-- 运行：mysql --batch --raw --skip-column-names --force，输出必须与 expected_output.tsv 一致。
-- pre-cleanup
DROP TABLE IF EXISTS tab_tucz_333_algo;
DROP TABLE IF EXISTS tab_tucz_333_ref;
DROP TABLE IF EXISTS tab_tucz_333_parent;
-- create objects
CREATE TABLE tab_tucz_333_parent (parent_id BIGINT NOT NULL, payload VARCHAR(32) NOT NULL, PRIMARY KEY(parent_id)) ENGINE=InnoDB;
INSERT INTO tab_tucz_333_parent (parent_id,payload) VALUES (1,'p001'),(2,'p002'),(3,'p003'),(4,'p004'),(5,'p005'),(6,'p006'),(7,'p007'),(8,'p008'),(9,'p009'),(10,'p010'),(11,'p011'),(12,'p012'),(13,'p013'),(14,'p014'),(15,'p015'),(16,'p016'),(17,'p017'),(18,'p018'),(19,'p019'),(20,'p020'),(21,'p021'),(22,'p022'),(23,'p023'),(24,'p024'),(101,'p101'),(102,'p102'),(103,'p103'),(104,'p104'),(105,'p105'),(106,'p106'),(107,'p107'),(108,'p108'),(109,'p109'),(110,'p110'),(111,'p111'),(112,'p112'),(113,'p113'),(114,'p114'),(115,'p115'),(116,'p116'),(117,'p117'),(118,'p118'),(119,'p119'),(120,'p120'),(121,'p121'),(122,'p122'),(123,'p123'),(124,'p124'),(201,'p201'),(202,'p202'),(203,'p203'),(204,'p204'),(205,'p205'),(206,'p206'),(207,'p207'),(208,'p208'),(209,'p209'),(210,'p210'),(211,'p211'),(212,'p212'),(213,'p213'),(214,'p214'),(215,'p215'),(216,'p216'),(217,'p217'),(218,'p218'),(219,'p219'),(220,'p220'),(221,'p221'),(222,'p222'),(223,'p223'),(224,'p224');
CREATE TABLE tab_tucz_333_ref (v VARBINARY(2) NULL, id BIGINT NOT NULL, fk_col BIGINT NULL, c VARCHAR(50) DEFAULT NULL, d CHAR(20) DEFAULT NULL, e INT DEFAULT NULL, f BIGINT DEFAULT NULL, KEY idx_tucz_333_fk (fk_col), KEY idx_tucz_333_v (v), PRIMARY KEY (id)) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE tab_tucz_333_algo (id BIGINT NOT NULL, v BINARY(0) NOT NULL DEFAULT x'', fk_col BIGINT NULL, c VARCHAR(50) DEFAULT NULL, d CHAR(20) DEFAULT NULL, e INT DEFAULT NULL, f BIGINT DEFAULT NULL, KEY idx_tucz_333_fk (fk_col), PRIMARY KEY (id)) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
ALTER TABLE tab_tucz_333_ref ADD CONSTRAINT fk_tucz_333_ref FOREIGN KEY (fk_col) REFERENCES tab_tucz_333_parent(parent_id);
ALTER TABLE tab_tucz_333_algo ADD CONSTRAINT fk_tucz_333_algo FOREIGN KEY (fk_col) REFERENCES tab_tucz_333_parent(parent_id);
-- seed data before first upgrade
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (1, x'', 1, 'canary-001', 'dddd-001', 111, 1111111111);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (2, x'', 2, 'canary-002', 'dddd-002', 222, 2222222222);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (3, x'', 3, 'canary-003', 'dddd-003', 333, 3333333333);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (4, x'', 4, 'canary-004', 'dddd-004', 444, 4444444444);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (5, x'', 5, 'canary-005', 'dddd-005', 555, 5555555555);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (6, x'', 6, 'canary-006', 'dddd-006', 666, 6666666666);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (7, x'', 7, 'canary-007', 'dddd-007', 777, 7777777777);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (8, x'', 8, 'canary-008', 'dddd-008', 888, 8888888888);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (9, x'', 9, 'canary-009', 'dddd-009', 999, 9999999999);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (10, x'', 10, 'canary-010', 'dddd-010', 1110, 11111111110);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (11, x'', 11, 'canary-011', 'dddd-011', 1221, 12222222221);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (12, x'', 12, 'canary-012', 'dddd-012', 1332, 13333333332);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (13, x'', 13, 'canary-013', 'dddd-013', 1443, 14444444443);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (14, x'', 14, 'canary-014', 'dddd-014', 1554, 15555555554);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (15, x'', 15, 'canary-015', 'dddd-015', 1665, 16666666665);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (16, x'', 16, 'canary-016', 'dddd-016', 1776, 17777777776);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (17, x'', 17, 'canary-017', 'dddd-017', 1887, 18888888887);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (18, x'', 18, 'canary-018', 'dddd-018', 1998, 19999999998);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (19, x'', 19, 'canary-019', 'dddd-019', 2109, 21111111109);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (20, x'', 20, 'canary-020', 'dddd-020', 2220, 22222222220);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (21, x'', 21, 'canary-021', 'dddd-021', 2331, 23333333331);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (22, x'', 22, 'canary-022', 'dddd-022', 2442, 24444444442);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (23, x'', 23, 'canary-023', 'dddd-023', 2553, 25555555553);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (24, x'', 24, 'canary-024', 'dddd-024', 2664, 26666666664);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (1, x'', 1, 'canary-001', 'dddd-001', 111, 1111111111);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (2, x'', 2, 'canary-002', 'dddd-002', 222, 2222222222);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (3, x'', 3, 'canary-003', 'dddd-003', 333, 3333333333);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (4, x'', 4, 'canary-004', 'dddd-004', 444, 4444444444);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (5, x'', 5, 'canary-005', 'dddd-005', 555, 5555555555);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (6, x'', 6, 'canary-006', 'dddd-006', 666, 6666666666);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (7, x'', 7, 'canary-007', 'dddd-007', 777, 7777777777);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (8, x'', 8, 'canary-008', 'dddd-008', 888, 8888888888);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (9, x'', 9, 'canary-009', 'dddd-009', 999, 9999999999);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (10, x'', 10, 'canary-010', 'dddd-010', 1110, 11111111110);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (11, x'', 11, 'canary-011', 'dddd-011', 1221, 12222222221);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (12, x'', 12, 'canary-012', 'dddd-012', 1332, 13333333332);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (13, x'', 13, 'canary-013', 'dddd-013', 1443, 14444444443);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (14, x'', 14, 'canary-014', 'dddd-014', 1554, 15555555554);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (15, x'', 15, 'canary-015', 'dddd-015', 1665, 16666666665);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (16, x'', 16, 'canary-016', 'dddd-016', 1776, 17777777776);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (17, x'', 17, 'canary-017', 'dddd-017', 1887, 18888888887);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (18, x'', 18, 'canary-018', 'dddd-018', 1998, 19999999998);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (19, x'', 19, 'canary-019', 'dddd-019', 2109, 21111111109);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (20, x'', 20, 'canary-020', 'dddd-020', 2220, 22222222220);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (21, x'', 21, 'canary-021', 'dddd-021', 2331, 23333333331);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (22, x'', 22, 'canary-022', 'dddd-022', 2442, 24444444442);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (23, x'', 23, 'canary-023', 'dddd-023', 2553, 25555555553);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (24, x'', 24, 'canary-024', 'dddd-024', 2664, 26666666664);
ALTER TABLE tab_tucz_333_algo MODIFY v VARBINARY(1) NULL FIRST, ADD KEY idx_tucz_333_v (v), ALGORITHM=COPY;
-- post-first-upgrade target-boundary data
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (101, NULL, 101, 'canary-101', 'dddd-101', 11211, 112222222211);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (102, x'01', 102, 'canary-102', 'dddd-102', 11322, 113333333322);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (103, x'7f', 103, 'canary-103', 'dddd-103', 11433, 114444444433);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (104, x'ff', 104, 'canary-104', 'dddd-104', 11544, 115555555544);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (105, NULL, 105, 'canary-105', 'dddd-105', 11655, 116666666655);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (106, x'01', 106, 'canary-106', 'dddd-106', 11766, 117777777766);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (107, x'7f', 107, 'canary-107', 'dddd-107', 11877, 118888888877);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (108, x'ff', 108, 'canary-108', 'dddd-108', 11988, 119999999988);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (109, NULL, 109, 'canary-109', 'dddd-109', 12099, 121111111099);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (110, x'01', 110, 'canary-110', 'dddd-110', 12210, 122222222210);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (111, x'7f', 111, 'canary-111', 'dddd-111', 12321, 123333333321);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (112, x'ff', 112, 'canary-112', 'dddd-112', 12432, 124444444432);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (113, NULL, 113, 'canary-113', 'dddd-113', 12543, 125555555543);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (114, x'01', 114, 'canary-114', 'dddd-114', 12654, 126666666654);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (115, x'7f', 115, 'canary-115', 'dddd-115', 12765, 127777777765);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (116, x'ff', 116, 'canary-116', 'dddd-116', 12876, 128888888876);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (117, NULL, 117, 'canary-117', 'dddd-117', 12987, 129999999987);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (118, x'01', 118, 'canary-118', 'dddd-118', 13098, 131111111098);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (119, x'7f', 119, 'canary-119', 'dddd-119', 13209, 132222222209);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (120, x'ff', 120, 'canary-120', 'dddd-120', 13320, 133333333320);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (121, NULL, 121, 'canary-121', 'dddd-121', 13431, 134444444431);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (122, x'01', 122, 'canary-122', 'dddd-122', 13542, 135555555542);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (123, x'7f', 123, 'canary-123', 'dddd-123', 13653, 136666666653);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (124, x'ff', 124, 'canary-124', 'dddd-124', 13764, 137777777764);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (101, NULL, 101, 'canary-101', 'dddd-101', 11211, 112222222211);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (102, x'01', 102, 'canary-102', 'dddd-102', 11322, 113333333322);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (103, x'7f', 103, 'canary-103', 'dddd-103', 11433, 114444444433);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (104, x'ff', 104, 'canary-104', 'dddd-104', 11544, 115555555544);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (105, NULL, 105, 'canary-105', 'dddd-105', 11655, 116666666655);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (106, x'01', 106, 'canary-106', 'dddd-106', 11766, 117777777766);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (107, x'7f', 107, 'canary-107', 'dddd-107', 11877, 118888888877);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (108, x'ff', 108, 'canary-108', 'dddd-108', 11988, 119999999988);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (109, NULL, 109, 'canary-109', 'dddd-109', 12099, 121111111099);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (110, x'01', 110, 'canary-110', 'dddd-110', 12210, 122222222210);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (111, x'7f', 111, 'canary-111', 'dddd-111', 12321, 123333333321);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (112, x'ff', 112, 'canary-112', 'dddd-112', 12432, 124444444432);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (113, NULL, 113, 'canary-113', 'dddd-113', 12543, 125555555543);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (114, x'01', 114, 'canary-114', 'dddd-114', 12654, 126666666654);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (115, x'7f', 115, 'canary-115', 'dddd-115', 12765, 127777777765);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (116, x'ff', 116, 'canary-116', 'dddd-116', 12876, 128888888876);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (117, NULL, 117, 'canary-117', 'dddd-117', 12987, 129999999987);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (118, x'01', 118, 'canary-118', 'dddd-118', 13098, 131111111098);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (119, x'7f', 119, 'canary-119', 'dddd-119', 13209, 132222222209);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (120, x'ff', 120, 'canary-120', 'dddd-120', 13320, 133333333320);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (121, NULL, 121, 'canary-121', 'dddd-121', 13431, 134444444431);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (122, x'01', 122, 'canary-122', 'dddd-122', 13542, 135555555542);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (123, x'7f', 123, 'canary-123', 'dddd-123', 13653, 136666666653);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (124, x'ff', 124, 'canary-124', 'dddd-124', 13764, 137777777764);
ALTER TABLE tab_tucz_333_algo MODIFY v VARBINARY(2) NULL FIRST, ALGORITHM=COPY;
-- post-second-upgrade final-boundary data
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (201, NULL, 201, 'canary-201', 'dddd-201', 22311, 223333333311);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (202, x'0101', 202, 'canary-202', 'dddd-202', 22422, 224444444422);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (203, x'7f7f', 203, 'canary-203', 'dddd-203', 22533, 225555555533);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (204, x'ffff', 204, 'canary-204', 'dddd-204', 22644, 226666666644);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (205, NULL, 205, 'canary-205', 'dddd-205', 22755, 227777777755);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (206, x'0101', 206, 'canary-206', 'dddd-206', 22866, 228888888866);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (207, x'7f7f', 207, 'canary-207', 'dddd-207', 22977, 229999999977);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (208, x'ffff', 208, 'canary-208', 'dddd-208', 23088, 231111111088);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (209, NULL, 209, 'canary-209', 'dddd-209', 23199, 232222222199);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (210, x'0101', 210, 'canary-210', 'dddd-210', 23310, 233333333310);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (211, x'7f7f', 211, 'canary-211', 'dddd-211', 23421, 234444444421);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (212, x'ffff', 212, 'canary-212', 'dddd-212', 23532, 235555555532);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (213, NULL, 213, 'canary-213', 'dddd-213', 23643, 236666666643);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (214, x'0101', 214, 'canary-214', 'dddd-214', 23754, 237777777754);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (215, x'7f7f', 215, 'canary-215', 'dddd-215', 23865, 238888888865);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (216, x'ffff', 216, 'canary-216', 'dddd-216', 23976, 239999999976);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (217, NULL, 217, 'canary-217', 'dddd-217', 24087, 241111111087);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (218, x'0101', 218, 'canary-218', 'dddd-218', 24198, 242222222198);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (219, x'7f7f', 219, 'canary-219', 'dddd-219', 24309, 243333333309);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (220, x'ffff', 220, 'canary-220', 'dddd-220', 24420, 244444444420);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (221, NULL, 221, 'canary-221', 'dddd-221', 24531, 245555555531);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (222, x'0101', 222, 'canary-222', 'dddd-222', 24642, 246666666642);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (223, x'7f7f', 223, 'canary-223', 'dddd-223', 24753, 247777777753);
INSERT INTO tab_tucz_333_ref (id,v,fk_col,c,d,e,f) VALUES (224, x'ffff', 224, 'canary-224', 'dddd-224', 24864, 248888888864);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (201, NULL, 201, 'canary-201', 'dddd-201', 22311, 223333333311);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (202, x'0101', 202, 'canary-202', 'dddd-202', 22422, 224444444422);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (203, x'7f7f', 203, 'canary-203', 'dddd-203', 22533, 225555555533);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (204, x'ffff', 204, 'canary-204', 'dddd-204', 22644, 226666666644);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (205, NULL, 205, 'canary-205', 'dddd-205', 22755, 227777777755);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (206, x'0101', 206, 'canary-206', 'dddd-206', 22866, 228888888866);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (207, x'7f7f', 207, 'canary-207', 'dddd-207', 22977, 229999999977);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (208, x'ffff', 208, 'canary-208', 'dddd-208', 23088, 231111111088);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (209, NULL, 209, 'canary-209', 'dddd-209', 23199, 232222222199);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (210, x'0101', 210, 'canary-210', 'dddd-210', 23310, 233333333310);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (211, x'7f7f', 211, 'canary-211', 'dddd-211', 23421, 234444444421);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (212, x'ffff', 212, 'canary-212', 'dddd-212', 23532, 235555555532);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (213, NULL, 213, 'canary-213', 'dddd-213', 23643, 236666666643);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (214, x'0101', 214, 'canary-214', 'dddd-214', 23754, 237777777754);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (215, x'7f7f', 215, 'canary-215', 'dddd-215', 23865, 238888888865);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (216, x'ffff', 216, 'canary-216', 'dddd-216', 23976, 239999999976);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (217, NULL, 217, 'canary-217', 'dddd-217', 24087, 241111111087);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (218, x'0101', 218, 'canary-218', 'dddd-218', 24198, 242222222198);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (219, x'7f7f', 219, 'canary-219', 'dddd-219', 24309, 243333333309);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (220, x'ffff', 220, 'canary-220', 'dddd-220', 24420, 244444444420);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (221, NULL, 221, 'canary-221', 'dddd-221', 24531, 245555555531);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (222, x'0101', 222, 'canary-222', 'dddd-222', 24642, 246666666642);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (223, x'7f7f', 223, 'canary-223', 'dddd-223', 24753, 247777777753);
INSERT INTO tab_tucz_333_algo (id,v,fk_col,c,d,e,f) VALUES (224, x'ffff', 224, 'canary-224', 'dddd-224', 24864, 248888888864);
-- deterministic assertions
SELECT CASE WHEN NOT EXISTS ((SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucz_333_ref' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucz_333_algo') UNION ALL (SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucz_333_algo' EXCEPT SELECT column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='tab_tucz_333_ref') LIMIT 1) THEN 'TUCZ-000333|SCHEMA|OK' ELSE 'TUCZ-000333|SCHEMA|FAIL' END;
SELECT CASE WHEN NOT EXISTS (SELECT 1 FROM tab_tucz_333_ref r LEFT JOIN tab_tucz_333_algo a USING(id) WHERE a.id IS NULL UNION ALL SELECT 1 FROM tab_tucz_333_algo a LEFT JOIN tab_tucz_333_ref r USING(id) WHERE r.id IS NULL UNION ALL SELECT 1 FROM tab_tucz_333_ref r JOIN tab_tucz_333_algo a USING(id) WHERE NOT (r.v <=> a.v AND r.fk_col <=> a.fk_col AND r.c <=> a.c AND r.d <=> a.d AND r.e <=> a.e AND r.f <=> a.f) LIMIT 1) THEN 'TUCZ-000333|DATA|OK' ELSE 'TUCZ-000333|DATA|FAIL' END;
SELECT CASE WHEN NOT EXISTS ((SELECT index_name, non_unique, seq_in_index, column_name, collation, sub_part, packed, nullable, index_type, comment, index_comment, expression FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='tab_tucz_333_ref' EXCEPT SELECT index_name, non_unique, seq_in_index, column_name, collation, sub_part, packed, nullable, index_type, comment, index_comment, expression FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='tab_tucz_333_algo') UNION ALL (SELECT index_name, non_unique, seq_in_index, column_name, collation, sub_part, packed, nullable, index_type, comment, index_comment, expression FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='tab_tucz_333_algo' EXCEPT SELECT index_name, non_unique, seq_in_index, column_name, collation, sub_part, packed, nullable, index_type, comment, index_comment, expression FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='tab_tucz_333_ref') LIMIT 1) THEN 'TUCZ-000333|INDEX|OK' ELSE 'TUCZ-000333|INDEX|FAIL' END;
SELECT CASE WHEN EXISTS (SELECT 1 FROM information_schema.REFERENTIAL_CONSTRAINTS WHERE constraint_schema=DATABASE() AND constraint_name='fk_tucz_333_ref' AND table_name='tab_tucz_333_ref' AND referenced_table_name='tab_tucz_333_parent') AND EXISTS (SELECT 1 FROM information_schema.REFERENTIAL_CONSTRAINTS WHERE constraint_schema=DATABASE() AND constraint_name='fk_tucz_333_algo' AND table_name='tab_tucz_333_algo' AND referenced_table_name='tab_tucz_333_parent') THEN 'TUCZ-000333|FK|OK' ELSE 'TUCZ-000333|FK|FAIL' END;
-- final cleanup
DROP TABLE IF EXISTS tab_tucz_333_algo;
DROP TABLE IF EXISTS tab_tucz_333_ref;
DROP TABLE IF EXISTS tab_tucz_333_parent;
