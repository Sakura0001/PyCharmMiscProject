DROP TYPE IF EXISTS composite_type CASCADE;
CREATE TYPE composite_type AS (
    id_col       INT4,
    varchar_col      VARCHAR(255),
    text_col   TEXT
);

DROP TYPE IF EXISTS enum_type CASCADE;
CREATE TYPE enum_type AS ENUM ('INIT', 'RUNNING', 'SUCCESS', 'FAILED');

DROP TABLE IF EXISTS tbl_composite_index;
CREATE TABLE tbl_composite_index
(
    id_col                      INT4 GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    smallint_col            SMALLINT,
    integer_col             INTEGER,
    bigint_col              BIGINT,
    numeric_col             NUMERIC(16,4),
    real_col                REAL,
    double_col              DOUBLE PRECISION,
    money_col               MONEY,
    char_col                CHAR(20),
    character_col           CHARACTER(20),
    varchar_col             VARCHAR(100),
    character_varying_col   CHARACTER VARYING(100),
    text_col                TEXT,
    bpchar_col              BPCHAR(20),
    boolean_col             BOOLEAN,
    bytea_col               BYTEA,
    date_col                DATE,
    time_col                TIME,
    timetz_col              TIMETZ,
    timestamp_col           TIMESTAMP,
    timestamptz_col         TIMESTAMPTZ,
    interval_col            INTERVAL,
    inet_col                INET,
    cidr_col                CIDR,
    macaddr_col             MACADDR,
    macaddr8_col            MACADDR8,
    bit_col                 BIT(8),
    varbit_col              VARBIT(32),
    tsvector_col            TSVECTOR,
    tsquery_col             TSQUERY,
    json_col                JSON,
    jsonb_col               JSONB,
    uuid_col                UUID,
    xml_col                 XML,
    point_col               POINT,
    line_col                LINE,
    lseg_col                LSEG,
    box_col                 BOX,
    path_col                PATH,
    polygon_col             POLYGON,
    circle_col              CIRCLE,
    int4range_col           INT4RANGE,
    int8range_col           INT8RANGE,
    numrange_col            NUMRANGE,
    tsrange_col             TSRANGE,
    tstzrange_col           TSTZRANGE,
    daterange_col           DATERANGE,
    int_array_col           INT4[],
    text_array_col          TEXT[],
    varchar_array_col       VARCHAR[],
    pg_lsn_col              PG_LSN,
    oid_col                 OID,
    tid_col                 TID,
    xid_col                 XID,
    xid8_col                XID8,
    cid_col                 CID,
    name_col                NAME,
    composite_type_col      composite_type,
	 enum_col                enum_type
);


ALTER TABLE tbl_composite_index ADD COLUMN composite_tsv tsvector GENERATED ALWAYS AS (to_tsvector('english',coalesce((composite_type_col).c_name, '') || ' ' ||  coalesce((composite_type_col).c_content, ''))) STORED;
CREATE INDEX idx_composite_fulltext_31 ON tbl_composite_index USING gin (composite_tsv);
CREATE INDEX idx_btree_integer_31 ON tbl_composite_index USING btree (integer_col);
CREATE UNIQUE INDEX idx_btree_uuid_31 ON tbl_composite_index USING btree (uuid_col);
CREATE INDEX idex_btree_boolean_31 ON tbl_composite_index USING btree(boolean_col);

CREATE INDEX idx_hash_varchar_31 ON tbl_composite_index USING hash (varchar_col);
CREATE INDEX idx_gist_point_31 ON tbl_composite_index USING gist (point_col);
CREATE INDEX idx_gist_box_31 ON tbl_composite_index USING gist (box_col);

CREATE INDEX idx_spgist_inet_31 ON tbl_composite_index USING spgist (inet_col);
CREATE INDEX idx_gin_tsvector_31 ON tbl_composite_index USING gin (tsvector_col);
CREATE INDEX idx_gin_jsonb_31 ON tbl_composite_index USING gin (jsonb_col);
CREATE INDEX idx_gin_int_array_31 ON tbl_composite_index USING gin (int_array_col);
CREATE INDEX idx_gin_money_31 on tbl_composite_index USING gin(text_array_col);
CREATE INDEX idx_brin_id_31 ON tbl_composite_index USING brin (id);
CREATE INDEX idx_brin_timestamp_31 ON tbl_composite_index USING brin (timestamp_col);
CREATE INDEX idx_composite_c_id_31 ON tbl_composite_index USING btree (composite_type_col);
CREATE UNIQUE INDEX idx_unique_uuid_31 ON tbl_composite_index USING btree (uuid_col);
CREATE INDEX idx_sort_uuid_31 ON tbl_composite_index USING btree (uuid_col ASC NULLS LAST);
CREATE INDEX idx_comb_pglsn_boolean_31 ON tbl_composite_index USING btree (pg_lsn_col, boolean_col);
CREATE INDEX idx_comb_ts_bit_enum_31 ON tbl_composite_index USING btree (tsvector_col, varbit_col, enum_col);
CREATE INDEX idx_comb_bit_enum_text_31 ON tbl_composite_index USING btree (varbit_col, boolean_col,enum_col);

DROP PROCEDURE IF EXISTS insert_full_test_data();
CREATE OR REPLACE PROCEDURE insert_full_test_data()
LANGUAGE plpgsql
AS $$
DECLARE i INT;
BEGIN
    FOR i IN 1..10000 LOOP
        INSERT INTO tbl_composite_index (
            smallint_col, integer_col, bigint_col, numeric_col, real_col, double_col, money_col,
            char_col, character_col, varchar_col, character_varying_col, text_col, bpchar_col,
            boolean_col, bytea_col, date_col, time_col, timetz_col, timestamp_col, timestamptz_col, interval_col,
            inet_col, cidr_col, macaddr_col, macaddr8_col, bit_col, varbit_col,
            tsvector_col, tsquery_col, json_col, jsonb_col, uuid_col, xml_col,
            point_col, line_col, lseg_col, box_col, path_col, polygon_col, circle_col,
            int4range_col, int8range_col, numrange_col, tsrange_col, tstzrange_col, daterange_col,
            int_array_col, text_array_col, varchar_array_col,
            pg_lsn_col, oid_col, tid_col, xid_col, xid8_col, cid_col, name_col,
            composite_type_col, enum_col
        ) VALUES (
            (i % 32767)::SMALLINT, i, i::BIGINT, (i * 1.2345)::NUMERIC(16,4), i::REAL, i::DOUBLE PRECISION, (i * 0.5)::MONEY,
            'CHAR' || i, 'CHAR' || i, 'VARCHAR' || i, 'C_VARYING' || i, 'test data', 'BPCHAR' || i,
            (i % 2) = 0, '\x00',
            CURRENT_DATE,
            LOCALTIME,
            LOCALTIME,
            LOCALTIMESTAMP,
            LOCALTIMESTAMP,
            INTERVAL '1 hour',
            '127.0.0.1', '127.0.0.0/24',
            '00:11:22:33:44:55', '00:11:22:33:44:55:66:77',
            B'00000000', B'00000000',
            to_tsvector('english', 'test'), to_tsquery('english', 'test'),
            '{}', '{}',
            uuid_in(md5(i::text)::cstring),
            NULL,
            POINT(0,0), LINE('(0,0),(1,1)'), LSEG('(0,0),(1,1)'), BOX('(0,0),(1,1)'),
            PATH('(0,0)'), POLYGON('(0,0),(1,1)'), CIRCLE('(0,0),1'),
            INT4RANGE(1,10), INT8RANGE(1,10), NUMRANGE(1,10),
            TSRANGE(LOCALTIMESTAMP, LOCALTIMESTAMP),
            TSTZRANGE(LOCALTIMESTAMP, LOCALTIMESTAMP),
            DATERANGE(CURRENT_DATE, CURRENT_DATE),
            ARRAY[1,2], ARRAY['test'], ARRAY['demo'],
            NULL, NULL, NULL, NULL, NULL, NULL,
            'test_name',
            (i, 'name_'||i, 'full text test content'),
            CASE i%4
                WHEN 0 THEN 'INIT'::enum_type
                WHEN 1 THEN 'RUNNING'::enum_type
                WHEN 2 THEN 'SUCCESS'::enum_type
                ELSE 'FAILED'::enum_type
            END
        );
    END LOOP;
END;
$$;

-- 执行插入
CALL insert_full_test_data();


CREATE INDEX idx_bit_enum_31 ON tbl_composite_index USING btree (bit_col,tsquery_col,enum_col);